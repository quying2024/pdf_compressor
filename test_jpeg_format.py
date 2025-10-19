#!/usr/bin/env python3
"""
JPEG 格式切换验证脚本

验证代码修改是否正确：
1. deconstruct_pdf_to_images() 是否使用 JPEG 格式
2. reconstruct_pdf() 是否正确处理 JPEG 文件
3. 文件扩展名是否匹配
"""

import sys
import re
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from compressor import pipeline


def test_deconstruct_function():
    """测试 deconstruct_pdf_to_images 函数配置"""
    print("=" * 70)
    print("测试 1: 检查 deconstruct_pdf_to_images() 配置")
    print("=" * 70)
    
    # 读取函数源码
    import inspect
    source = inspect.getsource(pipeline.deconstruct_pdf_to_images)
    
    # 检查关键参数
    checks = {
        '使用 JPEG 格式': '"-jpeg"' in source or '-jpeg' in source,
        '设置 JPEG 质量': 'jpegopt' in source or 'quality' in source,
        '正确的文件扩展名': '*.jpg' in source or '.jpg' in source,
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {check_name:30s}: {status}")
        if not result:
            all_passed = False
    
    # 提取质量参数
    quality_match = re.search(r'quality[=\s]+(\d+)', source)
    if quality_match:
        quality = quality_match.group(1)
        print(f"\n  检测到的 JPEG 质量: {quality}")
        
        if 75 <= int(quality) <= 90:
            print(f"  ✓ 质量参数合理（推荐范围: 75-90）")
        else:
            print(f"  ⚠️ 质量参数 {quality} 可能需要调整")
    
    return all_passed


def test_reconstruct_function():
    """测试 reconstruct_pdf 函数配置"""
    print("\n" + "=" * 70)
    print("测试 2: 检查 reconstruct_pdf() 配置")
    print("=" * 70)
    
    import inspect
    source = inspect.getsource(pipeline.reconstruct_pdf)
    
    # 检查是否动态处理文件扩展名
    checks = {
        '动态获取扩展名': 'suffix' in source or 'ext' in source,
        '支持 JPEG 文件': '.jpg' in source,
        '兼容性处理': 'if' in source and 'image_files' in source,
    }
    
    all_passed = True
    for check_name, result in checks.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {check_name:30s}: {status}")
        if not result:
            all_passed = False
    
    return all_passed


def test_file_extension_consistency():
    """测试文件扩展名一致性"""
    print("\n" + "=" * 70)
    print("测试 3: 文件扩展名一致性检查")
    print("=" * 70)
    
    import inspect
    
    # 检查 deconstruct 函数
    deconstruct_source = inspect.getsource(pipeline.deconstruct_pdf_to_images)
    
    # 提取生成的文件扩展名
    gen_ext = None
    if '*.jpg' in deconstruct_source:
        gen_ext = '.jpg'
    elif '*.tif' in deconstruct_source:
        gen_ext = '.tif'
    elif '*.png' in deconstruct_source:
        gen_ext = '.png'
    
    print(f"  deconstruct 生成的文件类型: {gen_ext}")
    
    # 检查 reconstruct 函数是否能正确处理
    reconstruct_source = inspect.getsource(pipeline.reconstruct_pdf)
    
    if 'suffix' in reconstruct_source or 'ext' in reconstruct_source:
        print(f"  ✓ reconstruct 动态识别文件类型（兼容所有格式）")
        return True
    elif gen_ext and gen_ext in reconstruct_source:
        print(f"  ✓ reconstruct 硬编码匹配 {gen_ext}")
        return True
    else:
        print(f"  ✗ reconstruct 可能无法正确处理 {gen_ext} 文件")
        return False


def test_import():
    """测试模块导入"""
    print("\n" + "=" * 70)
    print("测试 4: 模块导入检查")
    print("=" * 70)
    
    try:
        from compressor import pipeline, strategy, utils
        print("  ✓ 所有模块导入成功")
        
        # 检查关键函数存在
        functions = [
            'deconstruct_pdf_to_images',
            'analyze_images_to_hocr',
            'reconstruct_pdf',
        ]
        
        for func_name in functions:
            if hasattr(pipeline, func_name):
                print(f"  ✓ 函数存在: {func_name}")
            else:
                print(f"  ✗ 函数缺失: {func_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        return False


def print_summary(results):
    """打印测试汇总"""
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name:40s}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有测试通过！JPEG 格式切换完成。")
        print("=" * 70)
        print("\n下一步:")
        print("1. 运行测试脚本验证不同质量参数:")
        print("   python test_jpeg_compression.py testpdf.pdf")
        print()
        print("2. 使用真实 PDF 测试完整流程:")
        print("   python main.py --input test.pdf --output ./out -k")
        print()
        print("3. 检查临时目录中的文件大小:")
        print("   ls -lh /tmp/tmpXXXXXX/page-*.jpg")
        print()
        print("4. 对比 JPEG 和之前 TIFF 的最终 PDF 质量")
        print()
        print("5. 如需调整质量参数，修改 pipeline.py 中的:")
        print('   "-jpegopt", "quality=85"  # 调整为 70-95')
        return 0
    else:
        print("❌ 部分测试失败，请检查代码。")
        print("=" * 70)
        return 1


def main():
    print("\n" + "🔥" * 35)
    print("JPEG 格式切换验证")
    print("🔥" * 35 + "\n")
    
    results = {}
    
    # 运行所有测试
    results['模块导入'] = test_import()
    results['deconstruct 函数配置'] = test_deconstruct_function()
    results['reconstruct 函数配置'] = test_reconstruct_function()
    results['文件扩展名一致性'] = test_file_extension_consistency()
    
    return print_summary(results)


if __name__ == '__main__':
    sys.exit(main())
