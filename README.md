# PDF压缩与拆分工具

基于archive-pdf-tools的职称申报PDF文件自动化压缩与拆分工具，实现"解构-分析-重建"(DAR)三阶段处理流程。

## 功能特性

- **二分双向搜索压缩**: 采用智能算法快速找到最优质量参数
- **6方案策略优化**: S1-S6六级压缩方案，自动选择最佳质量
- **纯物理拆分**: 拆分时不重新压缩，复用压缩中间结果
- **批量处理**: 支持单文件和目录批量处理
- **详细日志**: 完整的处理过程记录和错误跟踪
- **中文支持**: 优化的中文OCR识别
- **手动模式**: 支持交互式手动输入压缩参数

## 技术架构

### DAR三阶段流程

1. **解构 (Deconstruct)**: 使用 `pdftoppm` 将PDF转换为高质量图像
2. **分析 (Analyze)**: 使用 `tesseract` 进行OCR并生成hOCR文件
3. **重建 (Reconstruct)**: 使用 `recode_pdf` 基于MRC技术重建优化PDF

### 分层压缩策略

项目采用**二分双向搜索算法**，定义了7个压缩方案（S1-S7）：

- **S1** (dpi=300, bg_downsample=2): 高质量起点，保守压缩
- **S2** (dpi=300, bg_downsample=3): 适度降低，温和压缩
- **S3** (dpi=250, bg_downsample=3): 平衡质量与体积
- **S4** (dpi=200, bg_downsample=4): 进取压缩
- **S5** (dpi=150, bg_downsample=5): 激进压缩
- **S6** (dpi=100, bg_downsample=8): 极限压缩
- **S7** (dpi=72, bg_downsample=10): 终极压缩 ⚠️ **会失去文本搜索功能，但可额外减小约7%体积**

**搜索策略**：
1. 从S1开始尝试
2. 若S1失败且结果>1.5倍目标，直接跳至S7（终极方案）
3. 若S7成功，向上回溯（S6→S5→...）找到最优质量
4. 否则按S1→S2→S3...顺序渐进搜索

**S7特殊说明**：S7方案会自动优化hOCR文件（移除文字标签），可额外减小约7%体积，但生成的PDF将失去文本搜索和复制功能。这是一个为极限压缩场景设计的权衡方案。

## 安装要求

### 系统环境

**仅支持Ubuntu/WSL环境:**
- Ubuntu 24.04+ 或 WSL2 (推荐)
- Python 3.7+
- 至少 2GB 可用磁盘空间（用于临时文件）

**注意**: 本项目专为Ubuntu/WSL环境设计和测试，不支持其他操作系统。

### 重要说明：pipx安装方式

本工具使用 `pipx` 安装 `archive-pdf-tools`，以避免污染系统Python环境。安装脚本会自动处理Ubuntu版本的兼容性问题。

如果您之前使用pip安装过archive-pdf-tools，建议先卸载：
```bash
pip3 uninstall archive-pdf-tools
```

### 系统工具依赖

在Ubuntu/WSL环境中安装必要工具：

```bash
# 更新包管理器
sudo apt update

# 安装核心工具
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-chi-sim qpdf pipx

# 安装archive-pdf-tools（推荐使用pipx）
pipx install archive-pdf-tools

# 确保PATH配置正确
pipx ensurepath
source ~/.bashrc
```

### Python环境

- Python 3.7+
- 标准库模块（无需额外安装）

## 使用方法

### Windows用户快速开始

```batch
# 使用Windows批处理脚本（自动处理WSL配置）
pdf_compress.bat C:\Documents\test.pdf

# 允许拆分的批量处理
pdf_compress.bat C:\Documents\PDFs --allow-splitting --target-size 8.0
```

### Linux/WSL用户

#### 基本用法

```bash
# 处理单个文件（允许拆分）
python main.py --input document.pdf --output ./output --allow-splitting

# 处理整个目录
python main.py --input ./pdf_folder --output ./processed

# 自定义目标大小
python main.py --input large.pdf --output ./output --target-size 8.0
```

### 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | 必需 | - | 输入PDF文件或目录路径 |
| `--output` | 必需 | - | 输出目录路径 |
| `--target-size` | 可选 | 2.0 | 目标文件大小(MB) |
| `--allow-splitting` | 可选 | False | 允许拆分文件 |
| `--max-splits` | 可选 | 4 | 最大拆分数量(2-10) |
| `--copy-small-files` | 可选 | False | 复制小文件到输出目录 |
| `--check-deps` | 可选 | False | 仅检查依赖工具 |
| `--verbose` | 可选 | False | 显示详细调试信息 |
| `-k, --keep-temp-on-failure` | 可选 | False | 失败时保留临时目录 |
| `-?, --examples` | 可选 | False | 显示使用示例 |
| `-m, --manual` | 可选 | False | 进入手动模式 |

### 使用示例

```bash
# 检查工具依赖
python main.py --check-deps

# 处理单个文件（将 single.pdf 压缩到目标 5MB 并输出到 out/）
python main.py --input single.pdf --output out --target-size 5

# 在批量目录上运行，允许拆分并保留临时目录以便调试失败项
python main.py --input ./pdfs --output ./out --target-size 3 --allow-splitting --max-splits 4 -k

# 仅检查依赖，不执行压缩（用于诊断）
python main.py --check-deps

# 快速输出常用命令示例
python main.py -?

# 进入交互式手动模式
python main.py --manual
```

## 项目结构

