# 端到端测试指南 - 直接使用 PDF 文件

## 🎯 测试目的

直接从 PDF 文件进行完整的 hOCR 优化测试，无需手动操作中间文件。

---

## 📋 准备工作

### 1. 将测试脚本上传到远程主机

```bash
# 在远程 Ubuntu/WSL 主机上
cd ~/pdf_compressor

# 确保脚本有执行权限
chmod +x test_hocr/test_pdf_e2e.sh
chmod +x test_hocr/test_quick_e2e.sh
```

### 2. 准备测试 PDF

将测试 PDF 文件上传到远程主机，或使用已有的 PDF：

```bash
# 示例：上传文件
scp testpdf156.pdf user@remote-host:~/

# 或者在远程主机上找到现有 PDF
ls ~/testpdf*.pdf
```

---

## 🚀 运行测试

### 方法 1: 快速测试（推荐）

**最简单、最快速的方式**

```bash
# 在远程主机上执行
cd ~/pdf_compressor
bash test_hocr/test_quick_e2e.sh ~/testpdf156.pdf
```

**输出示例**：
```
🎯 快速 hOCR 优化测试
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PDF: testpdf156.pdf (12.3M)

[1/4] 解构 PDF...
      ✅ 156 页
[2/4] OCR 识别...
[3/4] 优化 hOCR (删除 ocrx_word)...
      ✅ 优化: 9.1MB → 1.6MB (-82.4%)
[4/4] 生成 PDF...
      原始 hOCR...
      优化 hOCR...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
combined.hocr             9.1M
combined_no_words.hocr    1.6M
test_original.pdf         10.2M
test_no_words.pdf         2.8M

📁 位置: /tmp/hocr_quick_test_12345

✅ 成功! 节省 7.4MB (72.5%)
```

**时间**: 约 10-15 分钟（取决于页数和 CPU）

---

### 方法 2: 详细测试

**包含更详细的进度信息和分析**

```bash
bash test_hocr/test_pdf_e2e.sh ~/testpdf156.pdf
```

**可选：指定临时目录**

```bash
bash test_hocr/test_pdf_e2e.sh ~/testpdf156.pdf /tmp/my_test
```

**输出**: 包含完整的步骤说明和详细统计

---

## 📊 查看结果

### 1. 检查生成的文件

```bash
# 进入测试目录
cd /tmp/hocr_quick_test_*  # 使用实际的目录名

# 列出所有文件
ls -lh

# 应该看到:
# - page-*.tif          (图像文件)
# - page-*.hocr         (单页 hOCR)
# - combined.hocr       (原始合并 hOCR, ~9MB)
# - combined_no_words.hocr (优化 hOCR, ~1.6MB)
# - test_original.pdf   (使用原始 hOCR 生成)
# - test_no_words.pdf   (使用优化 hOCR 生成)
```

### 2. 对比文件大小

```bash
# 详细对比
echo "hOCR 文件:"
ls -lh combined*.hocr

echo ""
echo "PDF 文件:"
ls -lh test_*.pdf
```

### 3. 查看 PDF 信息

```bash
# 查看 PDF 元数据
pdfinfo test_original.pdf
pdfinfo test_no_words.pdf

# 检查页数
grep -c "Pages:" test_*.pdf
```

---

## 🧪 验证测试

### 1. 复制 PDF 到 Windows

```bash
# 复制到共享目录（根据你的环境调整）
cp test_*.pdf /mnt/c/Users/quying/Desktop/

# 或使用 scp
scp test_*.pdf user@windows-host:/path/to/destination/
```

### 2. 在 Windows 中打开 PDF

- 打开 `test_original.pdf` 和 `test_no_words.pdf`
- 对比显示质量
- 测试可搜索性（Ctrl+F）

### 3. 验证清单

- [ ] PDF 能正常打开
- [ ] 页面显示清晰
- [ ] 图像质量可接受
- [ ] 文字排版正确
- [ ] 文件大小显著减小

**预期结果**：
- ✅ `test_original.pdf` 可搜索（能搜到文字）
- ⚠️ `test_no_words.pdf` 不可搜索（这是预期的，因为删除了单词标签）
- ✅ 两个 PDF 的视觉质量应该完全相同
- ✅ `test_no_words.pdf` 应该小 20-70%

---

## 📈 预期结果分析

### 成功的标志

**hOCR 优化**：
- 原始 hOCR: 9.0-9.5 MB
- 优化 hOCR: 1.5-2.0 MB
- 减少比例: 80-85% ✅

**PDF 大小**（使用 DPI=300, BG-Downsample=2）：
- 原始版本: 8-12 MB
- 优化版本: 2-8 MB
- 节省空间: 20-70% ✅

