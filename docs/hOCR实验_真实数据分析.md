# hOCR 优化实验 - 真实数据分析报告

## 📊 实验数据

### 文件信息
- **测试文件**: testpdf156.hocr
- **原始大小**: 9.05 MB
- **总行数**: 101,812 行
- **页数**: 156 页

### 结构统计
| 元素类型 | 数量 | 说明 |
|---------|------|------|
| ocr_page | 156 | 每页一个 |
| ocr_carea | 1,356 | 内容区域，平均每页 8.7 个 |
| ocr_par | 2,063 | 段落，平均每页 13.2 个 |
| ocr_line | 5,107 | 文本行，平均每页 32.7 个 |
| **ocrx_word** | **77,971** | **单词/词组，平均每页 500 个** |

### 内容占比分析
| 组件 | 大小 | 占比 | 备注 |
|------|------|------|------|
| 文本内容 | 269.69 KB | 2.9% | ❌ 远低于预期 |
| bbox 坐标 | 1.96 MB | 21.7% | 🔴 最大单一组件 |
| 其他 | 6.83 MB | 75.4% | **标签结构本身** |

---

## 🎯 优化实验结果

### 完整对比表

| 优化策略 | 文件大小 | 减少量 | 减少率 | 评估 |
|---------|---------|--------|--------|------|
| **原始** | 9.05 MB | - | - | 基准 |
| 空文本 | 8.88 MB | 0.17 MB | 1.8% | ❌ 效果极差 |
| 最小化 | 8.49 MB | 0.56 MB | 6.2% | ⚠️ 效果有限 |
| **无单词** | **1.60 MB** | **7.46 MB** | **82.4%** | ✅ **惊人效果** |
| 无文本行 | 7.91 MB | 1.14 MB | 12.6% | ⚠️ 中等效果 |

---

## 🔥 关键发现

### 1. 理论预期 vs 实际结果

**预期**（基于样本文件）:
- 文本内容占 30-50%
- 空文本优化可减少 30-50%

**实际**（真实文件）:
- 文本内容只占 **2.9%** ❌
- 空文本优化只减少 **1.8%** ❌

**原因分析**:
- 中文单词数量极多（77,971 个）
- 但每个单词很短（平均 3-4 字节）
- 样本文件的文本占比被严重高估

### 2. 真正的瓶颈

**不是文本内容，而是标签结构本身！**

```
77,971 个 ocrx_word 标签 = 9.05 MB 的主要组成部分

每个标签平均约 100 字节：
- <span class='ocrx_word' id='word_1_1' title='bbox 792 118 1608 236; x_wconf 85'>
- 文本（3-6 字节）
- </span>

删除后：
9.05 MB → 1.60 MB（减少 82.4%）
```

### 3. "无单词"策略的惊人效果

- **9.05 MB → 1.60 MB**
- **减少 7.46 MB (82.4%)**
- **远超最乐观估计（6.8 MB）**

这是突破性的发现！🎉

---

## ⚠️ 关键问题

### recode_pdf 是否需要 ocrx_word 标签？

**测试矩阵**:

| hOCR 版本 | 大小 | PDF 生成? | PDF 大小? | 可用性 |
|-----------|------|-----------|-----------|--------|
| 原始 | 9.05 MB | ? | ? | 基准 |
| 空文本 | 8.88 MB | ? | ? | 低收益 |
| 最小化 | 8.49 MB | ? | ? | 低收益 |
| **无单词** | **1.60 MB** | **?** | **?** | **高收益** |
| 无文本行 | 7.91 MB | ? | ? | 中等收益 |

**必须验证的问题**:
1. ✅ 无单词 hOCR 能否成功生成 PDF？
2. ✅ 生成的 PDF 大小是否减小？
3. ✅ PDF 视觉质量是否受影响？
4. ✅ recode_pdf 执行时间是否合理？

---

## 🧪 下一步测试计划

### 步骤 1: 准备测试环境

```bash
# 在 WSL/Ubuntu 环境
cd ~/pdf_compressor

# 复制优化后的 hOCR 文件
cp docs/hocr_experiments/combined_no_words.hocr test_no_words.hocr
```

### 步骤 2: 使用原始 hOCR 生成 PDF（基准）

```bash
# 假设图像文件在 /tmp/tmpj9meff1r/
cd /tmp/tmpj9meff1r/

# 使用原始 hOCR
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_original.pdf

# 记录大小和时间
ls -lh test_original.pdf
```

### 步骤 3: 使用无单词 hOCR 生成 PDF

```bash
# 备份原始 hOCR
cp combined.hocr combined_original.hocr

# 使用无单词版本
cp ~/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr combined.hocr

# 生成 PDF
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_no_words.pdf

# 记录大小和时间
ls -lh test_no_words.pdf
```

### 步骤 4: 对比结果

```bash
# 大小对比
ls -lh test_*.pdf

# 计算减少量
# 如果 test_no_words.pdf 更小，记录具体减少了多少 MB
```

