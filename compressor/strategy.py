# compressor/strategy.py

import logging
import tempfile
from pathlib import Path
from . import utils, pipeline

# 定义从S1（最保守）到S6（最激进）的6个压缩方案
# 方案设计考虑了DPI、背景降采样和JPEG2000编码器的组合
COMPRESSION_SCHEMES = {
    1: {'name': 'S1-保守', 'dpi': 300, 'bg_downsample': 2, 'jpeg2000_encoder': 'openjpeg'},
    2: {'name': 'S2-温和', 'dpi': 300, 'bg_downsample': 3, 'jpeg2000_encoder': 'grok'},
    3: {'name': 'S3-平衡', 'dpi': 250, 'bg_downsample': 3, 'jpeg2000_encoder': 'openjpeg'},
    4: {'name': 'S4-进取', 'dpi': 200, 'bg_downsample': 4, 'jpeg2000_encoder': 'grok'},
    5: {'name': 'S5-激进', 'dpi': 150, 'bg_downsample': 5, 'jpeg2000_encoder': 'openjpeg'},
    6: {'name': 'S6-极限', 'dpi': 110, 'bg_downsample': 6, 'jpeg2000_encoder': 'grok'},
}

def _precompute_dar_steps(input_pdf_path, temp_dir):
    """
    执行一次性的解构和分析步骤。
    """
    try:
        # 使用S1的DPI进行解构，因为它是最高质量的
        dpi_for_deconstruct = COMPRESSION_SCHEMES[1]['dpi']
        logging.info(f"Deconstructing PDF with DPI: {dpi_for_deconstruct}")
        image_files = pipeline.deconstruct_pdf_to_images(input_pdf_path, temp_dir, dpi=dpi_for_deconstruct)
        if not image_files:
            logging.error("预处理失败：未能从PDF中提取图像。")
            return None
        
        logging.info("Analyzing images to generate hOCR...")
        hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
        if not hocr_file:
            logging.error("预处理失败：未能生成hOCR文件。")
            return None
            
        return {'image_files': image_files, 'hocr_file': hocr_file}
    except Exception as e:
        logging.error(f"预处理步骤中发生错误: {e}", exc_info=True)
        return None

def run_compression_strategy(input_pdf_path, output_dir, target_size_mb, keep_temp_on_failure=False):
    """
    运行新的二进制双向搜索压缩策略。
    返回一个状态元组 (status, details)。
    status: 'SUCCESS', 'FAILURE', 'SKIPPED', 'ERROR'
    details: 包含结果信息的字典
    """
    original_size_mb = utils.get_file_size_mb(input_pdf_path)
    logging.info(f"文件 {input_pdf_path.name} (大小: {original_size_mb:.2f}MB) 应用新的压缩策略...")

    if original_size_mb < target_size_mb:
        logging.warning(f"文件 {input_pdf_path.name} ({original_size_mb:.2f}MB) 已满足要求，跳过压缩。")
        return 'SKIPPED', {'message': 'File size is already within target.'}

    temp_dir = Path(utils.create_temp_directory())
    
    try:
        # 预计算步骤：只执行一次最耗时的解构和分析
        logging.info(f"预处理：使用最高DPI ({COMPRESSION_SCHEMES[1]['dpi']}) 生成图像和hOCR文件...")
        precomputed_data = _precompute_dar_steps(input_pdf_path, temp_dir)
        if not precomputed_data:
            return 'ERROR', {'message': 'Preprocessing (DAR) failed.'}

        # 运行核心策略逻辑
        final_result_path, all_results = _run_strategy_logic(
            input_pdf_path, output_dir, target_size_mb, temp_dir, precomputed_data
        )

        if final_result_path:
            best_scheme_id = final_result_path['scheme_id']
            final_path = final_result_path['path']
            return 'SUCCESS', {
                'best_scheme_id': best_scheme_id,
                'final_path': final_path,
                'all_results': all_results
            }
        else:
            return 'FAILURE', {'all_results': all_results}

    except Exception as e:
        logging.critical(f"压缩策略执行期间发生意外错误: {e}", exc_info=True)
        return 'ERROR', {'message': str(e), 'all_results': {}}
    finally:
        if keep_temp_on_failure and 'final_result_path' not in locals():
             logging.warning(f"压缩失败，临时目录保留在: {temp_dir}")
        else:
            utils.cleanup_directory(temp_dir)

