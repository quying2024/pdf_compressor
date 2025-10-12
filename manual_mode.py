"""manual_mode.py

交互式手动压缩模块。
此模块尽量独立于主调度器（orchestrator），直接使用 pipeline 中的低级函数完成一次性手动重建。
支持针对单个文件或目录的批量手动处理；可选择是否启用拆分（拆分会调用现有的 splitter 协议）。
"""

import logging
from pathlib import Path
from types import SimpleNamespace
from compressor import pipeline, utils, splitter


def prompt(prompt_text, default=None, cast=str):
    """辅助函数：带默认值的输入提示并进行类型转换。"""
    if default is not None:
        prompt_full = f"{prompt_text} [{default}]: "
    else:
        prompt_full = f"{prompt_text}: "

    val = input(prompt_full).strip()
    if val == "":
        return default
    try:
        return cast(val)
    except Exception:
        print(f"无效输入，期望类型 {cast.__name__}，请重试。")
        return prompt(prompt_text, default, cast)


def run_single_manual(pdf_path: Path, dest_path: Path, dpi: int, bg_downsample: int, jpeg2000: str, keep_temp_on_failure: bool = False):
    """对单个PDF运行手动DAR流程并将结果写入 dest_path（Path）。"""
    temp_dir_str = utils.create_temp_directory()
    temp_dir = Path(temp_dir_str)
    success = False
    try:
        logging.info(f"手动模式: 将 {pdf_path} 转为图像 (DPI={dpi})")
        image_files = pipeline.deconstruct_pdf_to_images(pdf_path, temp_dir, dpi)
        if not image_files:
            logging.error("生成图像失败，手动流程中止。")
            return False

        logging.info("运行 OCR 生成 hOCR ...")
        hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
        if not hocr_file:
            logging.error("生成 hOCR 失败，手动流程中止。")
            return False

        params = {
            'dpi': dpi,
            'bg_downsample': bg_downsample,
            'jpeg2000_encoder': jpeg2000
        }

        logging.info(f"开始重建 PDF，参数: {params}")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        success = pipeline.reconstruct_pdf(image_files, hocr_file, temp_dir, params, dest_path)
        if success:
            logging.info(f"手动重建成功: {dest_path}")
            return True
        else:
            logging.error("手动重建失败。")
            # 如果用户要求在失败时保留临时目录，则跳过清理
            if keep_temp_on_failure:
                logging.info(f"保留临时目录以便调试: {temp_dir_str}")
                print(f"临时目录保留: {temp_dir_str}")
                return False
            return False
    finally:
        # 只有在未要求保留或成功时才清理
        if not (keep_temp_on_failure and not success):
            utils.cleanup_directory(temp_dir_str)


def run_manual_interactive():
    """主交互入口：提示用户输入参数并执行单个或批量手动压缩。

    输入项（按提示）：
    - 源路径（单个PDF或目录）
    - 目的路径（如果源为文件，填写最终输出文件；如果为目录，填写输出目录）
    - DPI (int)
    - bg-downsample (int)
    - JPEG2000 工具（openjpeg/grok）
    - 是否启用拆分 (y/n)
    - 若启用拆分：最大拆分数量 (int) 与 目标大小 (MB)
    """
    print("进入交互式全手动压缩模式 (Manual Mode)")

    src = prompt("请输入源路径（PDF文件或包含PDF的目录）", None, str)
    if not src:
        print("必须提供源路径，退出。")
        return
    src_path = Path(src).expanduser()
    if not src_path.exists():
        print(f"源路径不存在: {src_path}")
        return

    dest = prompt("请输入目的路径（文件或目录，视源而定）", None, str)
    if not dest:
        print("必须提供目的路径，退出。")
        return
    dest_path = Path(dest).expanduser()

    # DPI 校验
    while True:
        dpi = prompt("请输入 DPI", 300, int)
        if dpi is None:
            print("DPI 不能为空")
            continue
        if 72 <= dpi <= 1200:
            break
        print("DPI 应该在 72 到 1200 之间，请重试。")

    # bg-downsample 校验
    while True:
        bg_downsample = prompt("请输入 bg-downsample", 2, int)
        if bg_downsample is None:
            print("bg-downsample 不能为空")
            continue
        if 1 <= bg_downsample <= 10:
            break
        print("bg-downsample 应该在 1 到 10 之间，请重试。")

    # JPEG2000 校验
    while True:
        jpeg2000 = prompt("请选择 JPEG2000 工具 (openjpeg/grok)", "openjpeg", str)
        if jpeg2000 is None:
            jpeg2000 = 'openjpeg'
        jpeg2000 = jpeg2000.lower()
        if jpeg2000 in ("openjpeg", "grok"):
            break
        print("无效选项，请输入 openjpeg 或 grok。")

    # 是否保留临时目录
    keep_choice = prompt("在失败时是否保留临时目录以便调试? (y/n)", "n", str)
    keep_temp_on_failure = str(keep_choice).lower().startswith('y')

    split_choice = prompt("是否启用拆分协议? (y/n)", "n", str)
    do_split = str(split_choice).lower().startswith('y')

    if do_split:
        while True:
            max_splits = prompt("最大拆分数量 (2-10)", 4, int)
            if 2 <= max_splits <= 10:
                break
            print("最大拆分数量应在2到10之间，请重试。")

        while True:
            target_size = prompt("拆分后每部分的目标大小 (MB)", 2.0, float)
            if target_size is not None and target_size > 0:
                break
            print("目标大小必须大于0，请重试。")

    # 处理文件或目录
    if src_path.is_file() and src_path.suffix.lower() == '.pdf':
        # 目标如果是目录，则构造文件名
        if dest_path.is_dir():
            out_file = dest_path / f"{src_path.stem}_manual.pdf"
        else:
            out_file = dest_path

        if do_split:
            # 使用拆分协议：需要构造一个带属性的小对象传给 splitter
            args = SimpleNamespace(target_size=target_size, max_splits=max_splits, allow_splitting=True, keep_temp_on_failure=keep_temp_on_failure)
            print("启动拆分协议 (interactive manual)...")
            return splitter.run_splitting_protocol(src_path, dest_path, args)
        else:
            return run_single_manual(src_path, out_file, dpi, bg_downsample, jpeg2000, keep_temp_on_failure=keep_temp_on_failure)

    elif src_path.is_dir():
        # 批量目录：确保目的地为目录
        out_dir = dest_path
        out_dir.mkdir(parents=True, exist_ok=True)
        pdfs = sorted([p for p in src_path.glob('*.pdf')])
        if not pdfs:
            print("在源目录中未找到 PDF 文件。")
            return

        success_count = 0
        for pdf in pdfs:
            print(f"处理: {pdf.name}")
            if do_split:
                args = SimpleNamespace(target_size=target_size, max_splits=max_splits, allow_splitting=True, keep_temp_on_failure=keep_temp_on_failure)
                ok = splitter.run_splitting_protocol(pdf, out_dir, args)
            else:
                out_file = out_dir / f"{pdf.stem}_manual.pdf"
                ok = run_single_manual(pdf, out_file, dpi, bg_downsample, jpeg2000, keep_temp_on_failure=keep_temp_on_failure)

            if ok:
                success_count += 1

        print(f"批量处理完成: 成功 {success_count}/{len(pdfs)}")
        return
    else:
        print("源路径既不是PDF文件也不是目录，退出。")
        return