### 步骤 5: 视觉质量检查

使用 PDF 阅读器打开两个文件，对比：
- ✅ 文字是否清晰？
- ✅ 布局是否正常？
- ✅ 图像是否完整？

---

## 📊 预期结果

### 场景 1: 成功（最理想）✨

```
原始 hOCR (9.05 MB) → PDF: X MB
无单词 hOCR (1.60 MB) → PDF: (X - 7.5) MB

实际减少: ~7.5 MB
```

**意义**: 
- 可以将 S7 方案的极限压缩能力提升到新的水平
- 许多"不可能"的任务变为"可能"

### 场景 2: 部分成功（可接受）⚠️

```
PDF 生成成功，但减少量小于预期

原始 hOCR (9.05 MB) → PDF: X MB
无单词 hOCR (1.60 MB) → PDF: (X - 2~4) MB

实际减少: 2-4 MB
```

**意义**: 
- 仍然是显著改进
- 可以作为 S7 的特殊优化

### 场景 3: 失败（需要备选方案）❌

```
recode_pdf 报错，无法生成 PDF
或生成的 PDF 质量严重下降
```

**备选方案**:
1. 尝试"无文本行"策略（减少 1.14 MB，12.6%）
2. 尝试"最小化"策略（减少 0.56 MB，6.2%）
3. 研究 recode_pdf 对 hOCR 的最低要求

---

## 💡 其他发现

### bbox 坐标占比高

- bbox 占 21.7% (1.96 MB)
- 但这是 recode_pdf 必需的定位信息
- **不能删除或简化**

### 标签层次的重要性

保留的层次结构：
```
ocr_page (156)
└── ocr_carea (1,356)
    └── ocr_par (2,063)
        └── ocr_line (5,107)
            └── [删除的] ocrx_word (77,971)
```

删除最底层的 ocrx_word 后，仍保留了 4 层结构，这可能足够 recode_pdf 使用。

---

## 📝 结论

### 主要成果

1. ✅ **发现真正的瓶颈**: 不是文本内容，而是 77,971 个 ocrx_word 标签
2. ✅ **找到最优策略**: 删除 ocrx_word 标签可减少 **82.4%** (7.46 MB)
3. ✅ **超越预期**: 实际效果远超最乐观估计

### 下一步关键

**必须验证**: 无单词 hOCR 能否成功生成 PDF

如果成功：
- 🎉 这将是项目的重大突破
- 🚀 可以立即整合到 S7 方案
- 📦 发布 v2.1.0 版本

如果失败：
- ⚠️ 需要测试其他策略
- 🔍 研究 recode_pdf 的最低要求
- 📋 可能需要保留部分 ocrx_word 标签

---

**创建日期**: 2025-10-19  
**实验状态**: 分析完成，等待 PDF 生成测试  
**关键数据**: 9.05 MB → 1.60 MB (-82.4%)  
**潜在影响**: 突破性改进 🌟

---

##  PDF生成测试指南

### 方法1：快速测试（推荐）

```bash
# 1. 切换到包含 page-*.tif 的目录
cd /path/to/your/imagestack

# 2. 运行快速测试脚本
bash /path/to/pdf_compressor/test_hocr/quick_test.sh
```

**脚本会自动**：
- 检查 no_words hOCR 文件 (1.60 MB)
- 使用 S7 参数生成 PDF (DPI=72, BG-Downsample=10, JPEG2000)
- 报告生成结果和文件大小

### 方法2：手动测试

```bash
# 在 WSL/Ubuntu 中执行
cd /path/to/imagestack

recode_pdf --from-imagestack page-*.tif \
    --hocr-file /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words.pdf

# 检查结果
ls -lh test_no_words.pdf
pdfinfo test_no_words.pdf
```

### 验证清单

- [ ] **命令执行成功** - 无错误退出
- [ ] **PDF 文件生成** - 文件存在且大小合理  
- [ ] **可搜索性测试** - 打开 PDF，按 Ctrl+F 搜索文本
- [ ] **文本选择测试** - 尝试选中和复制文本
- [ ] **显示质量** - 检查页面渲染是否正常
- [ ] **大小对比** - 与原始 hOCR 版本对比文件大小

### 预期结果

#### 如果成功 
- PDF 正常生成且可搜索
- 文件大小显著减小（约 7.5 MB）  
- **下一步**: 集成到 pipeline.py，发布 v2.1.0

#### 如果失败   
- recode_pdf 报错或 PDF 损坏
- **备选方案**:
  1. 测试 no_lines (-12.6%, 7.91 MB)
  2. 测试 minimal (-6.2%, 8.49 MB)
  3. 研究 recode_pdf 的最小要求

---

**测试脚本**: test_hocr/quick_test.sh  
**Windows路径**: C:\Users\quying\Projects\pdf_compressor\docs\hocr_experiments\combined_no_words.hocr  
**WSL路径**: /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr
