# compressor/utils.py

import logging
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

LOG_DIR = "logs"

def setup_logging():
    """配置日志记录器，同时输出到控制台和文件。"""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "process.log"

    # 防止重复添加处理器
    if logging.getLogger().hasHandlers():
        logging.getLogger().handlers.clear()

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 设置格式化器
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

def get_file_size_mb(file_path):
    """获取文件大小，单位为MB。"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except FileNotFoundError:
        logging.error(f"文件未找到: {file_path}")
        return 0

def run_command(command, cwd=None):
    """
    执行一个外部命令行命令。

    Args:
        command (list): 命令及其参数的列表。
        cwd (str, optional): 命令执行的工作目录。

    Returns:
        bool: 命令是否成功执行。
    """
    command_str = ' '.join(command)
    logging.info(f"执行命令: {command_str}")
    
    # 确保包含可能的pipx安装路径
    env = os.environ.copy()
    home = os.path.expanduser("~")
    local_bin = os.path.join(home, ".local", "bin")
    
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
        logging.debug(f"添加 {local_bin} 到 PATH")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            cwd=cwd,
            env=env  # 使用修改后的环境变量
        )
        if result.stdout:
            logging.debug(f"命令输出:\n{result.stdout}")
        if result.stderr:
            # 区分正常信息和真正的错误
            stderr_content = result.stderr.strip()
            if any(keyword in stderr_content.lower() for keyword in ['detected', 'diacritics', 'processing']):
                # Tesseract等工具的正常信息性输出
                logging.debug(f"命令信息输出:\n{stderr_content}")
            else:
                # 可能的警告或错误
                logging.warning(f"命令标准错误输出:\n{stderr_content}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"命令执行失败: {command_str}")
        logging.error(f"返回码: {e.returncode}")
        logging.error(f"标准输出:\n{e.stdout}")
        logging.error(f"标准错误:\n{e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"命令未找到: {command[0]}。请确保该工具已安装并在系统PATH中。")
        logging.error(f"提示: 如果使用pipx安装，请确保 ~/.local/bin 在PATH中")
        return False

def create_temp_directory():
    """创建临时目录。"""
    return tempfile.mkdtemp()

def cleanup_directory(directory_path):
    """清理临时目录。"""
    try:
        shutil.rmtree(directory_path)
        logging.debug(f"临时目录已清理: {directory_path}")
    except Exception as e:
        logging.warning(f"清理临时目录失败: {directory_path}, 错误: {e}")

def copy_file(src, dst):
    """复制文件到目标位置。"""
    try:
        shutil.copy2(src, dst)
        logging.info(f"文件已复制: {src} -> {dst}")
        return True
    except Exception as e:
        logging.error(f"文件复制失败: {src} -> {dst}, 错误: {e}")
        return False

def check_dependencies():
    """检查必要的外部工具是否已安装。"""
    required_tools = {
        'pdftoppm': 'poppler-utils',
        'pdfinfo': 'poppler-utils',
        'tesseract': 'tesseract-ocr tesseract-ocr-chi-sim',
        'qpdf': 'qpdf',
        'recode_pdf': 'archive-pdf-tools (via pipx)'
    }
    
    missing_tools = []
    
    # 确保包含pipx安装路径
    env = os.environ.copy()
    home = os.path.expanduser("~")
    local_bin = os.path.join(home, ".local", "bin")
    
    if local_bin not in env.get("PATH", ""):
        env["PATH"] = f"{local_bin}:{env.get('PATH', '')}"
        logging.debug(f"检查依赖时添加 {local_bin} 到 PATH")
    
    for tool, package in required_tools.items():
        try:
            # 使用which命令检查工具是否在PATH中
            result = subprocess.run(['which', tool], 
                                  capture_output=True, 
                                  check=True,
                                  timeout=5,
                                  env=env)
            tool_path = result.stdout.decode('utf-8').strip()
            logging.debug(f"{tool} 已安装在: {tool_path}")
            
        except subprocess.CalledProcessError:
            missing_tools.append((tool, package))
            logging.debug(f"{tool} 未在PATH中找到")
        except Exception as e:
            missing_tools.append((tool, package))
            logging.debug(f"{tool} 检查时出现错误: {e}")
    
    if missing_tools:
        logging.error(f"缺少必要工具: {', '.join([tool for tool, _ in missing_tools])}")
        logging.error("请安装缺少的工具后再运行程序")
        
        # 给出具体的安装建议
        apt_packages = set()
        for tool, package in missing_tools:
            if tool == 'recode_pdf':
                logging.error("安装recode_pdf: pipx install archive-pdf-tools")
            else:
                apt_packages.add(package)
        
        if apt_packages:
            logging.error(f"使用apt安装: sudo apt install {' '.join(apt_packages)}")
        
        return False
    
    logging.info("所有必要工具已安装")
    return True

def get_current_timestamp():
    """获取当前时间戳字符串。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")