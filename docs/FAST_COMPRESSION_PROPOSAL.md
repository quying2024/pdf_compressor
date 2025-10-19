# 快速压缩模式提案

## 📋 背景

**问题**: 当前项目速度较慢（110秒/页），主要瓶颈在 OCR 处理（tesseract）

**发现**: 专业 PDF 压缩工具速度达到 0.1秒/页，快约 1000 倍

**原因**: 专业工具直接压缩 PDF 内部图像，无需 OCR

---

## 🎯 提案：添加"快速模式"

### 核心思路

**保留现有功能**：
- ✅ 保留完整的 DAR (解构-分析-重建) 流程
- ✅ 保留 OCR 文字层生成
- ✅ 保留 S1-S7 智能压缩策略

**新增快速模式**：
- ✅ 跳过 OCR 步骤（最大瓶颈）
- ✅ 直接压缩 PDF 内部图像
- ✅ 速度提升 5-10 倍（预估）

---

## 🔧 技术方案

### 方案 1: 使用 Ghostscript 直接压缩（推荐）

**原理**: Ghostscript 可以直接重新编码 PDF 图像

**命令示例**:
```bash
gs -sDEVICE=pdfwrite \
   -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output.pdf input.pdf
```

**压缩级别**:
- `/screen`: 72 dpi, 最小文件 (类似 S7)
- `/ebook`: 150 dpi, 平衡 (类似 S4-S5)
- `/printer`: 300 dpi, 高质量 (类似 S1-S2)

**优点**:
- ✅ 速度极快（5-10秒/文档）
- ✅ 不需要临时文件
- ✅ 支持批量处理
- ✅ Ghostscript 已在项目依赖中

**缺点**:
- ❌ 无文字层（除非原 PDF 已有）
- ❌ 压缩控制较粗糙
- ❌ 质量可能不如 MRC

---

### 方案 2: 使用 PyMuPDF (fitz) 直接压缩

**原理**: PyMuPDF 可以重新压缩 PDF 内部图像

**代码示例**:
```python
import fitz

def fast_compress_pdf(input_pdf, output_pdf, quality=75):
    """快速压缩 PDF（无 OCR）"""
    doc = fitz.open(input_pdf)
    
    for page in doc:
        # 获取页面上的所有图像
        image_list = page.get_images()
        
        for img in image_list:
            xref = img[0]
            # 提取图像
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # 重新压缩为 JPEG
            from PIL import Image
            import io
            
            img_pil = Image.open(io.BytesIO(image_bytes))
            
            # 压缩并替换
            output_buffer = io.BytesIO()
            img_pil.save(output_buffer, format='JPEG', 
                        quality=quality, optimize=True)
            output_buffer.seek(0)
            
            # 替换 PDF 中的图像
            page.replace_image(xref, stream=output_buffer.read())
    
    # 保存压缩后的 PDF
    doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    doc.close()
```

**优点**:
- ✅ 速度快（10-30秒/文档）
- ✅ 精细控制压缩参数
- ✅ 可以选择性压缩大图像
- ✅ 保留原 PDF 文字层

**缺点**:
- ❌ 需要处理每个图像（相对慢）
- ❌ 压缩率可能不如 Ghostscript
- ❌ 不支持 MRC 分层压缩

---

### 方案 3: 使用 qpdf + Ghostscript 组合

**原理**: qpdf 优化 PDF 结构 + Ghostscript 压缩图像

**命令示例**:
```bash
# 步骤1: qpdf 优化结构
qpdf --linearize --object-streams=generate input.pdf temp.pdf

# 步骤2: Ghostscript 压缩图像
gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output.pdf temp.pdf
```

**优点**:
- ✅ 速度快（10-20秒/文档）
- ✅ 结构优化 + 图像压缩
- ✅ 压缩率高
- ✅ 工具已在依赖中

**缺点**:
- ❌ 两步处理
- ❌ 临时文件开销

---

## 📊 性能对比（预估）

| 方案 | 速度 (156页) | 压缩率 | 文字层 | 实现难度 |
|------|------------|--------|--------|---------|
| **当前 (DAR+OCR)** | 4.5 小时 | 极高 | ✅ 生成 | - |
| **方案1: Ghostscript** | 10-15 秒 | 高 | ⚠️ 保留原有 | ⭐ 简单 |
| **方案2: PyMuPDF** | 30-60 秒 | 中-高 | ✅ 保留原有 | ⭐⭐ 中等 |
| **方案3: qpdf+gs** | 20-30 秒 | 高 | ⚠️ 保留原有 | ⭐⭐ 中等 |
| **专业工具** | 15 秒 | 高 | ❌ 无 | - |

