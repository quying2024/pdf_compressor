# 快速开始指南

## 1. 系统要求

- Ubuntu 20.04+ 或 WSL2 (Ubuntu 24.04 推荐)
- Python 3.7+
- 至少 2GB 可用磁盘空间（用于临时文件）
- 4GB+ RAM（处理大文件时推荐）

## 2. 快速安装

### 方法一：使用安装脚本（推荐）

```bash
# 克隆或下载项目到本地
cd pdf_compressor

# 运行安装脚本
chmod +x install_dependencies.sh
./install_dependencies.sh

# 或者使用快速启动脚本
chmod +x run.sh
./run.sh --install
```

### 方法二：手动安装

```bash
# 更新系统包
sudo apt update

# 安装必要工具
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-chi-sim qpdf pipx

# 安装Python包（推荐使用pipx）
pipx install archive-pdf-tools

# 确保PATH正确配置
pipx ensurepath
source ~/.bashrc
```

## 3. 验证安装

```bash
# 使用Python脚本检查
python3 main.py --check-deps

# 或使用快速启动脚本
./run.sh --check

# 或使用测试工具
python3 test_tool.py
```

## 4. 基本使用

### 压缩单个文件

```bash
# 基本压缩
python3 main.py --input document.pdf --output-dir ./output

# 允许拆分（推荐）
python3 main.py --input document.pdf --output-dir ./output --allow-splitting

# 使用快速脚本
./run.sh -s document.pdf
```

### 批量处理目录

```bash
# 处理目录中所有PDF
python3 main.py --input ./pdf_folder --output-dir ./processed --allow-splitting

# 使用快速脚本
./run.sh -s -o ./processed ./pdf_folder
```

### 自定义参数

```bash
# 目标8MB，最多拆分6部分
python3 main.py --input large.pdf --output-dir ./output \
    --target-size 8.0 --max-splits 6 --allow-splitting

# 详细模式
python3 main.py --input document.pdf --output-dir ./output \
    --verbose --allow-splitting

# 使用快速脚本
./run.sh -v -s --target-size 8 --max-splits 6 large.pdf
```

## 5. 常见使用场景

### 场景1：职称申报文件处理

```bash
# 将所有申报材料压缩到2MB以下
./run.sh -s -o ./申报材料_压缩版 ./申报材料原始文件/
```

### 场景2：文档归档

```bash
# 压缩存档文件，允许稍大一些
./run.sh -s --target-size 5.0 -o ./归档文件 ./原始文档/
```

### 场景3：单个大文件处理

```bash
# 处理超大文件，允许拆分
./run.sh -v -s --max-splits 8 巨大文档.pdf
```

## 6. 输出文件说明

### 成功压缩的文件
- `原文件名_compressed.pdf` - 压缩后的单个文件

### 拆分的文件
- `原文件名_part1.pdf` - 第一部分
- `原文件名_part2.pdf` - 第二部分
- ...

### 报告文件
- `processing_report.txt` - 批量处理汇总报告
- `logs/process.log` - 详细处理日志

## 7. 性能优化建议

### 处理大批量文件
```bash
# 为大批量任务分配更多时间
# 可以先处理几个文件测试效果
./run.sh -v -s ./test_files/
```

### 处理超大文件
```bash
# 对于100MB+的文件，建议：
# 1. 使用详细模式监控进度
# 2. 允许较多拆分数量
# 3. 确保足够的磁盘空间
./run.sh -v -s --max-splits 10 超大文档.pdf
```

## 8. 故障排除

### 工具未找到
```bash
# 重新检查依赖
./run.sh --check

# 重新安装
./run.sh --install
```

### 处理失败
```bash
# 查看详细日志
cat logs/process.log

# 使用详细模式重试
./run.sh -v -s 问题文件.pdf
```

### 内存不足
```bash
# 单独处理文件，避免批量
./run.sh -s 单个文件.pdf

# 或者降低初始质量设置（需修改代码）
```

## 9. 高级技巧

### 自定义配置
```bash
# 复制配置文件模板
cp config.example.py config.py

# 编辑配置文件
nano config.py

# 重新运行程序将使用新配置
```

### 查看工具版本
```bash
python3 test_tool.py --versions
```

### 创建测试环境
```bash
python3 test_tool.py --create-test
```

## 10. 技术支持

- 查看 `README.md` 获取详细文档
- 检查 `logs/process.log` 了解处理详情
- 运行 `python3 main.py --help` 查看所有参数
- 使用 `./run.sh --help` 查看快速脚本选项