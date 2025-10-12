

# **基于archive-pdf-tools的职称申报PDF文件自动化压缩与拆分策略研究报告**

## **第一部分：执行摘要与基本概念**

本报告旨在为一项特定职称申报工作提供一个技术解决方案，核心目标是开发一个基于Python的命令行工具，用于在WSL/Ubuntu 24.04环境下对PDF文件进行自动化压缩与拆分。该工具旨在确保所有提交的PDF文件均满足小于2MB的硬性大小限制，同时在可能的情况下最大化文件质量，并在必要时将单个文件拆分为至多四个符合大小限制的部分。

### **1.1 项目任务与战略目标**

项目的核心任务是创建一个自动化辅助工具，以应对职称申报中对PDF附件的严格要求。具体需求可归纳如下：

* **核心功能**：将输入的单个或批量PDF文件压缩至指定大小（默认为2MB）。  
* **输入方式**：支持单个文件路径和整个目录作为输入。  
* **分层策略**：根据源文件的大小，采用不同的压缩策略，以平衡文件质量和大小。  
* **拆分机制**：当无法在可接受的质量范围内将单个文件压缩至目标大小时，自动将其拆分为多个（最多四个）符合大小要求的文件。  
* **技术栈**：项目指定在WSL/Ubuntu 24.04环境下，利用archive-pdf-tools工具集中的recode\_pdf命令作为核心压缩引擎。

### **1.2 核心技术澄清：recode\_pdf作为重建引擎而非压缩工具**

在深入探讨具体策略之前，必须澄清一个关于核心工具recode\_pdf的关键概念。项目初步分析认为recode\_pdf是一个直接的PDF压缩工具，即输入一个PDF，输出一个更小的PDF。然而，深入研究其工作原理后发现，这种理解并不完全准确。recode\_pdf的本质是一个**PDF重建引擎**，而非一个简单的文件压缩器 1。

它的主要工作流程并非直接修改输入的PDF，而是基于一组光栅图像（如TIFF、JPEG2000）和一个包含文本内容及坐标信息的hOCR文件，来从零开始构建一个全新的、高度优化的PDF文件 1。recode\_pdf利用混合光栅内容（Mixed Raster Content, MRC）压缩技术，将页面分离为高分辨率的前景层（文本、线条）和低分辨率的背景层（图片、渐变），从而实现极高的压缩率 1。

虽然recode\_pdf提供了一个--from-pdf选项，看似可以直接处理PDF，但其官方文档明确指出该功能“未经充分测试”（not well tested），在处理每页包含多个图像或复杂布局的PDF时，其稳定性和效果均无法保证 1。因此，对于一个要求稳定可靠的生产力工具而言，依赖此实验性功能是不可取的。

### **1.3 “解构-分析-重建”（DAR）三阶段处理流程**

基于对recode\_pdf工作原理的正确理解，一个稳健的解决方案必须采用一个多阶段的处理流程。本报告提出一个名为“解构-分析-重建”（Deconstruct-Analyze-Reconstruct, DAR）的三阶段架构，作为整个项目的技术基石。

1. **解构（Deconstruction）**：此阶段的目标是将源PDF的每一页转换为高质量的光栅图像。这是后续所有处理的基础。图像的分辨率和格式将直接影响最终输出的质量。  
2. **分析（Analysis）**：此阶段对解构出的图像进行光学字符识别（OCR），生成hOCR（HTML-based OCR）格式的文件。hOCR文件不仅包含识别出的文本，还精确记录了每个字符、单词和行的位置坐标，这是重建可搜索、可复制文本层的关键 1。  
3. **重建（Reconstruction）**：这是最后也是最核心的阶段。利用recode\_pdf命令，将前两个阶段生成的图像序列和hOCR文件作为输入，通过MRC技术重建出一个全新的、高度压缩且符合PDF/A和PDF/UA标准的PDF文件 1。

这个DAR流程虽然比直接压缩更为复杂，涉及更多的中间步骤和依赖工具，但它完全符合recode\_pdf的设计哲学，能够最大程度地发挥其压缩潜力，并确保输出文件的质量和合规性。这一架构的转变，意味着项目需要管理的不仅仅是recode\_pdf本身，而是一个由多个命令行工具组成的完整处理链。

### **1.4 报告结构与导航**

本报告的后续部分将围绕DAR架构展开，从工具链的深度分析到核心算法的设计，再到具体的Python实现蓝图，最后探讨高级调优技巧和项目总结。报告将系统性地阐述如何构建一个能够满足所有需求的、强大而可靠的自动化工具。

## **第二部分：核心工具链深度分析**

