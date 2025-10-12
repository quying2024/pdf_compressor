@echo off
REM pdf_compress.bat
REM Windows用户的PDF压缩工具快捷脚本

setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    PDF 压缩与拆分工具                         ║
echo ║                     Windows WSL 接口                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 检查WSL是否可用
wsl --status >nul 2>&1
if errorlevel 1 (
    echo 错误: WSL未安装或未正确配置
    echo 请先安装WSL和Ubuntu，参考文档: docs\WINDOWS_GUIDE.md
    pause
    exit /b 1
)

REM 检查项目是否在WSL中存在
wsl -e test -d ~/pdf_compressor
if errorlevel 1 (
    echo 正在复制项目到WSL文件系统...
    wsl -e cp -r /mnt/c/Users/%USERNAME%/Projects/pdf_compressor ~/pdf_compressor
    echo 项目已复制到WSL
)

REM 检查依赖工具
echo 检查依赖工具...
wsl -e bash -c "cd ~/pdf_compressor && python3 main.py --check-deps" >nul 2>&1
if errorlevel 1 (
    echo.
    echo 依赖工具未安装，正在安装...
    echo 这可能需要几分钟时间，请耐心等待...
    wsl -e bash -c "cd ~/pdf_compressor && chmod +x install_dependencies.sh && ./install_dependencies.sh"
    
    REM 再次检查
    wsl -e bash -c "cd ~/pdf_compressor && python3 main.py --check-deps" >nul 2>&1
    if errorlevel 1 (
        echo 安装失败，请手动在WSL中运行安装脚本
        pause
        exit /b 1
    )
)

echo 工具已就绪！

REM 如果没有参数，显示帮助
if "%~1"=="" (
    echo.
    echo 用法: pdf_compress.bat [PDF文件路径] [选项]
    echo.
    echo 示例:
    echo   pdf_compress.bat C:\Documents\test.pdf
    echo   pdf_compress.bat C:\Documents\test.pdf --allow-splitting
    echo   pdf_compress.bat C:\Documents\PDFs --target-size 8.0 --allow-splitting
    echo.
    echo 可用选项:
    echo   --allow-splitting      允许拆分文件
    echo   --target-size SIZE     目标大小(MB)
    echo   --max-splits NUM       最大拆分数量
    echo   --verbose              详细输出
    echo.
    pause
    exit /b 0
)

REM 转换第一个参数为WSL路径
set "input_path=%~1"
set "input_path=!input_path:\=/!"
set "input_path=!input_path::=!"
set "wsl_input=/mnt/!input_path!"

REM 设置输出目录
set "output_dir=~/pdf_output"

REM 构建命令
set "cmd=cd ~/pdf_compressor && python3 main.py --input '!wsl_input!' --output-dir !output_dir!"

REM 添加其他参数
shift
:parse_args
if "%~1"=="" goto run_command
set "cmd=!cmd! %1"
shift
goto parse_args

:run_command
REM 添加默认的拆分选项（如果用户没有指定）
echo !cmd! | findstr /C:"--allow-splitting" >nul
if errorlevel 1 (
    set "cmd=!cmd! --allow-splitting"
)

echo.
echo 正在处理PDF文件...
echo 输入: %~1
echo 输出: 将保存在WSL的 ~/pdf_output 目录
echo.

REM 执行命令
wsl -e bash -c "!cmd!"

if errorlevel 1 (
    echo.
    echo 处理失败，请查看错误信息
    pause
    exit /b 1
)

echo.
echo 处理完成！
echo.

REM 询问是否要复制输出文件到Windows
set /p copy_choice="是否要将输出文件复制到Windows？(y/n): "
if /i "%copy_choice%"=="y" (
    set "win_output=%USERPROFILE%\Documents\PDF压缩输出"
    echo 正在复制到: !win_output!
    
    REM 创建Windows输出目录
    if not exist "!win_output!" mkdir "!win_output!"
    
    REM 复制文件
    wsl -e bash -c "cp ~/pdf_output/* /mnt/c/Users/%USERNAME%/Documents/PDF压缩输出/ 2>/dev/null || true"
    
    echo 文件已复制到: !win_output!
    explorer "!win_output!"
)

echo.
echo 按任意键退出...
pause >nul