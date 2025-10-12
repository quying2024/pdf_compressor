# orchestrator.py

import logging
from pathlib import Path
from compressor import utils, strategy, splitter

def process_file(file_path, args):
    """
    处理单个PDF文件的总入口。
    """
    logging.info(f"================== 开始处理文件: {file_path.name} ==================")
    
    try:
        original_size_mb = utils.get_file_size_mb(file_path)
        logging.info(f"原始文件大小: {original_size_mb:.2f}MB")
        
        if original_size_mb < args.target_size:
            logging.info(f"文件大小 ({original_size_mb:.2f}MB) 已满足要求 (< {args.target_size}MB)，跳过处理。")
            # 可选：将文件复制到输出目录
            if args.copy_small_files:
                output_path = Path(args.output_dir) / file_path.name
                utils.copy_file(file_path, output_path)
                logging.info(f"原文件已复制到输出目录: {output_path}")
            return True

        # 运行迭代压缩
        logging.info(f"开始迭代压缩流程...")
        success, result_path = strategy.run_iterative_compression(
            file_path,
            Path(args.output_dir),
            args.target_size,
            keep_temp_on_failure=getattr(args, 'keep_temp_on_failure', False)
        )

        if success:
            logging.info(f"✓ 压缩成功: {file_path.name} -> {result_path.name}")
            return True
        elif args.allow_splitting:
            logging.info(f"压缩失败，但已启用拆分功能。启动拆分协议...")
            split_success = splitter.run_splitting_protocol(
                file_path, 
                Path(args.output_dir), 
                args
            )
            if split_success:
                logging.info(f"✓ 拆分压缩成功: {file_path.name}")
                return True
            else:
                logging.error(f"✗ 拆分压缩失败: {file_path.name}")
                return False
        else:
            logging.warning(f"✗ 压缩失败，且未启用拆分功能: {file_path.name}")
            return False

    except Exception as e:
        logging.critical(f"处理文件 {file_path.name} 时发生意外错误: {e}", exc_info=True)
        return False
    finally:
        logging.info(f"================== 文件处理结束: {file_path.name} ==================\n")

def process_directory(input_dir, args):
    """
    处理目录中的所有PDF文件。
    """
    input_path = Path(input_dir)
    logging.info(f"开始扫描目录: {input_path}")
    
    # 查找所有PDF文件（支持大小写不敏感）
    pdf_files = []
    for pattern in ["*.pdf", "*.PDF", "*.Pdf", "*.pDf", "*.pdF", "*.PdF", "*.PDf", "*.pDF"]:
        pdf_files.extend(sorted(input_path.glob(pattern)))
    
    # 去重（防止文件名大小写变化导致重复）
    unique_files = list(set(pdf_files))
    unique_files.sort()
    
    if not unique_files:
        logging.warning("在指定目录中未找到PDF文件。")
        return []
    
    logging.info(f"找到 {len(unique_files)} 个PDF文件，准备处理...")
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for i, pdf_file in enumerate(unique_files, 1):
        logging.info(f"\n>>> 处理进度: {i}/{len(unique_files)} <<<")
        success = process_file(pdf_file, args)
        results.append({
            'file': pdf_file,
            'success': success
        })
        
        if success:
            successful_count += 1
        else:
            failed_count += 1
    
    # 生成处理报告
    logging.info(f"\n" + "="*60)
    logging.info(f"批量处理完成")
    logging.info(f"总文件数: {len(unique_files)}")
    logging.info(f"处理成功: {successful_count}")
    logging.info(f"处理失败: {failed_count}")
    logging.info(f"成功率: {(successful_count/len(unique_files)*100):.1f}%")
    
    if failed_count > 0:
        logging.info(f"\n失败文件列表:")
        for result in results:
            if not result['success']:
                logging.info(f"  - {result['file'].name}")
    
    logging.info("="*60)
    
    return results

def generate_summary_report(results, output_dir):
    """
    生成处理结果汇总报告。
    """
    report_path = Path(output_dir) / "processing_report.txt"
    
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("PDF压缩处理报告\n")
            f.write("=" * 50 + "\n\n")
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            f.write(f"处理时间: {utils.get_current_timestamp()}\n")
            f.write(f"总文件数: {len(results)}\n")
            f.write(f"成功处理: {len(successful)}\n")
            f.write(f"处理失败: {len(failed)}\n")
            f.write(f"成功率: {(len(successful)/len(results)*100):.1f}%\n\n")
            
            if successful:
                f.write("成功处理的文件:\n")
                f.write("-" * 30 + "\n")
                for result in successful:
                    f.write(f"✓ {result['file'].name}\n")
                f.write("\n")
            
            if failed:
                f.write("处理失败的文件:\n")
                f.write("-" * 30 + "\n")
                for result in failed:
                    f.write(f"✗ {result['file'].name}\n")
                f.write("\n")
            
            f.write("详细日志请查看 logs/process.log 文件\n")
        
        logging.info(f"处理报告已生成: {report_path}")
        
    except Exception as e:
        logging.error(f"生成报告时出错: {e}")

def validate_arguments(args):
    """
    验证命令行参数的有效性。
    """
    input_path = Path(args.input)
    output_path = Path(args.output_dir)
    
    # 检查输入路径
    if not input_path.exists():
        logging.error(f"输入路径不存在: {input_path}")
        return False
    
    # 检查目标大小
    if args.target_size <= 0:
        logging.error(f"目标大小必须大于0: {args.target_size}")
        return False
    
    # 检查最大拆分数
    if args.max_splits < 2 or args.max_splits > 10:
        logging.error(f"最大拆分数应在2-10之间: {args.max_splits}")
        return False
    
    # 创建输出目录
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"无法创建输出目录 {output_path}: {e}")
        return False
    
    return True