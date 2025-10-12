# compressor/strategy.py

import logging
import tempfile
from pathlib import Path
from . import utils, pipeline

# 定义不同层级的压缩策略
STRATEGIES = {
    1: {  # 2MB <= S < 10MB
        "name": "高质量压缩",
        "params_sequence": [
            {'dpi': 300, 'bg_downsample': 1, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 300, 'bg_downsample': 2, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 300, 'bg_downsample': 3, 'jpeg2000_encoder': 'grok'},
            {'dpi': 250, 'bg_downsample': 3, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 200, 'bg_downsample': 4, 'jpeg2000_encoder': 'grok'},
        ]
    },
    2: {  # 10MB <= S < 50MB
        "name": "平衡压缩",
        "params_sequence": [
            {'dpi': 300, 'bg_downsample': 2, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 300, 'bg_downsample': 3, 'jpeg2000_encoder': 'grok'},
            {'dpi': 300, 'bg_downsample': 4, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 250, 'bg_downsample': 4, 'jpeg2000_encoder': 'grok'},
            {'dpi': 200, 'bg_downsample': 4, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 150, 'bg_downsample': 5, 'jpeg2000_encoder': 'grok'},
        ]
    },
    3: {  # S >= 50MB
        "name": "极限压缩",
        "params_sequence": [
            {'dpi': 200, 'bg_downsample': 3, 'jpeg2000_encoder': 'grok'},
            {'dpi': 200, 'bg_downsample': 4, 'jpeg2000_encoder': 'grok'},
            {'dpi': 200, 'bg_downsample': 5, 'jpeg2000_encoder': 'openjpeg'},
            {'dpi': 150, 'bg_downsample': 5, 'jpeg2000_encoder': 'grok'},
            {'dpi': 110, 'bg_downsample': 6, 'jpeg2000_encoder': 'grok'},
        ]
    }
}

def determine_tier(size_mb):
    """根据文件大小确定处理层级。"""
    if 2 <= size_mb < 10:
        return 1
    elif 10 <= size_mb < 50:
        return 2
    elif size_mb >= 50:
        return 3
    return 0  # 小于2MB或无效值

