#!/bin/bash

# install_dependencies.sh
# PDF压缩工具依赖安装脚本（Ubuntu/WSL）

echo "======================================"
echo "PDF压缩工具依赖安装脚本"
echo "======================================"

# 检查是否为Ubuntu/Debian系统
if ! command -v apt &> /dev/null; then
    echo "错误: 此脚本仅适用于Ubuntu/Debian系统"
    exit 1
fi

echo "正在更新包管理器..."
if ! sudo apt update; then
    echo "❌ 包管理器更新失败，请检查网络连接和软件源配置"
    exit 1
fi

echo "正在安装系统工具..."

# 安装poppler-utils (包含pdftoppm, pdfinfo)
echo "- 安装 poppler-utils..."
sudo apt install -y poppler-utils

# 安装tesseract-ocr
echo "- 安装 tesseract-ocr..."
sudo apt install -y tesseract-ocr

# 安装中文语言包
echo "- 安装中文语言包..."
sudo apt install -y tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# 安装qpdf
echo "- 安装 qpdf..."
sudo apt install -y qpdf

# 检查Python和pipx
if ! command -v python3 &> /dev/null; then
    echo "- 安装 Python3..."
    sudo apt install -y python3 python3-pip
fi

# 安装pipx（推荐的Python包管理工具）
if ! command -v pipx &> /dev/null; then
    echo "- 安装 pipx..."
    # 尝试通过apt安装（Ubuntu 22.04+）
    if sudo apt install -y pipx 2>/dev/null; then
        echo "  通过apt成功安装pipx"
    else
        echo "  apt安装失败，尝试通过pip安装..."
        # Ubuntu 20.04或更早版本的备选方案
        pip3 install --user pipx
        export PATH="$HOME/.local/bin:$PATH"
    fi
    # 确保pipx路径在PATH中
    pipx ensurepath 2>/dev/null || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# 安装archive-pdf-tools
echo "正在安装Python包..."
echo "- 安装 archive-pdf-tools (使用pipx)..."
if pipx install archive-pdf-tools; then
    echo "  通过pipx成功安装archive-pdf-tools"
else
    echo "  pipx安装失败，尝试pip用户安装..."
    if pip3 install --user archive-pdf-tools; then
        echo "  通过pip --user成功安装archive-pdf-tools"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    else
        echo "  ❌ 所有Python包安装方法都失败了"
        echo "  请手动安装: pip3 install --user archive-pdf-tools"
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "安装完成！正在验证工具..."
echo "======================================"

# 验证安装
check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "✓ $1 已安装"
        return 0
    else
        echo "✗ $1 未找到"
        return 1
    fi
}

all_good=true

check_tool "pdftoppm" || all_good=false
check_tool "pdfinfo" || all_good=false
check_tool "tesseract" || all_good=false
check_tool "qpdf" || all_good=false

# 检查recode_pdf
if command -v recode_pdf &> /dev/null; then
    echo "✓ recode_pdf 已安装"
elif python3 -c "import pkg_resources; pkg_resources.get_distribution('archive-pdf-tools')" &> /dev/null 2>&1; then
    echo "✓ archive-pdf-tools 已安装 (通过pip)"
else
    echo "✗ archive-pdf-tools 未正确安装"
    echo "  提示: 请确保 ~/.local/bin 在您的 PATH 中"
    echo "  运行: echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc && source ~/.bashrc"
    all_good=false
fi

# 检查tesseract语言包
if tesseract --list-langs 2>/dev/null | grep -q "chi_sim"; then
    echo "✓ 中文语言包已安装"
else
    echo "✗ 中文语言包未找到"
    all_good=false
fi

echo ""
if [ "$all_good" = true ]; then
    echo "🎉 所有依赖工具安装成功！"
    echo "现在可以运行PDF压缩工具了。"
    echo ""
    echo "注意: 如果在新终端中找不到 recode_pdf 命令，请运行："
    echo "  source ~/.bashrc"
    echo "  或重新打开终端"
    echo ""
    echo "使用方法："
    echo "  python3 main.py --check-deps  # 再次检查依赖"
    echo "  python3 main.py --input test.pdf --output-dir ./output --allow-splitting"
else
    echo "❌ 部分工具安装失败，请检查上述错误信息。"
    echo ""
    echo "常见问题解决："
    echo "1. 如果 recode_pdf 未找到，请确保 ~/.local/bin 在 PATH 中："
    echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "   source ~/.bashrc"
    echo "2. 如果权限问题，可以尝试："
    echo "   pip3 install --user archive-pdf-tools"
    exit 1
fi