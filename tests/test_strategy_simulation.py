"""简易模拟测试，不依赖实际PDF工具，仅验证控制流和参数传递"""
import sys
from pathlib import Path
import os

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from compressor import strategy, utils

# Monkey-patch pipeline methods to simulate behavior
from compressor import pipeline

def fake_deconstruct(pdf_path, temp_dir, dpi):
    # 模拟生成一组图像文件路径
    return [Path(temp_dir) / f"page-{i:02d}.tif" for i in range(1, 11)]

def fake_analyze(images, temp_dir):
    # 模拟生成 hocr 文件
    return Path(temp_dir) / "combined.hocr"

# reconstruct 模拟：根据params返回不同大小
def fake_reconstruct(images, hocr, temp_dir, params, output_pdf_path):
    # 使用dpi和bg_downsample计算假的大小（MB）
    dpi = params.get('dpi', 300)
    bg = params.get('bg_downsample', 2)
    size = max(0.5, 30.0 * (300.0 / dpi) * (1.0 / max(1, bg)))
    # 将结果写入输出文件（模拟）
    with open(output_pdf_path, 'w') as f:
        f.write(str(size))
    return True

pipeline.deconstruct_pdf_to_images = fake_deconstruct
pipeline.analyze_images_to_hocr = fake_analyze
pipeline.reconstruct_pdf = fake_reconstruct


def run_sim():
    tmp_out = Path('tests')
    tmp_out.mkdir(exist_ok=True)
    pdf = Path('dummy.pdf')
    # Create a dummy file of ~30MB (simulate large PDF)
    with open(pdf, 'wb') as f:
        f.seek(30 * 1024 * 1024 - 1)
        f.write(b'\0')
    success, out = strategy.run_iterative_compression(pdf, tmp_out, target_size_mb=2.0)
    print('SIM RESULT:', success, out)

if __name__ == '__main__':
    run_sim()