### 如果节省不明显...

可能原因：
1. PDF 本身很小（hOCR 占比低）
2. 图像部分占主导（hOCR 影响有限）
3. 使用了高 DPI（图像占用大）

**解决方案**：
- 尝试更激进的参数（DPI=72, BG-Downsample=10）
- 测试其他优化策略（no_lines, minimal）

---

## 🔧 测试不同参数

### 测试 S7 激进参数

```bash
# 进入测试目录
cd /tmp/hocr_quick_test_*

# 使用 S7 参数重新生成
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words_s7.pdf

# 查看大小
ls -lh test_no_words*.pdf
```

### 测试其他优化策略

```bash
# 生成 no_lines 版本（保留 ocrx_word，删除 ocr_line）
python3 -c "
import re
with open('combined.hocr', 'r') as f:
    content = f.read()
optimized = re.sub(r\"<span class='ocr_line'[^>]*>.*?</span>\", '', content, flags=re.DOTALL)
with open('combined_no_lines.hocr', 'w') as f:
    f.write(optimized)
"

# 测试生成
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_lines.hocr \
    --dpi 300 --bg-downsample 2 -J grok \
    -o test_no_lines.pdf
```

---

## ❓ 常见问题

### Q1: 脚本执行很慢怎么办？

**A**: 这是正常的。主要耗时：
- 解构 PDF: ~30秒
- OCR 识别: ~5-10 分钟（取决于页数）
- 生成 PDF: ~1-2 分钟

对于 156 页 PDF，总时间约 **10-15 分钟**。

### Q2: OCR 失败怎么办？

**A**: 检查 tesseract 和语言包：
```bash
tesseract --version
tesseract --list-langs

# 如果没有 chi_sim，安装它
sudo apt install tesseract-ocr-chi-sim
```

### Q3: recode_pdf 报错怎么办？

**A**: 检查安装：
```bash
recode_pdf --version

# 如果未安装
pip install archive-pdf-tools
# 或
pipx install archive-pdf-tools
```

### Q4: 想测试单页 PDF？

**A**: 先提取单页：
```bash
# 提取第一页
qpdf --pages test.pdf 1 -- test_1page.pdf

# 然后测试
bash test_hocr/test_quick_e2e.sh test_1page.pdf
```

---

## 🎯 下一步

### 如果测试成功

1. **记录结果**
   ```bash
   # 在测试目录中
   echo "测试日期: $(date)" > RESULTS.txt
   echo "原始 PDF: $(du -h ~/testpdf156.pdf | cut -f1)" >> RESULTS.txt
   echo "" >> RESULTS.txt
   ls -lh test_*.pdf combined*.hocr >> RESULTS.txt
   ```

2. **集成到项目**
   - 修改 `compressor/pipeline.py` 添加 hOCR 优化函数
   - 添加 `--optimize-hocr` 参数
   - 更新文档

3. **发布新版本**
   - 创建 v2.1.0 tag
   - 更新 CHANGELOG
   - 推送到 GitHub

### 如果测试失败

1. **收集错误信息**
   ```bash
   # 保存完整输出
   bash test_hocr/test_quick_e2e.sh test.pdf 2>&1 | tee test_error.log
   ```

2. **尝试备选方案**
   - 测试 `no_lines` 策略
   - 测试 `minimal` 策略
   - 研究 recode_pdf 文档

3. **报告问题**
   - 在项目中创建 issue
   - 附上错误日志和环境信息

---

## 📝 测试记录模板

```markdown
# hOCR 优化测试记录

## 测试环境
- 日期: 2025-10-19
- 主机: Ubuntu 22.04
- PDF: testpdf156.pdf (156页, 12.3 MB)

## 测试结果

### hOCR 文件
- 原始: 9.1 MB
- 优化: 1.6 MB
- 减少: 82.4%

### PDF 文件
- 原始参数 (DPI=300, BG=2): 10.2 MB
- 优化参数 (DPI=300, BG=2): 2.8 MB
- 节省: 7.4 MB (72.5%)

### S7 激进参数 (DPI=72, BG=10)
- 优化版本: 1.2 MB
- 节省: 90%

## 质量评估
- [ ] 显示质量: 优秀
- [ ] 可搜索性: 丧失（预期）
- [ ] 视觉完整性: 完整

## 结论
✅ 测试成功！建议集成到项目。
```

---

**创建日期**: 2025-10-19  
**适用场景**: 远程主机端到端测试  
**测试脚本**: test_quick_e2e.sh, test_pdf_e2e.sh  
**预计时间**: 10-15 分钟（156页PDF）
