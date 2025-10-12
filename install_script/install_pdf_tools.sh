#!/bin/bash

# ==============================================================================
# archive-pdf-tools 最终安装脚本 (install.sh) - qpdf 版
# ------------------------------------------------------------------------------
# 目标环境: Ubuntu 24.04 LTS (WSL)
# 功能:
#   1. APT 安装所有工具 (包括 qpdf, Grok, OpenJPEG 等)。
#   2. 从源码编译并安装 jbig2enc。
#   3. 使用 pipx 安全地安装 archive-pdf-tools。
# ==============================================================================

# --- 配置 ---
set -e 

# --- 辅助函数 (用于彩色输出) ---
print_info() { echo -e "\n\e[34m==> $1\e[0m"; }
print_success() { echo -e "  \e[32m✔ $1\e[0m"; }
print_error() { echo -e "  \e[31m✖ $1\e[0m"; }

# --- 检查运行用户 ---
if [ "$(id -u)" -eq 0 ]; then
  print_error "错误：请不要以 root 用户身份运行此脚本。"
  echo "  此脚本设计为由普通用户运行，它会在需要时通过 'sudo' 请求管理员权限。" >&2
  exit 1
fi

# --- 脚本开始 ---
echo "============================================================"
echo "开始安装 archive-pdf-tools 及其依赖 (APT 优化 qpdf 版)..."
echo "============================================================"

# --- 步骤 1: 更新系统并安装所有APT依赖包 ---
print_info "步骤 1/3: 更新系统软件包列表并安装所有依赖项 (需要 sudo 权限)..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    git \
    python3-pip \
    python3-dev \
    pipx \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
    autoconf \
    automake \
    libtool \
    pkg-config \
    autoconf-archive \
    libleptonica-dev \
    libjbig2dec0-dev \
    libtiff-dev \
    libpng-dev \
    libjpeg-turbo8-dev \
    imagemagick \
    ghostscript \
    enscript \
    qpdf \
    grokj2k-tools \
    libopenjp2-7 \
    libopenjp2-tools

print_success "APT依赖项安装完成。"

# --- 步骤 2: 从源码编译并安装 jbig2enc ---
print_info "步骤 2/3: 正在从源码编译并安装 jbig2enc..."
JBG2_DIR="/tmp/jbig2enc"
if [ -d "$JBG2_DIR" ]; then rm -rf "$JBG2_DIR"; fi
git clone https://github.com/agl/jbig2enc.git "$JBG2_DIR"
cd "$JBG2_DIR"
./autogen.sh
./configure
make -j$(nproc)
sudo make install
print_success "jbig2enc 安装完成。"

# --- 步骤 3: 使用 pipx 安全地安装 archive-pdf-tools ---
print_info "步骤 3/3: 正在使用 pipx 在隔离环境中安装 archive-pdf-tools..."
export PATH="$PATH:$HOME/.local/bin" 
pipx install archive-pdf-tools || pipx upgrade archive-pdf-tools
print_success "archive-pdf-tools 安装完成。"

# --- 最终总结 ---
echo
echo "============================================================"
echo -e "\e[32m🎉 所有依赖和工具安装成功！\e[0m"
echo "下一步：运行 'verify.sh' 脚本进行功能验证。"
echo "============================================================"
