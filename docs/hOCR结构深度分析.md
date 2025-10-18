# hOCR 文件结构深度分析

## 📚 hOCR 简介

**hOCR** (HTML-based OCR) 是一种开放标准，用于在 HTML/XHTML 中表示 OCR 结果。

### 核心用途
1. **文本坐标定位**: 记录每个单词/字符在页面中的精确位置
2. **文本内容存储**: 保存 OCR 识别的文字内容
3. **PDF 可搜索性**: 嵌入 PDF 后实现文字搜索和复制功能
4. **布局信息**: 保留页面、段落、行的层次结构

---

## 🏗️ hOCR 文件结构层次

```
HTML 文档
└── <body>
    └── <div class="ocr_page">          # 页面级别
        └── <div class="ocr_carea">     # 内容区域
            └── <p class="ocr_par">     # 段落
                └── <span class="ocr_line">     # 文本行
                    └── <span class="ocrx_word">    # 单词/词组
                        文本内容
```

---

## 📋 标签详细分析

### 1. `ocr_page` - 页面容器

**功能**: 代表一个完整的页面

**关键属性**:
```html
<div class='ocr_page' id='page_1' title='bbox 0 0 2550 3300; ppageno 0'>
```

- `bbox 0 0 2550 3300`: 页面边界框（左上角 x,y 到右下角 x,y）
- `ppageno 0`: 物理页码（从0开始）

**对文件大小的影响**: 
- 少量（每页一个）
- 包含页面尺寸信息，必须保留

**能否删除**: ❌ 否 - 必须保留，用于页面定位

---

### 2. `ocr_carea` - 内容区域

**功能**: 表示页面中的一个内容区域（如文本块、图片区域）

**关键属性**:
```html
<div class='ocr_carea' id='block_1_1' title="bbox 100 200 2450 3100">
```

- `bbox`: 区域边界框
- `id`: 唯一标识符

**对文件大小的影响**: 
- 中等（每页可能有多个区域）
- 提供粗粒度布局信息

**能否删除**: ⚠️ 可能 - 需要测试 recode_pdf 是否依赖

---

### 3. `ocr_par` - 段落

**功能**: 表示一个段落

**关键属性**:
```html
<p class='ocr_par' id='par_1_1' lang='zho' title="bbox 100 200 2450 500">
```

- `lang`: 语言代码（zho=中文，eng=英文）
- `bbox`: 段落边界框

**对文件大小的影响**: 
- 中等（每个内容区域可能有多个段落）
- 提供段落级布局

**能否删除**: ⚠️ 可能 - 需要测试

---

### 4. `ocr_line` - 文本行 ⭐ 重要

**功能**: 表示一行文本

**关键属性**:
```html
<span class='ocr_line' id='line_1_1' 
      title="bbox 100 200 2450 250; baseline -0.002 -5; x_size 45; x_descenders 10; x_ascenders 10">
```

- `bbox`: 行边界框
- `baseline`: 基线偏移
- `x_size`: 字体大小
- `x_descenders`: 下伸部分
- `x_ascenders`: 上伸部分

**对文件大小的影响**: 
- 🔴 **高** - 数量多，属性详细
- 包含大量字体度量信息

**能否删除**: ⚠️ 可能 - 或简化属性（只保留 bbox）

---

### 5. `ocrx_word` - 单词/词组 ⭐⭐⭐ 最关键

**功能**: 表示一个单词或词组，包含实际文本内容

**关键属性**:
```html
<span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250; x_wconf 95'>
    这是第一个
</span>
```

- `bbox`: 单词边界框
- `x_wconf`: 识别置信度（0-100）
- **标签内文本**: OCR 识别的实际文字

**对文件大小的影响**: 
- 🔴🔴🔴 **极高** - 数量最多，包含所有文本
- 文本内容占据大量空间
- 中文字符尤其占空间（UTF-8 每字符 3 字节）

**能否删除**: 
- 标签本身: ⚠️ 可能需要保留（recode_pdf 可能需要定位信息）
- 文本内容: ✅ **可以删除！**（这是优化的关键）

---

## 🎯 优化策略分析

### 策略 1: 删除文本内容（空 hOCR）⭐⭐⭐

**操作**: 保留所有标签和 bbox，只删除 `ocrx_word` 标签内的文本

```html
<!-- 原始 -->
<span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250'>这是文本</span>

<!-- 优化后 -->
<span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250'></span>
```

**预期效果**:
- 文本占比约 30-50%（中文更高）
- **预计减少**: 30-50% 文件大小
- **风险**: 丧失搜索功能（但我们不需要）

**实现难度**: ⭐ 简单（正则替换）

---

### 策略 2: 简化属性（最小 hOCR）⭐⭐

**操作**: 删除非必要属性，只保留 bbox

```html
<!-- 原始 -->
<span class='ocr_line' id='line_1_1' 
      title="bbox 100 200 2450 250; baseline -0.002 -5; x_size 45; x_descenders 10; x_ascenders 10">

<!-- 优化后 -->
<span class='ocr_line' id='line_1_1' title="bbox 100 200 2450 250">
```

**预期效果**:
- **预计减少**: 10-15% 额外空间
- **风险**: recode_pdf 可能需要某些属性

**实现难度**: ⭐⭐ 中等（需要测试兼容性）

---

### 策略 3: 删除整个 ocrx_word 标签 ⭐