def _run_strategy_logic(input_pdf_path, output_dir, target_size_mb, temp_dir, precomputed_data):
    """
    包含核心压缩策略逻辑的内部函数。
    返回 (final_result_path_dict, all_results) 或 (None, all_results)
    """
    all_results = {}

    # 步骤1: 总是先执行最保守的方案S1
    logging.info("--- 步骤1: 执行最保守方案 S1 ---")
    s1_result_path = _execute_scheme(1, temp_dir, precomputed_data, input_pdf_path.name)
    if not s1_result_path:
        logging.error("关键错误：方案S1执行失败，无法继续。")
        return None, all_results
    
    s1_size_mb = utils.get_file_size_mb(s1_result_path)
    all_results[1] = {'path': s1_result_path, 'size': s1_size_mb}

    # 检查S1是否已经满足要求
    if s1_size_mb <= target_size_mb:
        logging.info(f"太棒了！最保守的方案S1已满足要求 (大小: {s1_size_mb:.2f}MB)。")
        return _copy_to_output(1, all_results, output_dir, input_pdf_path.name), all_results
    
    # 根据S1的结果决定下一步策略
    try:
        # 如果S1的结果大于目标大小的1.5倍，则启动“跳跃-回溯”策略
        if s1_size_mb > target_size_mb * 1.5:
            logging.info(f"S1结果 ({s1_size_mb:.2f}MB) > 阈值 ({target_size_mb * 1.5:.2f}MB)，启动【跳跃-回溯】策略。")
            
            # 步骤2.1: 直接尝试最激进的方案S6
            logging.info("--- 步骤2.1: 执行最激进方案 S6 ---")
            s6_result_path = _execute_scheme(6, temp_dir, precomputed_data, input_pdf_path.name)
            if s6_result_path:
                s6_size_mb = utils.get_file_size_mb(s6_result_path)
                all_results[6] = {'path': s6_result_path, 'size': s6_size_mb}
                
                if s6_size_mb <= target_size_mb:
                    # S6成功，开始回溯以寻找更高质量的方案
                    logging.info("--- 步骤2.2: 回溯搜索更高质量的方案 ---")
                    best_scheme_id = 6
                    # 从S5到S2向上回溯
                    for i in range(5, 1, -1):
                        result_path = _execute_scheme(i, temp_dir, precomputed_data, input_pdf_path.name)
                        if result_path:
                            size_mb = utils.get_file_size_mb(result_path)
                            all_results[i] = {'path': result_path, 'size': size_mb}
                            if size_mb <= target_size_mb:
                                best_scheme_id = i # 更新为当前更优的方案
                                logging.info(f"方案 {COMPRESSION_SCHEMES[i]['name']} 成功，大小 {size_mb:.2f}MB，继续回溯...")
                            else:
                                logging.info(f"方案 {COMPRESSION_SCHEMES[i]['name']} 超出目标，选择前一个方案 {COMPRESSION_SCHEMES[best_scheme_id]['name']} 作为最优解。")
                                break # 当前方案失败，停止回溯
                    
                    logging.info(f"回溯完成，方案 {COMPRESSION_SCHEMES[best_scheme_id]['name']} 是可满足目标的最高质量方案。")
                    return _copy_to_output(best_scheme_id, all_results, output_dir, input_pdf_path.name), all_results

            # 如果S6失败或未执行，则按顺序尝试S2到S5
            logging.warning("S6方案未成功或未执行，将按顺序尝试剩余方案...")
            for i in range(2, 6):
                if i not in all_results:
                    result_path = _execute_scheme(i, temp_dir, precomputed_data, input_pdf_path.name)
                    if result_path:
                        size_mb = utils.get_file_size_mb(result_path)
                        all_results[i] = {'path': result_path, 'size': size_mb}
                        if size_mb <= target_size_mb:
                            logging.info(f"成功！方案 {COMPRESSION_SCHEMES[i]['name']} 满足要求。")
                            # 在这种情况下，我们找到了一个可行的方案，但不是通过回溯，所以直接返回
                            return _copy_to_output(i, all_results, output_dir, input_pdf_path.name), all_results
            
            logging.error("所有压缩方案均失败。")
            return None, all_results

        # 如果S1的结果在目标大小的1.5倍以内，则启动“渐进式”策略
        else:
            logging.info(f"S1结果 ({s1_size_mb:.2f}MB) <= 阈值 ({target_size_mb * 1.5:.2f}MB)，启动【渐进式压缩】策略。")
            # 从S2到S6顺序执行，直到找到第一个满足条件的
            for i in range(2, 7):
                result_path = _execute_scheme(i, temp_dir, precomputed_data, input_pdf_path.name)
                if result_path:
                    size_mb = utils.get_file_size_mb(result_path)
                    all_results[i] = {'path': result_path, 'size': size_mb}
                    if size_mb <= target_size_mb:
                        logging.info(f"成功！方案 {COMPRESSION_SCHEMES[i]['name']} 满足要求。")
                        return _copy_to_output(i, all_results, output_dir, input_pdf_path.name), all_results
            
            logging.error("所有渐进式压缩方案均失败。")
            return None, all_results
    except Exception as e:
        logging.critical(f"压缩策略逻辑执行期间发生意外错误: {e}", exc_info=True)
        return None, all_results

def _copy_to_output(scheme_id, all_results, output_dir, original_filename):
    """将最终选定的PDF复制到输出目录。"""
    source_path = all_results[scheme_id]['path']
    output_filename = Path(original_filename).stem + "_compressed.pdf"
    dest_path = output_dir / output_filename
    
    try:
        utils.copy_file(source_path, dest_path)
        logging.info(f"文件已复制: {source_path} -> {dest_path}")
        return {'path': dest_path, 'scheme_id': scheme_id}
    except Exception as e:
        logging.error(f"复制最终文件时出错: {e}")
        return None

def _execute_scheme(scheme_id, temp_dir, precomputed_data, original_filename):
    """
    执行单个压缩方案。
    现在接收 precomputed_data 字典。
    """
    scheme = COMPRESSION_SCHEMES[scheme_id]
    logging.info(f"--- 正在执行方案 {scheme['name']}: DPI={scheme['dpi']}, BG-Downsample={scheme['bg_downsample']}, Encoder={scheme['jpeg2000_encoder']} ---")
    
    output_pdf_path = temp_dir / f"output_{Path(original_filename).stem}_S{scheme_id}.pdf"
    
    params = {
        'name': scheme['name'],
        'dpi': scheme['dpi'],
        'bg_downsample': scheme['bg_downsample'],
        'jpeg2000_encoder': scheme['jpeg2000_encoder']
    }

    try:
        success = pipeline.reconstruct_pdf(
            image_files=precomputed_data['image_files'],
            hocr_file=precomputed_data['hocr_file'],
            temp_dir=temp_dir,
            params=params,
            output_pdf_path=output_pdf_path
        )
        if success:
            return output_pdf_path
        else:
            logging.error(f"方案 {scheme['name']} 重建PDF失败。")
            return None
    except Exception as e:
        logging.error(f"执行方案 {scheme['name']} 时发生意外错误: {e}", exc_info=True)
        return None