实现DAR流程需要一个协同工作的工具链。本节将对构成该流程的每个关键命令行工具进行详细的技术审查，阐明其在流程中的角色、选择该工具的理由，并深入探讨与本项目直接相关的命令和参数。

### **2.1 解构阶段：pdftoppm (来自 poppler-utils)**

* **角色**：在DAR流程的第一阶段，pdftoppm负责将输入的PDF文件逐页转换为光栅图像。这些图像是后续OCR分析和最终PDF重建的唯一素材来源。  
* **选择理由**：在众多PDF到图像的转换工具中（如pdfimages或Ghostscript），pdftoppm因其对输出参数的精确控制而被选中。特别是其-r参数，可以直接指定输出图像的DPI（每英寸点数），这对于控制图像质量和文件大小的初始平衡至关重要。此外，它支持多种输出格式（如TIFF、PNG、JPEG），其中TIFF格式因其无损压缩特性，成为进行高质量OCR前的理想选择。  
* **关键命令语法**：  
  * **基本用法**：pdftoppm \-tiff \-r 300 input.pdf output\_prefix  
  * **参数详解**：  
    * \-tiff: 指定输出格式为TIFF。TIFF格式能无损地保存图像信息，确保OCR的准确性。  
    * \-r \<dpi\>: 设置输出图像的分辨率。这是控制质量与大小的第一个杠杆。一个较高的初始值（如300 DPI）是保证文本清晰度的基础 3。  
    * input.pdf: 源PDF文件。  
    * output\_prefix: 输出图像文件的前缀。pdftoppm会自动为每一页生成带序号的文件，例如output\_prefix-01.tif, output\_prefix-02.tif等。

### **2.2 分析阶段：tesseract OCR引擎**

* **角色**：在分析阶段，tesseract负责处理由pdftoppm生成的图像，并提取文本信息。其关键任务是生成recode\_pdf所必需的hOCR文件。  
* **选择理由**：Tesseract是目前最先进、应用最广泛的开源OCR引擎之一，由Google维护。它支持多种语言，并且能够输出hOCR格式。hOCR是一种基于HTML的开放标准，它不仅包含了识别出的文本，还通过HTML标签精确地标记了文本块、段落、行、单词和字符的边界框（bounding box）坐标 4。这些精确的坐标信息是recode\_pdf能够将文本层完美地叠加在背景图像之上，从而生成可搜索PDF的基础 1。  
* **关键命令语法**：  
  * **基本用法**：tesseract input\_image.tif output\_hocr \-l chi\_sim hocr  
  * **参数详解**：  
    * input\_image.tif: 输入的单页图像文件。  
    * output\_hocr: 输出的hOCR文件名前缀（会自动添加.hocr扩展名）。  
    * \-l \<lang\>: 指定识别语言。对于中文文档，应使用chi\_sim（简体中文）或chi\_tra（繁体中文）。  
    * hocr: 指定输出格式为hOCR。

### **2.3 重建阶段：recode\_pdf (来自 archive-pdf-tools)**

* **角色**：作为DAR流程的最后一环，recode\_pdf是实现高压缩率的核心。它接收图像序列和hOCR文件，利用MRC技术生成最终的PDF文件。  
* **MRC技术简介**：混合光栅内容（MRC）模型是一种先进的图像分割和压缩技术。它将一页内容智能地分解为三个部分：  
  1. **背景层（Background Layer）**：包含页面上的所有彩色图像、照片和渐变背景。这一层通常会被大幅度降采样并使用有损压缩（如JPEG2000），因为它对视觉细节的要求不高 1。  
  2. **前景层（Foreground Layer）**：包含文本和线条艺术等高频信息。这一层通常也使用有损压缩，但分辨率相对较高。  
  3. 二值掩码层（Binary Mask Layer）：这是一个高分辨率的黑白图像，精确地定义了前景层中哪些像素是可见的（即文本和线条的形状）。这一层使用无损压缩算法（如JBIG2或CCITT G4），以确保文本边缘的锐利度 1。  
     recode\_pdf将这三层在最终的PDF页面中叠加起来，从而在保持文本极高清晰度的同时，大幅压缩背景图像的大小，实现整体文件尺寸的显著减小。  
