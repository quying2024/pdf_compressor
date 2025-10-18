# hOCR 文件优化研究方向

## 重要发现
**日期**: 2025-10-19  
**测试文件**: 156页 PDF (136MB)  
**hOCR 文件大小**: 9.04 MB

### 关键观察
在测试 156 页 PDF 压缩时发现，生成的 hOCR 文件大小达到 **9.04 MB**，这对于极限压缩场景（目标 2MB）来说，占比非常显著。

**影响分析**:
- hOCR 文件会被嵌入到最终的 PDF 中
- 9.04MB 的 hOCR 相当于目标大小的 4.5 倍
- 在 S7 终极方案中，hOCR 可能成为瓶颈因素

---

## 研究方向

### 1. **空 hOCR 技术** (高优先级)

#### 概念
保留 hOCR 文件的结构，但删除所有 OCR 识别的文字内容。

#### 预期效果
根据研究文献，空 hOCR 可以显著降低极限压缩条件下的文件大小。

#### 实现方案
```python
def create_empty_hocr(input_hocr_file, output_hocr_file):
    """
    创建空 hOCR 文件（保留结构，删除文字内容）
    
    保留:
    - XML 结构
    - 页面信息 (ocr_page)
    - 区域信息 (ocr_carea)
    - 行信息 (ocr_line)
    - 单词边界框 (ocrx_word)
    
    删除:
    - 所有文字内容 (title 属性中的 bbox 保留)
    """
    import xml.etree.ElementTree as ET
    
    tree = ET.parse(input_hocr_file)
    root = tree.getroot()
    
    # 遍历所有包含文字的元素
    for elem in root.iter():
        if elem.text:
            elem.text = ''  # 清空文字内容
        if elem.tail:
            elem.tail = ''  # 清空尾部文字
    
    tree.write(output_hocr_file, encoding='utf-8', xml_declaration=True)
    
    return output_hocr_file
```

#### 测试计划
1. 生成原始 hOCR (9.04MB)
2. 创建空 hOCR 版本
3. 分别使用两种 hOCR 运行 S7 方案
4. 对比最终 PDF 大小和可读性

---

### 2. **可变 DPI hOCR** (中优先级)

#### 当前问题
所有压缩方案（S1-S7）都使用 300 DPI 生成的 hOCR 文件。

#### 研究问题
- S7 使用 DPI=72 重建，但 hOCR 是 300 DPI 生成的
- 这种不匹配是否会影响最终文件大小？
- 影响方向：正向（更小）还是反向（更大）？

#### 实现方案
```python
def _precompute_dar_steps_variable_dpi(input_pdf_path, temp_dir, target_scheme):
    """
    根据目标方案的 DPI 生成对应的 hOCR
    """
    scheme = COMPRESSION_SCHEMES[target_scheme]
    target_dpi = scheme['dpi']
    
    # 使用目标方案的 DPI 进行解构
    image_files = pipeline.deconstruct_pdf_to_images(
        input_pdf_path, temp_dir, dpi=target_dpi
    )
    
    # 生成对应 DPI 的 hOCR
    hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
    
    return {'image_files': image_files, 'hocr_file': hocr_file}
```

#### 测试计划
1. S1 使用 300 DPI hOCR
2. S7 使用 72 DPI hOCR
3. 对比相同方案使用不同 DPI hOCR 的效果

---

### 3. **hOCR 压缩技术** (低优先级)

#### 方向
- 使用 gzip 压缩 hOCR 文件
- 简化 hOCR XML 结构
- 移除冗余属性

#### 测试优先级
低（先验证上述两个方向的效果）

---

## 实验设计

### 实验 1: 空 hOCR vs 原始 hOCR

**测试文件**: testpdf156.pdf (156页, 136MB)

| 方案 | hOCR 类型 | hOCR 大小 | 最终 PDF 大小 | 可读性 |
|------|-----------|-----------|---------------|--------|
| S7   | 原始 (9.04MB) | 9.04MB | ? | ? |
| S7   | 空 hOCR | ? | ? | ? |

### 实验 2: 不同 DPI hOCR 对比

| 方案 | DPI | hOCR DPI | hOCR 大小 | 最终 PDF 大小 |
|------|-----|----------|-----------|---------------|
| S7   | 72  | 300      | 9.04MB    | ?             |
| S7   | 72  | 72       | ?         | ?             |

---

## 预期收益

### 乐观估计
如果空 hOCR 能减少 50% 的文件大小：
- 原 hOCR: 9.04MB
- 空 hOCR: ~4.5MB
- **节省**: 4.5MB

对于目标 2MB 的压缩任务，这是巨大的改进！

### 保守估计
即使只减少 30%：
- **节省**: 2.7MB

仍然非常可观。

---

## 实施建议

### 阶段 1: 验证空 hOCR 效果 (1-2天)
1. 实现 `create_empty_hocr()` 函数
2. 在 testpdf156.pdf 上测试
3. 评估效果和可读性

### 阶段 2: 可变 DPI 研究 (2-3天)
1. 实现 `_precompute_dar_steps_variable_dpi()` 
2. 对比不同 DPI hOCR 的效果
3. 确定最优策略

### 阶段 3: 整合到生产 (1天)
1. 为 S7 方案启用空 hOCR
2. 添加命令行参数 `--empty-hocr`
3. 更新文档

---

## 技术细节

### hOCR 文件结构示例
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <title></title>
  <meta http-equiv="content-type" content="text/html; charset=utf-8" />
  <meta name='ocr-system' content='tesseract 5.3.0' />
</head>
<body>
  <div class='ocr_page' id='page_1' title='bbox 0 0 2550 3300; ppageno 0'>
    <div class='ocr_carea' id='block_1_1' title="bbox 100 200 2450 3100">
      <p class='ocr_par' id='par_1_1' title="bbox 100 200 2450 250">
        <span class='ocr_line' id='line_1_1' title="bbox 100 200 2450 250">
          <span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250'>
            这里是识别的文字  <!-- 这部分会被删除 -->
          </span>
        </span>
      </p>
    </div>
  </div>
</body>
</html>
```

### 空 hOCR 示例
```xml
<!-- 保留所有 bbox 信息，删除文字内容 -->
<span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250'></span>
```

---

## 相关研究

### 文献参考
1. "Efficient PDF Compression Using Mixed Raster Content"
2. "hOCR: An Open Standard for Representing OCR Results"
3. Archive PDF Tools 文档关于 hOCR 处理的说明

### 社区经验
- 有用户报告空 hOCR 可减少 40-60% 文件大小
- 适用于不需要文字搜索功能的场景
- 对视觉质量无影响

---

## 风险评估

### 空 hOCR 风险
- ❌ 丧失文字搜索能力
- ❌ 丧失文字复制功能
- ✅ 保留视觉效果
- ✅ 保留页面布局

### 适用场景
- 纯归档用途（不需要搜索）
- 极限压缩场景（< 2MB）
- 图片型 PDF（OCR 准确率低）

---

## 下一步行动

**明天继续时**:
1. [ ] 实现 `create_empty_hocr()` 函数
2. [ ] 在 testpdf156.pdf 上测试空 hOCR 效果
3. [ ] 记录详细的测试数据
4. [ ] 评估是否值得整合到主流程

**备注**: 当前 v2.0.2 已解决所有紧急问题，可以从容进行 hOCR 优化研究。

---

**创建日期**: 2025-10-19  
**状态**: 待研究  
**优先级**: 高  
**预计工作量**: 4-6 天
