# 故障排除指南

## 安装相关问题

### 1. pipx相关问题

#### 问题：找不到recode_pdf命令
```bash
bash: recode_pdf: command not found
```

**解决方案：**
```bash
# 方法1：确保pipx路径在PATH中
pipx ensurepath
source ~/.bashrc

# 方法2：手动添加到PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 方法3：重新安装
pipx uninstall archive-pdf-tools
pipx install archive-pdf-tools
```

#### 问题：pipx未安装
```bash
bash: pipx: command not found
```

**解决方案：**
```bash
# Ubuntu 22.04+
sudo apt install pipx

# Ubuntu 20.04或更早版本
sudo apt install python3-pip
pip3 install --user pipx
export PATH="$HOME/.local/bin:$PATH"
```

#### 问题：pipx安装失败
```bash
pipx install archive-pdf-tools
# 出现权限或依赖错误
```

**备选方案：**
```bash
# 使用pip用户安装
pip3 install --user archive-pdf-tools

# 使用虚拟环境
python3 -m venv ~/pdf_env
source ~/pdf_env/bin/activate
pip install archive-pdf-tools
```

### 2. 系统工具问题

#### 问题：tesseract语言包问题
```bash
Error: Tesseract couldn't load any languages!
```

**解决方案：**
```bash
# 重新安装语言包
sudo apt install --reinstall tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# 检查语言包
tesseract --list-langs

# 如果仍有问题，安装所有语言包
sudo apt install tesseract-ocr-all
```

#### 问题：poppler-utils版本问题
```bash
pdftoppm: error while loading shared libraries
```

**解决方案：**
```bash
# 更新系统和重新安装
sudo apt update && sudo apt upgrade
sudo apt install --reinstall poppler-utils

# 检查版本
pdftoppm -v
```

### 3. 权限问题

#### 问题：无法写入输出目录
```bash
Permission denied: '/path/to/output'
```

**解决方案：**
```bash
# 检查目录权限
ls -la /path/to/output

# 修改权限
chmod 755 /path/to/output

# 或使用用户主目录
python3 main.py --input test.pdf --output-dir ~/output --allow-splitting
```

#### 问题：临时文件权限问题
```bash
PermissionError: [Errno 13] Permission denied: '/tmp/...'
```

**解决方案：**
```bash
# 清理临时文件
sudo rm -rf /tmp/pdf_compressor_*

# 检查/tmp权限
ls -la /tmp | grep pdf_compressor

# 设置环境变量使用其他临时目录
export TMPDIR=~/tmp
mkdir -p ~/tmp
```

## 运行时问题

### 1. 内存不足

#### 症状：
- 进程被杀死
- 系统变慢
- "Killed"消息

**解决方案：**
```bash
# 检查内存使用
free -h
htop

# 处理小文件或减少并发
python3 main.py --input small_file.pdf --output-dir ./output

# 增加swap空间（如果可能）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 2. 磁盘空间不足

#### 症状：
- "No space left on device"
- 处理中断

**解决方案：**
```bash
# 检查磁盘空间
df -h

# 清理旧的日志和临时文件
rm -rf logs/*.log.old
rm -rf /tmp/pdf_compressor_*

# 使用其他磁盘位置
python3 main.py --input test.pdf --output-dir /mnt/d/output
```

### 3. 处理超时

#### 症状：
- 长时间无响应
- 进程挂起

**解决方案：**
```bash
# 使用详细模式监控进度
python3 main.py --input test.pdf --output-dir ./output --verbose

# 减小文件或预先拆分
# 检查文件是否损坏
pdfinfo test.pdf
```

## WSL特定问题

### 1. 文件路径问题

#### 问题：找不到Windows文件
```bash
No such file or directory: '/mnt/c/...'
```

**解决方案：**
```bash
# 检查WSL挂载
ls /mnt/c/

# 确保WSL2配置正确
wsl --list --verbose

# 使用正确的路径格式
python3 main.py --input "/mnt/c/Users/username/Documents/file.pdf"
```

### 2. 性能问题

#### 问题：跨文件系统访问慢

**解决方案：**
```bash
# 复制文件到WSL文件系统
cp /mnt/c/path/to/file.pdf ~/input/
python3 main.py --input ~/input/file.pdf --output-dir ~/output

# 处理完成后复制回Windows
cp ~/output/* /mnt/c/Users/username/Documents/
```

### 3. 编码问题

#### 问题：中文文件名乱码

**解决方案：**
```bash
# 设置正确的locale
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 永久设置
echo 'export LANG=zh_CN.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=zh_CN.UTF-8' >> ~/.bashrc
```

## 调试技巧

### 1. 启用详细日志
```bash
python3 main.py --input test.pdf --output-dir ./output --verbose
```

### 2. 检查中间文件
```bash
# 修改代码中的KEEP_INTERMEDIATE_FILES为True
# 在config.py中设置：
KEEP_INTERMEDIATE_FILES = True
```

### 3. 逐步调试
```bash
# 先测试单个组件
pdftoppm -tiff -r 300 test.pdf page
tesseract page-01.tif output -l chi_sim hocr
```

### 4. 使用测试工具
```bash
# 运行完整的工具检查
python3 test_tool.py

# 检查版本信息
python3 test_tool.py --versions

# 创建测试环境
python3 test_tool.py --create-test
```

## 获取帮助

### 1. 查看日志
```bash
# 查看最新日志
tail -f logs/process.log

# 搜索错误信息
grep ERROR logs/process.log
```

### 2. 收集系统信息
```bash
# 系统版本
lsb_release -a

# 工具版本
python3 test_tool.py --versions

# 环境变量
echo $PATH
echo $TMPDIR
```

### 3. 重置环境
```bash
# 完全重新安装
pipx uninstall archive-pdf-tools
sudo apt remove --purge tesseract-ocr poppler-utils qpdf
sudo apt autoremove

# 重新运行安装脚本
./install_dependencies.sh
```