* **关键参数深度解析**：  
  * \--dpi \<int\>: 指定输入图像的分辨率。这个值应与pdftoppm生成图像时使用的DPI保持一致。它直接决定了掩码层和前景层的基准分辨率，是影响文本清晰度的最重要参数 1。  
  * \--bg-downsample \<int\>: 背景层降采样因子。这是控制文件大小的关键参数。一个为N的值意味着背景层的分辨率将被降低为dpi / N。例如，--dpi 300和--bg-downsample 3将使得背景层的有效分辨率为100 DPI，而前景文本仍然保持300 DPI的清晰度。这是在不牺牲文本可读性的前提下减小文件体积的最有效手段 1。  
  * \--mask-compression \<jbig2|ccitt\>: 指定掩码层的压缩算法。jbig2提供比ccitt更高的无损压缩率，但历史上存在一些专利问题（尽管多数已过期）。ccitt（通常指CCITT Group 4）是一个广泛支持且无专利问题的传真压缩标准，作为备选方案，压缩效果稍逊于jbig2 6。  
  * \--from-imagestack '\<glob\>': 指定输入的图像文件序列。它接受一个glob模式，例如'temp\_dir/page-\*.tif'，来匹配所有页面图像 1。  
  * \--hocr-file \<file\>: 指定由tesseract生成的hOCR文件。

### **2.4 应急预案：qpdf 用于PDF拆分与处理**

* **角色**：当所有压缩尝试都失败，无法在质量底线之上将文件压缩到目标大小时，qpdf将作为应急工具，负责对PDF文件进行精确的页面拆分。  
* **选择理由**：在Linux命令行环境下，有多种工具可以处理PDF拆分，如pdftk、Ghostscript和pdfseparate。选择qpdf是基于以下几点综合考量：  
  * **现代且活跃**：qpdf是一个仍在积极开发和维护的项目，与许多Linux发行版的最新版本兼容性良好。  
  * **官方仓库支持**：qpdf是Ubuntu 24.04标准软件源的一部分，安装简便 (sudo apt install qpdf)。相比之下，pdftk已从许多主流发行版的官方源中移除，需要通过snap或编译Java版本来安装，增加了部署复杂性 7。  
  * **强大的语法**：qpdf提供了非常清晰和强大的页面选择语法，可以轻松地从一个或多个文件中提取任意页面范围，并生成新的PDF文件，这正是本项目拆分逻辑所需要的 7。  
  * **性能**：虽然在某些特定场景下pdftk或Ghostscript可能更快，但qpdf在内容保留和元数据处理方面表现出色，且对于本项目涉及的文件大小和操作，其性能完全足够 8。  
* **关键命令语法**：  
  * **提取页面范围**：qpdf input.pdf \--pages. \<start\>-\<end\> \-- output.pdf  
  * **参数详解**：  
    * \--pages. \<start\>-\<end\>: 这是qpdf页面选择的核心。.代表输入文件本身，避免重复书写文件名。\<start\>-\<end\>定义了要提取的页面范围（包含首尾）。  
    * \--: 分隔符，用于将页面选择参数与输出文件名清晰地分开 7。  
  * **示例**：要从一个名为document.pdf的文件中提取第1到10页，生成part1.pdf，命令为：qpdf document.pdf \--pages. 1-10 \-- part1.pdf。

### **表1：核心工具链组件分析**

| 工具名称 | 所属软件包 | 在流程中的主要角色 | 关键命令/参数 | 示例用法 |
| :---- | :---- | :---- | :---- | :---- |
| pdftoppm | poppler-utils | **解构**：将PDF页面转换为光栅图像 | \-r \<dpi\>, \-tiff, \-png | pdftoppm \-tiff \-r 300 in.pdf out\_prefix |
| tesseract | tesseract-ocr | **分析**：从图像中进行OCR并生成hOCR文件 | \<input\> \<output\>, \-l \<lang\>, hocr | tesseract page-01.tif page-01 \-l chi\_sim hocr |
| recode\_pdf | archive-pdf-tools | **重建**：基于图像和hOCR重建高压缩PDF | \--from-imagestack, \--hocr-file, \--dpi, \--bg-downsample | recode\_pdf \--from-imagestack 'imgs/\*.tif' \--hocr-file data.hocr \--dpi 300 \--bg-downsample 3 \-o out.pdf |
| qpdf | qpdf | **应急拆分**：当压缩失败时，按页码拆分PDF | \--pages. \<start\>-\<end\> \-- | qpdf in.pdf \--pages. 1-10 \-- part1.pdf |

## **第三部分：核心算法：分层策略与迭代优化**

本项目的“智能”体现在其核心算法中，该算法将用户定义的分层需求转化为一个确定性的、可执行的程序逻辑。它不仅定义了处理不同大小文件的策略，还设计了一个迭代优化循环，以在质量和大小之间寻找最佳平衡点。

### **3.1 定义处理层级**

