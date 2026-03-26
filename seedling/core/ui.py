import sys
import os
import tempfile
import time
import random
import io
from pathlib import Path
from typing import Optional
from seedling.core.logger import logger

# UI 核心配置图标
UI_CONFIG = {
    "DIR": "📁",
    "FILE": "📄",
    "MATCH": "🎯",
    "WAIT": "⏳",
    "SUCCESS": "🎉"
}

def setup_ui_theme(no_emoji: bool = False) -> None:
    """根据环境设置 UI 主题"""
    is_old_windows = False
    try:
        is_old_windows = sys.platform == "win32" and os.get_terminal_size().columns < 10
    except OSError:
        pass
    
    has_no_color = "NO_COLOR" in os.environ
    if no_emoji or is_old_windows or has_no_color:
        UI_CONFIG.update({
            "DIR": "[DIR]",
            "FILE": "[FILE]",
            "MATCH": "[MATCHED]",
            "WAIT": "...",
            "SUCCESS": "SUCCESS"
        })

def ensure_utf8_output() -> None:
    """Windows 编码防御"""
    if sys.platform == "win32":
        for stream_name in ('stdout', 'stderr'):
            try:
                stream = getattr(sys, stream_name)
                if stream and hasattr(stream, 'buffer') and stream.buffer:
                    setattr(sys, stream_name, io.TextIOWrapper(
                        stream.buffer, encoding='utf-8', line_buffering=True
                    ))
            except Exception:
                # 重定向失败，静默处理
                pass

def ask_yes_no(prompt_text: str, default_no: bool = True) -> bool:
    """交互式确认提示"""
    if not sys.stdin.isatty():
        logger.warning("\n⚠️ Non-interactive terminal detected: defaulting to 'no' to prevent blocking.")
        return False if default_no else True

    while True:
        try:
            ans = input(prompt_text).strip().lower()
            if ans in ['y', 'yes']:
                return True
            if ans in ['n', 'no']:
                return False
            print("⚠️ Invalid input. Please enter 'y' or 'n'.")
        except EOFError:
            logger.warning("\n⚠️ Input stream closed (EOF): defaulting to 'no'.")
            return False

def print_progress_bar(count: int, label: str = "Processing", icon: str = "⏳", quiet: bool = False) -> None:
    """动态进度条"""
    if quiet:
        return
    
    pulse = ["#---", "-#--", "--#-", "---#", "--#-", "-#--"]
    idx = (count // 5) % len(pulse)
    sys.stdout.write(f"\r{icon} {label}... [{pulse[idx]}] Scanned: {count} items ")
    sys.stdout.flush()

def _get_state_file(tool_name: str) -> Path: 
    """获取状态文件路径"""
    try:
        ppid = os.getppid()
    except AttributeError:
        ppid = "default"
    temp_dir = Path(tempfile.gettempdir())
    return temp_dir / f"seedling_session_{ppid}_{tool_name}.state"

def _get_and_increment_run_count(tool_name: str) -> int: 
    """获取并递增工具运行计数"""
    state_file = _get_state_file(tool_name)
    count = 0
    try:
        if state_file.exists():
            count = int(state_file.read_text().strip())
    except Exception: pass
    count += 1
    try:
        state_file.write_text(str(count))
    except Exception: pass
    return count

# --- 欢迎与彩蛋 ---

def print_welcome_message():
    """欢迎信息"""
    welcome_text = """
    ==================================================================
      🌲 Seedling, A Directory Tree Scanner & Builder 🌲
    ==================================================================
    [ Basic Usage ]
      scan .                  -> Scan current directory
      
    [ Advanced Features ]
      scan . --full           -> Context Aggregation for LLMs
      scan . --skeleton       -> Extract Python AST structure
      build blueprint.md      -> Reconstruct file system
    ==================================================================
    """
    print(welcome_text)

def handle_empty_run():
    """彩蛋"""
    count = _get_and_increment_run_count("scan")
    if count == 1:
        print_welcome_message()
    elif count == 2:
        print("\n💡 [ Tip ] Use 'scan --help' to see all flags!\n")
    elif count == 3:
        print("\n🐿️  [ Easter Egg ] A squirrel is looking for arguments...\n")
        track_len = 30
        for i in range(track_len):
            sys.stdout.write(f"\r  [{'.' * i}🐿️ {'.' * (track_len - i - 1)}]")
            sys.stdout.flush()
            time.sleep(0.05)
        print("\n")
    else:
        print(f"\n🤖 You've called 'scan' {count} times without path.")
        if ask_yes_no("👉 Brew some virtual coffee? [y/n]: "):
            sys.stdout.write("  Brewing : [")
            for _ in range(20):
                sys.stdout.write("☕")
                sys.stdout.flush()
                time.sleep(0.1)
            print("] 100% Done!")
    sys.exit(0)

def handle_empty_build_run():
    """彩蛋"""
    count = _get_and_increment_run_count("build")
    if count == 1:
        print("\n🏗️  Welcome to Build mode! Give me a blueprint file (.md/.txt).")
    else:
        print(f"\n👷 Chief, that's {count} empty calls! The workers are on break. 🃏")
    sys.exit(0)