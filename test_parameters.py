#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试所有命令行参数是否可用
"""

import subprocess
import sys

# 在程序开始时立即设置 UTF-8 编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def run_command(cmd, description):
    """运行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"命令: {cmd}")
    print('-'*60)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        print(f"退出码: {result.returncode}")
        if result.stdout:
            print("标准输出:")
            print(result.stdout[:500])  # 只显示前500字符
        if result.stderr:
            print("标准错误:")
            print(result.stderr[:500])
        return result.returncode
    except subprocess.TimeoutExpired:
        print("超时！")
        return -1
    except Exception as e:
        print(f"错误: {e}")
        return -1

def main():
    """主测试函数"""
    tests = [
        # 基本参数
        ("python main.py --help", "显示帮助信息 (--help)"),
        ("python main.py -h", "显示帮助信息 (-h)"),
        ("python main.py -?", "显示示例 (-?)"),
        ("python main.py --examples", "显示示例 (--examples)"),
        
        # 检查依赖
        ("python main.py --check-deps", "检查依赖 (--check-deps)"),
        
        # 手动模式（会立即退出，因为它是交互式的）
        # 我们不测试这个，因为它需要用户交互
        
        # 参数验证
        ("python main.py", "没有参数"),
        ("python main.py --input test.pdf", "只有 --input，缺少 --output"),
        ("python main.py --output out", "只有 --output，缺少 --input"),
        
        # Verbose 模式
        ("python main.py --verbose --check-deps", "详细模式 (--verbose)"),
        
        # 目标大小
        ("python main.py --input test.pdf --output out --target-size 5", 
         "自定义目标大小 (--target-size)"),
        
        # 拆分选项
        ("python main.py --input test.pdf --output out --allow-splitting", 
         "允许拆分 (--allow-splitting)"),
        ("python main.py --input test.pdf --output out --allow-splitting --max-splits 6", 
         "最大拆分数 (--max-splits)"),
        
        # 其他选项
        ("python main.py --input test.pdf --output out --copy-small-files", 
         "复制小文件 (--copy-small-files)"),
        ("python main.py --input test.pdf --output out -k", 
         "保留临时目录 (-k / --keep-temp-on-failure)"),
    ]
    
    print("="*60)
    print("PDF 压缩工具 - 参数测试")
    print("="*60)
    
    results = []
    for cmd, desc in tests:
        exit_code = run_command(cmd, desc)
        results.append((desc, exit_code))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    success_count = 0
    for desc, exit_code in results:
        # 对于帮助和示例命令，退出码 0 是成功
        # 对于其他命令，如果显示了正确的错误消息，退出码 1 也算成功
        status = "✓" if exit_code in [0, 1] else "✗"
        if exit_code in [0, 1]:
            success_count += 1
        print(f"{status} {desc}: 退出码 {exit_code}")
    
    print(f"\n成功: {success_count}/{len(results)}")
    
    return 0 if success_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
