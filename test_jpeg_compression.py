#!/usr/bin/env python3
"""
JPEG 压缩质量测试脚本

测试不同 JPEG 质量参数对文件大小和 OCR 识别率的影响。
帮助选择最佳的质量参数（目标：约 1MB/页）。
"""

import sys
import subprocess
import tempfile
from pathlib import Path


def test_jpeg_quality(pdf_file, dpi=300):
    """测试不同 JPEG 质量设置"""
    
    if not Path(pdf_file).exists():
        print(f"❌ 错误: PDF 文件不存在: {pdf_file}")
        return
    
    print("=" * 70)
    print("JPEG 压缩质量测试")
    print("=" * 70)
    print(f"输入文件: {pdf_file}")
    print(f"DPI: {dpi}")
    print()
    
    # 测试不同的质量参数
    qualities = [70, 75, 80, 85, 90, 95]
    
    results = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for quality in qualities:
            print(f"\n{'─' * 70}")
            print(f"测试 JPEG 质量: {quality}")
            print(f"{'─' * 70}")
            
            output_prefix = Path(temp_dir) / f"test_q{quality}"
            
            # 生成 JPEG 图像（仅第一页）
            cmd = [
                "pdftoppm",
                "-jpeg",
                "-jpegopt", f"quality={quality}",
                "-r", str(dpi),
                "-f", "1",  # 仅第一页
                "-l", "1",  # 仅第一页
                str(pdf_file),
                str(output_prefix)
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    print(f"  ❌ pdftoppm 失败: {result.stderr}")
                    continue
                
                # 查找生成的文件
                jpg_file = output_prefix.parent / f"{output_prefix.name}-1.jpg"
                
                if not jpg_file.exists():
                    print(f"  ❌ 未找到生成的文件: {jpg_file}")
                    continue
                
                # 获取文件大小
                file_size_bytes = jpg_file.stat().st_size
                file_size_mb = file_size_bytes / 1024 / 1024
                
                print(f"  ✓ 文件大小: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
                
                # 可选: 测试 OCR（如果安装了 tesseract）
                ocr_text = ""
                try:
                    ocr_result = subprocess.run(
                        ["tesseract", str(jpg_file), "stdout", "-l", "chi_sim"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if ocr_result.returncode == 0:
                        ocr_text = ocr_result.stdout.strip()
                        char_count = len(ocr_text)
                        print(f"  ✓ OCR 识别字符数: {char_count}")
                    else:
                        print(f"  ⚠️ OCR 失败（可能未安装 tesseract）")
                except FileNotFoundError:
                    print(f"  ⚠️ tesseract 未安装，跳过 OCR 测试")
                except subprocess.TimeoutExpired:
                    print(f"  ⚠️ OCR 超时")
                
                results.append({
                    'quality': quality,
                    'size_mb': file_size_mb,
                    'size_bytes': file_size_bytes,
                    'ocr_chars': len(ocr_text) if ocr_text else 0
                })
                
            except subprocess.TimeoutExpired:
                print(f"  ❌ 命令超时")
            except Exception as e:
                print(f"  ❌ 错误: {e}")
    
    # 打印汇总结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print(f"{'质量':<10} {'文件大小':<15} {'压缩比':<15} {'OCR字符数':<15} {'推荐':<10}")
    print("─" * 70)
    
    for r in results:
        compression_ratio = (1 - r['size_mb'] / 25.0) * 100  # 假设原始 25MB
        recommendation = ""
        
        # 根据目标 1MB 给出推荐
        if 0.8 <= r['size_mb'] <= 1.5:
            recommendation = "⭐ 推荐"
        elif r['size_mb'] < 0.8:
            recommendation = "可能过小"
        else:
            recommendation = "稍大"
        
        print(f"{r['quality']:<10} {r['size_mb']:.2f} MB{'':<7} "
              f"{compression_ratio:.1f}%{'':<8} "
              f"{r['ocr_chars']:<15} {recommendation:<10}")
    
    print("\n" + "=" * 70)
    print("建议:")
    print("=" * 70)
    
    # 找到最接近 1MB 的质量设置
    target_size = 1.0
    best_match = min(results, key=lambda x: abs(x['size_mb'] - target_size))
    
    print(f"• 目标文件大小: 约 1 MB")
    print(f"• 推荐 JPEG 质量: {best_match['quality']}")
    print(f"• 预期文件大小: {best_match['size_mb']:.2f} MB")
    print(f"• 压缩率: {(1 - best_match['size_mb'] / 25.0) * 100:.1f}%")
    print()
    print("修改 compressor/pipeline.py:")
    print(f'  command = ["pdftoppm", "-jpeg", "-jpegopt", "quality={best_match["quality"]}", ...]')
    print()
    print("⚠️ 注意:")
    print("  - JPEG 是有损压缩，会轻微降低图像质量")
    print("  - 对 OCR 识别率影响通常很小（质量 ≥ 75）")
    print("  - 如果发现 OCR 识别率下降，可以适当提高质量参数")
    print()


def main():
    if len(sys.argv) < 2:
        print("用法: python test_jpeg_compression.py <pdf_file> [dpi]")
        print()
        print("示例:")
        print("  python test_jpeg_compression.py testpdf.pdf")
        print("  python test_jpeg_compression.py testpdf.pdf 300")
        return 1
    
    pdf_file = sys.argv[1]
    dpi = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    
    test_jpeg_quality(pdf_file, dpi)
    return 0


if __name__ == '__main__':
    sys.exit(main())