**操作**: 完全移除 `<span class="ocrx_word">` 标签

```html
<!-- 原始 -->
<span class='ocr_line' id='line_1_1' title="...">
  <span class='ocrx_word' id='word_1_1' title='...'>文本1</span>
  <span class='ocrx_word' id='word_1_2' title='...'>文本2</span>
</span>

<!-- 优化后 -->
<span class='ocr_line' id='line_1_1' title="...">
</span>
```

**预期效果**:
- **预计减少**: 50-70% 文件大小
- **风险**: ⚠️ 高 - recode_pdf 可能依赖单词级定位

**实现难度**: ⭐ 简单

---

### 策略 4: 删除 ocr_line 标签 ⭐

**操作**: 移除文本行级别的结构

**预期效果**:
- **预计减少**: 60-80% 文件大小
- **风险**: 🔴 很高 - 可能导致 recode_pdf 失败

**实现难度**: ⭐ 简单

---

## 🔬 实验计划

### 第 1 阶段: 文件大小分析（无需重建 PDF）

1. ✅ **分析原始 hOCR**
   - 测量总大小
   - 统计各级元素数量
   - 计算文本内容占比

2. ✅ **创建优化版本**
   - 空文本版（删除 ocrx_word 文本）
   - 最小版（简化属性）
   - 无单词版（删除 ocrx_word 标签）
   - 无文本行版（删除 ocr_line 标签）

3. ✅ **对比大小**
   - 记录每个版本的文件大小
   - 计算减少百分比

### 第 2 阶段: PDF 重建测试

使用真实 PDF 测试每个优化版本：

```bash
# 测试命令
recode_pdf --from-imagestack /tmp/page-*.tif \
           --hocr-file <优化后的hocr文件> \
           --dpi 72 \
           --bg-downsample 10 \
           --mask-compression jbig2 \
           -J grok \
           -o test_output.pdf
```

**测试矩阵**:
| hOCR 版本 | PDF 能否生成 | PDF 大小 | 可读性 | 可搜索性 |
|-----------|--------------|----------|--------|----------|
| 原始      | ✓            | ?        | ✓      | ✓        |
| 空文本    | ?            | ?        | ?      | ✗        |
| 最小化    | ?            | ?        | ?      | ✗        |
| 无单词    | ?            | ?        | ?      | ✗        |
| 无文本行  | ?            | ?        | ?      | ✗        |

### 第 3 阶段: 整合到生产

根据测试结果，选择最优策略：

```python
def optimize_hocr_for_compression(hocr_file, strategy='empty_text'):
    """
    为极限压缩优化 hOCR 文件
    
    Args:
        hocr_file: 原始 hOCR 文件路径
        strategy: 优化策略
            - 'empty_text': 删除文本内容（推荐）
            - 'minimal': 简化属性
            - 'no_words': 删除单词标签
    
    Returns:
        优化后的 hOCR 文件路径
    """
    pass
```

---

## 📊 预期收益（基于 9.04MB hOCR）

### 保守估计

| 策略 | 减少率 | 节省空间 | 备注 |
|------|--------|----------|------|
| 空文本 | 30% | 2.7 MB | 最安全 |
| 最小化 | 40% | 3.6 MB | 中等风险 |
| 无单词 | 60% | 5.4 MB | 高风险 |

### 乐观估计

| 策略 | 减少率 | 节省空间 | 备注 |
|------|--------|----------|------|
| 空文本 | 50% | 4.5 MB | 文本占比高 |
| 最小化 | 65% | 5.9 MB | 成功简化属性 |
| 无单词 | 75% | 6.8 MB | recode_pdf 不依赖 |

**关键结论**: 即使保守估计，空文本策略也能节省 **2.7 MB**，这对 2MB 目标极其关键！

---

## 🛠️ 实现工具

已创建 `hocr_analyzer.py` 工具，包含：

1. ✅ `HocrAnalyzer` 类
2. ✅ `analyze_structure()` - 结构分析
3. ✅ `create_empty_hocr()` - 创建空文本版
4. ✅ `create_minimal_hocr()` - 创建最小版
5. ✅ `create_no_words_hocr()` - 创建无单词版
6. ✅ `create_no_lines_hocr()` - 创建无文本行版
7. ✅ `run_hocr_experiments()` - 完整实验流程

---

## 📝 使用示例

```bash
# 分析真实的 hOCR 文件
python test_hocr/hocr_analyzer.py /tmp/tmpxxx/combined.hocr

# 输出:
# - 结构分析报告
# - 各优化版本的文件
# - 大小对比表
```

---

## 🔍 关键发现总结

1. **文本内容是最大的占比** - 可能达到 30-50%
2. **ocrx_word 标签最多** - 每个单词一个
3. **中文占用更多空间** - UTF-8 编码，每字符 3 字节
4. **bbox 信息必须保留** - recode_pdf 需要坐标定位
5. **删除文本内容最安全** - 保留所有结构和坐标

---

## 下一步行动

1. [ ] 运行 `hocr_analyzer.py` 分析真实的 9.04MB hOCR 文件
2. [ ] 测试各优化版本能否成功生成 PDF
3. [ ] 对比最终 PDF 大小
4. [ ] 选择最优策略
5. [ ] 整合到 `pipeline.py`

---

**创建日期**: 2025-10-19  
**研究状态**: 准备就绪  
**预期收益**: 2.7-6.8 MB 文件大小减少
