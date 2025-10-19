#!/bin/bash
# 快速 hOCR 优化测试 - 直接使用 PDF 文件

PDF_FILE="${1:-}"

if [ -z "$PDF_FILE" ] || [ ! -f "$PDF_FILE" ]; then
    echo "用法: $0 <PDF文件>"
    echo ""
    echo "示例: bash test_quick_e2e.sh test.pdf"
    exit 1
fi

# 转换为绝对路径
PDF_FILE=$(realpath "$PDF_FILE")

echo "🎯 快速 hOCR 优化测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PDF: $PDF_FILE"
echo "大小: $(du -h "$PDF_FILE" | cut -f1)"
echo ""

# 创建临时目录
TEMP_DIR="/tmp/hocr_quick_test_$$"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "[1/4] 解构 PDF..."
pdftoppm -tiff -tiffcompression lzw -r 300 "$PDF_FILE" page 2>&1 | head -5
echo "      ✅ $(ls page-*.tif | wc -l) 页"

echo "[2/4] OCR 识别..."
for img in page-*.tif; do
    tesseract "$img" "$(basename "$img" .tif)" -l chi_sim hocr 2>/dev/null
done

# 简单合并 hOCR（只取第一个文件的框架，插入所有页面）
python3 -c "
import glob, re
files = sorted(glob.glob('page-*.hocr'))
with open(files[0], 'r', encoding='utf-8') as f:
    template = f.read()
header = template.split('<body>')[0] + '<body>\n'
footer = '\n</body></html>'
pages = []
for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    match = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
    if match:
        pages.append(match.group(1))
with open('combined.hocr', 'w', encoding='utf-8') as out:
    out.write(header + '\n'.join(pages) + footer)
"
echo "      ✅ hOCR: $(du -h combined.hocr | cut -f1)"

echo "[3/4] 优化 hOCR (删除 ocrx_word)..."
python3 -c "
import re
with open('combined.hocr', 'r', encoding='utf-8') as f:
    content = f.read()
optimized = re.sub(r\"<span class='ocrx_word'[^>]*>.*?</span>\", '', content, flags=re.DOTALL)
with open('combined_no_words.hocr', 'w', encoding='utf-8') as f:
    f.write(optimized)
reduction = (1 - len(optimized)/len(content)) * 100
print(f'      ✅ 优化: {len(content)/1024/1024:.1f}MB → {len(optimized)/1024/1024:.1f}MB (-{reduction:.1f}%)')
"

echo "[4/4] 生成 PDF..."
echo "      原始 hOCR..."
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined.hocr \
    --dpi 300 --bg-downsample 2 -J grok \
    -o test_original.pdf 2>&1 | grep -v "^$"

echo "      优化 hOCR..."
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 300 --bg-downsample 2 -J grok \
    -o test_no_words.pdf 2>&1 | grep -v "^$"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 结果"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -lh test_*.pdf combined*.hocr | awk '{printf "%-25s %5s\n", $9, $5}'
echo ""
echo "📁 位置: $TEMP_DIR"
echo ""

if [ -f "test_original.pdf" ] && [ -f "test_no_words.pdf" ]; then
    ORIG_SIZE=$(stat -c%s test_original.pdf 2>/dev/null || stat -f%z test_original.pdf)
    OPT_SIZE=$(stat -c%s test_no_words.pdf 2>/dev/null || stat -f%z test_no_words.pdf)
    DIFF=$((ORIG_SIZE - OPT_SIZE))
    
    if [ $DIFF -gt 0 ]; then
        DIFF_MB=$(echo "scale=2; $DIFF / 1024 / 1024" | bc)
        PCT=$(echo "scale=1; $DIFF * 100 / $ORIG_SIZE" | bc)
        echo "✅ 成功! 节省 ${DIFF_MB}MB (${PCT}%)"
    else
        echo "⚠️  优化后大小未减小"
    fi
fi