---

## 🚀 推荐实施方案

### 阶段 1: 添加 Ghostscript 快速模式

**命令行参数**:
```bash
python main.py --input large.pdf --output out/ --fast-mode
```

**实现**:
1. 添加 `--fast-mode` 参数
2. 检测到快速模式时，跳过 DAR 流程
3. 直接调用 Ghostscript 压缩
4. 使用映射关系：
   - S1-S2 → `/printer` (300 DPI)
   - S3-S5 → `/ebook` (150 DPI)
   - S6-S7 → `/screen` (72 DPI)

**代码修改点**:
- `main.py`: 添加 `--fast-mode` 参数
- `compressor/pipeline.py`: 添加 `fast_compress_with_ghostscript()` 函数
- `compressor/strategy.py`: 快速模式下跳过 DAR，直接调用 Ghostscript

---

### 阶段 2: 添加智能模式选择

**自动检测**:
```python
def should_use_fast_mode(pdf_path):
    """决定是否使用快速模式"""
    doc = fitz.open(pdf_path)
    
    # 检测是否已有文字层
    has_text = False
    for page in doc:
        if page.get_text().strip():
            has_text = True
            break
    
    doc.close()
    
    if has_text:
        # 已有文字层，建议快速模式
        return True, "PDF 已包含文字层，推荐使用快速模式"
    else:
        # 无文字层，建议完整模式
        return False, "PDF 无文字层，推荐使用完整模式（含 OCR）"
```

**用户交互**:
```bash
$ python main.py --input document.pdf --output out/

检测到 PDF 已包含文字层
推荐使用快速模式（预计 15 秒）

是否使用快速模式？[Y/n]: y

使用快速模式压缩...
完成！耗时 12 秒
```

---

### 阶段 3: 混合模式（最优方案）

**场景**: 部分页面有文字层，部分没有

**策略**:
1. 分析每一页是否有文字
2. 有文字的页面：快速压缩
3. 无文字的页面：完整 DAR+OCR
4. 最后合并所有页面

**预期效果**:
- 100 页有文字 → 快速压缩（10秒）
- 56 页无文字 → DAR+OCR（1小时）
- 总耗时：1小时（而非 4.5小时）

---

## 📝 用户使用场景

### 场景 1: 扫描件（无文字层）
```bash
# 必须使用完整模式
python main.py --input scan.pdf --output out/
# 自动检测无文字层，使用 DAR+OCR
# 耗时: 4.5 小时
```

### 场景 2: 电子文档（已有文字层）
```bash
# 推荐快速模式
python main.py --input ebook.pdf --output out/ --fast-mode
# 使用 Ghostscript 直接压缩
# 耗时: 15 秒
```

### 场景 3: 混合文档
```bash
# 自动智能处理
python main.py --input mixed.pdf --output out/ --auto
# 自动分析，混合使用快速+完整模式
# 耗时: 根据文字页面比例
```

---

## ⚠️ 注意事项

### 快速模式的限制

1. **不生成新文字层**
   - 仅压缩图像
   - 如果原 PDF 无文字，输出也无文字

2. **压缩率可能较低**
   - Ghostscript 不如 MRC 精细
   - 预计压缩率 50-70%（vs MRC 80-90%）

3. **质量控制较粗**
   - 只能选择预设级别
   - 无法像 S1-S7 那样精细调整

### 建议

- **扫描件**: 必须用完整模式（需要 OCR）
- **电子书**: 优先用快速模式（已有文字）
- **不确定**: 让程序自动检测

---

## 🎯 总结

### 我们的优势（保留）
- ✅ 生成高质量文字层（OCR）
- ✅ MRC 压缩率极高
- ✅ S1-S7 智能策略
- ✅ 适合归档和检索

### 新增能力（快速模式）
- ✅ 速度提升 100-300 倍
- ✅ 适合已有文字层的 PDF
- ✅ 实现简单（Ghostscript）
- ✅ 保持工具的灵活性

### 最终定位
**全能 PDF 压缩工具**:
- 需要 OCR？ → 完整模式（4.5小时）
- 仅需压缩？ → 快速模式（15秒）
- 不确定？ → 自动模式（智能选择）

**目标**: 成为既快又准的专业工具！

---

**下一步**: 实现方案 1（Ghostscript 快速模式）？
