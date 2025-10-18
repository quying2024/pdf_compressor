# main.py

import argparse
import logging
import sys
from pathlib import Path
from compressor import utils
import orchestrator

# 在程序开始时立即设置 UTF-8 编码，避免 Windows 下的编码问题
if sys.platform == 'win32':
    try:
        # 设置标准输出和标准错误为 UTF-8
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        # 如果 reconfigure 不可用（旧版 Python），使用包装器
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def create_argument_parser():
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="基于 archive-pdf-tools 的PDF自动化压缩与拆分工具",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用示例:
  # 处理单个文件，允许拆分
  python main.py --input document.pdf --output ./output --allow-splitting

  # 处理整个目录，使用默认设置
  python main.py --input ./pdf_folder --output ./processed

  # 自定义目标大小为8MB，不允许拆分
  python main.py --input large.pdf --output ./output --target-size 8.0

注意事项:
  - 确保已安装必要工具: pdftoppm, tesseract, recode_pdf, qpdf
  - 处理大文件可能需要较长时间
  - 所有处理日志保存在 logs/process.log 文件中
        """
    )
    
    parser.add_argument(
        "--input",
        help="输入的源路径，可以是一个PDF文件或一个包含PDF文件的目录。"
    )
    
    parser.add_argument(
        "--output",
        dest="output_dir",  # 内部仍使用 output_dir 变量名以保持代码兼容
        metavar="DIR",
        help="处理后文件的存放目录。"
    )
    
    parser.add_argument(
        "--target-size",
        type=float,
        default=2.0,
        help="目标文件大小，单位为MB。默认值为 2.0。"
    )
    
    parser.add_argument(
        "--allow-splitting",
        action="store_true",
        help="如果提供此参数，则允许在压缩失败时启用拆分功能。"
    )
    
    parser.add_argument(
        "--max-splits",
        type=int,
        default=4,
        choices=[2, 3, 4, 5, 6, 7, 8, 9, 10],
        help="允许的最大拆分数量。默认值为 4。"
    )
    
    parser.add_argument(
        "--copy-small-files",
        action="store_true",
        help="是否将已经满足大小要求的文件复制到输出目录。"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="仅检查依赖工具是否安装，不执行处理。"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细的调试信息。"
    )

    parser.add_argument(
        "-k", "--keep-temp-on-failure",
        action="store_true",
        help="如果压缩失败，保留临时目录以便调试（默认失败时会删除）。"
    )
    parser.add_argument(
        "-?", "--examples",
        action="store_true",
        help="输出常用参数示例并退出。"
    )
    parser.add_argument(
        "-m", "--manual",
        action="store_true",
        help="进入交互式全手动压缩模式，允许输入 DPI/bg-downsample/JPEG2000 等参数。"
    )
    
    return parser

def print_banner():
    """打印程序启动横幅。"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    PDF 压缩与拆分工具                         ║
║                                                              ║
║  基于 archive-pdf-tools 的职称申报PDF文件自动化处理工具       ║
║  实现"解构-分析-重建"(DAR)三阶段压缩策略                      ║
║                                                              ║
║  版本: 1.0.0                                                 ║
╚══════════════════════════════════════════════════════════════╝
    """
    try:
        print(banner)
    except UnicodeEncodeError:
        # 如果遇到编码问题，尝试使用 UTF-8 编码
        import sys
        sys.stdout.buffer.write(banner.encode('utf-8'))
        sys.stdout.buffer.write(b'\n')

def main():
    """主函数：解析参数并分发任务。"""
    print_banner()
    
    parser = create_argument_parser()
    args = parser.parse_args()

    # 如果用户请求显示示例用法，打印几个常用命令并退出
    if getattr(args, 'examples', False):
        examples = [
            "# 将 single.pdf 压缩到目标 5MB 并输出到 out/ 目录",
            "python main.py --input single.pdf --output out --target-size 5",
            "",
            "# 处理 ./pdfs 目录中的所有PDF，允许拆分，并在失败时保留临时目录以供调试",
            "python main.py --input ./pdfs --output ./out --target-size 3 --allow-splitting --max-splits 4 -k",
            "",
            "# 仅检查依赖，不执行压缩（用于诊断）",
            "python main.py --check-deps",
            "",
            "# 进入全手动模式，手动输入 DPI、bg-downsample、JPEG2000 编码器等参数",
            "python main.py --manual",
        ]
        print("示例用法:")
        for line in examples:
            print(line)
        return
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 初始化日志系统
    utils.setup_logging()
    
    logging.info("程序启动")
    logging.info(f"Python版本: {sys.version}")
    
    # 仅检查依赖
    if args.check_deps:
        print("\n正在检查依赖工具...")
        if utils.check_dependencies():
            print("✓ 所有必要工具已安装")
            sys.exit(0)
        else:
            print("✗ 缺少必要工具，请安装后重试")
            sys.exit(1)
    
    # 交互式全手动模式（独立模块） - 放在必需参数检查之前以便单独运行
    if getattr(args, 'manual', False):
        # 延迟导入，避免影响正常流程
        try:
            import manual_mode
        except Exception as e:
            logging.error(f"无法加载手动模式模块: {e}")
            sys.exit(1)

        manual_mode.run_manual_interactive()
        return

    # 检查必需参数
    if not args.input:
        logging.error("错误: 必须指定 --input 参数")
        parser.print_help()
        sys.exit(1)
    
    if not args.output_dir:
        logging.error("错误: 必须指定 --output 参数")
        parser.print_help()
        sys.exit(1)
    
    # 验证参数
    if not orchestrator.validate_arguments(args):
        logging.error("参数验证失败")
        sys.exit(1)
    
    # 检查依赖工具
    logging.info("检查必要工具...")
    if not utils.check_dependencies():
        logging.error("依赖检查失败，程序退出")
        sys.exit(1)
    
    input_path = Path(args.input)
    output_path = Path(args.output_dir)
    
    logging.info("=== 任务开始 ===")
    logging.info(f"输入路径: {input_path}")
    logging.info(f"输出目录: {output_path}")
    logging.info(f"目标大小: < {args.target_size} MB")
    logging.info(f"允许拆分: {'是' if args.allow_splitting else '否'}")
    if args.allow_splitting:
        logging.info(f"最大拆分: {args.max_splits} 部分")
    logging.info(f"复制小文件: {'是' if args.copy_small_files else '否'}")

    try:
        if input_path.is_dir():
            # 处理目录
            logging.info("输入为目录，开始批量处理...")
            results = orchestrator.process_directory(input_path, args)
            
            # 生成汇总报告
            if results:
                orchestrator.generate_summary_report(results, output_path)
                
        elif input_path.is_file() and input_path.suffix.lower() == '.pdf':
            # 处理单个文件
            logging.info("输入为单个PDF文件，开始处理...")
            success = orchestrator.process_file(input_path, args)
            
            if success:
                logging.info("✓ 文件处理成功")
            else:
                logging.error("✗ 文件处理失败")
                sys.exit(1)
        else:
            logging.error("输入路径既不是有效的目录，也不是PDF文件。")
            sys.exit(1)

    except KeyboardInterrupt:
        logging.warning("用户中断了程序执行")
        sys.exit(130)
    except Exception as e:
        logging.critical(f"程序执行过程中发生意外错误: {e}", exc_info=True)
        sys.exit(1)
    
    logging.info("=== 所有任务已完成 ===")
    print("\n处理完成！详细日志请查看 logs/process.log 文件。")

if __name__ == "__main__":
    main()