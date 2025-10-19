# 如何获取 hOCR 测试所需的文件

## 📋 需要的文件

测试 hOCR 优化需要两类文件：

1. **图像栈** (imagestack): `page-001.tif`, `page-002.tif`, ..., `page-156.tif`
2. **原始 hOCR 文件**: `combined.hocr` (9.05 MB)

---

## 🔧 方法1：从压缩任务中获取（推荐）

### 步骤1：运行压缩任务并保留临时文件

```bash
# 在 WSL/Ubuntu 环境中
cd ~/pdf_compressor

# 运行压缩，保留临时文件
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure
```

**关键参数**：
- `--keep-temp-on-failure`: 即使失败也保留临时目录
- 或者修改代码临时禁用自动清理

### 步骤2：找到临时目录

在压缩过程的输出中，会显示临时目录路径：

```
[信息] 临时工作目录: /tmp/tmpXXXXXX
```

或者在日志文件中搜索：

```bash
grep "临时" logs/compression_*.log
```

### 步骤3：进入临时目录查看文件

```bash
cd /tmp/tmpXXXXXX

# 列出所有文件
ls -lh

# 你应该看到：
# page-001.tif
# page-002.tif
# ...
# page-156.tif
# combined.hocr  ← 原始 hOCR 文件 (约 9 MB)
```

### 步骤4：复制文件到项目目录（可选）

```bash
# 复制原始 hOCR（如果还没有）
cp combined.hocr /mnt/c/Users/quying/Projects/pdf_compressor/docs/testpdf156.hocr

# 注意：图像文件很大（约 400-500 MB），通常不需要复制
# 直接在临时目录中进行测试即可
```

---

## 🧪 方法2：手动解构 PDF（如果需要）

如果临时目录已被清理，可以手动解构 PDF：

### 使用 Ghostscript 提取图像

```bash
# 安装 ghostscript（如果还没安装）
sudo apt-get install ghostscript

# 解构 PDF 为 TIFF 图像
gs -dNOPAUSE -dBATCH -sDEVICE=tiff24nc -r300 \
   -sOutputFile=page-%03d.tif \
   testpdf156.pdf
```

**说明**：
- `-r300`: 分辨率 300 DPI
- `-sDEVICE=tiff24nc`: 24位彩色 TIFF
- `-sOutputFile=page-%03d.tif`: 输出文件名格式

### 使用 ocrmypdf-recode 生成 hOCR

```bash
# 对所有图像进行 OCR
tesseract page-001.tif page-001 -l chi_sim hocr
tesseract page-002.tif page-002 -l chi_sim hocr
# ... (重复所有页面)

# 或使用循环
for i in {001..156}; do
    tesseract page-$i.tif page-$i -l chi_sim hocr
done

# 合并所有 hOCR 文件
# （这一步比较复杂，通常用 Python 脚本处理）
```

**⚠️ 注意**：手动方式很繁琐，强烈推荐使用方法1！

---

## 🎯 在临时目录中直接测试（最简单）

**推荐做法**：不复制文件，直接在临时目录测试

### 步骤1：运行压缩任务

```bash
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure
```

### 步骤2：在压缩失败后，进入临时目录

```bash
cd /tmp/tmpXXXXXX  # 使用输出中显示的实际路径
```

### 步骤3：直接在这里测试优化后的 hOCR

```bash
# 复制优化后的 hOCR 文件到这里
cp /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr ./

# 使用原始图像和优化 hOCR 生成 PDF
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words.pdf

# 检查结果
ls -lh test_no_words.pdf

# 对比原始 hOCR 版本（如果 combined.hocr 还在）
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_original.pdf

# 对比大小
ls -lh test_*.pdf
```

---

## 📊 文件大小参考

**图像栈**（156 页）：
- 单个 TIFF 文件：约 2-3 MB（300 DPI）
- 总大小：约 **300-500 MB**

**hOCR 文件**：
- 原始：9.05 MB
- 优化后（no_words）：1.60 MB

**生成的 PDF**（S7 参数）：
- 预期：2-8 MB 范围

---

## 🔍 验证文件是否正确

### 检查图像文件

```bash
# 统计文件数量
ls page-*.tif | wc -l
# 应该输出: 156

# 检查文件格式
file page-001.tif
# 应该输出: TIFF image data, ...

# 查看图像信息
identify page-001.tif
# 应该显示: 宽度 x 高度, 分辨率, 颜色深度
```

### 检查 hOCR 文件

```bash
# 查看文件大小
ls -lh combined.hocr
# 应该约 9 MB

# 检查 XML 格式
head -20 combined.hocr
# 应该看到: <?xml version="1.0"...
#           <html xmlns="http://www.w3.org/1999/xhtml"...

# 统计页面数
grep -c "ocr_page" combined.hocr
# 应该输出: 156
```

---

## 💡 实用技巧

### 1. 保留临时目录的方法

**方法A**：修改代码临时禁用清理

编辑 `compressor/pipeline.py`：

```python
# 找到清理临时目录的代码，注释掉
# shutil.rmtree(temp_dir)
print(f"临时目录已保留: {temp_dir}")
```

**方法B**：在失败时自动保留

代码已支持 `--keep-temp-on-failure` 参数。

### 2. 快速定位最新临时目录

```bash
# 找到最近创建的 /tmp/tmp* 目录
ls -lt /tmp/ | grep tmp | head -1

# 或者
cd $(ls -td /tmp/tmp* | head -1)
```

### 3. 节省磁盘空间

图像文件很大，测试完成后及时清理：

```bash
# 只保留必要的文件
rm page-*.tif  # 删除图像（如果不再需要）
# 保留 hOCR 和生成的 PDF 用于分析
```

---

## ✅ 准备就绪的检查清单

在开始 hOCR 测试前，确认：

- [ ] 有 156 个 `page-XXX.tif` 文件
- [ ] 有原始 `combined.hocr` 文件（约 9 MB）
- [ ] 优化后的 hOCR 文件已准备好
- [ ] `recode_pdf` 命令可用
- [ ] 有足够的磁盘空间（至少 1 GB）

---

## 🚀 快速测试命令

```bash
# 一键测试流程
cd /tmp/tmpXXXXXX  # 你的临时目录

# 复制优化 hOCR
cp /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr ./

# 生成测试 PDF
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 --bg-downsample 10 -J grok \
    -o test_no_words.pdf

# 查看结果
ls -lh test_no_words.pdf
echo "如果 PDF 成功生成，这将是一个重大突破！"
```

---

**创建日期**: 2025-10-19  
**适用场景**: hOCR 优化测试  
**关键提示**: 直接在压缩任务的临时目录中测试最简单！
