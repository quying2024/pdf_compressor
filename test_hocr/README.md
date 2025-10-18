# hOCR 优化研究 - 快速开始指南

## 🎯 研究目标

在 156 页 PDF 测试中发现 hOCR 文件达到 **9.04 MB**，这是极限压缩的巨大瓶颈。
本研究旨在找到最优的 hOCR 优化策略，在不影响 PDF 生成的前提下最大化减小文件大小。

---

## 📋 已完成的工作

### 1. ✅ 理论分析
- 📄 `docs/hOCR结构深度分析.md` - 详细的结构分析文档
- 📄 `docs/hOCR优化研究方向.md` - 研究方向规划

### 2. ✅ 工具开发
- 🛠️ `test_hocr/hocr_analyzer.py` - hOCR 分析和优化工具
- 📝 `test_hocr/sample_hocr.html` - hOCR 样本文件

### 3. ✅ 实验框架
工具可自动生成 4 种优化版本：
- **空文本版**: 删除 `ocrx_word` 标签内的文本内容
- **最小化版**: 简化属性，只保留 bbox
- **无单词版**: 完全删除 `ocrx_word` 标签
- **无文本行版**: 删除 `ocr_line` 标签

---

## 🚀 下一步行动

### 步骤 1: 生成真实 hOCR 文件

运行压缩任务，保留临时目录以获取 hOCR 文件：

```bash
# 在 WSL/Ubuntu 环境
cd ~/pdf_compressor
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure
```

临时目录位置通常在 `/tmp/tmpXXXXXX/combined.hocr`

### 步骤 2: 分析 hOCR 文件

```bash
# 复制 hOCR 到项目目录
cp /tmp/tmpXXXXXX/combined.hocr test_hocr/real_hocr.html

# 运行分析工具
python test_hocr/hocr_analyzer.py test_hocr/real_hocr.html
```

**输出**:
- 详细的结构分析报告
- 4 个优化版本文件
- 大小对比表

### 步骤 3: 测试 PDF 生成

使用每个优化版本测试 PDF 是否能正常生成：

```bash
# 进入临时目录
cd /tmp/tmpXXXXXX

# 备份原始 hOCR
cp combined.hocr combined_original.hocr

# 测试 1: 空文本版
cp ~/pdf_compressor/test_hocr/hocr_experiments/combined_empty.hocr combined.hocr
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_empty.pdf

# 检查文件大小
ls -lh test_empty.pdf

# 测试 2: 最小化版
cp ~/pdf_compressor/test_hocr/hocr_experiments/combined_minimal.hocr combined.hocr
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_minimal.pdf

ls -lh test_minimal.pdf

# 测试 3: 无单词版
cp ~/pdf_compressor/test_hocr/hocr_experiments/combined_no_words.hocr combined.hocr
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_no_words.pdf

ls -lh test_no_words.pdf

# 对比原始版本
cp combined_original.hocr combined.hocr
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_original.pdf

ls -lh test_original.pdf

# 对比所有版本
ls -lh test_*.pdf
```

### 步骤 4: 记录结果

创建测试结果表格：

| hOCR 版本 | hOCR 大小 | PDF 能否生成 | PDF 大小 | 减少量 | 视觉质量 |
|-----------|-----------|--------------|----------|--------|----------|
| 原始 (9.04MB) | 9.04 MB | ✓ | ? MB | - | ✓ |
| 空文本 | ? MB | ? | ? MB | ? MB | ? |
| 最小化 | ? MB | ? | ? MB | ? MB | ? |
| 无单词 | ? MB | ? | ? MB | ? MB | ? |
| 无文本行 | ? MB | ? | ? MB | ? MB | ? |

---

## 📊 预期结果

### 保守估计（基于样本分析）

样本文件显示：
- 空文本版: **-3.3%**
- 最小化版: **-10.4%**
- 无单词版: **-44.0%**
- 无文本行版: **-27.7%**

对于 9.04MB 的真实 hOCR：
- 空文本版: 可能减少 **0.3-4.5 MB**
- 最小化版: 可能减少 **0.9-5.9 MB**
- 无单词版: 可能减少 **4.0-6.8 MB** ⭐

**关键**: 真实文件的文本占比可能更高（中文内容多），实际减少量可能超过估计。

---

## ⚠️ 注意事项

