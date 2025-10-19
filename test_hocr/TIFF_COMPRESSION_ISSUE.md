# TIFF 图像文件过大问题分析与解决方案

## 🔍 问题描述

**现象**: 项目生成的每个 TIFF 图像文件高达 **25 MB**

**影响**:
- 156 页 PDF → 156 个 TIFF 文件 → **约 3.9 GB** 磁盘占用
- 严重浪费磁盘空间
- 增加 I/O 开销，拖慢处理速度

---

## 🎯 根本原因

### 当前使用的命令

```bash
pdftoppm -tiff -r 300 input.pdf output_prefix
```

**问题**: `-tiff` 参数生成的是 **未压缩的 TIFF 文件**！

### TIFF 文件大小分析

**以 A4 纸张 300 DPI 为例**：

```
计算公式：
文件大小 = 宽度 × 高度 × 颜色深度 / 8

A4 @ 300 DPI:
- 宽度: 8.27 英寸 × 300 DPI = 2,481 像素
- 高度: 11.69 英寸 × 300 DPI = 3,507 像素
- 颜色深度: 24 位（RGB，每通道 8 位）

未压缩大小 = 2,481 × 3,507 × 24 / 8
           = 2,481 × 3,507 × 3
           = 26,096,301 字节
           ≈ 24.9 MB  ← 正好是你看到的 25 MB！
```

**确认**: 你的 TIFF 文件是完全未压缩的原始位图。

---

## ✅ 解决方案

### 方案 1: 使用 LZW 压缩（推荐）

**特点**:
- ✅ **无损压缩**（质量不变）
- ✅ 兼容性极佳（所有工具都支持）
- ✅ 压缩率：约 50-70%（25 MB → 7-12 MB）
- ✅ 速度快

**修改命令**:

```bash
pdftoppm -tiff -tiffcompression lzw -r 300 input.pdf output_prefix
```

**或者使用 Ghostscript**:

```bash
gs -dNOPAUSE -dBATCH -sDEVICE=tifflzw -r300 \
   -sOutputFile=page-%03d.tif input.pdf
```

---

### 方案 2: 使用 ZIP 压缩（最佳压缩率）

**特点**:
- ✅ **无损压缩**
- ✅ 压缩率最高：约 70-80%（25 MB → 5-7 MB）
- ⚠️ 兼容性稍差（老版本工具可能不支持）

**修改命令**:

```bash
pdftoppm -tiff -tiffcompression zip -r 300 input.pdf output_prefix
```

---

### 方案 3: 使用 JPEG 压缩（如果可接受轻微损失）

**特点**:
- ⚠️ **有损压缩**（轻微质量损失）
- ✅ 压缩率极高：约 90-95%（25 MB → 1-2 MB）
- ✅ 兼容性好
- ⚠️ 不推荐用于 OCR（可能影响识别率）

**修改命令**:

```bash
pdftoppm -jpeg -r 300 input.pdf output_prefix
```

---

### 方案 4: 使用 PNG 格式（平衡选择）

**特点**:
- ✅ **无损压缩**
- ✅ 自动压缩
- ✅ 压缩率：约 50-60%（25 MB → 10-12 MB）
- ✅ 兼容性极佳
- ⚠️ 需要确认 recode_pdf 是否支持 PNG

**修改命令**:

```bash
pdftoppm -png -r 300 input.pdf output_prefix
```

---

## 📊 方案对比

| 方案 | 文件大小 | 压缩率 | 质量 | 兼容性 | OCR适用 | 推荐度 |
|------|---------|--------|------|--------|---------|--------|
| **未压缩 TIFF** | 25 MB | 0% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ 浪费空间 |
| **LZW TIFF** | 7-12 MB | 50-70% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ 首选 |
| **ZIP TIFF** | 5-7 MB | 70-80% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ 备选 |
| **JPEG** | 1-2 MB | 90-95% | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⚠️ 不推荐 OCR |
| **PNG** | 10-12 MB | 50-60% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ 需测试 |

---

## 🔧 代码修改

### 修改 `compressor/pipeline.py`

#### 方案 1: 添加 LZW 压缩（推荐）

