#!/bin/bash

# run.sh
# PDF压缩工具快速启动脚本

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色文本
print_colored() {
    echo -e "${1}${2}${NC}"
}

# 显示使用帮助
show_help() {
    print_colored $BLUE "PDF压缩工具快速启动脚本"
    echo ""
    echo "用法: ./run.sh [选项] [PDF文件或目录]"
    echo ""
    echo "选项:"
    echo "  -h, --help              显示此帮助信息"
    echo "  -c, --check             检查依赖工具"
    echo "  -i, --install           安装依赖工具"
    echo "  -t, --test              运行测试检查"
    echo "  -s, --split             允许拆分文件"
    echo "  -v, --verbose           详细输出模式"
    echo "  -o, --output DIR        指定输出目录（默认: ./output）"
    echo "  --target-size SIZE      目标文件大小MB（默认: 2.0）"
    echo "  --max-splits NUM        最大拆分数量（默认: 4）"
    echo ""
    echo "示例:"
    echo "  ./run.sh document.pdf                    # 压缩单个文件"
    echo "  ./run.sh -s document.pdf                 # 压缩并允许拆分"
    echo "  ./run.sh -o ./processed ./pdf_folder     # 批量处理目录"
    echo "  ./run.sh -v -s --target-size 8 big.pdf  # 详细模式，8MB目标"
    echo ""
}

# 检查Python是否可用
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_colored $RED "错误: 未找到Python。请安装Python 3.7+。"
        exit 1
    fi
}

# 检查main.py是否存在
check_main_script() {
    if [ ! -f "main.py" ]; then
        print_colored $RED "错误: 未找到main.py文件。请确保在正确的目录中运行此脚本。"
        exit 1
    fi
}

# 解析命令行参数
parse_arguments() {
    OUTPUT_DIR="./output"
    ALLOW_SPLITTING=""
    VERBOSE=""
    TARGET_SIZE=""
    MAX_SPLITS=""
    INPUT_FILE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--check)
                check_python
                check_main_script
                print_colored $BLUE "检查依赖工具..."
                $PYTHON_CMD main.py --check-deps
                exit $?
                ;;
            -i|--install)
                print_colored $BLUE "运行依赖安装脚本..."
                if [ -f "install_dependencies.sh" ]; then
                    chmod +x install_dependencies.sh
                    ./install_dependencies.sh
                else
                    print_colored $RED "错误: 未找到install_dependencies.sh文件"
                    exit 1
                fi
                exit $?
                ;;
            -t|--test)
                check_python
                print_colored $BLUE "运行测试检查..."
                $PYTHON_CMD test_tool.py
                exit $?
                ;;
            -s|--split)
                ALLOW_SPLITTING="--allow-splitting"
                shift
                ;;
            -v|--verbose)
                VERBOSE="--verbose"
                shift
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --target-size)
                TARGET_SIZE="--target-size $2"
                shift 2
                ;;
            --max-splits)
                MAX_SPLITS="--max-splits $2"
                shift 2
                ;;
            -*)
                print_colored $RED "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                if [ -z "$INPUT_FILE" ]; then
                    INPUT_FILE="$1"
                else
                    print_colored $RED "错误: 只能指定一个输入文件或目录"
                    exit 1
                fi
                shift
                ;;
        esac
    done
}

# 验证输入文件
validate_input() {
    if [ -z "$INPUT_FILE" ]; then
        print_colored $RED "错误: 请指定输入PDF文件或目录"
        echo ""
        show_help
        exit 1
    fi
    
    if [ ! -e "$INPUT_FILE" ]; then
        print_colored $RED "错误: 输入文件或目录不存在: $INPUT_FILE"
        exit 1
    fi
}

# 主执行函数
main() {
    check_python
    check_main_script
    parse_arguments "$@"
    
    if [ -z "$INPUT_FILE" ]; then
        show_help
        exit 0
    fi
    
    validate_input
    
    # 构建命令
    CMD="$PYTHON_CMD main.py --input \"$INPUT_FILE\" --output-dir \"$OUTPUT_DIR\""
    
    if [ -n "$ALLOW_SPLITTING" ]; then
        CMD="$CMD $ALLOW_SPLITTING"
    fi
    
    if [ -n "$VERBOSE" ]; then
        CMD="$CMD $VERBOSE"
    fi
    
    if [ -n "$TARGET_SIZE" ]; then
        CMD="$CMD $TARGET_SIZE"
    fi
    
    if [ -n "$MAX_SPLITS" ]; then
        CMD="$CMD $MAX_SPLITS"
    fi
    
    # 显示即将执行的命令
    print_colored $BLUE "执行命令:"
    print_colored $YELLOW "$CMD"
    echo ""
    
    # 创建输出目录
    mkdir -p "$OUTPUT_DIR"
    
    # 执行命令
    eval $CMD
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_colored $GREEN "✅ 处理完成！"
        print_colored $GREEN "输出文件位置: $OUTPUT_DIR"
    else
        print_colored $RED "❌ 处理失败（退出码: $exit_code）"
        print_colored $YELLOW "请检查错误信息或查看日志文件: logs/process.log"
    fi
    
    exit $exit_code
}

# 设置脚本为可执行
chmod +x "$0"

# 运行主函数
main "$@"