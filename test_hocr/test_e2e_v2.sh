#!/bin/bash
# 快速 hOCR 优化测试 - 直接使用 PDF 文件（改进版）

set -e  # 遇到错误立即退出

PDF_FILE="${1:-}"

if [ -z "$PDF_FILE" ]; then
    echo "用法: $0 <PDF文件>"
    echo ""
    echo "示例: bash test_quick_e2e.sh test.pdf"
    exit 1
fi

if [ ! -f "$PDF_FILE" ]; then
    echo "❌ 错误: 找不到文件: $PDF_FILE"
    exit 1
fi

# 转换为绝对路径
PDF_FILE=$(realpath "$PDF_FILE")
PDF_NAME=$(basename "$PDF_FILE")

echo "=========================================="
echo "🎯 hOCR 优化端到端测试"
echo "=========================================="
echo ""
echo "📄 PDF 文件: $PDF_NAME"
echo "📁 完整路径: $PDF_FILE"
echo "📊 文件大小: $(du -h "$PDF_FILE" | cut -f1)"
echo ""

# 创建临时目录
TEMP_DIR="/tmp/hocr_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEMP_DIR"
echo "📂 临时目录: $TEMP_DIR"
echo ""

cd "$TEMP_DIR"

# ============================================
# 步骤 1: 解构 PDF
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[1/5] 解构 PDF → TIFF 图像"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pdftoppm -tiff -tiffcompression lzw -r 300 "$PDF_FILE" page

IMAGE_COUNT=$(ls page-*.tif 2>/dev/null | wc -l)

if [ $IMAGE_COUNT -eq 0 ]; then
    echo ""
    echo "❌ 错误: 未生成任何图像文件"
    echo ""
    echo "请检查:"
    echo "1. PDF 文件是否正常"
    echo "2. pdftoppm 是否已安装: sudo apt install poppler-utils"
    exit 1
fi

FIRST_IMAGE=$(ls page-*.tif | head -1)
IMAGE_SIZE=$(du -h "$FIRST_IMAGE" | cut -f1)

echo "✅ 成功: 生成 $IMAGE_COUNT 个图像文件"
echo "   单个文件大小: ~$IMAGE_SIZE"
echo ""

# ============================================
# 步骤 2: OCR 识别
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[2/5] OCR 识别 → 生成 hOCR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

OCR_COUNT=0
for img in page-*.tif; do
    base=$(basename "$img" .tif)
    OCR_COUNT=$((OCR_COUNT + 1))
    echo -ne "\r   进度: $OCR_COUNT/$IMAGE_COUNT"
    tesseract "$img" "$base" -l chi_sim hocr 2>/dev/null
done
echo ""

HOCR_COUNT=$(ls page-*.hocr 2>/dev/null | wc -l)
if [ $HOCR_COUNT -eq 0 ]; then
    echo ""
    echo "❌ 错误: OCR 未生成任何 hOCR 文件"
    echo ""
    echo "请检查:"
    echo "1. tesseract 是否已安装: sudo apt install tesseract-ocr"
    echo "2. 中文语言包是否已安装: sudo apt install tesseract-ocr-chi-sim"
    exit 1
fi

echo "✅ 成功: 生成 $HOCR_COUNT 个 hOCR 文件"
echo ""

# ============================================
# 步骤 3: 合并 hOCR
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[3/5] 合并 hOCR 文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'PYTHON_MERGE'
import glob
import re
import sys

files = sorted(glob.glob('page-*.hocr'))
if not files:
    print("❌ 错误: 没有找到 hOCR 文件")
    sys.exit(1)

print(f"   合并 {len(files)} 个文件...")

# 读取第一个文件作为模板
with open(files[0], 'r', encoding='utf-8') as f:
    template = f.read()

# 分离头部和尾部
body_match = re.search(r'<body>(.*?)</body>', template, re.DOTALL)
if not body_match:
    print("❌ 错误: 无法解析 hOCR 格式")
    sys.exit(1)

header = template[:body_match.start(1)]
footer = template[body_match.end(1):]

