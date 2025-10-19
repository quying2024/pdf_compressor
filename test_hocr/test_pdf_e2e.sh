#!/bin/bash
# hOCR 优化端到端测试脚本
# 直接从 PDF 文件测试完整流程

set -e  # 遇到错误立即退出

echo "=========================================="
echo "hOCR 优化 - 端到端测试"
echo "=========================================="
echo ""

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <PDF文件路径> [临时目录]"
    echo ""
    echo "示例:"
    echo "  $0 test.pdf"
    echo "  $0 test.pdf /tmp/my_test"
    echo ""
    exit 1
fi

PDF_FILE="$1"
TEMP_DIR="${2:-/tmp/hocr_test_$(date +%s)}"

# 检查 PDF 文件
if [ ! -f "$PDF_FILE" ]; then
    echo "❌ 错误: 找不到 PDF 文件: $PDF_FILE"
    exit 1
fi

echo "📄 测试文件: $PDF_FILE"
echo "📂 临时目录: $TEMP_DIR"
echo "📊 PDF 大小: $(du -h "$PDF_FILE" | cut -f1)"
echo ""

# 创建临时目录
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "=========================================="
echo "步骤 1/5: 解构 PDF → TIFF 图像"
echo "=========================================="
echo ""

pdftoppm -tiff -tiffcompression lzw -r 300 "$PDF_FILE" page
IMAGE_COUNT=$(ls page-*.tif 2>/dev/null | wc -l)

if [ $IMAGE_COUNT -eq 0 ]; then
    echo "❌ 错误: 未生成任何图像文件"
    exit 1
fi

echo "✅ 成功生成 $IMAGE_COUNT 个图像"
echo "   大小: $(du -sh page-*.tif | head -1 | cut -f1) (每个)"
echo ""

echo "=========================================="
echo "步骤 2/5: OCR 识别 → 生成原始 hOCR"
echo "=========================================="
echo ""

# OCR 处理所有图像
for img in page-*.tif; do
    base=$(basename "$img" .tif)
    echo "   处理: $img"
    tesseract "$img" "$base" -l chi_sim hocr 2>/dev/null
done

# 合并 hOCR 文件
echo ""
echo "合并 hOCR 文件..."
python3 << 'EOF'
import glob
import re
from pathlib import Path

