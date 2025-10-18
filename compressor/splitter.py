# compressor/splitter.py

import logging
import math
from pathlib import Path
from . import utils, pipeline

def run_splitting_strategy(compression_results, output_dir, args):
    """
    执行新的拆分策略。
    该策略不进行二次压缩，只对选定的最佳母版进行物理拆分。

    Args:
        compression_results (dict): 压缩阶段生成的所有中间结果。
        output_dir (Path): 最终输出目录。
        args (argparse.Namespace): 命令行参数。

    Returns:
        bool: 拆分是否成功。
    """
    logging.info("=== 启动新版拆分策略 ===")
    
    # 1. 选择拆分母版 (Select Splitting Source)
    source_to_split = _select_splitting_source(compression_results)
    if not source_to_split:
        logging.error("拆分失败：在压缩结果中找不到合适的拆分母版。")
        return False

    source_path = source_to_split['path']
    source_size_mb = source_to_split['size_mb']
    logging.info(f"选定拆分母版: {source_path.name}, 大小: {source_size_mb:.2f}MB")

    # 2. 计算页面密度 (Calculate Page Density)
    total_pages = pipeline.get_pdf_page_count(source_path)
    if total_pages == 0:
        logging.error(f"无法获取 {source_path.name} 的页数，拆分中止。")
        return False
    
    page_density = source_size_mb / total_pages
    logging.info(f"母版总页数: {total_pages}, 平均页面密度: {page_density:.4f} MB/页")

    # 3. 确定最优拆分数量 (Determine Optimal Split Count)
    target_size_mb = args.target_size
    try:
        split_count = _determine_optimal_split_count(source_size_mb, target_size_mb, args.max_splits)
    except ValueError as e:
        logging.error(f"拆分失败: {e}")
        return False
    
    logging.info(f"目标拆分数量: {split_count} 部分")

    # 4. 计算各部分页数 (Calculate Pages per Split)
    try:
        split_plan = _calculate_split_plan(total_pages, split_count, page_density, target_size_mb)
    except ValueError as e:
        logging.error(f"拆分失败: 无法规划页面分配。{e}")
        return False

    logging.info("生成拆分计划:")
    for i, part in enumerate(split_plan, 1):
        logging.info(f"  - 部分 {i}: 页码 {part['start']} - {part['end']} ({part['pages']} 页)")

    # 5. 执行物理拆分 (Execute Physical Split)
    logging.info("开始执行物理拆分...")
    original_stem = Path(args.input).stem
    
    for i, part_info in enumerate(split_plan, 1):
        part_path = output_dir / f"{original_stem}_part{i}.pdf"
        success = _split_pdf_physical(
            source_path,
            part_path,
            part_info['start'],
            part_info['end']
        )
        if not success:
            logging.error(f"拆分第 {i} 部分时失败。")
            # 理论上qpdf很稳定，如果失败，通常是IO问题，直接宣告失败
            return False
    
    logging.info("所有部分均已成功拆分！")
    # 清理压缩阶段留下的临时目录
    temp_dir_of_compression = source_path.parent
    if getattr(args, 'keep_temp_on_failure', False) is False:
        utils.cleanup_directory(temp_dir_of_compression)
    return True

def _select_splitting_source(all_results):
    """
    从所有压缩结果中选择最佳的拆分母版。
    规则：
    1. 寻找大小最接近8MB但 <= 8MB 的文件。
    2. 如果没有，则选择所有结果中最小的那个。
    """
    if not all_results:
        return None

    # 筛选出小于等于8MB的结果
    under_8mb = [res for res in all_results.values() if res['size_mb'] <= 8.0]

    if under_8mb:
        # 在小于8MB的结果中，按大小降序排序，取第一个（最接近8MB）
        best_source = sorted(under_8mb, key=lambda x: x['size_mb'], reverse=True)[0]
        logging.info(f"找到 {len(under_8mb)} 个小于8MB的候选母版，选择最大的一个。")
        return best_source
    else:
        # 如果没有小于8MB的，就选择所有结果中最小的那个
        logging.warning("没有找到小于8MB的压缩结果，将选择最小的一个作为拆分母版。")
        smallest_source = sorted(all_results.values(), key=lambda x: x['size_mb'])[0]
        return smallest_source

def _determine_optimal_split_count(source_size_mb, target_size_mb, max_splits):
    """
    计算最优的拆分数量 k。
    """
    if source_size_mb <= target_size_mb:
        # 这种情况理论上不应该发生，因为如果满足要求，压缩会成功
        logging.warning("拆分母版大小已满足要求，但仍启动拆分。将默认拆分为2部分。")
        return 2

    min_k = math.ceil(source_size_mb / target_size_mb)
    
    if min_k > max_splits:
        raise ValueError(f"即使按目标大小 {target_size_mb}MB 拆分，也需要 {min_k} 个部分，超过了最大限制 {max_splits}。")

    return int(min_k) if min_k > 1 else 2

def _calculate_split_plan(total_pages, k, page_density, target_size_mb):
    """
    动态计算每个部分的页码范围。
    """
    plan = []
    
    # 计算单个部分能容纳的最大页数（安全红线）
    # 留出一点缓冲，例如98%
    safe_target_size = target_size_mb * 0.98
    if page_density == 0:
        # 避免除零错误，虽然不太可能发生
        raise ValueError("页面密度为0，无法进行拆分规划。")
    max_pages_per_part = math.floor(safe_target_size / page_density)
    if max_pages_per_part == 0:
        raise ValueError(f"页面密度过高 ({page_density:.4f} MB/页)，单页大小已超过目标。")

    logging.debug(f"每个拆分部分的安全页数上限: {max_pages_per_part}")

    start_page = 1
    remaining_pages = total_pages
    
    for i in range(k):
        remaining_parts = k - i
        
        # 计算当前部分应分配的页数
        if remaining_parts == 1:
            # 最后一部分，分配所有剩余页数
            pages_for_this_part = remaining_pages
        else:
            # 动态计算平均页数
            avg_pages = math.ceil(remaining_pages / remaining_parts)
            # 不能超过安全红线
            pages_for_this_part = min(avg_pages, max_pages_per_part)

        end_page = start_page + pages_for_this_part - 1
        
        # 确保不会超过总页数
        if end_page > total_pages:
            end_page = total_pages
            pages_for_this_part = end_page - start_page + 1

        plan.append({
            'start': start_page,
            'end': end_page,
            'pages': pages_for_this_part
        })

        start_page = end_page + 1
        remaining_pages -= pages_for_this_part

        if remaining_pages <= 0 and i < k - 1:
            # 页数提前分配完了，说明计划有误或页数太少
            logging.warning(f"页数在第 {i+1} 部分已分配完毕，实际拆分部分将少于计划的 {k} 部分。")
            break
    
    # 最终验证
    if sum(p['pages'] for p in plan) != total_pages or (plan and plan[-1]['end'] != total_pages):
        # 这是一个健壮性检查，理论上不应发生
        raise RuntimeError(f"页面分配计划生成错误：总页数不匹配。计划总页数: {sum(p['pages'] for p in plan)}, 实际总页数: {total_pages}")

    return plan

def _split_pdf_physical(pdf_path, output_path, start_page, end_page):
    """
    使用 qpdf 进行纯物理拆分。
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