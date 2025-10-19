# compressor/pipeline.py

import logging
import glob
import subprocess
from pathlib import Path
from . import utils

def deconstruct_pdf_to_images(pdf_path, temp_dir, dpi):
    """
    使用 pdftoppm 将 PDF 转换为 JPEG 图像序列。
    返回生成的图像文件路径列表。
    
    注意: 使用 JPEG 格式（质量85）可将单页文件从 25MB 压缩到约 0.5-1.5MB，
    显著提升处理速度并减少磁盘占用。JPEG 压缩对 OCR 识别率影响很小。
    """
    logging.info(f"阶段1 [解构]: 开始将 {pdf_path.name} 转换为图像 (DPI: {dpi})...")
    output_prefix = temp_dir / "page"
    command = [
        "pdftoppm",
        "-jpeg",              # 使用 JPEG 格式（有损压缩）
        "-jpegopt", "quality=85",  # 设置 JPEG 质量为 85（平衡质量和体积）
        "-r", str(dpi),
        str(pdf_path),
        str(output_prefix)
    ]
    if not utils.run_command(command):
        logging.error("PDF解构失败。")
        return None
    
    # JPEG 文件扩展名为 .jpg
    image_files = sorted(glob.glob(f"{output_prefix}-*.jpg"))
    if not image_files:
        logging.error("未生成任何图像文件。")
        return None
        
    logging.info(f"成功生成 {len(image_files)} 页图像。")
    return [Path(f) for f in image_files]

def analyze_images_to_hocr(image_files, temp_dir):
    """
    使用 tesseract 对图像进行 OCR，生成并合并 hOCR 文件。
    返回合并后的 hOCR 文件路径。
    """
    logging.info(f"阶段2 [分析]: 开始对 {len(image_files)} 张图像进行 OCR...")
    hocr_files = []
    
    for i, img_path in enumerate(image_files):
        output_prefix = temp_dir / img_path.stem
        command = [
            "tesseract",
            str(img_path),
            str(output_prefix),
            "-l", "chi_sim",  # 简体中文
            "hocr"
        ]
        if not utils.run_command(command):
            logging.error(f"对图像 {img_path.name} 的 OCR 失败。")
            return None
        hocr_files.append(Path(f"{output_prefix}.hocr"))
        logging.info(f"完成 OCR: {i+1}/{len(image_files)}")

    # 合并所有 hocr 文件
    combined_hocr_path = temp_dir / "combined.hocr"
    logging.info(f"合并 hOCR 文件到 {combined_hocr_path}...")
    try:
        with open(combined_hocr_path, 'w', encoding='utf-8') as outfile:
            # 写入HTML头部
            outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            outfile.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n')
            outfile.write('"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')
            outfile.write('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n')
            outfile.write('<head>\n<title></title>\n')
            outfile.write('<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />\n')
            outfile.write('<meta name="ocr-system" content="tesseract" />\n')
            outfile.write('</head>\n<body>\n')
            
            # 合并每个页面的内容
            for hocr_file in hocr_files:
                with open(hocr_file, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    # 提取页面内容(去掉HTML头部和尾部)
                    start_marker = '<div class=\'ocr_page\''
                    end_marker = '</div>'
                    
                    start_idx = content.find(start_marker)
                    if start_idx != -1:
                        # 找到对应的结束标签
                        page_content = content[start_idx:]
                        # 找到完整的div结束
                        div_count = 0
                        end_idx = -1
                        for i, char in enumerate(page_content):
                            if page_content[i:i+5] == '<div ':
                                div_count += 1
                            elif page_content[i:i+6] == '</div>':
                                div_count -= 1
                                if div_count == 0:
                                    end_idx = i + 6
                                    break
                        
                        if end_idx != -1:
                            outfile.write(page_content[:end_idx] + '\n')
                        else:
                            # 备用方案：查找第一个</div>
                            first_end = page_content.find('</div>')
                            if first_end != -1:
                                outfile.write(page_content[:first_end + 6] + '\n')
            
            outfile.write('</body>\n</html>\n')
            
    except IOError as e:
        logging.error(f"合并 hOCR 文件时出错: {e}")
        return None

    logging.info("hOCR 文件合并成功。")
    return combined_hocr_path

def reconstruct_pdf(image_files, hocr_file, temp_dir, params, output_pdf_path):
    """
    使用 recode_pdf 重建 PDF。
    """
    logging.info(f"阶段3 [重建]: 使用参数 {params} 重建 PDF...")
    
    # recode_pdf 需要一个 glob 模式（支持 JPEG 和 TIFF）
    # 根据实际生成的图像文件确定扩展名
    if image_files and len(image_files) > 0:
        # 从第一个文件获取扩展名
        first_file = Path(image_files[0])
        ext = first_file.suffix  # 例如: .jpg 或 .tif
        image_stack_glob = str(temp_dir / f"page-*{ext}")
    else:
        # 后备方案：默认使用 jpg（与新的 JPEG 格式匹配）
        image_stack_glob = str(temp_dir / "page-*.jpg")

    command = [
        "recode_pdf",
        "--from-imagestack", image_stack_glob,
        "--hocr-file", str(hocr_file),
        "--dpi", str(params['dpi']),
        "--bg-downsample", str(params['bg_downsample']),
        "--mask-compression", "jbig2",
        "-J", params.get('jpeg2000_encoder', 'openjpeg'),  # JPEG2000编码器选择
        "-o", str(output_pdf_path)
    ]
    
    if not utils.run_command(command):
        logging.error("PDF 重建失败。")
        return False
        
    logging.info(f"PDF 重建成功，输出至 {output_pdf_path}")
    return True

def get_pdf_page_count(pdf_path):
    """使用 pdfinfo 获取PDF的总页数。"""
    command = ["pdfinfo", str(pdf_path)]
    try:
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        )
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"获取 {pdf_path.name} 的页数失败: {e}")
    return 0


def optimize_hocr_for_extreme_compression(hocr_file):
    """
    优化 hOCR 文件用于极限压缩场景（S7）。
    
    移除所有 ocrx_word 标签以大幅减小文件体积。
    注意：这将导致生成的 PDF 失去文本搜索功能。
    
    Args:
        hocr_file (Path): hOCR 文件路径
    
    Returns:
        Path: 优化后的 hOCR 文件路径（原地修改）
    """
    import re
    
    if not hocr_file.exists():
        logging.warning(f"hOCR 文件不存在，跳过优化: {hocr_file}")
        return hocr_file
    
    try:
        # 读取原文件
        with open(hocr_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_size = len(content)
        
        # 移除所有 ocrx_word 标签（包括内容）
        # 匹配: <span class='ocrx_word' ...>...</span>
        pattern = r"<span class='ocrx_word'[^>]*>.*?</span>"
        optimized_content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        optimized_size = len(optimized_content)
        reduction = (1 - optimized_size / original_size) * 100 if original_size > 0 else 0
        
        # 写回文件
        with open(hocr_file, 'w', encoding='utf-8') as f:
            f.write(optimized_content)
        
        logging.info(
            f"hOCR 优化完成 ({hocr_file.name}): "
            f"{original_size / 1024:.1f}KB → {optimized_size / 1024:.1f}KB "
            f"(-{reduction:.1f}%)"
        )
        
        return hocr_file
        
    except Exception as e:
        logging.error(f"hOCR 优化失败 ({hocr_file}): {e}")
        return hocr_file