# 收集所有页面
pages = []
for hocr_file in files:
    with open(hocr_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
    if match:
        pages.append(match.group(1))

# 合并并写入
merged = header + '\n'.join(pages) + footer
with open('combined.hocr', 'w', encoding='utf-8') as f:
    f.write(merged)

print(f"✅ 成功: combined.hocr ({len(merged)/1024/1024:.1f} MB)")
PYTHON_MERGE

if [ ! -f "combined.hocr" ]; then
    echo "❌ 错误: 合并失败"
    exit 1
fi

ORIGINAL_HOCR_SIZE=$(du -h combined.hocr | cut -f1)
echo ""

# ============================================
# 步骤 4: 优化 hOCR
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[4/5] 优化 hOCR (删除 ocrx_word 标签)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'PYTHON_OPTIMIZE'
import re

with open('combined.hocr', 'r', encoding='utf-8') as f:
    content = f.read()

original_size = len(content)

# 删除所有 ocrx_word 标签
optimized = re.sub(
    r"<span class='ocrx_word'[^>]*>.*?</span>",
    '',
    content,
    flags=re.DOTALL
)

optimized_size = len(optimized)
reduction = (1 - optimized_size / original_size) * 100

with open('combined_no_words.hocr', 'w', encoding='utf-8') as f:
    f.write(optimized)

print(f"   原始大小: {original_size/1024/1024:.2f} MB")
print(f"   优化后:   {optimized_size/1024/1024:.2f} MB")
print(f"   减少:     {reduction:.1f}%")
print(f"✅ 成功: combined_no_words.hocr")
PYTHON_OPTIMIZE

echo ""

# ============================================
# 步骤 5: 生成 PDF
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[5/5] 生成测试 PDF"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 测试 1: 原始 hOCR
echo "   [1/2] 使用原始 hOCR..."
if recode_pdf --from-imagestack "page-*.tif" \
    --hocr-file combined.hocr \
    --dpi 300 \
    --bg-downsample 2 \
    -J grok \
    -o test_original.pdf 2>&1 | grep -i "error\|traceback" ; then
    echo "      ⚠️  原始版本生成时出现错误（继续）"
fi

if [ -f "test_original.pdf" ]; then
    echo "      ✅ test_original.pdf ($(du -h test_original.pdf | cut -f1))"
else
    echo "      ⚠️  未生成（可能有错误）"
fi
echo ""

# 测试 2: 优化 hOCR
echo "   [2/2] 使用优化 hOCR (no_words)..."
if recode_pdf --from-imagestack "page-*.tif" \
    --hocr-file combined_no_words.hocr \
    --dpi 300 \
    --bg-downsample 2 \
    -J grok \
    -o test_no_words.pdf 2>&1 | grep -i "error\|traceback" ; then
    echo "      ❌ 优化版本生成失败"
    exit 1
fi

if [ -f "test_no_words.pdf" ]; then
    echo "      ✅ test_no_words.pdf ($(du -h test_no_words.pdf | cut -f1))"
else
    echo "      ❌ 未生成"
    exit 1
fi

echo ""
echo "=========================================="
echo "📊 测试结果"
echo "=========================================="
echo ""

# 详细列表
echo "hOCR 文件:"
ls -lh combined*.hocr | awk '{printf "  %-30s %8s\n", $9, $5}'

echo ""
echo "PDF 文件:"
ls -lh test_*.pdf | awk '{printf "  %-30s %8s\n", $9, $5}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 计算节省
if [ -f "test_original.pdf" ] && [ -f "test_no_words.pdf" ]; then
    ORIG_SIZE=$(stat -c%s test_original.pdf 2>/dev/null || stat -f%z test_original.pdf)
    OPT_SIZE=$(stat -c%s test_no_words.pdf 2>/dev/null || stat -f%z test_no_words.pdf)
    DIFF=$((ORIG_SIZE - OPT_SIZE))
    
    if [ $DIFF -gt 0 ]; then
        DIFF_MB=$(echo "scale=2; $DIFF / 1024 / 1024" | bc)
        PCT=$(echo "scale=1; $DIFF * 100 / $ORIG_SIZE" | bc)
        echo "💾 节省空间: ${DIFF_MB} MB (${PCT}%)"
    elif [ $DIFF -lt 0 ]; then
        DIFF_MB=$(echo "scale=2; -$DIFF / 1024 / 1024" | bc)
        echo "⚠️  优化后反而增大了 ${DIFF_MB} MB"
    else
        echo "📊 大小基本相同"
    fi
fi

echo ""
echo "📁 所有文件位置:"
echo "   $TEMP_DIR"
echo ""
echo "✅ 测试完成!"
echo ""
echo "下一步:"
echo "1. 检查 PDF 质量: cd $TEMP_DIR"
echo "2. 复制到 Windows: cp test_*.pdf /mnt/c/Users/..."
echo "3. 测试可搜索性（预期：原始可搜索，优化不可搜索）"
