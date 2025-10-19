#!/bin/bash
# 简化版测试脚本 - 快速验证no_words hOCR

echo "=== hOCR优化 快速测试 ==="
echo ""
echo "⚠️  使用前请确保："
echo "1. 当前目录包含 page-*.tif 图像栈"
echo "   (通常在压缩任务的临时目录中，如 /tmp/tmpXXXXXX)"
echo "2. 在 WSL/Ubuntu 环境中运行"
echo "3. 已安装 ocrmypdf-recode"
echo ""
echo "💡 提示：如果还没有图像栈，请查看 HOW_TO_GET_TEST_FILES.md"
echo ""

# 检查是否有图像文件
if ! ls page-*.tif 1> /dev/null 2>&1; then
    echo "❌ 错误：当前目录没有 page-*.tif 文件"
    echo ""
    echo "请先："
    echo "1. 运行压缩任务: python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure"
    echo "2. 进入临时目录: cd /tmp/tmpXXXXXX"
    echo "3. 再运行本脚本"
    echo ""
    echo "详细说明请查看: test_hocr/HOW_TO_GET_TEST_FILES.md"
    exit 1
fi

IMAGE_COUNT=$(ls page-*.tif 2>/dev/null | wc -l)
echo "✅ 找到 $IMAGE_COUNT 个图像文件"
echo ""

# 设置路径 - 自动检测多个可能的位置
POSSIBLE_PATHS=(
    "/mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
    "$HOME/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
    "~/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
    "./combined_no_words.hocr"
)

HOCR_FILE=""
for path in "${POSSIBLE_PATHS[@]}"; do
    expanded_path=$(eval echo "$path")
    if [ -f "$expanded_path" ]; then
        HOCR_FILE="$expanded_path"
        break
    fi
done

IMAGE_PATTERN="page-*.tif"
OUTPUT_PDF="test_no_words.pdf"

# 检查 hOCR 文件
if [ -z "$HOCR_FILE" ] || [ ! -f "$HOCR_FILE" ]; then
    echo "❌ 找不到优化后的 hOCR 文件"
    echo ""
    echo "已尝试的路径："
    for path in "${POSSIBLE_PATHS[@]}"; do
        echo "  - $path"
    done
    echo ""
    echo "解决方案："
    echo "1. 将 combined_no_words.hocr 复制到当前目录："
    echo "   cp ~/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr ."
    echo ""
    echo "2. 或手动指定 hOCR 文件路径运行 recode_pdf："
    echo "   recode_pdf --from-imagestack page-*.tif \\"
    echo "       --hocr-file /path/to/combined_no_words.hocr \\"
    echo "       --dpi 72 --bg-downsample 10 -J grok \\"
    echo "       -o test_no_words.pdf"
    exit 1
fi

echo "📄 hOCR文件：$(basename "$HOCR_FILE") ($(du -h "$HOCR_FILE" | cut -f1))"
echo "🖼️  图像模式：$IMAGE_PATTERN"
echo "📦 输出文件：$OUTPUT_PDF"
echo ""
echo "开始生成PDF..."
echo ""

# 执行关键命令
recode_pdf --from-imagestack $IMAGE_PATTERN \
    --hocr-file "$HOCR_FILE" \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o "$OUTPUT_PDF"

# 检查结果
if [ $? -eq 0 ] && [ -f "$OUTPUT_PDF" ]; then
    echo ""
    echo "✅ 成功！PDF已生成"
    echo "   大小：$(du -h "$OUTPUT_PDF" | cut -f1)"
    echo "   位置：$OUTPUT_PDF"
    echo ""
    echo "请测试："
    echo "• 打开PDF，检查显示是否正常"
    echo "• 尝试搜索文本（Ctrl+F）"
    echo "• 尝试选择和复制文本"
else
    echo ""
    echo "❌ 失败！请检查错误信息"
    exit 1
fi
