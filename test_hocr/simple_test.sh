#!/bin/bash
# 超简单测试脚本 - 在临时目录中测试 hOCR 优化

echo "=== hOCR 优化测试（简化版）==="
echo ""

# 检查是否有图像文件
if ! ls page-*.tif 1> /dev/null 2>&1; then
    echo "❌ 当前目录没有 page-*.tif 文件"
    echo "请先 cd 到包含图像的目录（如 /tmp/tmpXXXXXX）"
    exit 1
fi

IMAGE_COUNT=$(ls page-*.tif 2>/dev/null | wc -l)
echo "✅ 找到 $IMAGE_COUNT 个图像文件"
echo ""

# 检查是否已有优化后的 hOCR
if [ ! -f "combined_no_words.hocr" ]; then
    echo "📥 未找到优化后的 hOCR，正在从项目复制..."
    
    # 尝试多个可能的源路径
    POSSIBLE_SOURCES=(
        "$HOME/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
        "/mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
    )
    
    COPIED=false
    for src in "${POSSIBLE_SOURCES[@]}"; do
        if [ -f "$src" ]; then
            cp "$src" ./combined_no_words.hocr
            echo "✅ 已复制: $(basename "$src")"
            COPIED=true
            break
        fi
    done
    
    if [ "$COPIED" = false ]; then
        echo ""
        echo "❌ 无法找到优化后的 hOCR 文件"
        echo ""
        echo "请手动复制文件到当前目录："
        echo "  cp /path/to/combined_no_words.hocr ."
        echo ""
        echo "或者使用原始临时目录中的 combined.hocr："
        echo "  recode_pdf --from-imagestack page-*.tif \\"
        echo "      --hocr-file combined.hocr \\"
        echo "      --dpi 72 --bg-downsample 10 -J grok \\"
        echo "      -o test_original.pdf"
        exit 1
    fi
fi

echo "📄 hOCR 文件: combined_no_words.hocr ($(du -h combined_no_words.hocr | cut -f1))"
echo "🖼️  图像数量: $IMAGE_COUNT"
echo ""
echo "开始生成 PDF..."
echo ""

# 执行 recode_pdf
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words.pdf

# 检查结果
if [ $? -eq 0 ] && [ -f "test_no_words.pdf" ]; then
    echo ""
    echo "=========================================="
    echo "✅ 成功！PDF 已生成"
    echo "=========================================="
    echo "文件: test_no_words.pdf"
    echo "大小: $(du -h test_no_words.pdf | cut -f1)"
    echo ""
    echo "下一步："
    echo "1. 检查 PDF 质量: 打开 test_no_words.pdf"
    echo "2. 对比原始版本（如果有 combined.hocr）:"
    echo "   recode_pdf --from-imagestack page-*.tif \\"
    echo "       --hocr-file combined.hocr \\"
    echo "       --dpi 72 --bg-downsample 10 -J grok \\"
    echo "       -o test_original.pdf"
    echo "3. 对比文件大小:"
    echo "   ls -lh test_*.pdf"
else
    echo ""
    echo "❌ PDF 生成失败"
    echo "请检查上面的错误信息"
    exit 1
fi
