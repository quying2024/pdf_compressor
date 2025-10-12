#!/bin/bash

# test_pipx_migration.sh
# 测试pipx迁移可能引发的连锁问题

echo "======================================"
echo "pipx迁移连锁错误测试脚本"
echo "======================================"

# 测试1: 检查pipx是否在不同Ubuntu版本中可用
echo "测试1: pipx可用性检查"
echo "----------------------------------------"

if command -v lsb_release &> /dev/null; then
    UBUNTU_VERSION=$(lsb_release -rs)
    echo "Ubuntu版本: $UBUNTU_VERSION"
    
    # 检查pipx包是否存在于仓库中
    if apt-cache show pipx &> /dev/null; then
        echo "✓ pipx包在当前Ubuntu版本的仓库中可用"
    else
        echo "⚠ pipx包在当前Ubuntu版本的仓库中不可用"
        echo "  将使用pip安装方案"
    fi
else
    echo "⚠ 无法检测Ubuntu版本"
fi

# 测试2: 模拟PATH问题
echo ""
echo "测试2: PATH配置问题模拟"
echo "----------------------------------------"

LOCAL_BIN="$HOME/.local/bin"
if [[ ":$PATH:" == *":$LOCAL_BIN:"* ]]; then
    echo "✓ ~/.local/bin 已在PATH中"
else
    echo "⚠ ~/.local/bin 不在PATH中"
    echo "  这可能导致recode_pdf命令找不到"
fi

# 测试3: 检查现有Python环境
echo ""
echo "测试3: Python环境检查"
echo "----------------------------------------"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "Python版本: $PYTHON_VERSION"
    
    # 检查pip
    if python3 -m pip --version &> /dev/null; then
        echo "✓ pip可用"
    else
        echo "⚠ pip不可用，可能影响备选安装方案"
    fi
    
    # 检查现有的archive-pdf-tools安装
    if python3 -c "import pkg_resources; pkg_resources.get_distribution('archive-pdf-tools')" &> /dev/null 2>&1; then
        echo "⚠ 检测到已有archive-pdf-tools安装（可能通过pip）"
        echo "  pipx安装可能会产生冲突"
    else
        echo "✓ 未检测到现有的archive-pdf-tools安装"
    fi
else
    echo "❌ Python3未安装"
fi

# 测试4: 网络连接检查
echo ""
echo "测试4: 网络连接检查"
echo "----------------------------------------"

if ping -c 1 pypi.org &> /dev/null; then
    echo "✓ 可以连接到PyPI"
else
    echo "⚠ 无法连接到PyPI，可能影响包安装"
fi

if ping -c 1 archive.ubuntu.com &> /dev/null; then
    echo "✓ 可以连接到Ubuntu软件源"
else
    echo "⚠ 无法连接到Ubuntu软件源，可能影响系统包安装"
fi

# 测试5: 权限检查
echo ""
echo "测试5: 权限检查"
echo "----------------------------------------"

if [ -w "$HOME" ]; then
    echo "✓ 用户主目录可写"
else
    echo "❌ 用户主目录不可写，可能影响pipx安装"
fi

if [ -w "$HOME/.bashrc" ] || [ ! -f "$HOME/.bashrc" ]; then
    echo "✓ .bashrc文件可写或不存在"
else
    echo "⚠ .bashrc文件不可写，可能影响PATH配置"
fi

# 测试6: 模拟常见错误场景
echo ""
echo "测试6: 常见错误场景模拟"
echo "----------------------------------------"

# 模拟pipx安装失败的情况
echo "模拟pipx安装失败..."
if ! command -v pipx &> /dev/null; then
    echo "  当前pipx未安装，这是正常情况"
    echo "  安装脚本会处理这种情况"
else
    echo "  pipx已安装，测试跳过"
fi

# 测试PATH环境变量修改的影响
OLD_PATH="$PATH"
export PATH="/usr/bin:/bin"  # 模拟最小PATH
echo "测试最小PATH环境下的工具检查..."

if command -v python3 &> /dev/null; then
    echo "  ✓ python3在最小PATH中可用"
else
    echo "  ⚠ python3在最小PATH中不可用"
fi

# 恢复PATH
export PATH="$OLD_PATH"

echo ""
echo "======================================"
echo "测试完成"
echo "======================================"

echo ""
echo "潜在风险总结:"
echo "1. Ubuntu 20.04及更早版本pipx可能不在默认仓库中"
echo "2. PATH配置可能需要用户重新加载shell"
echo "3. 现有pip安装的archive-pdf-tools可能产生冲突"
echo "4. 网络问题可能导致安装失败"
echo "5. 权限问题可能影响配置文件修改"
echo ""
echo "缓解措施:"
echo "1. 安装脚本已添加pip备选方案"
echo "2. Python代码已自动添加~/.local/bin到PATH"
echo "3. 安装脚本会检测和处理冲突"
echo "4. 安装脚本会检查网络连接"
echo "5. 提供详细的错误信息和解决方案"