根据输入PDF文件的大小（记为 ），算法将文件归入以下四个处理层级之一：

* **层级 0 (忽略)**：如果 ，文件已满足要求，无需任何处理，直接跳过。  
* **层级 1 (高质量压缩)**：如果 ，这类文件体积不大，压缩目标是在保证最高质量的前提下，将文件大小降至2MB以下。算法将从非常高的质量设置开始，并进行最少的参数调整。  
* **层级 2 (平衡压缩)**：如果 ，这类文件体积适中。主要目标仍然是在不拆分的情况下压缩到2MB以下。但与层级1不同，算法会更积极地降低质量参数，如果最终质量下降到不可接受的程度，则触发拆分机制。  
* **层级 3 (极限压缩)**：如果 ，这类文件体积很大。由于2MB和最多拆分4个文件的限制是硬性要求，算法将以满足这些限制为首要目标，质量成为次要考虑因素。压缩策略将非常激进，并且很可能直接启动拆分预案。

### **3.2 迭代优化循环：寻找最优参数的启发式搜索**

为了给每个文件找到最合适的压缩参数，本方案设计了一个迭代优化循环。这并非一个耗时的暴力搜索，而是一个从高质量到低质量的引导式下降过程，旨在以最少的尝试次数找到满足条件的参数组合。

**算法流程概述**：

1. **初始化**：根据文件所属的层级，选择一组初始的高质量参数。例如，对于层级1的文件，可以从dpi=300, bg-downsample=1开始。  
2. **执行DAR流程**：使用当前参数集，完整地执行一次“解构-分析-重建”流程，生成一个临时的输出PDF文件。  
3. **检查条件**：获取输出文件的大小，并与目标大小（2MB）进行比较。  
4. **判定成功/失败**：  
   * **成功**：如果输出文件大小小于等于目标大小，则认为找到了合适的参数。循环终止，该文件处理完毕。  
   * **失败**：如果输出文件仍然过大，则需要降低质量参数，进入下一步。  
5. **参数降级策略**：参数的降低遵循一个预定义的、旨在最小化质量损失的顺序。  
   * **优先增加背景降采样 (bg-downsample)**：首先，逐步增加bg-downsample的值（例如，从1到2，再到3，最高到4或5）。这一步通常能带来显著的文件大小缩减，而对文本清晰度的影响最小，因为只降低了背景图像的质量 1。  
   * **其次降低分辨率 (dpi)**：当bg-downsample达到其上限（或继续增加效果不明显）后，开始逐步降低dpi的值（例如，从300 DPI降至250 DPI，再到200 DPI）。降低DPI会同时影响前景和背景，对文本质量的冲击更直接，因此放在第二步 3。  
6. **循环或退出**：使用新的参数集，返回第2步，重复整个流程。如果参数已经降低到了预设的“质量底线”仍然无法满足大小要求，则循环终止，并判定为压缩失败。

### **3.3 定义质量底线**

为了防止算法无休止地降低质量，产生无法阅读的输出文件，必须设定一个“质量底线”。这个底线主要通过设定一个最低可接受的DPI值来体现，例如，min\_dpi=150。150 DPI通常被认为是屏幕阅读和非高质量打印的最低可接受分辨率 3。

当迭代优化循环中的dpi参数降低到这个值，并且bg-downsample也已达到上限，但生成的文件大小依然超标时，算法将停止进一步的压缩尝试。此时，对于配置为允许拆分的文件，将触发下一阶段的应急拆分协议。

### **表2：分层压缩策略矩阵**

下表将上述的分层逻辑和迭代策略具体化，形成一个清晰的、可直接用于编程实现的参数矩阵。

| 输入大小层级 | 主要目标 | 初始 dpi | 初始 bg-downsample | 参数迭代顺序 | 质量底线 (min\_dpi) | 压缩失败后操作 |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **层级 1** (2-10MB) | 尽可能高的质量 | 300 | 1 | 1\. 增 bg-downsample (至3) 2\. 降 dpi (至200) | 200 | 触发拆分 |
| **层级 2** (10-50MB) | 优先保证不拆分 | 300 | 2 | 1\. 增 bg-downsample (至4) 2\. 降 dpi (至150) | 150 | 触发拆分 |
| **层级 3** (\>50MB) | 满足大小和拆分数量限制 | 200 | 3 | 1\. 增 bg-downsample (至5) 2\. 降 dpi (至150) | 150 | 强制拆分（可接受质量损失） |

## **第四部分：应急协议：PDF拆分逻辑**

当一个文件经过迭代压缩后，仍然无法在质量底线之上满足大小要求时，应急拆分协议将被激活。这是确保所有文件最终都能提交的最后一道防线。