### 1. 功能损失
所有优化版本都会**丧失 PDF 可搜索性**：
- ❌ 无法搜索文字
- ❌ 无法复制文字
- ✅ 视觉效果保持不变
- ✅ 文件大小大幅减小

### 2. 兼容性风险
- **空文本版**: 风险低，保留所有结构
- **最小化版**: 风险中，简化属性
- **无单词版**: 风险高，删除单词级定位
- **无文本行版**: 风险很高，删除行级定位

### 3. 推荐策略
优先测试顺序：
1. **空文本版** ⭐⭐⭐ 最安全，预期有效
2. **最小化版** ⭐⭐ 额外优化，需要验证
3. **无单词版** ⭐ 激进优化，可能失败

---

## 🔧 整合到生产代码

如果测试成功，在 `pipeline.py` 中添加：

```python
def optimize_hocr_for_compression(hocr_file: Path, strategy: str = 'empty') -> Path:
    """
    为极限压缩优化 hOCR 文件
    
    Args:
        hocr_file: 原始 hOCR 文件路径
        strategy: 优化策略
            - 'empty': 删除文本内容（推荐）
            - 'minimal': 简化属性
            - 'none': 不优化
    
    Returns:
        优化后的 hOCR 文件路径
    """
    if strategy == 'none':
        return hocr_file
    
    with open(hocr_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if strategy == 'empty':
        # 删除 ocrx_word 标签内的文本内容
        optimized_content = re.sub(
            r'(<span[^>]*?ocrx_word[^>]*?>)([^<]+)(</span>)',
            r'\1\3',
            content
        )
    elif strategy == 'minimal':
        # 先删除文本
        optimized_content = re.sub(
            r'(<span[^>]*?ocrx_word[^>]*?>)([^<]+)(</span>)',
            r'\1\3',
            content
        )
        # 再简化属性
        def simplify_title(match):
            full_title = match.group(1)
            bbox_match = re.search(r'bbox \d+ \d+ \d+ \d+', full_title)
            if bbox_match:
                return f'title="{bbox_match.group()}"'
            return match.group(0)
        
        optimized_content = re.sub(
            r'title="([^"]*)"',
            simplify_title,
            optimized_content
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    # 保存优化后的文件
    optimized_file = hocr_file.parent / f"{hocr_file.stem}_optimized.hocr"
    with open(optimized_file, 'w', encoding='utf-8') as f:
        f.write(optimized_content)
    
    return optimized_file
```

在 `strategy.py` 中为 S7 方案启用：

```python
def _precompute_dar_steps(input_pdf_path, temp_dir):
    """执行一次性的解构和分析步骤"""
    # ... 现有代码 ...
    
    # 为极限压缩优化 hOCR
    if getattr(args, 'optimize_hocr', False):
        hocr_file = optimize_hocr_for_compression(hocr_file, strategy='empty')
    
    return {'image_files': image_files, 'hocr_file': hocr_file}
```

添加命令行参数：

```python
parser.add_argument('--optimize-hocr', 
                    action='store_true',
                    help='优化 hOCR 文件以减小最终 PDF 大小（丧失搜索功能）')
```

---

## 📈 成功标准

实验成功的条件：
1. ✅ PDF 能够成功生成
2. ✅ 视觉质量无明显下降
3. ✅ 文件大小有明显减少（> 2MB）
4. ✅ recode_pdf 执行时间无明显增加

如果满足以上条件，优化策略值得整合到生产环境。

---

## 📝 下一步实验检查清单

- [ ] 运行压缩任务生成真实 hOCR 文件
- [ ] 使用 hocr_analyzer.py 分析文件
- [ ] 测试空文本版能否生成 PDF
- [ ] 测试最小化版能否生成 PDF
- [ ] 测试无单词版能否生成 PDF
- [ ] 对比所有版本的 PDF 大小
- [ ] 检查视觉质量
- [ ] 记录详细测试结果
- [ ] 选择最优策略
- [ ] 整合到代码
- [ ] 更新文档

---

## 💡 预期影响

如果空文本优化成功，对于 156 页 PDF：
- hOCR: 9.04MB → 约 6MB（减少 3MB）
- 最终 PDF: 可能从无法达到 2MB → 可以达到 2MB
- **这将是突破性的改进！** 🎉

---

**创建日期**: 2025-10-19  
**状态**: 准备测试  
**下一步**: 获取真实 hOCR 文件进行实验
