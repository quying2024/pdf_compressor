"""
hOCR 文件分析和优化工具

功能：
1. 分析 hOCR 文件结构
2. 实验性删除不同部分
3. 测量文件大小变化
4. 评估对 PDF 生成的影响
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple
import logging

class HocrAnalyzer:
    """hOCR 文件分析器"""
    
    def __init__(self, hocr_file: Path):
        self.hocr_file = Path(hocr_file)
        self.original_size = self.hocr_file.stat().st_size
        
        # 读取文件内容
        with open(self.hocr_file, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        print(f"📄 原始 hOCR 文件: {self.hocr_file.name}")
        print(f"📊 原始大小: {self.original_size / 1024 / 1024:.2f} MB")
        print(f"📏 原始行数: {len(self.content.splitlines())}")
    
    def analyze_structure(self) -> Dict:
        """分析 hOCR 文件的基本结构"""
        print("\n" + "="*70)
        print("🔍 hOCR 文件结构分析")
        print("="*70)
        
        analysis = {
            'total_size': self.original_size,
            'total_lines': len(self.content.splitlines()),
            'elements': {}
        }
        
        # 分析各种 HTML 标签
        tags = [
            ('ocr_page', '页面容器'),
            ('ocr_carea', '内容区域'),
            ('ocr_par', '段落'),
            ('ocr_line', '文本行'),
            ('ocrx_word', '单词/词组'),
        ]
        
        for tag_class, description in tags:
            pattern = rf"class=['\"].*?{tag_class}.*?['\"]"
            matches = re.findall(pattern, self.content)
            analysis['elements'][tag_class] = {
                'count': len(matches),
                'description': description
            }
            print(f"  📌 {tag_class:15} ({description:10}): {len(matches):6} 个")
        
        # 分析文本内容大小
        text_pattern = r'<span[^>]*?ocrx_word[^>]*?>([^<]+)</span>'
        text_matches = re.findall(text_pattern, self.content)
        total_text_size = sum(len(text.encode('utf-8')) for text in text_matches)
        
        print(f"\n  💬 文本内容:")
        print(f"     - 单词数量: {len(text_matches)}")
        print(f"     - 文本大小: {total_text_size / 1024:.2f} KB")
        print(f"     - 占比: {total_text_size / self.original_size * 100:.1f}%")
        
        analysis['text_content'] = {
            'word_count': len(text_matches),
            'text_size': total_text_size,
            'percentage': total_text_size / self.original_size * 100
        }
        
        # 分析 bbox 信息
        bbox_pattern = r"bbox \d+ \d+ \d+ \d+"
        bbox_matches = re.findall(bbox_pattern, self.content)
        bbox_size = sum(len(bbox.encode('utf-8')) for bbox in bbox_matches)
        
        print(f"\n  📍 坐标信息 (bbox):")
        print(f"     - bbox 数量: {len(bbox_matches)}")
        print(f"     - bbox 大小: {bbox_size / 1024:.2f} KB")
        print(f"     - 占比: {bbox_size / self.original_size * 100:.1f}%")
        
        analysis['bbox_info'] = {
            'count': len(bbox_matches),
            'size': bbox_size,
            'percentage': bbox_size / self.original_size * 100
        }
        
        return analysis
    
    def create_empty_hocr(self, output_file: Path) -> Tuple[Path, int]:
        """
        创建空 hOCR - 删除所有文本内容，保留结构
        
        策略：删除 <span class="ocrx_word"> 标签内的文本内容
        """
        print("\n" + "="*70)
        print("🧪 实验 1: 创建空 hOCR（删除文本内容）")
        print("="*70)
        
        # 删除 ocrx_word 标签内的文本内容
        empty_content = re.sub(
            r'(<span[^>]*?ocrx_word[^>]*?>)([^<]+)(</span>)',
            r'\1\3',  # 保留开始和结束标签，删除文本
            self.content
        )
        
        output_file.write_text(empty_content, encoding='utf-8')
        new_size = output_file.stat().st_size
        reduction = self.original_size - new_size
        percentage = (reduction / self.original_size) * 100
        
        print(f"  ✅ 已创建: {output_file.name}")
        print(f"  📊 新大小: {new_size / 1024 / 1024:.2f} MB")
        print(f"  📉 减少: {reduction / 1024 / 1024:.2f} MB ({percentage:.1f}%)")
        
        return output_file, new_size
    
    def create_minimal_hocr(self, output_file: Path) -> Tuple[Path, int]:
        """
        创建最小 hOCR - 只保留页面结构和 bbox
        
        策略：删除所有文本内容和不必要的属性
        """
        print("\n" + "="*70)
        print("🧪 实验 2: 创建最小 hOCR（只保留必要结构）")
        print("="*70)
        
        minimal_content = self.content
        
        # 步骤1: 删除文本内容
        minimal_content = re.sub(
            r'(<span[^>]*?ocrx_word[^>]*?>)([^<]+)(</span>)',
            r'\1\3',
            minimal_content
        )
        
        # 步骤2: 简化 title 属性（只保留 bbox）
        def simplify_title(match):
            full_title = match.group(1)
            bbox_match = re.search(r'bbox \d+ \d+ \d+ \d+', full_title)
            if bbox_match:
                return f'title="{bbox_match.group()}"'
            return match.group(0)
        
        minimal_content = re.sub(
            r'title="([^"]*)"',
            simplify_title,
            minimal_content
        )
        
        output_file.write_text(minimal_content, encoding='utf-8')
        new_size = output_file.stat().st_size
        reduction = self.original_size - new_size
        percentage = (reduction / self.original_size) * 100
        
        print(f"  ✅ 已创建: {output_file.name}")
        print(f"  📊 新大小: {new_size / 1024 / 1024:.2f} MB")
        print(f"  📉 减少: {reduction / 1024 / 1024:.2f} MB ({percentage:.1f}%)")
        
        return output_file, new_size
    
    def create_no_words_hocr(self, output_file: Path) -> Tuple[Path, int]:
        """
        创建无单词 hOCR - 删除所有 ocrx_word 标签
        
        策略：完全移除 <span class="ocrx_word"> 标签
        """
        print("\n" + "="*70)
        print("🧪 实验 3: 创建无单词 hOCR（删除 ocrx_word 标签）")
        print("="*70)
        
        # 删除整个 ocrx_word span 标签
        no_words_content = re.sub(
            r'<span[^>]*?ocrx_word[^>]*?>.*?</span>\s*',
            '',
            self.content
        )
        
        output_file.write_text(no_words_content, encoding='utf-8')
        new_size = output_file.stat().st_size
        reduction = self.original_size - new_size
        percentage = (reduction / self.original_size) * 100
        
        print(f"  ✅已创建: {output_file.name}")
        print(f"  📊 新大小: {new_size / 1024 / 1024:.2f} MB")
        print(f"  📉 减少: {reduction / 1024 / 1024:.2f} MB ({percentage:.1f}%)")
        
        return output_file, new_size
    
    def create_no_lines_hocr(self, output_file: Path) -> Tuple[Path, int]:
        """
        创建无文本行 hOCR - 删除所有 ocr_line 标签
        
        策略：移除 <span class="ocr_line"> 标签及其内容
        """
        print("\n" + "="*70)
        print("🧪 实验 4: 创建无文本行 hOCR（删除 ocr_line 标签）")
        print("="*70)
        
        # 删除整个 ocr_line span 标签
        no_lines_content = re.sub(
            r'<span[^>]*?ocr_line[^>]*?>.*?</span>\s*',
            '',
            self.content,
            flags=re.DOTALL
        )
        
        output_file.write_text(no_lines_content, encoding='utf-8')
        new_size = output_file.stat().st_size
        reduction = self.original_size - new_size
        percentage = (reduction / self.original_size) * 100
        
        print(f"  ✅ 已创建: {output_file.name}")
        print(f"  📊 新大小: {new_size / 1024 / 1024:.2f} MB")
        print(f"  📉 减少: {reduction / 1024 / 1024:.2f} MB ({percentage:.1f}%)")
        
        return output_file, new_size
    
    def show_sample(self, lines: int = 50):
        """显示 hOCR 文件的样本内容"""
        print("\n" + "="*70)
        print(f"📝 hOCR 文件样本（前 {lines} 行）")
        print("="*70)
        
        content_lines = self.content.splitlines()
        for i, line in enumerate(content_lines[:lines], 1):
            print(f"{i:3}: {line}")
        
        if len(content_lines) > lines:
            print(f"\n... (省略 {len(content_lines) - lines} 行)")


def run_hocr_experiments(hocr_file: Path):
    """运行完整的 hOCR 优化实验"""
    
    print("\n" + "="*70)
    print("🔬 hOCR 文件优化研究实验")
    print("="*70)
    print(f"📅 日期: 2025-10-19")
    print(f"🎯 目标: 研究 hOCR 文件优化以减小最终 PDF 大小")
    print("="*70)
    
    # 创建输出目录
    output_dir = hocr_file.parent / "hocr_experiments"
    output_dir.mkdir(exist_ok=True)
    
    # 初始化分析器
    analyzer = HocrAnalyzer(hocr_file)
    
    # 显示样本
    analyzer.show_sample(30)
    
    # 分析结构
    analysis = analyzer.analyze_structure()
    
    # 运行各种优化实验
    experiments = []
    
    # 实验 1: 空 hOCR（删除文本）
    exp1_file = output_dir / "combined_empty.hocr"
    exp1_path, exp1_size = analyzer.create_empty_hocr(exp1_file)
    experiments.append(('空文本', exp1_size))
    
    # 实验 2: 最小 hOCR（只保留 bbox）
    exp2_file = output_dir / "combined_minimal.hocr"
    exp2_path, exp2_size = analyzer.create_minimal_hocr(exp2_file)
    experiments.append(('最小化', exp2_size))
    
    # 实验 3: 无单词 hOCR
    exp3_file = output_dir / "combined_no_words.hocr"
    exp3_path, exp3_size = analyzer.create_no_words_hocr(exp3_file)
    experiments.append(('无单词', exp3_size))
    
    # 实验 4: 无文本行 hOCR
    exp4_file = output_dir / "combined_no_lines.hocr"
    exp4_path, exp4_size = analyzer.create_no_lines_hocr(exp4_file)
    experiments.append(('无文本行', exp4_size))
    
    # 总结对比
    print("\n" + "="*70)
    print("📊 实验结果对比")
    print("="*70)
    print(f"\n{'类型':<12} {'大小 (MB)':<12} {'减少 (MB)':<12} {'减少率':<10}")
    print("-" * 70)
    
    original_mb = analyzer.original_size / 1024 / 1024
    print(f"{'原始':<12} {original_mb:<12.2f} {'-':<12} {'-':<10}")
    
    for name, size in experiments:
        size_mb = size / 1024 / 1024
        reduction_mb = (analyzer.original_size - size) / 1024 / 1024
        reduction_pct = (analyzer.original_size - size) / analyzer.original_size * 100
        print(f"{name:<12} {size_mb:<12.2f} {reduction_mb:<12.2f} {reduction_pct:<10.1f}%")
    
    print("\n" + "="*70)
    print("✅ 实验完成！所有变体已保存到:", output_dir)
    print("="*70)
    
    return output_dir, analysis


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python hocr_analyzer.py <hocr_file>")
        print("\n示例: python hocr_analyzer.py /tmp/tmpxxx/combined.hocr")
        sys.exit(1)
    
    hocr_file = Path(sys.argv[1])
    
    if not hocr_file.exists():
        print(f"❌ 错误: 文件不存在: {hocr_file}")
        sys.exit(1)
    
    run_hocr_experiments(hocr_file)