```
pdf_compressor/
├── main.py                 # 主程序入口
├── orchestrator.py         # 业务流程调度器
├── compressor/
│   ├── __init__.py
│   ├── pipeline.py         # DAR三阶段流程实现
│   ├── strategy.py         # 分层压缩策略
│   ├── splitter.py         # PDF拆分逻辑
│   └── utils.py            # 工具函数
├── logs/
│   └── process.log         # 处理日志（自动生成）
├── docs/                   # 项目文档
├── requirements.txt        # Python依赖
└── README.md              # 项目说明
```

## 算法说明

### 二分双向搜索算法

程序采用智能搜索算法，快速找到最优质量参数：

1. **渐进式搜索**: 从S1开始，若成功则直接返回
2. **快速跳跃**: 若S1失败且结果远超目标（>1.5倍），直接跳至S6
3. **向上回溯**: 若S6成功，向上测试S5、S4...找到最优质量
4. **顺序尝试**: 若不满足跳跃条件，按S1→S2→S3...顺序尝试

**优势**：
- 减少不必要的中间尝试
- 在满足大小要求的前提下最大化质量
- DAR阶段1-2只执行一次，所有方案复用中间结果

### 拆分策略

当压缩失败时启动**纯物理拆分**协议：

1. **智能源选择**: 从所有中间结果中选择≤8MB的最大文件作为拆分源
2. **密度计算**: 基于文件大小估算最优拆分数量
3. **物理拆分**: 使用qpdf直接拆分，不重新压缩
4. **页面分配**: 基于密度均衡分配页面到各分片

**优势**：
- 避免重复压缩，直接使用最佳中间结果
- 基于密度分配，比简单平均分页更合理
- 显著提升大文件处理效率

## 日志和监控

### 日志文件

- **位置**: `logs/process.log`
- **内容**: 详细的处理过程、参数选择、错误信息
- **格式**: 时间戳 + 日志级别 + 模块信息 + 消息

### 处理报告

批量处理后自动生成 `processing_report.txt`，包含：
- 处理统计信息
- 成功/失败文件列表
- 处理时间记录

## 性能考量

### 处理时间

- **单页文档**: 通常30秒-2分钟
- **多页文档**: 按页数线性增长
- **大文件**: 可能需要10-30分钟

### 影响因素

- PDF页数和复杂度
- 图像分辨率设置
- 系统硬件性能
- OCR处理复杂度

### 优化建议

- 为大批量任务预留充足时间
- 在性能较好的机器上运行
- 考虑使用SSD存储临时文件

## 故障排除

### 常见问题

1. **工具未找到错误**
   ```bash
   # 检查工具安装
   python main.py --check-deps
   
   # 重新安装缺失工具
   sudo apt install poppler-utils tesseract-ocr qpdf pipx
   pipx install archive-pdf-tools
   ```

2. **recode_pdf命令未找到**
   ```bash
   # 确保pipx路径在PATH中
   pipx ensurepath
   source ~/.bashrc
   ```

3. **内存不足**
   - 减少并发处理文件数量
   - 降低初始DPI设置
   - 确保有足够磁盘空间存储临时文件

4. **OCR识别错误**
   - 检查tesseract语言包安装
   - 尝试提高图像分辨率
   - 确认PDF内容清晰度

5. **权限问题**
   ```bash
   # 确保输出目录有写权限
   chmod 755 output_directory
   ```

### 详细排除指南

查看完整的故障排除指南：`docs/TROUBLESHOOTING.md`

### 调试技巧

- 使用 `--verbose` 参数查看详细信息
- 检查 `logs/process.log` 文件
- 逐个处理问题文件以定位问题

## 技术支持

### 日志分析

重要日志信息说明：
- `阶段1 [解构]`: PDF转图像过程
- `阶段2 [分析]`: OCR处理过程  
- `阶段3 [重建]`: PDF重建过程
- `压缩结果大小`: 每次尝试的结果

### 联系信息

如遇技术问题，请提供：
1. 完整的错误信息
2. `logs/process.log` 文件
3. 问题文件的基本信息（大小、页数等）
4. 使用的命令和参数

## 许可证

本项目基于MIT许可证开源。

## 更新日志

### v2.0.3 (2025-10-19)
- **性能优化**: TIFF文件生成时使用LZW压缩，减小68%临时文件体积（25MB→8MB/页）
- **新增**: S7终极压缩方案（DPI=72, BG-Downsample=10, 自动hOCR优化）
- **优化**: S7方案自动移除hOCR文字标签，可额外减小约7%最终PDF体积
- **权衡**: S7方案生成的PDF将失去文本搜索功能（适用于极限压缩场景）
- **文档**: 更新压缩策略说明，添加S7特殊说明

### v2.0.2 (2025-10-18)
- **Bug修复**: 修复S7方案参数配置问题
- **优化**: 改进日志输出格式

### v2.0.0 (2025-10-18)
- **重大更新**: 完全重写压缩和拆分算法
- 新增：二分双向搜索算法（6方案策略）
- 新增：纯物理拆分策略（复用中间结果）
- 新增：手动模式支持交互式参数输入
- 新增：参数示例显示（-?参数）
- 优化：UTF-8编码支持，解决Windows中文显示问题
- 优化：参数名称简化（--output-dir → --output）
- 完善：单元测试覆盖所有算法分支

### v1.0.0 (2024-10-09)
- 初始版本发布
- 实现完整的DAR处理流程
- 支持分层压缩策略
- 集成PDF拆分功能
- 添加详细日志记录