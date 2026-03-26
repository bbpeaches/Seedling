import sys
import platform
import re
from pathlib import Path, PureWindowsPath
from .logger import logger

def is_safe_path(path: Path, base_dir: Path) -> bool:
    """路径安全检查"""
    try:
        p_resolved = Path(path).resolve()
        base_resolved = Path(base_dir).resolve()
        if sys.version_info >= (3, 9):
            return p_resolved.is_relative_to(base_resolved)
        else:
            try:
                p_resolved.relative_to(base_resolved)
                return True
            except ValueError:
                return False
    except Exception:
        return False

def get_dynamic_fence(content: str) -> str:
    """计算最小反引号数量"""
    max_ticks = 2 # 最小为2
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('`'):
            ticks = len(stripped) - len(stripped.lstrip('`'))
            if ticks > max_ticks:
                max_ticks = ticks
    return '`' * (max_ticks + 1)


def extract_tree_block(file_path):
    """目录树提取"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f: 
            lines = f.readlines()
    except Exception as e:
        logger.error(f"文件读取失败: {e}")
        return []

    tree_lines = []
    in_tree = False # 是否正在读取

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        # 处理空行
        if not stripped:
            if in_tree: 
                break
            continue
            
        # 是否包含目录树符号
        has_tree_chars = any(c in line for c in ['├──', '└──', '│'])
        next_has_tree_chars = False
        if i + 1 < len(lines):
            next_has_tree_chars = any(c in lines[i+1] for c in ['├──', '└──', '│'])
            
        # 匹配
        if has_tree_chars or (not in_tree and next_has_tree_chars):
            in_tree = True
            if not stripped.startswith('```'): 
                tree_lines.append(stripped)
        elif in_tree:
            if stripped.startswith('```') or not has_tree_chars: 
                break 
    return tree_lines

def extract_file_contents(file_path):
    """内容提取"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f: 
            lines = f.readlines()
    except Exception:
        return {}
        
    file_contents = {}
    current_file = None       # 正在解析的路径
    in_code_block = False     # 是否在代码块内
    current_content = []      # 存储当前文件的内容行
    current_fence = None      # 当前代码块的围栏符号

    for line in lines:
        if not in_code_block and line.startswith('### FILE: '):
            raw_path = line.replace('### FILE: ', '').strip()
            current_file = PureWindowsPath(raw_path).as_posix()
            # 重置内容缓存
            current_content = []
            in_code_block = False
            current_fence = None
            continue
            
        # 解析内容
        if current_file:
            stripped_line = line.strip()

            if stripped_line.startswith('```') and not in_code_block:
                in_code_block = True
                match = re.match(r'^`+', stripped_line)
                current_fence = match.group() if match else '```'
                continue
                
            elif in_code_block and stripped_line == current_fence:
                in_code_block = False
                file_contents[current_file] = "".join(current_content)
                # 重置当前文件状态
                current_file = None
                current_fence = None
                continue
                
            # 代码块内的内容，添加到缓存
            if in_code_block:
                current_content.append(line)
                
    return file_contents

def handle_path_error(path_str):
    """处理路径错误"""
    path = Path(path_str).resolve()
    logger.error(f"The path '{path_str}' is not a valid directory.")
    if path.is_file():
        logger.info(f"📄 It looks like this is a FILE, but I need a FOLDER.")
        logger.info(f"👉 Did you mean the parent folder: {path.parent} ?")
    elif not path.exists():
        logger.info(f"🔍 The directory does not exist. Please check the path.")
    sys.exit(1)

def clean_text_for_image(text):
    """图片文本清理"""
    cleaned = text.replace('📁 ', '').replace('📄 ', '')
    cleaned = cleaned.replace('📁', '').replace('📄', '')
    return cleaned