def run_iterative_compression(pdf_path, output_dir, target_size_mb, keep_temp_on_failure=False):
    """
    执行迭代压缩流程。
    返回 (bool, Path): (是否成功, 输出文件路径)
    """
    original_size_mb = utils.get_file_size_mb(pdf_path)
    tier = determine_tier(original_size_mb)
    
    if tier == 0:
        logging.warning(f"文件 {pdf_path.name} 大小不符合压缩范围，跳过。")
        return False, None

    strategy = STRATEGIES[tier]
    logging.info(f"文件 {pdf_path.name} (大小: {original_size_mb:.2f}MB) 应用策略: 层级 {tier} ({strategy['name']})")

    # 为了避免对每次尝试重复生成 hOCR，我们先选择用于 OCR 的最高 dpi 并仅生成一次 hOCR
    max_dpi = max(p['dpi'] for p in strategy['params_sequence'])
    temp_dir_str = utils.create_temp_directory()
    temp_dir = Path(temp_dir_str)
    try:
        logging.info(f"生成一次性图像和 hOCR (使用 DPI={max_dpi})，以便在所有尝试中复用")
        # 生成图像（使用最高 dpi）并运行 OCR 一次
        image_files = pipeline.deconstruct_pdf_to_images(pdf_path, temp_dir, max_dpi)
        if not image_files:
            logging.error("在生成用于 hOCR 的图像时失败，终止压缩流程。")
            return False, None

        hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
        if not hocr_file:
            logging.error("生成 hOCR 文件失败，终止压缩流程。")
            return False, None

        logging.info(f"将复用 hOCR 文件: {hocr_file}")

        # 首先执行第1次尝试
        first_params = strategy['params_sequence'][0]
        encoder = first_params.get('jpeg2000_encoder', 'openjpeg')
        logging.info(f"--- 首次尝试 (保守): DPI={first_params['dpi']}, BG-Downsample={first_params['bg_downsample']}, JPEG2000={encoder} ---")
        output_pdf_path = temp_dir / f"output_{pdf_path.stem}_first.pdf"
        if pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, first_params, output_pdf_path):
            result_size_mb = utils.get_file_size_mb(output_pdf_path)
            logging.info(f"首次尝试结果大小: {result_size_mb:.2f}MB (目标: < {target_size_mb}MB)")
            if result_size_mb <= target_size_mb:
                final_path = output_dir / f"{pdf_path.stem}_compressed.pdf"
                final_path.parent.mkdir(parents=True, exist_ok=True)
                utils.copy_file(output_pdf_path, final_path)
                logging.info(f"成功！文件已压缩并保存至: {final_path}")
                return True, final_path

            # 如果与目标相差较远 (阈值: 1.5x)，直接尝试最激进的参数
            threshold_factor = 1.5
            if result_size_mb > target_size_mb * threshold_factor:
                logging.info("首次结果离目标较远，直接尝试最激进策略")
                last_index = len(strategy['params_sequence']) - 1
                last_params = strategy['params_sequence'][last_index]
                logging.info(f"--- 直接尝试最激进参数: DPI={last_params['dpi']}, BG-Downsample={last_params['bg_downsample']} ---")
                last_output = temp_dir / f"output_{pdf_path.stem}_last.pdf"
                if not pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, last_params, last_output):
                    logging.error("最激进参数尝试失败，整体压缩失败。")
                    return False, None

                last_size = utils.get_file_size_mb(last_output)
                logging.info(f"最激进尝试结果大小: {last_size:.2f}MB (目标: < {target_size_mb}MB)")
                if last_size > target_size_mb:
                    logging.error("最激进尝试仍未达到目标，宣告失败。")
                    return False, None

                # 最激进成功，向上回溯以提高质量
                logging.info("最激进尝试成功，开始向上回溯尝试更高质量的参数")
                # 从 last_index-1 向 0 回溯，直到找到第一个不满足目标为止
                chosen_path = last_output
                for idx in range(last_index - 1, -1, -1):
                    params = strategy['params_sequence'][idx]
                    logging.info(f"--- 回溯尝试 idx={idx}: DPI={params['dpi']}, BG-Downsample={params['bg_downsample']} ---")
                    test_output = temp_dir / f"output_{pdf_path.stem}_back_{idx}.pdf"
                    if not pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, params, test_output):
                        logging.warning(f"回溯尝试 idx={idx} 重建失败，保留之前的成功结果")
                        break
                    test_size = utils.get_file_size_mb(test_output)
                    logging.info(f"回溯尝试结果大小: {test_size:.2f}MB")
                    if test_size <= target_size_mb:
                        chosen_path = test_output
                    else:
                        # 当前质量超过目标，停止回溯，使用上一次成功的结果
                        logging.info("当前回溯尝试超出目标，停止回溯，采用上一次成功结果")
                        break

                final_path = output_dir / f"{pdf_path.stem}_compressed.pdf"
                final_path.parent.mkdir(parents=True, exist_ok=True)
                utils.copy_file(chosen_path, final_path)
                logging.info(f"成功！最终文件已保存至: {final_path}")
                return True, final_path

            # 否则按序继续后续配置（从2开始顺序尝试）
        else:
            logging.warning("首次尝试重建失败，继续顺序尝试后续参数")

        # 顺序尝试剩下的配置（从第二项开始）
        for i in range(1, len(strategy['params_sequence'])):
            params = strategy['params_sequence'][i]
            encoder = params.get('jpeg2000_encoder', 'openjpeg')
            logging.info(f"--- 顺序尝试 {i+1}/{len(strategy['params_sequence'])}: DPI={params['dpi']}, BG-Downsample={params['bg_downsample']}, JPEG2000={encoder} ---")
            output_pdf_path = temp_dir / f"output_{pdf_path.stem}_{i}.pdf"
            try:
                if not pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, params, output_pdf_path):
                    continue
                result_size_mb = utils.get_file_size_mb(output_pdf_path)
                logging.info(f"尝试结果大小: {result_size_mb:.2f}MB (目标: < {target_size_mb}MB)")
                if result_size_mb <= target_size_mb:
                    final_path = output_dir / f"{pdf_path.stem}_compressed.pdf"
                    final_path.parent.mkdir(parents=True, exist_ok=True)
                    utils.copy_file(output_pdf_path, final_path)
                    logging.info(f"成功！文件已压缩并保存至: {final_path}")
                    return True, final_path
            except Exception as e:
                logging.error(f"顺序尝试 {i+1} 时发生错误: {e}")
                continue

        logging.warning(f"所有压缩尝试均失败，无法将 {pdf_path.name} 压缩至目标大小。")
        return False, None

    finally:
        # 根据 keep_temp_on_failure 标志决定是否删除临时目录
        if keep_temp_on_failure:
            logging.info(f"保留临时目录以便调试: {temp_dir_str}")
        else:
            utils.cleanup_directory(temp_dir_str)

