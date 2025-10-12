# compressor/splitter.py

import logging
import math
import tempfile
from pathlib import Path
from . import utils, strategy, pipeline

def split_pdf(pdf_path, output_path, start_page, end_page):
    """
    使用 qpdf 拆分PDF文件。
    """
    logging.info(f"正在拆分 {pdf_path.name}: 页码 {start_page}-{end_page} -> {output_path.name}")
    command = [
        "qpdf",
        str(pdf_path),
        "--pages",
        ".",  # 代表输入文件
        f"{start_page}-{end_page}",
        "--",
        str(output_path)
    ]
    return utils.run_command(command)

def calculate_split_strategy(total_size_mb, max_splits):
    """
    根据文件大小计算最优的拆分策略。
    返回建议的初始拆分数量。
    """
    # 启发式算法：假设一个25MB的块比较有希望被压缩到2MB
    estimated_chunk_size = 25
    initial_k = min(max_splits, math.ceil(total_size_mb / estimated_chunk_size))
    
    # 最小拆分数为2
    if initial_k < 2:
        initial_k = 2
    
    logging.info(f"文件大小 {total_size_mb:.2f}MB，建议初始拆分数: {initial_k}")
    return initial_k

def run_splitting_protocol(pdf_path, output_dir, args):
    """
    执行拆分协议。
    """
    logging.info(f"为 {pdf_path.name} 启动应急拆分协议...")
    
    # 获取PDF页数
    total_pages = pipeline.get_pdf_page_count(pdf_path)
    if total_pages == 0:
        logging.error("无法获取页数，拆分中止。")
        return False

    logging.info(f"PDF总页数: {total_pages}")
    
    # 计算初始拆分策略
    original_size_mb = utils.get_file_size_mb(pdf_path)
    initial_k = calculate_split_strategy(original_size_mb, args.max_splits)

    # 尝试不同的拆分数量
    for k in range(initial_k, args.max_splits + 1):
        logging.info(f"=== 尝试拆分为 {k} 部分 ===")
        
        if not try_split_and_compress(pdf_path, output_dir, args, k, total_pages):
            logging.warning(f"拆分为 {k} 部分失败，尝试增加拆分数...")
            continue
        else:
            logging.info(f"成功将 {pdf_path.name} 拆分为 {k} 部分并全部压缩成功！")
            return True

    logging.error(f"拆分协议失败：即使拆分为 {args.max_splits} 部分，也无法完成压缩。")
    return False

def try_split_and_compress(pdf_path, output_dir, args, k, total_pages):
    """
    尝试将PDF拆分为k部分并压缩每一部分。
    """
    pages_per_split = math.ceil(total_pages / k)
    split_files = []
    temp_split_files = []
    
    # 创建临时目录用于存放拆分文件
    temp_dir_str = utils.create_temp_directory()
    temp_dir = Path(temp_dir_str)
    
    try:
        # 第一阶段：拆分PDF
        for i in range(k):
            start_page = i * pages_per_split + 1
            end_page = min((i + 1) * pages_per_split, total_pages)
            
            if start_page > total_pages:
                break

            part_path = temp_dir / f"{pdf_path.stem}_temp_part{i+1}.pdf"
            
            # 拆分PDF
            if not split_pdf(pdf_path, part_path, start_page, end_page):
                logging.error(f"拆分第 {i+1} 部分失败。")
                return False
            
            temp_split_files.append(part_path)
            logging.info(f"成功拆分第 {i+1} 部分 (页码 {start_page}-{end_page})")

        # 第二阶段：压缩每个拆分文件
        for i, part_path in enumerate(temp_split_files):
            logging.info(f"开始压缩第 {i+1} 部分: {part_path.name}")
            
            # 对拆分后的文件使用激进压缩策略（传递 keep_temp_on_failure）
            keep_temp = getattr(args, 'keep_temp_on_failure', False)
            success, compressed_path = strategy.run_aggressive_compression(
                part_path, output_dir, args.target_size, keep_temp_on_failure=keep_temp
            )

            if success:
                # 重命名为最终文件名
                final_part_name = f"{pdf_path.stem}_part{i+1}.pdf"
                final_part_path = output_dir / final_part_name
                
                if compressed_path != final_part_path:
                    utils.copy_file(compressed_path, final_part_path)
                    # 删除临时压缩文件
                    if compressed_path.exists():
                        compressed_path.unlink()
                
                split_files.append(final_part_path)
                logging.info(f"第 {i+1} 部分压缩成功: {final_part_path}")
            else:
                logging.error(f"第 {i+1} 部分压缩失败。")
                # 清理已成功的文件
                for success_file in split_files:
                    if success_file.exists():
                        success_file.unlink()
                return False

        # 所有部分都成功
        logging.info(f"所有 {len(split_files)} 个部分都已成功压缩")
        return True
        
    except Exception as e:
        logging.error(f"拆分和压缩过程中发生错误: {e}")
        # 清理已创建的文件
        for success_file in split_files:
            if success_file.exists():
                success_file.unlink()
        return False
    finally:
        # 清理临时目录（如果用户要求在失败时保留，则跳过清理）
        keep_temp = getattr(args, 'keep_temp_on_failure', False)
        # 如果要求保留且有失败发生，则保留临时目录
        if keep_temp:
            logging.info(f"保留拆分临时目录以便调试: {temp_dir_str}")
        else:
            utils.cleanup_directory(temp_dir_str)

def estimate_compression_feasibility(pdf_path, target_size_mb):
    """
    估算文件是否有可能被压缩到目标大小。
    这是一个启发式函数，用于优化拆分策略。
    """
    current_size_mb = utils.get_file_size_mb(pdf_path)
    compression_ratio = target_size_mb / current_size_mb
    
    # 基于经验的可行性判断
    if compression_ratio > 0.5:  # 压缩比超过50%
        return "很可能成功"
    elif compression_ratio > 0.2:  # 压缩比超过20%
        return "可能成功"
    elif compression_ratio > 0.05:  # 压缩比超过5%
        return "困难但可能"
    else:
        return "几乎不可能"

def validate_split_results(split_files, target_size_mb):
    """
    验证拆分结果是否符合要求。
    """
    all_valid = True
    total_size = 0
    
    for file_path in split_files:
        if not file_path.exists():
            logging.error(f"拆分文件不存在: {file_path}")
            all_valid = False
            continue
            
        size_mb = utils.get_file_size_mb(file_path)
        total_size += size_mb
        
        if size_mb > target_size_mb:
            logging.error(f"拆分文件 {file_path.name} 大小 {size_mb:.2f}MB 超过目标 {target_size_mb}MB")
            all_valid = False
        else:
            logging.info(f"拆分文件 {file_path.name} 大小 {size_mb:.2f}MB 符合要求")
    
    logging.info(f"拆分文件总大小: {total_size:.2f}MB")
    return all_valid