```python
def deconstruct_pdf_to_images(pdf_path, temp_dir, dpi):
    """
    使用 pdftoppm 将 PDF 转换为 TIFF 图像序列。
    返回生成的图像文件路径列表。
    """
    logging.info(f"阶段1 [解构]: 开始将 {pdf_path.name} 转换为图像 (DPI: {dpi})...")
    output_prefix = temp_dir / "page"
    command = [
        "pdftoppm",
        "-tiff",
        "-tiffcompression", "lzw",  # ← 添加 LZW 压缩
        "-r", str(dpi),
        str(pdf_path),
        str(output_prefix)
    ]
    if not utils.run_command(command):
        logging.error("PDF解构失败。")
        return None
    
    image_files = sorted(glob.glob(f"{output_prefix}-*.tif"))
    if not image_files:
        logging.error("未生成任何图像文件。")
        return None
        
    logging.info(f"成功生成 {len(image_files)} 页图像。")
    return [Path(f) for f in image_files]
```

#### 方案 2: 使用 PNG 格式（需测试兼容性）

```python
def deconstruct_pdf_to_images(pdf_path, temp_dir, dpi):
    """
    使用 pdftoppm 将 PDF 转换为 PNG 图像序列。
    返回生成的图像文件路径列表。
    """
    logging.info(f"阶段1 [解构]: 开始将 {pdf_path.name} 转换为图像 (DPI: {dpi})...")
    output_prefix = temp_dir / "page"
    command = [
        "pdftoppm",
        "-png",  # ← 改用 PNG
        "-r", str(dpi),
        str(pdf_path),
        str(output_prefix)
    ]
    if not utils.run_command(command):
        logging.error("PDF解构失败。")
        return None
    
    # 注意文件扩展名变化
    image_files = sorted(glob.glob(f"{output_prefix}-*.png"))
    if not image_files:
        logging.error("未生成任何图像文件。")
        return None
        
    logging.info(f"成功生成 {len(image_files)} 页图像。")
    return [Path(f) for f in image_files]
```

**⚠️ PNG 方案需要确认**：
1. `recode_pdf` 是否支持 PNG 输入
2. `tesseract` 是否支持 PNG（通常支持）

---

## 🧪 测试方法

### 测试不同压缩方案

```bash
# 测试 LZW TIFF
pdftoppm -tiff -tiffcompression lzw -r 300 test.pdf test_lzw

# 测试 ZIP TIFF
pdftoppm -tiff -tiffcompression zip -r 300 test.pdf test_zip

# 测试 PNG
pdftoppm -png -r 300 test.pdf test_png

# 对比文件大小
ls -lh test_*-1.*
```

### 测试 recode_pdf 兼容性

```bash
# 测试 LZW TIFF
tesseract test_lzw-1.tif test_lzw -l chi_sim hocr
recode_pdf --from-imagestack test_lzw-*.tif \
    --hocr-file test_lzw.hocr \
    --dpi 300 --bg-downsample 2 \
    -o test_lzw.pdf

# 测试 PNG
tesseract test_png-1.png test_png -l chi_sim hocr
recode_pdf --from-imagestack test_png-*.png \
    --hocr-file test_png.hocr \
    --dpi 300 --bg-downsample 2 \
    -o test_png.pdf
```

---

## 📈 预期效果

### 对 156 页 PDF 项目的影响

**当前情况（未压缩 TIFF）**:
- 单个文件: 25 MB
- 156 页总计: **3.9 GB**
- 处理时间: 约 5-10 分钟
- 磁盘 I/O: 很高

**使用 LZW 压缩后**:
- 单个文件: 约 8 MB（减少 68%）
- 156 页总计: **约 1.25 GB**（节省 2.65 GB！）
- 处理时间: 约 5-10 分钟（几乎不变）
- 磁盘 I/O: 显著降低

**使用 PNG 格式后**:
- 单个文件: 约 10 MB（减少 60%）
- 156 页总计: **约 1.56 GB**（节省 2.34 GB）
- 处理时间: 可能稍慢（PNG 编码）
- 兼容性: 需要测试