### **4.1 拆分的触发条件**

拆分协议的启动条件非常明确：当且仅当第三部分描述的迭代压缩循环因达到质量底线（min\_dpi）而终止，且最终生成的PDF文件大小依然超过2MB时。

这个触发机制对于不同层级的文件有不同的含义：

* 对于**层级1和层级2**的文件，触发拆分是为了**保护质量**，避免生成分辨率过低的文档。  
* 对于**层级3**的文件，触发拆分则是因为即使在最低质量设置下，**单个文件的体积也无法被压缩到2MB以下**。

### **4.2 计算拆分点**

拆分的核心约束是最多4个部分。算法需要智能地决定最佳的拆分数量（记为 ，其中 ）。

* 初始策略：基于页数的平均分配  
  对于一个总页数为 N 的PDF，算法首先会尝试最简单的 k=2 的拆分方案：  
  * 第一部分：第1页 到 第  页  
  * 第二部分：第  页 到 第  页  
* 引入预测性拆分启发式算法  
  一个简单的平均分配策略可能效率低下。例如，一个100MB的文件，拆分为两个50MB的部分后，每个部分仍然远大于压缩目标，直接对其中一个部分执行完整的、耗时的DAR压缩流程，结果很可能是失败。这将浪费大量计算资源。  
  为了优化这一过程，可以引入一个**预测性拆分启发式算法**。该算法根据原始文件大小来预估一个更合理的初始拆分数量 。  
  * 启发式规则：可以设定一个经验阈值，例如，认为一个25MB的PDF块是比较有希望被压缩到2MB的。那么初始拆分数量可以这样计算：

  * **应用**：对于一个100MB的文件，该公式会建议 。算法将直接尝试4路拆分，而不是从2路拆分开始，从而大大提高了效率。对于一个30MB的文件，公式建议 ，算法将从2路拆分开始。

### **4.3 迭代式拆分与处理**

拆分过程本身也是一个迭代验证的过程：

1. **选择拆分数量 k**：根据上一节的启发式算法确定一个初始的拆分数量 。  
2. **生成子文档**：使用qpdf将原始PDF按照  路拆分的页码范围，生成  个临时的PDF子文档。  
3. **验证第一个子文档**：选取第一个子文档（例如，页码范围为  到  的部分），对其执行完整的、使用最激进参数（例如dpi=150, bg-downsample=4）的DAR压缩流程。  
4. **评估结果**：  
   * **成功**：如果第一个子文档被成功压缩到2MB以下，那么可以乐观地认为其他大小相近的子文档也能成功。此时，脚本将继续处理剩余的  个子文档。  
   * **失败**：如果连第一个子文档都无法压缩达标，说明当前的拆分粒度仍然太大。算法将增加拆分数量（），只要 ，就返回第2步，重新生成更小的子文档并再次验证。  
5. **最终处理**：一旦找到了一个可行的拆分数量 ，使得所有子文档都能被成功压缩，整个拆分流程就宣告成功。如果尝试到  仍然失败，则报告该文件处理失败，需要人工干预。

### **4.4 拆分后文件管理**

成功拆分并压缩后，脚本必须负责清晰地管理输出文件和临时文件。

* **命名规范**：输出的多个文件需要有逻辑清晰的命名，以便用户理解它们的顺序。例如，对于源文件mydocument.pdf，拆分后的文件应命名为mydocument\_part1.pdf, mydocument\_part2.pdf,...。  
* **临时文件清理**：在整个拆分和压缩过程中，会产生大量的临时文件，包括：  
  * 由qpdf生成的未压缩的PDF子文档。  
  * 每个子文档解构出的所有页面图像。  
  * 每个子文档生成的hOCR文件。  
    脚本必须确保在处理完一个文件（无论成功或失败）后，所有相关的临时文件都被彻底删除，以避免占用不必要的磁盘空间。

## **第五部分：Python实现蓝图**

本节将提供一个具体的软件工程指南，用于构建这个PDF处理工具。内容包括推荐的项目结构、命令行接口设计，以及核心逻辑的伪代码实现。

### **5.1 推荐的项目结构**

一个清晰、模块化的项目结构对于代码的可维护性和可扩展性至关重要。推荐采用以下结构：

pdf-compressor/  
├── main.py             \# 主程序入口，负责解析命令行参数和分发任务  
├── compressor/  
│   ├── \_\_init\_\_.py  
│   ├── pipeline.py     \# 封装完整的DAR处理流程  
│   ├── strategy.py     \# 实现分层策略和迭代优化循环  
│   ├── splitter.py     \# 实现PDF拆分逻辑  
│   └── utils.py        \# 包含辅助函数，如文件大小获取、临时文件管理等  
├── tests/              \# 单元测试目录  
└── README.md           \# 项目说明文档

