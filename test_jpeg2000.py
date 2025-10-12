#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# test_jpeg2000.py
# 测试JPEG2000编码器参数

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compressor.strategy import STRATEGIES

def test_jpeg2000_params():
    """测试所有策略是否包含JPEG2000编码器参数"""
    print("测试JPEG2000编码器参数配置:")
    print("=" * 50)
    
    for tier, strategy in STRATEGIES.items():
        print(f"\n层级 {tier}: {strategy['name']}")
        print("-" * 30)
        
        for i, params in enumerate(strategy['params_sequence'], 1):
            dpi = params['dpi']
            bg_downsample = params['bg_downsample']
            encoder = params.get('jpeg2000_encoder', '未设置')
            
            print(f"  {i}. DPI={dpi}, BG-Downsample={bg_downsample}, JPEG2000={encoder}")
    
    print(f"\n总结:")
    print(f"- 总策略层级: {len(STRATEGIES)}")
    
    total_configs = sum(len(strategy['params_sequence']) for strategy in STRATEGIES.values())
    print(f"- 总参数配置: {total_configs}")
    
    # 检查所有配置是否都有JPEG2000参数
    missing_encoder = []
    for tier, strategy in STRATEGIES.items():
        for i, params in enumerate(strategy['params_sequence']):
            if 'jpeg2000_encoder' not in params:
                missing_encoder.append(f"层级{tier}-配置{i+1}")
    
    if missing_encoder:
        print(f"- 缺少JPEG2000参数的配置: {', '.join(missing_encoder)}")
    else:
        print(f"- ✅ 所有配置都包含JPEG2000编码器参数")

def test_command_generation():
    """测试命令生成逻辑"""
    print(f"\n" + "=" * 50)
    print("测试recode_pdf命令生成:")
    print("=" * 50)
    
    # 模拟参数
    test_params = {
        'dpi': 300,
        'bg_downsample': 2,
        'jpeg2000_encoder': 'grok'
    }
    
    # 模拟命令构建
    image_stack_glob = "/tmp/test/page-*.tif"
    hocr_file = "/tmp/test/combined.hocr"
    output_pdf = "/tmp/test/output.pdf"
    
    command = [
        "recode_pdf",
        "--from-imagestack", image_stack_glob,
        "--hocr-file", hocr_file,
        "--dpi", str(test_params['dpi']),
        "--bg-downsample", str(test_params['bg_downsample']),
        "--mask-compression", "jbig2",
        "-J", test_params.get('jpeg2000_encoder', 'openjpeg'),
        "-o", output_pdf
    ]
    
    print("生成的命令:")
    print(" ".join(command))
    
    print(f"\n参数解析:")
    print(f"- JPEG2000编码器: {test_params.get('jpeg2000_encoder', 'openjpeg')}")
    print(f"- DPI: {test_params['dpi']}")
    print(f"- 背景下采样: {test_params['bg_downsample']}")

if __name__ == "__main__":
    test_jpeg2000_params()
    test_command_generation()