def merge_hocr_files(output_path):
    """合并多个 hOCR 文件"""
    hocr_files = sorted(glob.glob('page-*.hocr'))
    if not hocr_files:
        print("错误: 没有找到 hOCR 文件")
        return False
    
    print(f"找到 {len(hocr_files)} 个 hOCR 文件")
    
    # 读取第一个文件作为模板
    with open(hocr_files[0], 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取头部和尾部
    body_match = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
    if not body_match:
        print("错误: 无法解析 hOCR 格式")
        return False
    
    header = content[:body_match.start(1)]
    footer = content[body_match.end(1):]
    
    # 收集所有页面内容
    all_pages = []
    for hocr_file in hocr_files:
        with open(hocr_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 提取 body 中的页面内容
        page_match = re.search(r'<body>(.*?)</body>', file_content, re.DOTALL)
        if page_match:
            all_pages.append(page_match.group(1))
    
    # 合并
    merged_content = header + '\n'.join(all_pages) + footer
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"✅ 合并完成: {output_path}")
    return True

merge_hocr_files('combined_original.hocr')
EOF

if [ ! -f "combined_original.hocr" ]; then
    echo "❌ 错误: 合并 hOCR 失败"
    exit 1
fi

ORIGINAL_HOCR_SIZE=$(du -h combined_original.hocr | cut -f1)
echo "✅ 原始 hOCR: combined_original.hocr ($ORIGINAL_HOCR_SIZE)"
echo ""

echo "=========================================="
echo "步骤 3/5: 优化 hOCR → 删除 ocrx_word"
echo "=========================================="
echo ""

python3 << 'EOF'
import re

def optimize_hocr_no_words(input_file, output_file):
    """删除所有 ocrx_word 标签"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 删除 ocrx_word 标签（包括其内容）
    optimized = re.sub(
        r"<span class='ocrx_word'[^>]*>.*?</span>",
        '',
        content,
        flags=re.DOTALL
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(optimized)
    
    original_size = len(content)
    optimized_size = len(optimized)
    reduction = (1 - optimized_size / original_size) * 100
    
    print(f"原始大小: {original_size:,} 字节")
    print(f"优化后:   {optimized_size:,} 字节")
    print(f"减少:     {reduction:.1f}%")
    
    return True

optimize_hocr_no_words('combined_original.hocr', 'combined_no_words.hocr')
EOF

if [ ! -f "combined_no_words.hocr" ]; then
    echo "❌ 错误: 优化 hOCR 失败"
    exit 1
fi

OPTIMIZED_HOCR_SIZE=$(du -h combined_no_words.hocr | cut -f1)
echo "✅ 优化 hOCR: combined_no_words.hocr ($OPTIMIZED_HOCR_SIZE)"
echo ""

echo "=========================================="
echo "步骤 4/5: 生成测试 PDF"
echo "=========================================="
echo ""

# 测试1: 使用原始 hOCR
echo "[测试 1] 使用原始 hOCR 生成 PDF..."
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_original.hocr \
    --dpi 300 \
    --bg-downsample 2 \
    -J grok \
    -o test_original.pdf

if [ -f "test_original.pdf" ]; then
    ORIGINAL_PDF_SIZE=$(du -h test_original.pdf | cut -f1)
    echo "✅ 原始版本: test_original.pdf ($ORIGINAL_PDF_SIZE)"
else
    echo "⚠️  原始版本生成失败"
fi
echo ""

# 测试2: 使用优化后的 hOCR
echo "[测试 2] 使用优化 hOCR (no_words) 生成 PDF..."
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 300 \
    --bg-downsample 2 \
    -J grok \
    -o test_no_words.pdf

if [ -f "test_no_words.pdf" ]; then
    OPTIMIZED_PDF_SIZE=$(du -h test_no_words.pdf | cut -f1)
    echo "✅ 优化版本: test_no_words.pdf ($OPTIMIZED_PDF_SIZE)"
else
    echo "❌ 优化版本生成失败"
    exit 1
fi
echo ""

echo "=========================================="
echo "步骤 5/5: 结果分析"
echo "=========================================="
echo ""

# 详细对比
ls -lh test_*.pdf combined_*.hocr

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 测试结果汇总"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "原始 hOCR:   $ORIGINAL_HOCR_SIZE"
echo "优化 hOCR:   $OPTIMIZED_HOCR_SIZE"
echo ""

if [ -f "test_original.pdf" ]; then
    echo "原始 PDF:    $ORIGINAL_PDF_SIZE"
fi
echo "优化 PDF:    $OPTIMIZED_PDF_SIZE"
echo ""

# 计算节省
if [ -f "test_original.pdf" ]; then
    ORIGINAL_BYTES=$(stat -f%z test_original.pdf 2>/dev/null || stat -c%s test_original.pdf)
    OPTIMIZED_BYTES=$(stat -f%z test_no_words.pdf 2>/dev/null || stat -c%s test_no_words.pdf)
    SAVED_BYTES=$((ORIGINAL_BYTES - OPTIMIZED_BYTES))
    SAVED_MB=$(echo "scale=2; $SAVED_BYTES / 1024 / 1024" | bc)
    SAVED_PCT=$(echo "scale=1; $SAVED_BYTES * 100 / $ORIGINAL_BYTES" | bc)
    
    if [ $SAVED_BYTES -gt 0 ]; then
        echo "💾 节省空间: ${SAVED_MB} MB (${SAVED_PCT}%)"
    elif [ $SAVED_BYTES -lt 0 ]; then
        echo "⚠️  优化后反而增大了 $(echo "scale=2; -$SAVED_BYTES / 1024 / 1024" | bc) MB"
    else
        echo "📊 大小基本相同"
    fi
fi

echo ""
echo "📁 所有文件位置: $TEMP_DIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 测试完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "下一步:"
echo "1. 检查 PDF 质量:"
echo "   cd $TEMP_DIR"
echo "   # 复制 PDF 到 Windows 查看"
echo ""
echo "2. 测试可搜索性:"
echo "   打开 test_original.pdf 和 test_no_words.pdf"
echo "   尝试搜索文本 (Ctrl+F)"
echo ""
echo "3. 如果成功，集成到项目:"
echo "   - 修改 pipeline.py 添加 hOCR 优化"
echo "   - 发布 v2.1.0"