def run_aggressive_compression(pdf_path, output_dir, target_size_mb, keep_temp_on_failure=False):
    """
    运行最激进的压缩策略，用于拆分后的文件片段。
    """
    logging.info(f"对拆分文件片段 {pdf_path.name} 运行激进压缩策略...")
    
    # 使用最激进的参数组合
    aggressive_params = [
        {'dpi': 150, 'bg_downsample': 4},
        {'dpi': 150, 'bg_downsample': 5},
        {'dpi': 120, 'bg_downsample': 3},
        {'dpi': 100, 'bg_downsample': 2},
    ]
    
    # 对于激进压缩，也先生成一次 hOCR（使用最高 dpi）并在多个激进参数中复用
    max_dpi = max(p['dpi'] for p in aggressive_params)
    temp_dir_str = utils.create_temp_directory()
    temp_dir = Path(temp_dir_str)
    try:
        logging.info(f"激进压缩：生成一次图像和 hOCR (DPI={max_dpi}) 用于后续多次尝试")
        image_files = pipeline.deconstruct_pdf_to_images(pdf_path, temp_dir, max_dpi)
        if not image_files:
            logging.error("生成用于激进压缩的图像失败。")
            return False, None

        hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
        if not hocr_file:
            logging.error("生成 hOCR 文件失败（激进压缩）。")
            return False, None

        for i, params in enumerate(aggressive_params):
            logging.info(f"--- 激进压缩尝试 {i+1}/{len(aggressive_params)}: DPI={params['dpi']}, BG-Downsample={params['bg_downsample']} ---")
            output_pdf_path = temp_dir / f"compressed_{pdf_path.stem}_{i}.pdf"
            try:
                if not pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, params, output_pdf_path):
                    continue

                result_size_mb = utils.get_file_size_mb(output_pdf_path)
                logging.info(f"激进压缩结果大小: {result_size_mb:.2f}MB (目标: < {target_size_mb}MB)")

                if result_size_mb <= target_size_mb:
                    final_path = output_dir / f"{pdf_path.stem}_compressed.pdf"
                    final_path.parent.mkdir(parents=True, exist_ok=True)
                    utils.copy_file(output_pdf_path, final_path)
                    logging.info(f"激进压缩成功！文件已保存至: {final_path}")
                    return True, final_path
            except Exception as e:
                logging.error(f"激进压缩尝试 {i+1} 时发生错误: {e}")
                continue

        logging.error(f"激进压缩失败，无法将 {pdf_path.name} 压缩至目标大小。")
        return False, None
    finally:
        if keep_temp_on_failure:
            logging.info(f"保留激进压缩临时目录以便调试: {temp_dir_str}")
        else:
            utils.cleanup_directory(temp_dir_str)