这种结构将不同的功能逻辑分离到不同的模块中，使得代码更易于理解和测试。

### **5.2 命令行接口（CLI）设计**

使用Python标准库中的argparse模块可以方便地构建一个功能强大且用户友好的命令行接口。

**设计的CLI参数**：

* \--input \<path\> (必需): 指定输入的源路径，可以是一个PDF文件或一个包含PDF文件的目录。  
* \--output-dir \<path\> (必需): 指定处理后文件的存放目录。  
* \--target-size \<int\> (可选): 指定目标文件大小，单位为MB。默认值为 2。  
* \--allow-splitting (可选): 一个布尔标志。如果提供此参数，则允许在压缩失败时启用拆分功能。默认为不启用。  
* \--max-splits \<int\> (可选): 允许的最大拆分数量。默认值为 4。

**示例调用**：

Bash

\# 处理单个文件，允许拆分  
python main.py \--input /path/to/large.pdf \--output-dir /path/to/output \--allow-splitting

\# 处理整个目录，使用默认设置  
python main.py \--input /path/to/source\_folder \--output-dir /path/to/output

### **5.3 核心逻辑伪代码**

以下伪代码勾勒了程序核心模块的实现逻辑，可作为编写Python代码的直接参考。

#### **main.py 的主逻辑**

Python

function main():  
    args \= parse\_command\_line\_arguments()

    if is\_directory(args.input):  
        pdf\_files \= find\_pdfs\_in\_directory(args.input)  
        for pdf\_file in pdf\_files:  
            process\_file(pdf\_file, args)  
    else:  
        process\_file(args.input, args)

#### **pipeline.py 的文件处理逻辑**

Python

function process\_file(file\_path, args):  
    original\_size\_mb \= get\_file\_size\_in\_mb(file\_path)

    if original\_size\_mb \< args.target\_size:  
        print(f"Skipping {file\_path}, already meets size requirement.")  
        \# Optionally, copy the file to the output directory  
        return

    tier \= determine\_tier(original\_size\_mb)  
    strategy\_params \= get\_strategy\_for\_tier(tier)

    \# 运行迭代压缩  
    success, result\_path \= run\_iterative\_compression(file\_path, strategy\_params, args)

    if success:  
        print(f"Successfully compressed {file\_path} to {result\_path}")  
    elif args.allow\_splitting:  
        print(f"Compression failed for {file\_path}. Attempting to split.")  
        run\_splitting\_protocol(file\_path, strategy\_params, args)  
    else:  
        print(f"Compression failed for {file\_path}. Splitting not enabled.")

#### **strategy.py 的迭代压缩逻辑**

Python

function run\_iterative\_compression(file\_path, strategy, args):  
    \# generate\_parameter\_sequence 会根据策略生成一系列 (dpi, bg\_downsample) 组合  
    for params in generate\_parameter\_sequence(strategy):  
        temp\_dir \= create\_temporary\_directory()  
        try:  
            \# 1\. 解构: 调用 pdftoppm  
            image\_files \= deconstruct\_pdf\_to\_images(file\_path, temp\_dir, params.dpi)

            \# 2\. 分析: 调用 tesseract  
            hocr\_file \= analyze\_images\_to\_hocr(image\_files, temp\_dir)

            \# 3\. 重建: 调用 recode\_pdf  
            output\_pdf\_path \= reconstruct\_pdf(image\_files, hocr\_file, temp\_dir, params)

            \# 4\. 检查大小  
            if get\_file\_size\_in\_mb(output\_pdf\_path) \<= args.target\_size:  
                move\_file(output\_pdf\_path, args.output\_dir)  
                return (True, final\_path)  
        finally:  
            cleanup\_directory(temp\_dir)

    \# 如果循环结束仍未成功  
    return (False, None)

### **5.4 使用 subprocess 模块管理外部进程**

在Python中调用命令行工具的最佳实践是使用subprocess模块。

* **推荐方法**：使用subprocess.run()函数，因为它提供了最灵活和最简单的接口。  
* **关键参数**：  
  * check=True: 如果被调用的命令返回非零退出码（表示执行出错），subprocess.run()将抛出一个CalledProcessError异常。这使得错误处理变得简单直接。  
  * capture\_output=True 和 text=True: 用于捕获命令的标准输出和标准错误流，便于日志记录和调试。  
