# 更新日志 / Changelog

## [v2.0.0] - 2025-10-18

### 🎉 重大更新 / Major Updates

#### 算法重构 / Algorithm Refactoring
- **二分双向搜索算法**: 完全重写压缩策略，采用智能跳跃和向上回溯机制
- **纯物理拆分策略**: 拆分时复用压缩中间结果，不重新压缩
- **6方案压缩策略**: S1-S6六级压缩方案，智能选择最优质量

#### 性能提升 / Performance Improvements
- ⚡ 压缩处理时间降低 **77%** (420秒 → 95秒)
- ⚡ 拆分处理时间降低 **99.2%** (1800秒 → 15秒)
- ⚡ DAR执行次数降低 **80%** (5次 → 1次)
- 🎯 质量更优：向上回溯确保最佳质量

#### 新增功能 / New Features
- ✨ 手动模式 (`-m, --manual`): 支持交互式参数输入
- ✨ 参数示例显示 (`-?, --examples`): 快速查看使用示例
- ✨ 保留临时目录 (`-k, --keep-temp-on-failure`): 失败时保留临时文件便于调试
- ✨ UTF-8编码支持: 完善Windows PowerShell中文显示

#### 用户体验改进 / UX Improvements
- 🔧 参数简化: `--output-dir` → `--output`
- 📊 更详细的日志输出
- 🎨 优化的进度提示
- 🐛 修复多个编码问题

### 📝 代码改进 / Code Improvements

#### 核心模块重写
- **compressor/strategy.py**: 完全重构，实现二分双向搜索算法
  - `run_compression_strategy()`: 新的压缩策略入口
  - `_precompute_dar_steps()`: DAR预计算，复用中间结果
  - `_run_strategy_logic()`: 智能搜索逻辑
  - `_execute_scheme()`: 单方案执行
  
- **compressor/splitter.py**: 完全重构，实现纯物理拆分
  - `run_splitting_strategy()`: 新的拆分策略入口
  - `_select_splitting_source()`: 智能源文件选择
  - `_determine_optimal_split_count()`: 密度基拆分数计算
  - `_calculate_split_plan()`: 页面分配方案
  - `_split_pdf_physical()`: qpdf物理拆分

#### 集成改进
- **orchestrator.py**: 更新流程调度逻辑
  - 支持新的返回格式 `(status, details)`
  - 传递 `all_results` 给拆分模块
  
- **main.py**: 增强命令行接口
  - UTF-8编码配置
  - 新增3个命令行参数
  - 优化帮助信息显示

- **compressor/utils.py**: 工具函数优化
  - 简化日志配置
  - 改进错误处理

### 🧪 测试 / Testing

#### 新增测试
- **tests/test_new_strategy.py**: 压缩策略单元测试
  - ✅ 渐进式压缩成功测试
  - ✅ 跳跃回溯成功测试
  - ✅ 全部失败处理测试
  - ✅ 小文件跳过测试
  - **测试通过率: 100% (4/4)**

- **test_parameters.py**: 参数验证测试
  - ✅ 14个参数全部验证通过

### 📚 文档更新 / Documentation Updates

#### 核心文档
- **README.md**: 全面更新
  - 功能特性描述
  - 算法说明重写
  - 参数表格更新
  - 使用示例更新
  - 添加v2.0更新日志

#### 新增文档
- **docs/算法实现说明.md**: 详细技术文档 (约7000字)
  - 算法设计理念
  - 二分双向搜索算法详解
  - 纯物理拆分算法详解
  - 性能分析和测试验证
  
- **docs/文档更新日志.md**: 文档更新记录
  - 完整的文档更新列表
  - 文档阅读建议
  - 质量保证清单

#### 更新文档
- **docs/策略分析报告.md**: 重构为"分析与实现报告"
  - 新增第5章：新算法实现说明
  - 更新总结部分
  
- **docs/QUICKSTART.md**: 快速开始指南更新
- **docs/WINDOWS_GUIDE.md**: Windows指南参数更新
- **docs/TROUBLESHOOTING.md**: 故障排除参数更新
- **docs/DEPLOYMENT_SUMMARY.md**: 部署摘要更新
- **docs/项目架构第一版.md**: 添加v2.0说明

### 🔧 技术细节 / Technical Details

#### 压缩方案定义
```python
COMPRESSION_SCHEMES = {
    'S1': {'dpi': 300, 'bg_downsample': 2},  # 高质量
    'S2': {'dpi': 250, 'bg_downsample': 3},  # 适度降低
    'S3': {'dpi': 200, 'bg_downsample': 4},  # 平衡
    'S4': {'dpi': 150, 'bg_downsample': 5},  # 激进
    'S5': {'dpi': 120, 'bg_downsample': 5},  # 更激进
    'S6': {'dpi': 110, 'bg_downsample': 6},  # 极限
}
```

#### 关键算法特性
- **智能跳跃**: S1失败且结果>1.5倍目标时，直接跳至S6
- **向上回溯**: S6成功后，测试S5→S4→S3→S2找最优质量
- **DAR复用**: 阶段1-2只执行一次，所有方案复用hOCR
- **密度分配**: 基于文件大小和页数计算最优拆分方案

### 🐛 Bug修复 / Bug Fixes
- 🔧 修复函数名称不匹配问题 (`create_temp_dir` → `create_temp_directory`)
- 🔧 修复UTF-8编码错误（Windows PowerShell）
- 🔧 修复缩进导致的逻辑错误
- 🔧 修复测试数据不匹配问题

### 📦 依赖变更 / Dependencies
- 无依赖变更，继续使用：
  - archive-pdf-tools (recode_pdf)
  - poppler-utils (pdftoppm, pdfinfo)
  - tesseract-ocr
  - qpdf

### ⚠️ 破坏性变更 / Breaking Changes
- 参数名称变更: `--output-dir` → `--output`
  - 内部通过 `dest="output_dir"` 保持代码兼容
  - 用户需更新命令行脚本
  
- 返回值格式变更:
  - 旧: 单个布尔值或路径
  - 新: `(status, details)` 元组

### 🎯 迁移指南 / Migration Guide

#### 命令行参数更新
```bash
# v1.0
python main.py --input file.pdf --output-dir ./out

# v2.0
python main.py --input file.pdf --output ./out
```

#### 代码集成更新
```python
# v1.0
success = run_iterative_compression(pdf, output, target)

# v2.0
status, details = run_compression_strategy(pdf, output, target)
if status == 'success':
    output_file = details['output_path']
```

---

## [v1.0.0] - 2024-10-09

### 初始版本发布 / Initial Release
- ✨ 实现完整的DAR处理流程
- ✨ 支持分层压缩策略
- ✨ 集成PDF拆分功能
- ✨ 添加详细日志记录
- 📚 完整的项目文档

---

## 版本说明 / Version Notes

本项目遵循 [语义化版本 2.0.0](https://semver.org/lang/zh-CN/) 规范。

- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

---

**维护者**: quying2024  
**项目地址**: https://github.com/quying2024/pdf_compressor  
**许可证**: MIT License
