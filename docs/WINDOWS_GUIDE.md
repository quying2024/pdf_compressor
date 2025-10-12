# Windows 用户使用指南

## WSL环境部署说明

由于此PDF压缩工具依赖的命令行工具（`pdftoppm`, `tesseract`, `recode_pdf`, `qpdf`）主要在Linux环境中可用，Windows用户需要通过WSL（Windows Subsystem for Linux）来使用本工具。

## 1. 安装WSL

### 方法一：使用Windows 11/10的内置命令
```powershell
# 在管理员PowerShell中运行
wsl --install

# 或安装指定的Ubuntu版本
wsl --install -d Ubuntu-24.04
```

### 方法二：通过Microsoft Store
1. 打开Microsoft Store
2. 搜索"Ubuntu 24.04 LTS"
3. 点击安装

## 2. 配置WSL

### 启动WSL
```powershell
# 启动默认的Linux发行版
wsl

# 或启动指定版本
wsl -d Ubuntu-24.04
```

### 更新系统
```bash
sudo apt update && sudo apt upgrade -y
```

## 3. 安装项目依赖

### 在WSL中安装Python和pip
```bash
sudo apt install python3 python3-pip
```

### 复制项目到WSL
```bash
# 方法1：直接访问Windows文件系统
cd /mnt/c/Users/quying/Projects/pdf_compressor

# 方法2：复制到WSL文件系统（推荐）
cp -r /mnt/c/Users/quying/Projects/pdf_compressor ~/pdf_compressor
cd ~/pdf_compressor
```

### 运行安装脚本
```bash
# 给脚本执行权限
chmod +x install_dependencies.sh

# 运行安装脚本
./install_dependencies.sh
```

## 4. 验证安装

```bash
# 检查依赖
python3 main.py --check-deps

# 运行测试工具
python3 test_tool.py
```

## 5. 使用示例

### 处理Windows文件系统中的PDF
```bash
# 处理C盘中的PDF文件
python3 main.py --input /mnt/c/Users/quying/Documents/test.pdf --output-dir ./output --allow-splitting

# 批量处理Windows目录
python3 main.py --input /mnt/c/Users/quying/Documents/PDFs --output-dir ./processed --allow-splitting
```

### 使用快速脚本
```bash
# 给快速脚本执行权限
chmod +x run.sh

# 使用快速脚本
./run.sh -s /mnt/c/Users/quying/Documents/test.pdf
./run.sh -s -o ./processed /mnt/c/Users/quying/Documents/PDFs
```

## 6. 文件路径说明

### Windows和WSL文件系统对应关系
- Windows `C:\` → WSL `/mnt/c/`
- Windows `D:\` → WSL `/mnt/d/`
- WSL主目录 `~` → Windows `\\wsl$\Ubuntu-24.04\home\username`

### 示例路径转换
```bash
# Windows路径: C:\Users\quying\Projects\pdf_compressor\test.pdf
# WSL路径:     /mnt/c/Users/quying/Projects/pdf_compressor/test.pdf

# Windows路径: D:\Documents\PDFs
# WSL路径:     /mnt/d/Documents/PDFs
```

## 7. 性能优化建议

### 文件存储位置
```bash
# 推荐：将项目复制到WSL文件系统以获得更好性能
cp -r /mnt/c/Users/quying/Projects/pdf_compressor ~/pdf_compressor

# 处理大文件时，建议输出也在WSL文件系统
python3 main.py --input /mnt/c/path/to/large.pdf --output-dir ~/output --allow-splitting
```

### 内存和存储
- 确保WSL有足够的内存分配（在`.wslconfig`中配置）
- 为临时文件预留足够的磁盘空间

## 8. 故障排除

### WSL相关问题
```powershell
# 重启WSL
wsl --shutdown
wsl

# 查看WSL状态
wsl --list --verbose

# 设置默认版本
wsl --set-default Ubuntu-24.04
```

### 权限问题
```bash
# 确保文件有正确权限
chmod +x *.sh
chmod +x *.py
```

### 路径问题
```bash
# 使用绝对路径避免路径错误
python3 main.py --input "$(pwd)/test.pdf" --output-dir "$(pwd)/output"
```

## 9. WSL配置文件

### 创建 `.wslconfig` 文件
在Windows用户目录下创建 `C:\Users\quying\.wslconfig`：

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

### 应用配置
```powershell
# 重启WSL以应用新配置
wsl --shutdown
wsl
```

## 10. 完整工作流程示例

```bash
# 1. 进入WSL
wsl

# 2. 切换到项目目录
cd ~/pdf_compressor

# 3. 检查依赖（应该全部通过）
python3 main.py --check-deps

# 4. 处理Windows中的PDF文件
python3 main.py --input /mnt/c/Users/quying/Documents/申报材料.pdf \
                --output-dir ~/output \
                --allow-splitting \
                --verbose

# 5. 查看结果
ls -la ~/output/

# 6. 复制结果到Windows
cp ~/output/* /mnt/c/Users/quying/Documents/压缩后/
```

## 11. 自动化脚本

创建一个Windows批处理文件来简化操作：

```batch
@echo off
echo 启动PDF压缩工具...
wsl -d Ubuntu-24.04 -e bash -c "cd ~/pdf_compressor && python3 main.py %*"
```

保存为 `pdf_compress.bat`，然后可以在Windows中这样使用：
```cmd
pdf_compress.bat --input C:\path\to\file.pdf --output-dir C:\path\to\output --allow-splitting
```

这样就可以在Windows环境中无缝使用WSL中的PDF压缩工具了！