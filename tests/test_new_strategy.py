# tests/test_new_strategy.py

import unittest
import sys
import shutil
from pathlib import Path
import logging

# 将项目根目录添加到 sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from compressor import strategy, utils
from compressor import pipeline

# --- 模拟（Monkey-Patch）核心功能 ---

# 模拟的压缩方案与文件大小的映射关系
# (dpi, bg_downsample) -> size_mb
FAKE_SIZE_MAP = {
    (300, 2): 30.0,  # S1
    (300, 3): 15.0,  # S2
    (250, 3): 8.0,   # S3
    (200, 4): 4.0,   # S4
    (150, 5): 1.8,   # S5
    (110, 6): 0.9,   # S6
}

def fake_deconstruct(pdf_path, temp_dir, dpi):
    """模拟解构过程，返回伪造的图像路径列表。"""
    logging.debug(f"SIMULATE: Deconstructing {pdf_path} in {temp_dir} with dpi {dpi}")
    # 创建临时目录，如果它不存在
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    return [Path(temp_dir) / f"page-{i:02d}.tif" for i in range(1, 11)]

def fake_analyze(images, temp_dir):
    """模拟分析过程，返回伪造的hocr文件路径。"""
    logging.debug(f"SIMULATE: Analyzing images in {temp_dir}")
    hocr_path = Path(temp_dir) / "combined.hocr"
    hocr_path.touch() # 创建一个空的hocr文件
    return hocr_path

def fake_reconstruct(images, hocr, temp_dir, params, output_pdf_path):
    """
    模拟重建过程。
    根据传入的 'dpi' 和 'bg_downsample' 参数，从 FAKE_SIZE_MAP 查找对应的文件大小，
    并创建一个内容为该大小（字符串形式）的伪造PDF文件。
    """
    dpi = params.get('dpi', 300)
    bg = params.get('bg_downsample', 1)
    
    # 查找对应的模拟大小
    size_mb = FAKE_SIZE_MAP.get((dpi, bg))
    if size_mb is None:
        # 如果方案未在MAP中定义，则返回一个默认大文件大小
        size_mb = 50.0
        
    logging.debug(f"SIMULATE: Reconstructing to {output_pdf_path} with params {params}, fake size: {size_mb}MB")
    
    # 创建伪造的PDF文件，文件内容就是它的大小
    with open(output_pdf_path, 'w') as f:
        f.write(str(size_mb))
        
    return True

def fake_get_file_size_mb(file_path):
    """模拟获取文件大小，直接读取伪造PDF文件的内容（即其大小）。"""
    try:
        with open(file_path, 'r') as f:
            size = float(f.read())
            logging.debug(f"SIMULATE: Getting size for {file_path}: {size}MB")
            return size
    except (IOError, ValueError):
        # 对于原始输入文件，返回一个预设的较大值
        logging.debug(f"SIMULATE: Getting size for original file {file_path}: 40MB")
        return 40.0

# 应用模拟补丁
pipeline.deconstruct_pdf_to_images = fake_deconstruct
pipeline.analyze_images_to_hocr = fake_analyze
pipeline.reconstruct_pdf = fake_reconstruct
utils.get_file_size_mb = fake_get_file_size_mb

class TestNewCompressionStrategy(unittest.TestCase):

    def setUp(self):
        """在每个测试前运行，设置测试环境。"""
        self.test_dir = Path('./test_temp_output')
        self.test_dir.mkdir(exist_ok=True)
        self.input_pdf = self.test_dir / 'dummy_input.pdf'
        self.input_pdf.touch() # 创建一个空的输入文件
        # 配置日志记录器以查看模拟过程的输出
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def tearDown(self):
        """在每个测试后运行，清理测试环境。"""
        shutil.rmtree(self.test_dir)

    def test_compression_success_progressive(self):
        """
        测试成功场景（渐进式）:
        - 目标大小: 10MB
        - S1 (30MB) > 1.5 * 10MB (15MB) -> 不满足，所以是 > 1.5x
        - 预期: 跳到 S6 (0.9MB)，成功。然后回溯到 S5(1.8), S4(4), S3(8)。S2(15)太大。
        - 最佳方案应为 S3。
        """
        logging.info("\n--- Running test_compression_success_jump_and_backtrack ---")
        target_size = 10.0
        status, details = strategy.run_compression_strategy(self.input_pdf, self.test_dir, target_size)
        
        self.assertEqual(status, 'SUCCESS')
        self.assertEqual(details['best_scheme_id'], 3) # S3 是最佳方案
        self.assertIn('final_path', details)
        self.assertTrue(Path(details['final_path']).exists())

    def test_compression_success_jump_and_backtrack(self):
        """
        测试成功场景（跳转回溯式）:
        - target_size = 20MB
        - S1 (30MB) <= 1.5 * 20MB (30MB) -> 满足
        - 预期: 走渐进路线 S1 -> S2。S2(15MB) < 20MB，成功。
        - 最佳方案应为 S2。
        """
        logging.info("\n--- Running test_compression_success_progressive ---")
        target_size = 20.0
        status, details = strategy.run_compression_strategy(self.input_pdf, self.test_dir, target_size)

        self.assertEqual(status, 'SUCCESS')
        self.assertEqual(details['best_scheme_id'], 2) # S2 是第一个成功的方案
        self.assertIn('final_path', details)
        self.assertTrue(Path(details['final_path']).exists())

    def test_compression_failure(self):
        """
        测试失败场景:
        - 目标大小: 0.5MB
        - 预期: 所有方案都无法满足大小，最终失败。
        """
        logging.info("\n--- Running test_compression_failure ---")
        target_size = 0.5
        status, details = strategy.run_compression_strategy(self.input_pdf, self.test_dir, target_size)

        self.assertEqual(status, 'FAILURE')
        self.assertIn('all_results', details)
        self.assertEqual(len(details['all_results']), 6) # 应包含所有6个方案的尝试结果

    def test_file_already_small_enough(self):
        """
        测试文件本身已经小于目标大小的场景。
        """
        logging.info("\n--- Running test_file_already_small_enough ---")
        # 模拟原始文件大小为1MB
        utils.get_file_size_mb = lambda x: 1.0 if x == self.input_pdf else fake_get_file_size_mb(x)
        
        target_size = 2.0
        status, details = strategy.run_compression_strategy(self.input_pdf, self.test_dir, target_size)

        self.assertEqual(status, 'SKIPPED')
        self.assertIn('message', details)

if __name__ == '__main__':
    unittest.main()
