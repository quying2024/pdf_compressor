#!/usr/bin/env python3
"""
S7 hOCR优化集成测试脚本

测试 S7 方案是否正确调用 hOCR 优化功能。
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from compressor import pipeline


def test_optimize_hocr_function():
    """测试 optimize_hocr_for_extreme_compression 函数"""
    print("=" * 60)
    print("测试 1: hOCR 优化函数单元测试")
    print("=" * 60)
    
    # 创建测试 hOCR 内容
    test_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<title>Test hOCR</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
</head>
<body>
  <div class='ocr_page' id='page_1'>
    <div class='ocr_carea' id='carea_1_1'>
      <p class='ocr_par' id='par_1_1'>
        <span class='ocr_line' id='line_1_1'>
          <span class='ocrx_word' id='word_1_1' title='bbox 100 100 200 120'>Hello</span>
          <span class='ocrx_word' id='word_1_2' title='bbox 210 100 300 120'>World</span>
        </span>
      </p>
    </div>
  </div>
</body>
</html>"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hocr', delete=False, encoding='utf-8') as f:
        test_file = Path(f.name)
        f.write(test_content)
    
    try:
        # 记录原始大小
        original_size = test_file.stat().st_size
        print(f"✓ 创建测试文件: {test_file.name}")
        print(f"  原始大小: {original_size} bytes")
        
        # 执行优化
        result = pipeline.optimize_hocr_for_extreme_compression(test_file)
        
        # 验证结果
        optimized_size = result.stat().st_size
        print(f"  优化大小: {optimized_size} bytes")
        print(f"  减少: {original_size - optimized_size} bytes ({(1 - optimized_size / original_size) * 100:.1f}%)")
        
        # 读取优化后的内容
        with open(result, 'r', encoding='utf-8') as f:
            optimized_content = f.read()
        
        # 验证 ocrx_word 标签已移除
        if 'ocrx_word' not in optimized_content:
            print("✓ ocrx_word 标签已成功移除")
            return True
        else:
            print("✗ 错误: ocrx_word 标签仍然存在")
            return False
            
    finally:
        # 清理
        if test_file.exists():
            test_file.unlink()
            print(f"✓ 清理测试文件")


def test_strategy_import():
    """测试 strategy.py 能否正确导入和使用 pipeline 模块"""
    print("\n" + "=" * 60)
    print("测试 2: 模块导入测试")
    print("=" * 60)
    
    try:
        from compressor import strategy
        print("✓ strategy 模块导入成功")
        
        # 检查 _execute_scheme 函数是否存在
        if hasattr(strategy, '_execute_scheme'):
            print("✓ _execute_scheme 函数存在")
        else:
            print("✗ 错误: _execute_scheme 函数不存在")
            return False
        
        # 检查 COMPRESSION_SCHEMES 是否包含 S7
        if 7 in strategy.COMPRESSION_SCHEMES:
            s7_config = strategy.COMPRESSION_SCHEMES[7]
            print(f"✓ S7 方案配置: {s7_config}")
            
            # 验证 S7 参数
            expected = {'name': 'S7-终极', 'dpi': 72, 'bg_downsample': 10, 'jpeg2000_encoder': 'grok'}
            if s7_config == expected:
                print("✓ S7 参数配置正确")
                return True
            else:
                print(f"✗ S7 参数配置错误，期望: {expected}")
                return False
        else:
            print("✗ 错误: S7 方案不存在")
            return False
            
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_function_signature():
    """测试函数签名是否正确"""
    print("\n" + "=" * 60)
    print("测试 3: 函数签名检查")
    print("=" * 60)
    
    import inspect
    
    # 检查 optimize_hocr_for_extreme_compression
    if hasattr(pipeline, 'optimize_hocr_for_extreme_compression'):
        func = pipeline.optimize_hocr_for_extreme_compression
        sig = inspect.signature(func)
        print(f"✓ 函数签名: optimize_hocr_for_extreme_compression{sig}")
        
        # 检查参数
        params = list(sig.parameters.keys())
        if params == ['hocr_file']:
            print("✓ 参数签名正确")
            return True
        else:
            print(f"✗ 参数错误，期望 ['hocr_file']，实际 {params}")
            return False
    else:
        print("✗ 函数不存在")
        return False


def main():
    """运行所有测试"""
    print("\n" + "🔥" * 30)
    print("S7 hOCR 优化集成测试")
    print("🔥" * 30 + "\n")
    
    results = []
    
    # 测试 1: 函数功能
    results.append(("hOCR优化功能", test_optimize_hocr_function()))
    
    # 测试 2: 模块导入
    results.append(("模块导入", test_strategy_import()))
    
    # 测试 3: 函数签名
    results.append(("函数签名", test_function_signature()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:20s}: {status}")
    
    all_passed = all(r for _, r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！S7 集成完成。")
        print("=" * 60)
        print("\n下一步:")
        print("1. 使用真实PDF测试 S7 方案")
        print("2. 验证最终PDF文件失去搜索功能")
        print("3. 确认体积减小约7%")
        print("4. 提交代码到 Git")
        return 0
    else:
        print("❌ 部分测试失败，请检查代码。")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