---

## ⚠️ 注意事项

### 1. 不要使用有损压缩

- ❌ JPEG: 会引入压缩伪影，影响 OCR 识别率
- ✅ LZW/ZIP/PNG: 无损压缩，质量完全保留

### 2. 确认工具链兼容性

**需要验证**:
- `tesseract` 是否支持压缩 TIFF/PNG（通常支持）
- `recode_pdf` 是否支持压缩 TIFF/PNG（需要查文档或测试）

**测试命令**:
```bash
# 测试 tesseract
tesseract compressed.tif output -l chi_sim hocr

# 查看 recode_pdf 支持的格式
recode_pdf --help | grep -i format
```

### 3. 性能考虑

**压缩开销**:
- LZW: 几乎无开销（+0-5%）
- ZIP: 轻微开销（+5-10%）
- PNG: 可能较慢（+10-20%）

**建议**: 优先使用 LZW，如果工具支持的话。

---

## 🎯 推荐实施步骤

### 步骤 1: 快速测试

```bash
# 在 WSL/Ubuntu 中测试
cd ~/pdf_compressor

# 测试 LZW 压缩
pdftoppm -tiff -tiffcompression lzw -r 300 \
    testpdf156.pdf /tmp/test_lzw

# 检查文件大小
ls -lh /tmp/test_lzw-000001.tif
# 应该显示约 7-12 MB

# 测试 OCR
tesseract /tmp/test_lzw-000001.tif /tmp/test_lzw -l chi_sim hocr

# 检查 hOCR 生成是否正常
ls -lh /tmp/test_lzw.hocr
```

### 步骤 2: 修改代码

如果测试成功，修改 `compressor/pipeline.py`：

```python
command = [
    "pdftoppm",
    "-tiff",
    "-tiffcompression", "lzw",  # 添加这一行
    "-r", str(dpi),
    str(pdf_path),
    str(output_prefix)
]
```

### 步骤 3: 完整测试

```bash
# 运行完整压缩流程
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure

# 检查临时目录中的文件大小
cd /tmp/tmpXXXXXX
ls -lh page-*.tif

# 应该看到每个文件约 7-12 MB（而不是 25 MB）
```

### 步骤 4: 性能对比

记录优化前后的指标：

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| 单个 TIFF 大小 | 25 MB | 8 MB | -68% |
| 156 页总大小 | 3.9 GB | 1.25 GB | -68% |
| 解构时间 | ? 分钟 | ? 分钟 | ? |
| 总处理时间 | ? 分钟 | ? 分钟 | ? |

---

## 📝 相关文档更新

需要更新的文档：
- [x] `test_hocr/TIFF_COMPRESSION_ISSUE.md` - 本文档
- [ ] `README.md` - 更新技术说明
- [ ] `docs/TROUBLESHOOTING.md` - 添加 TIFF 大小问题说明
- [ ] `docs/QUICKSTART.md` - 提及压缩优化

---

## 🔍 延伸阅读

### TIFF 压缩算法对比

- **LZW**: Lempel-Ziv-Welch，无损，专利已过期，广泛支持
- **ZIP**: Deflate 算法，无损，压缩率高，较新的标准
- **PackBits**: 最简单的 RLE，压缩率低，兼容性最好
- **JPEG**: 有损，不适合 OCR
- **CCITT Group 4**: 仅用于黑白图像，不适合彩色

### pdftoppm 支持的压缩选项

```bash
pdftoppm --help | grep -A 10 tiffcompression

# 支持的值:
# - none       (未压缩，25 MB)
# - lzw        (LZW 压缩，7-12 MB) ← 推荐
# - zip        (ZIP 压缩，5-7 MB)
# - jpeg       (JPEG 压缩，不推荐 OCR)
# - packbits   (PackBits 压缩，15-20 MB)
```

---

**创建日期**: 2025-10-19  
**问题**: TIFF 文件 25 MB 过大  
**根本原因**: 未使用压缩  
**解决方案**: 添加 `-tiffcompression lzw` 参数  
**预期效果**: 节省 68% 磁盘空间（3.9 GB → 1.25 GB）
