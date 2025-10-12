#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# diagnose_dependencies.py
# WSL/Ubuntu环境依赖诊断工具

import subprocess
import os
import sys
from pathlib import Path

def check_tool_detailed(tool_name, install_method=None):
    """详细检查单个工具的安装状态"""
    print(f"\n{'='*50}")
    print(f"检查工具: {tool_name}")
    print(f"{'='*50}")
    
    # 检查which命令
    try:
        result = subprocess.run(['which', tool_name], 
                              capture_output=True, 
                              check=True,
                              timeout=5)
        tool_path = result.stdout.decode('utf-8').strip()
        print(f"✓ 工具路径: {tool_path}")
        
        # 尝试获取版本信息
        version_commands = [['--version'], ['--help'], ['-v'], ['-h']]
        version_found = False
        
        for cmd in version_commands:
            try:
                ver_result = subprocess.run([tool_name] + cmd,
                                          capture_output=True,
                                          timeout=10)
                if ver_result.returncode in [0, 1]:  # 成功或帮助信息
                    output = ver_result.stdout.decode('utf-8', errors='ignore')
                    if not output:
                        output = ver_result.stderr.decode('utf-8', errors='ignore')
                    
                    if output:
                        # 只显示前几行
                        lines = output.split('\n')[:3]
                        clean_output = ' '.join(lines).strip()
                        if clean_output:
                            print(f"✓ 版本信息: {clean_output}")
                            version_found = True
                            break
            except:
                continue
        
        if not version_found:
            print("⚠ 无法获取版本信息，但工具存在")
        
        return True
        
    except subprocess.CalledProcessError:
        print(f"✗ 工具未找到")
        if install_method:
            print(f"  安装方法: {install_method}")
        return False
    except Exception as e:
        print(f"✗ 检查时出错: {e}")
        return False

def check_path_configuration():
    """检查PATH配置"""
    print(f"\n{'='*50}")
    print("PATH配置检查")
    print(f"{'='*50}")
    
    current_path = os.environ.get('PATH', '')
    path_dirs = current_path.split(':')
    
    print(f"当前PATH包含 {len(path_dirs)} 个目录:")
    for i, dir_path in enumerate(path_dirs[:10], 1):  # 只显示前10个
        exists = "✓" if os.path.exists(dir_path) else "✗"
        print(f"  {i:2d}. {exists} {dir_path}")
    
    if len(path_dirs) > 10:
        print(f"     ... 还有 {len(path_dirs) - 10} 个目录")
    
    # 检查重要目录
    important_dirs = [
        '/usr/bin',
        '/usr/local/bin', 
        os.path.expanduser('~/.local/bin')
    ]
    
    print("\n重要目录检查:")
    for dir_path in important_dirs:
        in_path = dir_path in path_dirs
        exists = os.path.exists(dir_path)
        status = "✓" if in_path and exists else "✗"
        print(f"  {status} {dir_path} (在PATH: {in_path}, 存在: {exists})")

def check_python_environment():
    """检查Python环境"""
    print(f"\n{'='*50}")
    print("Python环境检查")
    print(f"{'='*50}")
    
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    # 检查pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'],
                              capture_output=True, check=True, timeout=10)
        print(f"pip版本: {result.stdout.decode('utf-8').strip()}")
    except:
        print("✗ pip不可用")
    
    # 检查pipx
    try:
        result = subprocess.run(['pipx', '--version'],
                              capture_output=True, check=True, timeout=10)
        print(f"pipx版本: {result.stdout.decode('utf-8').strip()}")
    except:
        print("✗ pipx不可用")
    
    # 检查archive-pdf-tools
    try:
        result = subprocess.run([sys.executable, '-c', 
                               'import pkg_resources; print(pkg_resources.get_distribution("archive-pdf-tools").version)'],
                              capture_output=True, check=True, timeout=10)
        print(f"archive-pdf-tools版本: {result.stdout.decode('utf-8').strip()}")
    except:
        print("✗ archive-pdf-tools未通过pip安装")

def main():
    print("PDF压缩工具 - 详细依赖诊断")
    print("="*60)
    
    # 工具列表和安装方法
    tools_info = {
        'pdftoppm': 'sudo apt install poppler-utils',
        'pdfinfo': 'sudo apt install poppler-utils', 
        'tesseract': 'sudo apt install tesseract-ocr tesseract-ocr-chi-sim',
        'qpdf': 'sudo apt install qpdf',
        'recode_pdf': 'pipx install archive-pdf-tools'
    }
    
    # 检查每个工具
    results = {}
    for tool, install_cmd in tools_info.items():
        results[tool] = check_tool_detailed(tool, install_cmd)
    
    # 检查PATH和Python环境
    check_path_configuration()
    check_python_environment()
    
    # 总结
    print(f"\n{'='*60}")
    print("诊断总结")
    print(f"{'='*60}")
    
    missing_tools = [tool for tool, found in results.items() if not found]
    
    if missing_tools:
        print(f"缺少的工具 ({len(missing_tools)}):")
        for tool in missing_tools:
            print(f"  ✗ {tool}")
            print(f"    安装: {tools_info[tool]}")
        
        print(f"\n推荐操作:")
        apt_tools = [tool for tool in missing_tools if tool != 'recode_pdf']
        if apt_tools:
            # 构建apt安装命令
            packages = []
            if 'pdftoppm' in apt_tools or 'pdfinfo' in apt_tools:
                packages.append('poppler-utils')
            if 'tesseract' in apt_tools:
                packages.append('tesseract-ocr tesseract-ocr-chi-sim')
            if 'qpdf' in apt_tools:
                packages.append('qpdf')
            
            if packages:
                print(f"  1. sudo apt update && sudo apt install {' '.join(packages)}")
        
        if 'recode_pdf' in missing_tools:
            print(f"  2. pipx install archive-pdf-tools")
            print(f"     如果没有pipx: sudo apt install pipx")
    else:
        print("✓ 所有必要工具都已安装！")
    
    print(f"\n运行主程序检查:")
    print(f"  python3 main.py --check-deps")

if __name__ == "__main__":
    main()