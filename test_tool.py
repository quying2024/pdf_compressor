#!/usr/bin/env python3
# test_tool.py
# 测试工具功能的简单脚本

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from compressor import utils
import logging

def test_dependencies():
    """测试依赖工具是否正确安装"""
    print("=" * 50)
    print("PDF压缩工具 - 依赖检查")
    print("=" * 50)
    
    utils.setup_logging()
    
    if utils.check_dependencies():
        print("\n✅ 所有依赖工具检查通过！")
        print("工具已准备就绪，可以开始处理PDF文件。")
        return True
    else:
        print("\n❌ 依赖检查失败！")
        print("请运行 install_dependencies.sh 脚本安装缺失的工具。")
        return False

def show_tool_versions():
    """显示各工具版本信息"""
    import subprocess
    
    tools = {
        'pdftoppm': ['pdftoppm', '-v'],
        'tesseract': ['tesseract', '--version'],
        'qpdf': ['qpdf', '--version'],
        'pdfinfo': ['pdfinfo', '-v']
    }
    
    print("\n工具版本信息:")
    print("-" * 30)
    
    for tool_name, command in tools.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            # 获取版本信息的第一行
            version_info = result.stderr.split('\n')[0] if result.stderr else result.stdout.split('\n')[0]
            print(f"{tool_name:12}: {version_info}")
        except Exception as e:
            print(f"{tool_name:12}: 无法获取版本信息")

def create_test_structure():
    """创建测试目录结构"""
    from pathlib import Path
    
    test_dirs = [
        "test_input",
        "test_output", 
        "examples"
    ]
    
    base_path = Path(__file__).parent
    
    for dir_name in test_dirs:
        dir_path = base_path / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"创建目录: {dir_path}")
    
    # 创建示例说明文件
    readme_path = base_path / "test_input" / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""测试输入目录
================

将需要测试的PDF文件放入此目录。

测试建议:
1. 准备不同大小的PDF文件：
   - 小文件 (< 2MB) - 测试跳过功能
   - 中等文件 (2-10MB) - 测试高质量压缩
   - 大文件 (10-50MB) - 测试平衡压缩
   - 超大文件 (> 50MB) - 测试极限压缩和拆分

2. 测试命令示例：
   python main.py --input test_input --output-dir test_output --allow-splitting --verbose
""")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--create-test':
        create_test_structure()
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == '--versions':
        show_tool_versions()
        return
    
    # 默认运行依赖检查
    if test_dependencies():
        show_tool_versions()
        
        print(f"\n使用 'python {sys.argv[0]} --create-test' 创建测试目录")
        print(f"使用 'python {sys.argv[0]} --versions' 查看工具版本")

if __name__ == "__main__":
    main()