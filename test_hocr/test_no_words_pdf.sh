#!/bin/bash
# hOCR优化 - PDF生成测试脚本
# 测试删除ocrx_word标签后的hOCR是否能正常生成PDF

set -e  # 遇到错误立即退出

echo "=========================================="
echo "hOCR优化 PDF生成测试"
echo "测试目标：验证no_words版本能否生成PDF"
echo "=========================================="

# 1. 检查必要文件
echo ""
echo "[1/5] 检查测试文件..."
if [ ! -f "docs/hocr_experiments/combined_no_words.hocr" ]; then
    echo "❌ 错误：找不到 combined_no_words.hocr"
    exit 1
fi
echo "✅ hOCR文件就绪 ($(du -h docs/hocr_experiments/combined_no_words.hocr | cut -f1))"

# 2. 检查原始图像栈
echo ""
echo "[2/5] 检查原始图像栈..."
# 这里需要你提供原始的 page-*.tif 文件路径
# 假设它们在某个临时目录或测试目录中
if [ -z "$IMAGE_DIR" ]; then
    echo "⚠️  警告：未设置 IMAGE_DIR 环境变量"
    echo "请使用: IMAGE_DIR=/path/to/images ./test_no_words_pdf.sh"
    exit 1
fi

if [ ! -d "$IMAGE_DIR" ]; then
    echo "❌ 错误：图像目录不存在: $IMAGE_DIR"
    exit 1
fi

IMAGE_COUNT=$(ls "$IMAGE_DIR"/page-*.tif 2>/dev/null | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "❌ 错误：在 $IMAGE_DIR 中找不到 page-*.tif 文件"
    exit 1
fi
echo "✅ 找到 $IMAGE_COUNT 个图像文件"

# 3. 创建输出目录
echo ""
echo "[3/5] 准备测试环境..."
TEST_DIR="docs/hocr_experiments/pdf_test"
mkdir -p "$TEST_DIR"
echo "✅ 测试目录：$TEST_DIR"

# 4. 运行 recode_pdf (关键测试)
echo ""
echo "[4/5] 运行 recode_pdf (使用no_words hOCR)..."
echo "命令：recode_pdf --from-imagestack $IMAGE_DIR/page-*.tif \\"
echo "                  --hocr-file docs/hocr_experiments/combined_no_words.hocr \\"
echo "                  --dpi 72 \\"
echo "                  --bg-downsample 10 \\"
echo "                  -J grok \\"
echo "                  -o $TEST_DIR/test_no_words.pdf"
echo ""

START_TIME=$(date +%s)
recode_pdf --from-imagestack "$IMAGE_DIR"/page-*.tif \
    --hocr-file docs/hocr_experiments/combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o "$TEST_DIR/test_no_words.pdf"
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
if [ -f "$TEST_DIR/test_no_words.pdf" ]; then
    echo "✅ PDF 生成成功！"
    echo "   耗时：${ELAPSED}秒"
else
    echo "❌ PDF 生成失败"
    exit 1
fi

# 5. 分析结果
echo ""
echo "[5/5] 测试结果分析..."
PDF_SIZE=$(du -h "$TEST_DIR/test_no_words.pdf" | cut -f1)
PDF_SIZE_MB=$(du -m "$TEST_DIR/test_no_words.pdf" | cut -f1)
echo "PDF大小：$PDF_SIZE (${PDF_SIZE_MB}MB)"

# 如果存在原始PDF（使用完整hOCR），进行对比
if [ -n "$ORIGINAL_PDF" ] && [ -f "$ORIGINAL_PDF" ]; then
    ORIGINAL_SIZE_MB=$(du -m "$ORIGINAL_PDF" | cut -f1)
    SAVED_MB=$((ORIGINAL_SIZE_MB - PDF_SIZE_MB))
    SAVED_PERCENT=$((SAVED_MB * 100 / ORIGINAL_SIZE_MB))
    
    echo ""
    echo "=========================================="
    echo "对比分析"
    echo "=========================================="
    echo "原始PDF (完整hOCR)：${ORIGINAL_SIZE_MB}MB"
    echo "优化PDF (no_words)：${PDF_SIZE_MB}MB"
    echo "节省空间：${SAVED_MB}MB (${SAVED_PERCENT}%)"
fi

echo ""
echo "=========================================="
echo "✅ 测试完成"
echo "=========================================="
echo "输出文件：$TEST_DIR/test_no_words.pdf"
echo ""
echo "下一步："
echo "1. 打开PDF检查可搜索性"
echo "2. 测试文本选择和复制功能"
echo "3. 如果成功，准备集成到 pipeline.py"
