#!/bin/bash

# ==============================================================================
# archive-pdf-tools 最终功能验证脚本 (verify.sh) - qpdf 版
# ------------------------------------------------------------------------------
# 功能: 验证 Grok, OpenJPEG, qpdf 均可正常工作。
# ==============================================================================

# --- 配置 ---
all_ok=true
test_dir=""
export PATH="$PATH:$HOME/.local/bin" # 确保 pipx 命令可用
# 修正 jbig2enc 的参数顺序，解决 WSL 管道语法问题
export RECODE_PDF_JBIG2ENC_ARGS="--output-file={output} {input}" 

# --- 辅助函数 (用于彩色输出) ---
print_info() { echo -e "\n\e[34m==> $1\e[0m"; }
print_success() { echo -e "  \e[32m✔ $1\e[0m"; }
print_error() { echo -e "  \e[31m✖ $1\e[0m"; }
print_step() { echo -e "  - $1"; }
# 集中处理验证失败，并保留文件
handle_failure() {
    print_error "💥 功能验证失败。请仔细检查上面的日志。"
    print_info "保留临时文件用于调试..."
    echo "  临时文件位于: $test_dir"
    cd ~ # 返回主目录
    exit 1
}

# --- 脚本开始 ---
echo "============================================================"
echo "开始 archive-pdf-tools 功能验证测试 (qpdf 双工具验证)..."
echo "============================================================"

# --- 步骤 1: 验证所有已安装的工具 ---
print_info "步骤 1/5: 验证所有已安装的关键工具命令..."

print_step "检查关键依赖命令..."
# Grok, OpenJPEG, qpdf, recode_pdf
tools=("pdftoppm" "tesseract" "jbig2" "grk_compress" "opj_compress" "qpdf" "recode_pdf")
for tool in "${tools[@]}"; do
    if command -v "$tool" &> /dev/null; then
        print_success "$tool 命令已找到 ($tool)。"
    else
        print_error "$tool 命令未找到！"
        all_ok=false
    fi
done

if [ "$all_ok" = false ]; then
    print_error "\n基础命令检查失败，无法继续进行工作流测试。"
    handle_failure
fi

# --- 步骤 2: 准备测试文件 (创建包含两页的 PDF) ---
print_info "步骤 2/5: 准备端到端工作流测试文件 (创建 2 页 PDF)..."
test_dir=$(mktemp -d)
cd "$test_dir"
print_step "在临时目录创建测试文件: $test_dir"

# 创建一个包含两页文本的PDF
echo -e "Page 1" > page1.txt
echo -e "\n\n\nPage 2" > page2.txt # 确保是单独一页
enscript -o temp.ps page1.txt page2.txt &> /dev/null
ps2pdf temp.ps test_2page.pdf &> /dev/null
rm -f temp.ps page1.txt page2.txt

if ! [ -s "test_2page.pdf" ]; then print_error "创建 2 页 PDF 失败！"; handle_failure; fi
print_success "成功创建 2 页测试 PDF (test_2page.pdf)。"

# 继续创建单页的 recode 输入文件
pdftoppm -png -r 300 test_2page.pdf test_page &> /dev/null
tesseract test_page-1.png test_hocr -l eng hocr &> /dev/null
print_success "成功创建 recode 所需的 PNG 和 hOCR 文件。"


# --- 步骤 3: 验证 Grok 压缩 ---
print_info "步骤 3/5: 验证 Grok (grk_compress) 压缩功能..."
RECODE_CMD_GROK="timeout 1m recode_pdf -v --from-imagestack 'test_page-1.png' --hocr-file 'test_hocr.hocr' --dpi 300 --mask-compression jbig2 -J grok -o 'compressed_grok.pdf'"

print_step "执行 Grok 压缩测试..."
eval $RECODE_CMD_GROK &> recode_grok_log.txt
if [[ ${PIPESTATUS[0]} -ne 0 ]] && [[ ${PIPESTATUS[0]} -ne 124 ]]; then # 确保检查的是 eval 命令的退出状态
    print_error "(Grok 测试) 压缩失败 (退出码: ${PIPESTATUS[0]})！"
    all_ok=false
elif ! [ -s "compressed_grok.pdf" ]; then
    print_error "(Grok 测试) 压缩超时或失败！"
    all_ok=false
else
    print_success "(Grok 测试) 成功创建压缩PDF (compressed_grok.pdf)。"
fi


# --- 步骤 4: 验证 OpenJPEG 压缩 ---
print_info "步骤 4/5: 验证 OpenJPEG (opj_compress) 压缩功能..."
RECODE_CMD_OPENJPEG="timeout 1m recode_pdf -v --from-imagestack 'test_page-1.png' --hocr-file 'test_hocr.hocr' --dpi 300 --mask-compression jbig2 -J openjpeg -o 'compressed_openjpeg.pdf'"

print_step "执行 OpenJPEG 压缩测试..."
eval $RECODE_CMD_OPENJPEG &> recode_openjpeg_log.txt
if [[ ${PIPESTATUS[0]} -ne 0 ]] && [[ ${PIPESTATUS[0]} -ne 124 ]]; then
    print_error "(OpenJPEG 测试) 压缩失败 (退出码: ${PIPESTATUS[0]})！"
    all_ok=false
elif ! [ -s "compressed_openjpeg.pdf" ]; then
    print_error "(OpenJPEG 测试) 压缩超时或失败！"
    all_ok=false
else
    print_success "(OpenJPEG 测试) 成功创建压缩PDF (compressed_openjpeg.pdf)。"
fi


# --- 步骤 5: 验证 qpdf 拆分功能 ---
print_info "步骤 5/5: 验证 qpdf PDF 拆分功能..."
print_step "正在使用 qpdf 拆分 test_2page.pdf..."

# 尝试将第二页拆分出来
qpdf --empty --pages test_2page.pdf 2 -- split_page2.pdf 2>/dev/null

if [ -s "split_page2.pdf" ]; then
    print_success "(qpdf 测试) 成功将 PDF 拆分为 split_page2.pdf。"
else
    print_error "(qpdf 测试) 拆分 PDF 失败！"
    all_ok=false
fi


# --- 最终总结与清理 ---
if [ "$all_ok" = true ]; then
    print_info "清理临时验证文件..."
    rm -rf "$test_dir"
    echo "============================================================"
    echo -e "\e[32m🎉 全部验证成功！所有工具均可正常工作。\e[0m"
    echo "============================================================"
    cd ~ # 返回主目录
else
    handle_failure
fi