def get_best_font(font_size=18):
    """字体获取"""
    try:
        from PIL import ImageFont # type: ignore
    except ImportError:
        logger.error("Pillow library is missing. Image export disabled.")
        return None

    system = platform.system() # 获取当前操作系统

    # 各系统优先字体路径
    font_paths = {
        "Darwin": [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Cache/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.cjk",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            # 备用
            "Arial Unicode.ttf",
            "/Library/Fonts/Arial Unicode.ttf",
            "Menlo.ttc",
            "/System/Library/Fonts/Menlo.ttc",
        ],
        "Windows": [
            "C:\\Windows\\Fonts\\msyh.ttc",      # 微软雅黑
            "C:\\Windows\\Fonts\\msyhbd.ttc",    # 微软雅黑粗体
            "C:\\Windows\\Fonts/simhei.ttf",     # 黑体
            "C:\\Windows\\Fonts\\simsun.ttc",    # 宋体
            "C:\\Windows\\Fonts\\simkai.ttf",    # 楷体
            # 备用
            "C:\\Windows\\Fonts\\consola.ttf",   # Consolas
            "C:\\Windows\\Fonts\\arial.ttf",     # Arial
        ],
        "Linux": [
            # 默认字体
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            # 国产开源中文字体
            "/usr/share/fonts/wenquanyi/wqy-microhei/wqy-microhei.ttc",
            "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/wenquanyi/wqy-zenhei/wqy-zenhei.ttc",
            # Adobe开源字体
            "/usr/share/fonts/adobe-source-han-sans/SourceHanSansCN-Regular.otf",
            "/usr/share/fonts/opentype/source-han-sans/SourceHanSansCN-Regular.otf",
            "/usr/share/fonts/source-han-sans/SourceHanSansCN-Regular.otf",
            # 备用字体
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    }

    # 优先尝试硬编码的字体路径
    for font_path in font_paths.get(system, []):
        try:
            return ImageFont.truetype(font_path, font_size)
        except IOError:
            continue

    # Linux尝试通过fontconfig动态查找字体
    if system == "Linux":
        font = _try_fontconfig_discovery(font_size)
        if font:
            return font

    # 无可用系统字体
    logger.warning("No system fonts found. Falling back to Pillow default (Limited CJK support).")
    return ImageFont.load_default()

def _try_fontconfig_discovery(font_size: int):
    """Linux字体动态查找"""
    try:
        import subprocess

        # 查询系统中支持中文的字体
        result = subprocess.run(
            ['fc-list', ':lang=zh', 'file'],
            capture_output=True,
            text=True,
            timeout=5
        )

        # 加载第一个可用的中文字体
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n')[:10]:
                font_path = line.split(':')[0].strip()
                if font_path:
                    try:
                        from PIL import ImageFont # type: ignore
                        return ImageFont.truetype(font_path, font_size)
                    except IOError:
                        continue

        # 备用查找等宽字体
        result = subprocess.run(
            ['fc-list', ':spacing=100', 'file'],  # 等宽字体
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n')[:5]:
                font_path = line.split(':')[0].strip()
                if font_path:
                    try:
                        from PIL import ImageFont # type: ignore
                        return ImageFont.truetype(font_path, font_size)
                    except IOError:
                        continue

    except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
        pass

    return None

def create_image_from_text(text, output_file, line_count):
    """文本转图片"""
    if line_count > 1500:
        logger.error(f"❌ Directory too large ({line_count} lines). Image export aborted to prevent memory overflow.")
        logger.info("💡 Tip: Try using '--depth' to limit the scan, or export to Markdown/TXT instead.")
        return False

    try:
        from PIL import Image, ImageDraw, ImageFont # type: ignore
    except ImportError:
        logger.error("Exporting as image requires the Pillow library. Try: pip install Pillow")
        return False
    
    clean_text = clean_text_for_image(text)
    font_size = 18
    font = get_best_font(font_size)
    if font is None:
        return False

    lines = clean_text.split('\n')
    dummy_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    
    max_width = 0
    line_heights = []
    
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
        except AttributeError:
            width, height = draw.textsize(line, font=font)
            
        max_width = max(max_width, width)
        line_heights.append(max(height, font_size) + 6) 
        
    img_width = int(max_width + 80)  
    img_height = int(sum(line_heights) + 80) 
    
    bg_color = (40, 44, 52)
    text_color = (171, 178, 191)
    
    image = Image.new('RGB', (img_width, img_height), color=bg_color)
    draw = ImageDraw.Draw(image)
    
    y_offset = 40
    total_lines = len(lines)
    
    for i, line in enumerate(lines):
        draw.text((40, y_offset), line, font=font, fill=text_color)
        y_offset += line_heights[i]
        
        if i % max(1, (total_lines // 20)) == 0 or i == total_lines - 1:
            percent = int((i + 1) / total_lines * 100)
            bar = '█' * (percent // 5) + '-' * (20 - (percent // 5))
            sys.stdout.write(f"\r🎨 Rendering Image: [{bar}] {percent}% ")
            sys.stdout.flush()
            
    print() 
    try:
        image.save(output_file)
        return True
    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        return False

def check_overwrite_safely(output_path: Path) -> bool:
    """文件覆盖安全检查交互"""
    if output_path.exists():
        from seedling.core.ui import ask_yes_no
        logger.warning(f"NOTICE: Target file already exists:\n   👉 {output_path}")
        if not ask_yes_no("Do you want to overwrite it? [y/n]: "):
            logger.info("Operation aborted. No changes were made.")
            return False
    return True