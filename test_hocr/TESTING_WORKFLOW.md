# hOCR 优化测试 - 完整流程指南

## 🎯 测试目标

验证删除 `ocrx_word` 标签后的 hOCR 文件能否成功生成可用的 PDF。

**如果成功**：可以将 hOCR 从 9.05 MB 减小到 1.60 MB，节省 7.46 MB！

---

## 📋 测试流程概览

```
1. 运行压缩任务 → 生成图像栈和原始 hOCR
                     ↓
2. 分析原始 hOCR → 生成 4 种优化版本
                     ↓
3. 使用优化 hOCR → 测试 PDF 生成
                     ↓
4. 验证结果 → 检查大小、质量、可搜索性
```

---

## 🔧 详细步骤

### 步骤 1: 获取测试文件

#### 方法A：从压缩任务获取（推荐）

```bash
# 在 WSL/Ubuntu 中运行
cd ~/pdf_compressor

# 运行压缩任务，保留临时文件
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure
```

**输出示例**：
```
[信息] 临时工作目录: /tmp/tmp1a2b3c4d
[执行] 解构PDF...
[执行] OCR识别...
...
[失败] 未能达到目标...
[保留] 临时目录已保留: /tmp/tmp1a2b3c4d
```

**进入临时目录**：
```bash
cd /tmp/tmp1a2b3c4d

# 查看文件
ls -lh
# 应该看到:
# page-001.tif, page-002.tif, ..., page-156.tif
# combined.hocr (约 9 MB)
```

---

### 步骤 2: 分析 hOCR 文件（如果还没做）

```bash
# 在 Windows 或 WSL 中运行
python test_hocr/hocr_analyzer.py docs/testpdf156.hocr
```

**输出**：
```
========================================
hOCR 文件分析报告
========================================

文件: docs/testpdf156.hocr
大小: 9.05 MB
总行数: 101,812

结构统计:
- ocr_page: 156
- ocr_carea: 1,356
- ocr_par: 2,063
- ocr_line: 5,107
- ocrx_word: 77,971  ← 关键！

内容占比:
- 文本内容: 269.69 KB (2.9%)
- bbox坐标: 1.96 MB (21.7%)
- 其他: 6.83 MB (75.4%)  ← 标签结构

========================================
生成优化版本
========================================

✅ 空文本版: 8.88 MB (-1.8%)
✅ 最小化版: 8.49 MB (-6.2%)
✅ 无单词版: 1.60 MB (-82.4%)  ← 重点测试！
✅ 无行版: 7.91 MB (-12.6%)

所有文件保存到: docs/hocr_experiments/
```

---

### 步骤 3: 测试 PDF 生成

#### 方法A：使用快速测试脚本

```bash
# 进入临时目录（包含 page-*.tif 的地方）
cd /tmp/tmp1a2b3c4d

# 运行测试脚本
bash /mnt/c/Users/quying/Projects/pdf_compressor/test_hocr/quick_test.sh
```

#### 方法B：手动测试

```bash
# 在临时目录中
cd /tmp/tmp1a2b3c4d

# 复制优化后的 hOCR
cp /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr ./

# 生成 PDF（使用 S7 参数）
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words.pdf

# 检查结果
ls -lh test_no_words.pdf
```

**预期输出**：
```
# 如果成功
-rw-r--r-- 1 user user 2.5M Oct 19 10:30 test_no_words.pdf
✅ PDF 生成成功！

# 如果失败
错误: [recode_pdf 的错误信息]
❌ 需要尝试其他策略
```

---

### 步骤 4: 验证和对比

#### 4.1 基本检查

```bash
# 查看 PDF 信息
pdfinfo test_no_words.pdf

# 应该显示:
# Pages: 156
# Page size: XXX x YYY pts
# File size: X MB
# ...
```

#### 4.2 生成对照组（使用原始 hOCR）

```bash
# 如果原始 combined.hocr 还在
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_original.pdf

# 对比大小
ls -lh test_*.pdf
```

**对比示例**：
```
-rw-r--r-- 1 user user 10.2M  test_original.pdf   ← 原始 hOCR
-rw-r--r-- 1 user user  2.8M  test_no_words.pdf   ← 优化 hOCR
                        ^^^^
                     节省 7.4 MB！
```

#### 4.3 质量检查

```bash
# 在 Windows 中打开 PDF
explorer.exe test_no_words.pdf

# 或复制到 Windows
cp test_no_words.pdf /mnt/c/Users/quying/Desktop/
```

**手动检查**：
- [ ] 页面显示正常
- [ ] 图像清晰度可接受
- [ ] 文字排版正确
- [ ] 无损坏或乱码

**可搜索性测试**（预期会失败）：
- [ ] 按 Ctrl+F 搜索文字 → ❌ 无法搜索（预期）
- [ ] 尝试选择文字 → ❌ 无法选择（预期）

**注意**：无单词版会丧失可搜索性，这是预期的权衡。

---

## 📊 结果记录

### 测试结果表格

| hOCR 版本 | hOCR 大小 | PDF 生成 | PDF 大小 | 节省量 | 可搜索 | 质量 |
|-----------|-----------|----------|----------|--------|--------|------|
| 原始 | 9.05 MB | ✓ | ? MB | - | ✓ | ✓ |
| no_words | 1.60 MB | ? | ? MB | ? MB | ✗ | ? |
| no_lines | 7.91 MB | ? | ? MB | ? MB | ? | ? |
| minimal | 8.49 MB | ? | ? MB | ? MB | ? | ? |