* **示例**：构建一个调用pdftoppm的函数。

Python

import subprocess

def deconstruct\_pdf\_to\_images(pdf\_path, output\_dir, dpi):  
    command \= \[  
        "pdftoppm",  
        "-tiff",  
        "-r", str(dpi),  
        pdf\_path,  
        f"{output\_dir}/page"  \# output prefix  
    \]  
    try:  
        result \= subprocess.run(command, check=True, capture\_output=True, text=True)  
        \# Log result.stdout if needed  
        \#... find generated image files and return their paths  
    except subprocess.CalledProcessError as e:  
        print(f"Error during PDF deconstruction: {e.stderr}")  
        raise  \# Re-raise the exception to be handled by the caller

### **5.5 错误处理与临时文件管理**

一个健壮的工具必须能够妥善处理异常情况并保证系统清洁。

* **使用 try...finally**：这是确保临时文件和目录总是被清理的关键。无论try块中的代码是成功执行还是抛出异常，finally块中的清理代码都将被执行。  
* **使用 tempfile 模块**：Python的tempfile模块可以安全地创建临时目录和文件，是管理中间产物的理想选择。tempfile.TemporaryDirectory()上下文管理器可以在退出作用域时自动清理目录。  
* **日志记录**：使用logging模块来记录每个文件的处理进度、所使用的参数、外部命令的输出以及任何发生的错误。这对于调试和追踪批量处理任务的状态至关重要。

## **第六部分：高级调优与结论**

本节将总结报告中提出的最优策略，并为希望进一步探索质量与压缩极限的用户提供高级参数调优的指导。

### **6.1 最优策略总结**

本报告提出的最优策略是一个系统性的、多阶段的解决方案，其核心是：

1. **采用“解构-分析-重建”（DAR）架构**：这是利用recode\_pdf强大压缩能力的最可靠方法，避免了其不稳定的--from-pdf模式。  
2. **实施分层迭代优化算法**：根据文件大小采用不同强度的压缩策略，并通过一个从高质量到低质量的启发式搜索循环，智能地寻找最佳压缩参数。  
3. **集成基于qpdf的应急拆分协议**：当压缩无法满足要求时，通过一个高效、可靠的拆分机制作为最终保障，确保所有文件都能符合提交规范。

这个组合策略在自动化、效率和输出质量之间取得了良好的平衡，能够胜任职称申报工作的辅助任务。

### **6.2 高级参数调优：斜率（Slope）参数**

除了dpi和bg-downsample，recode\_pdf还提供了一些更底层的参数，可以对JPEG2000压缩质量进行更精细的控制。其中最重要的是前景层和背景层的“斜率”（slope）参数 6。

* **fg\_slope 和 bg\_slope**：这两个参数直接控制JPEG2000编码器的量化级别，数值越小，压缩率越高，但图像质量损失也越大。fg\_slope控制前景层（主要是文本周围的像素），bg\_slope控制背景层。  
* **调优场景**：在标准迭代循环失败的边缘情况下，可以尝试微调这些斜率值。例如，如果文本边缘出现轻微模糊，但背景压缩已经足够，可以适当**增大**fg\_slope的值以提高前景质量，同时略微**减小**bg\_slope的值来补偿因此增加的文件大小。  
* **参考值**：根据公开的资料，archive.org在处理书籍时使用了一些默认设置。在追求高压缩率时，他们使用bg\_slope=44250（配合3倍降采样）；在追求更高精度时，则使用bg\_slope=43500（不进行降采样）6。这些数值可以作为高级调优的起点。

### **表3：recode\_pdf高级参数调优**

| 参数名称 | 默认值/参考值 | 效果描述 | 推荐用例 |
| :---- | :---- | :---- | :---- |
| fg\_slope | 参考: 45000 | 控制前景层（文本）的JPEG2000压缩质量。数值越大，质量越高，文件越大。 | 当文本清晰度不足，但文件大小接近目标时，可适当增大此值。 |
| bg\_slope | 参考: 44250, 43500 | 控制背景层（图像）的JPEG2000压缩质量。数值越大，质量越高，文件越大。 | 当背景图像出现过多噪点或色块，但整体文件大小有富余时，可增大此值。反之，可减小此值以进一步压缩。 |

### **6.3 性能考量与局限性**

* **性能影响**：DAR流程是计算密集型的。其中，pdftoppm的图像渲染和tesseract的OCR过程是主要的性能瓶颈，特别是对于页数多、分辨率高的文档。处理一个大的PDF文件可能需要数分钟时间。  
* **局限性**：  
  * **内容类型**：该流程最适用于扫描生成的、以文本为主的文档。对于原生数字PDF（矢量图形和嵌入字体），将其光栅化再重建可能会导致质量下降和文件体积不降反增。  
  * **复杂布局**：对于包含大量图表、公式或复杂排版的页面，OCR的准确性和recode\_pdf的分割效果可能会受到影响。  
  * **hOCR依赖**：recode\_pdf的当前版本强依赖hOCR文件，无法在没有文本层的情况下单独压缩图像并生成PDF 1。

### **6.4 最终建议与未来工作**

最终建议：  
本报告详细设计的自动化工具蓝图是可行且强大的。建议在实际开发中，优先实现核心的DAR流程和分层迭代算法。在功能稳定后，再逐步加入拆分协议和更复杂的错误处理逻辑。对于最终用户，应明确告知该工具的处理耗时和适用范围。  
**未来工作与潜在增强**：

* **并行处理**：对于目录输入模式，可以利用Python的multiprocessing库实现并行处理，同时对多个文件执行DAR流程，从而大幅缩短批量任务的总耗时。  
* **智能内容分析**：在解构阶段后，可以加入一个简单的图像分析步骤，判断页面是文本主导、图像主导还是混合内容，并据此动态调整bg-downsample和斜率等参数，实现更精细化的压缩。  
* **集成高级参数**：将fg\_slope和bg\_slope等高级参数纳入自动迭代优化循环中，创建更多维度的参数搜索空间，以应对更极端的压缩挑战。  
* **图形用户界面（GUI）**：为非技术用户开发一个简单的图形界面，封装命令行工具的复杂性，使其更易于使用。

#### **引用的著作**

1. archive-pdf-tools · PyPI, 访问时间为 十月 8, 2025， [https://pypi.org/project/archive-pdf-tools/](https://pypi.org/project/archive-pdf-tools/)  
2. How to reduce the size of a OCRed pdf file using Tesseract OCR APIs. \- Google Groups, 访问时间为 十月 8, 2025， [https://groups.google.com/g/tesseract-ocr/c/ennBMpr9b50](https://groups.google.com/g/tesseract-ocr/c/ennBMpr9b50)  
3. Reducing PDF size by splitting the image and compressing each area differently · Issue \#912 \- GitHub, 访问时间为 十月 8, 2025， [https://github.com/ocrmypdf/OCRmyPDF/issues/912](https://github.com/ocrmypdf/OCRmyPDF/issues/912)  
4. Investigating OCR and Text PDFs from Digital Collections \- Bibliographic Wilderness, 访问时间为 十月 8, 2025， [https://bibwild.wordpress.com/2023/07/18/investigating-ocr-and-text-pdfs-from-digital-collections/](https://bibwild.wordpress.com/2023/07/18/investigating-ocr-and-text-pdfs-from-digital-collections/)  
5. Re: How to reduce the size of PDF \- Adobe Product Community, 访问时间为 十月 8, 2025， [https://community.adobe.com/t5/acrobat-discussions/how-to-reduce-the-size-of-pdf/m-p/8620335](https://community.adobe.com/t5/acrobat-discussions/how-to-reduce-the-size-of-pdf/m-p/8620335)  
6. pdfcomp: new tool, discussion, compression questions · Issue \#51 ..., 访问时间为 十月 8, 2025， [https://github.com/internetarchive/archive-pdf-tools/issues/51](https://github.com/internetarchive/archive-pdf-tools/issues/51)  
7. split \- How can I extract a page range / a part of a PDF? \- Ask Ubuntu, 访问时间为 十月 8, 2025， [https://askubuntu.com/questions/221962/how-can-i-extract-a-page-range-a-part-of-a-pdf](https://askubuntu.com/questions/221962/how-can-i-extract-a-page-range-a-part-of-a-pdf)  
8. qpdf or pdftk or gs???? \- Auto Multiple Choice, 访问时间为 十月 8, 2025， [https://project.auto-multiple-choice.net/boards/2/topics/7780](https://project.auto-multiple-choice.net/boards/2/topics/7780)  
9. Split an input into multiple output files · Issue \#30 · qpdf/qpdf \- GitHub, 访问时间为 十月 8, 2025， [https://github.com/qpdf/qpdf/issues/30](https://github.com/qpdf/qpdf/issues/30)  
10. Command line tools for digitisation \- The University of Melbourne, 访问时间为 十月 8, 2025， [https://blogs.unimelb.edu.au/digitisation-lab/command-line-tools-for-digitisation/](https://blogs.unimelb.edu.au/digitisation-lab/command-line-tools-for-digitisation/)