填写实际测试数据...

---

## ✅ 成功标准

测试成功需要满足：

1. **PDF 生成成功** 
   - `recode_pdf` 正常退出
   - 生成的 PDF 文件存在

2. **文件大小合理**
   - 比原始 hOCR 版本小（预期减少 7+ MB）
   - 在可接受范围内（2-8 MB）

3. **视觉质量可接受**
   - 页面显示正常
   - 无明显损坏或失真

4. **功能损失可接受**
   - 丧失可搜索性（已知且可接受）
   - 显示功能完整

---

## 🎉 如果测试成功

### 立即行动

1. **记录详细数据**
   - PDF 文件大小
   - 生成时间
   - 质量评估

2. **更新文档**
   - 在 `docs/hOCR实验_真实数据分析.md` 中记录结果
   - 更新 README.md

3. **准备集成**
   - 设计 `optimize_hocr()` 函数
   - 添加到 `pipeline.py`
   - 创建 `--optimize-hocr` 参数

4. **发布新版本**
   - 打 v2.1.0 标签
   - 写 CHANGELOG
   - 推送到 GitHub

### 潜在影响

**对 156 页 PDF 项目**：
- 当前: S7 生成 4-5 MB（未达标）
- 优化后: S7 可能生成 2 MB 以下（成功！）

**对项目整体**：
- 极限压缩成功率大幅提升
- 可以使用更温和的参数（保持质量）
- 显著减少处理时间

---

## ❌ 如果测试失败

### 错误分析

**常见失败情况**：

1. **recode_pdf 报错**
   ```
   错误: hOCR 文件格式不正确
   ```
   → 说明 recode_pdf 需要 ocrx_word 标签

2. **PDF 生成但损坏**
   ```
   PDF 无法打开或显示异常
   ```
   → 说明结构不完整

3. **PDF 过大**
   ```
   文件大小没有减小
   ```
   → 说明 hOCR 大小不是瓶颈

### 备选方案

**按优先级测试**：

#### 备选1: no_lines 版本（-12.6%）

```bash
recode_pdf --from-imagestack page-*.tif \
    --hocr-file /mnt/c/.../combined_no_lines.hocr \
    --dpi 72 --bg-downsample 10 -J grok \
    -o test_no_lines.pdf
```

**优势**：保留 ocrx_word，只删除 ocr_line

#### 备选2: minimal 版本（-6.2%）

```bash
recode_pdf --from-imagestack page-*.tif \
    --hocr-file /mnt/c/.../combined_minimal.hocr \
    --dpi 72 --bg-downsample 10 -J grok \
    -o test_minimal.pdf
```

**优势**：保留所有标签，只简化属性

#### 备选3: 研究 recode_pdf 需求

- 查看 ocrmypdf-recode 源码
- 确定最低要求的标签
- 设计最小可行的 hOCR 结构

---

## 🔍 故障排查

### 问题1: 找不到图像文件

```
❌ 错误：找不到 page-*.tif 文件
```

**解决**：
- 确认在正确的目录（临时目录）
- 检查文件命名格式
- 查看 `HOW_TO_GET_TEST_FILES.md`

### 问题2: 找不到 hOCR 文件

```
❌ 找不到优化后的 hOCR 文件
```

**解决**：
```bash
# 先运行分析工具
python test_hocr/hocr_analyzer.py docs/testpdf156.hocr

# 确认文件存在
ls -lh docs/hocr_experiments/combined_no_words.hocr
```

### 问题3: recode_pdf 未安装

```
bash: recode_pdf: command not found
```

**解决**：
```bash
# 安装 ocrmypdf-recode
pip install ocrmypdf-recode

# 或
sudo apt-get install ocrmypdf-recode
```

---

## 📝 测试检查清单

开始测试前：
- [ ] 有 156 个 page-*.tif 文件
- [ ] 有原始 combined.hocr（9.05 MB）
- [ ] 已生成优化版本（1.60 MB）
- [ ] recode_pdf 命令可用
- [ ] 有足够磁盘空间（1+ GB）

执行测试：
- [ ] 运行 quick_test.sh 或手动命令
- [ ] PDF 成功生成
- [ ] 记录文件大小
- [ ] 检查视觉质量
- [ ] 测试功能（可搜索性）

记录结果：
- [ ] 填写测试结果表格
- [ ] 截图或保存样本页
- [ ] 更新文档
- [ ] 提交 Git 记录

---

## 🚀 快速命令参考

```bash
# 1. 运行压缩任务
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure

# 2. 进入临时目录
cd /tmp/tmpXXXXXX

# 3. 快速测试
bash /mnt/c/Users/quying/Projects/pdf_compressor/test_hocr/quick_test.sh

# 4. 手动测试（如果需要）
cp /mnt/c/.../combined_no_words.hocr ./
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 --bg-downsample 10 -J grok \
    -o test_no_words.pdf

# 5. 查看结果
ls -lh test_no_words.pdf
pdfinfo test_no_words.pdf
```

---

**创建日期**: 2025-10-19  
**目标**: 验证 82.4% hOCR 减小的可行性  
**关键文件**: combined_no_words.hocr (1.60 MB)  
**预期影响**: 🌟🌟🌟 突破性改进（如果成功）
