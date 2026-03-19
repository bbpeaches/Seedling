import sys
import difflib
import fnmatch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Set, List, Optional, Dict, Tuple
from .ui import print_progress_bar
from .logger import logger 
from .sysinfo import get_system_mem_limit_mb, get_system_depth_limit 

# --- 核心约束常量 ---
MAX_FILE_SIZE = 2 * 1024 * 1024 # 2MB 磁盘限制
MAX_ITERATION_DEPTH = 1000      # 显式遍历硬上限
HARD_DEPTH_LIMIT = min(get_system_depth_limit(), MAX_ITERATION_DEPTH)

SPECIAL_TEXT_NAMES = {'makefile', 'dockerfile', 'license', 'caddyfile', 'procfile'}
TEXT_EXTENSIONS = {
    '.c', '.h', '.cpp', '.cc', '.cxx', '.c++', '.cp',         
    '.hpp', '.hxx', '.h++', '.hh', '.inc', '.inl', 
    '.cu', '.cuh',                                           
    '.py', '.js', '.ts', '.java', '.go', '.rs', '.cs',
    '.html', '.css', '.md', '.txt', 
    '.json', '.yaml', '.yml', '.toml', '.xml', 
    '.ini', '.cfg', '.csv',
    '.sh', '.bat', '.ps1', '.sql'
}

# Dataclass
@dataclass
class ScanConfig:
    """封装扫描引擎的所有配置项，避免函数参数爆炸"""
    max_depth: Optional[int] = None
    show_hidden: bool = False
    excludes: List[str] = field(default_factory=list)
    text_only: bool = False
    quiet: bool = False
    highlights: Set[Path] = field(default_factory=set)

# 底层探测函数

def is_text_file(file_path: Path) -> bool:
    """判断是否为已知的文本文件类型"""
    if file_path.suffix.lower() in TEXT_EXTENSIONS: return True
    if file_path.name.lower() in SPECIAL_TEXT_NAMES: return True
    if file_path.name.startswith('.') and not file_path.suffix: return True
    return False

def is_binary_content(file_path: Path) -> bool:
    """Heuristic binary detection with magic numbers"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            # 常见的二进制文件头
            binary_signatures = [
                b'\x89PNG', b'GIF89a', b'GIF87a', b'\xff\xd8\xff', 
                b'MZ', b'\x7fELF', b'PK\x03\x04', b'%PDF-', b'Rar!\x1a\x07'
            ]
            if b'\x00' in chunk or any(chunk.startswith(sig) for sig in binary_signatures):
                return True
    except Exception as e:
        logger.debug(f"Binary probe failed for {file_path.name}: {e}")
        return True 
    return False

def matches_exclude_pattern(item_path: Path, base_dir: Path, exclude_patterns: List[str]) -> bool:
    """
    检查路径是否匹配 Git 风格的过滤规则
    """
    # 生成以 / 开头的标准 POSIX 相对路径
    rel_path = "/" + item_path.relative_to(base_dir).as_posix()
    item_name = item_path.name
    
    for pattern in exclude_patterns:
        is_dir_only = pattern.endswith('/')
        clean_pattern = pattern.rstrip('/')
        
        # 路径锚定规则
        if clean_pattern.startswith('/'):
            if fnmatch.fnmatch(rel_path, clean_pattern):
                if not is_dir_only or item_path.is_dir():
                    return True
        
        # 全局规则 
        else:
            # 匹配文件名
            if fnmatch.fnmatch(item_name, clean_pattern):
                if not is_dir_only or item_path.is_dir():
                    return True
            # 匹配路径中段 
            if fnmatch.fnmatch(rel_path, f"*/{clean_pattern}") or \
               fnmatch.fnmatch(rel_path, f"*/{clean_pattern}/*") or \
               fnmatch.fnmatch(rel_path, f"**/{clean_pattern}"):
                if not is_dir_only or item_path.is_dir():
                    return True
    return False

def is_valid_item(item: Path, base_dir: Path, config: ScanConfig) -> bool:
    """综合校验文件/目录是否应包含在结果中"""
    if not config.show_hidden and item.name.startswith('.'): 
        return False
    
    if matches_exclude_pattern(item, base_dir, config.excludes):
        return False
        
    if config.text_only and item.is_file() and not is_text_file(item): 
        return False
    return True

def safe_read_text(file_path: Path, quiet: bool = False) -> Optional[str]:
    """尝试多种编码读取文本内容"""
    if is_binary_content(file_path):
        return None

    encodings = ['utf-8', 'gbk', 'big5', 'utf-16', 'latin-1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc, errors='strict') as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue

    if not quiet:
        logger.warning(f"Skipped {file_path.name}: Unsupported encoding.")
    return None

def scan_dir_lines(dir_path: Path, config: ScanConfig, stats: Dict[str, int]) -> List[str]:
    lines = []
    path = Path(dir_path)
    base_dir = path.resolve()
    seen_real_paths = {base_dir}

    def _get_children(p: Path) -> List[Path]:
        valid_items = [
            item for item in p.iterdir() 
            if is_valid_item(item, base_dir, config)
        ]
        valid_items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        return valid_items

    # 捕获根目录的权限错误
    try:
        initial_items = _get_children(path)
    except PermissionError:
        lines.append("[Permission Denied - Cannot read directory]")
        return lines

    stack: List[Tuple[Path, int, str, bool]] = []
    for i, item in enumerate(reversed(initial_items)):
        stack.append((item, 1, "", i == 0))

    while stack:
        item, depth, curr_prefix, is_last = stack.pop()
        if depth > HARD_DEPTH_LIMIT:
            if not config.quiet: lines.append(f"{curr_prefix}└── ⚠️ [SYSTEM MAX DEPTH REACHED]")
            continue
        
        connector = "└── " if is_last else "├── "
        symlink_mark = " (symlink)" if item.is_symlink() else ""
        match_mark = " 🎯 [MATCHED]" if item in config.highlights else ""
        display_name = f"{item.name}/" if item.is_dir() else item.name
        lines.append(f"{curr_prefix}{connector}{display_name}{symlink_mark}{match_mark}")
        
        if item.is_dir(): stats["dirs"] += 1
        else: stats["files"] += 1
            
        total_scanned = stats["dirs"] + stats["files"]
        if total_scanned % 15 == 0:
            print_progress_bar(total_scanned, label="Scanning", quiet=config.quiet)

        # 深入子目录
        if item.is_dir() and not item.is_symlink():
            if config.max_depth is not None and depth >= config.max_depth:
                continue  
            
            try:
                real_path = item.resolve(strict=True)
                if real_path in seen_real_paths:
                    if not config.quiet:
                        lines.append(f"{curr_prefix}    └── 🔄 [Recursion Blocked]")
                    continue  
                seen_real_paths.add(real_path)
            except Exception: pass

            # 捕获子目录的权限错误
            try:
                children = _get_children(item)
            except PermissionError:
                extension = "    " if is_last else "│   "
                lines.append(f"{curr_prefix}{extension}[Permission Denied - Cannot read directory]")
                continue
                
            new_prefix = curr_prefix + ("    " if is_last else "│   ")
            for i, child in enumerate(reversed(children)):
                stack.append((child, depth + 1, new_prefix, i == 0))
                
    return lines
# 检索与聚合

def search_items(dir_path: Path, keyword: str, config: ScanConfig) -> Tuple[List[Path], List[Path]]:
    """搜索文件和文件夹"""
    exact_matches: List[Path] = []
    all_seen: List[Tuple[str, Path]] = []
    keyword_lower = keyword.lower()
    base_dir = dir_path.resolve()
    count = 0

    stack = [dir_path]
    while stack:
        curr = stack.pop()
        try:
            for item in curr.iterdir():
                if not is_valid_item(item, base_dir, config): continue
                
                count += 1
                all_seen.append((item.name, item))
                if keyword_lower in item.name.lower():
                    exact_matches.append(item)
                
                if count % 15 == 0:
                    print_progress_bar(count, label="Searching", icon="🔍", quiet=config.quiet)

                if item.is_dir() and not item.is_symlink():
                    stack.append(item)
        except PermissionError: pass

    # 模糊匹配逻辑
    unique_names = list(set([n for n, p in all_seen]))
    close_names = difflib.get_close_matches(keyword, unique_names, n=10, cutoff=0.7)
    fuzzy_matches = [p for n, p in all_seen if n in close_names and p not in exact_matches]

    return exact_matches, fuzzy_matches

def get_full_context(target_path: Path, config: ScanConfig) -> List[Tuple[Path, str]]:
    """收集所有文本文件的内容 (Power Mode)"""
    context_data = []
    dynamic_limit_mb = get_system_mem_limit_mb()
    total_mem_limit = dynamic_limit_mb * 1024 * 1024
    curr_mem_usage = 0
    base_dir = target_path.resolve()
    
    stack = [(target_path, 0)]
    while stack:
        curr, depth = stack.pop()
        if config.max_depth and depth >= config.max_depth: continue
            
        try:
            items = sorted(list(curr.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if not is_valid_item(item, base_dir, config): continue
                    
                if item.is_file():
                    try:
                        f_stat = item.stat()
                        if f_stat.st_size > MAX_FILE_SIZE: continue
                        
                        content = safe_read_text(item, quiet=config.quiet)
                        if content is not None:
                            if sys.getsizeof(content) > MAX_FILE_SIZE * 2:
                                logger.debug(f"Memory limit triggered (decoded) for {item.name}")
                                continue

                            encoded_size = len(content.encode('utf-8'))
                            if curr_mem_usage + encoded_size > total_mem_limit:
                                logger.error(f"Hardware RAM limit ({dynamic_limit_mb}MB) reached! Safety abort.")
                                return context_data
                                
                            context_data.append((item.relative_to(base_dir), content))
                            curr_mem_usage += encoded_size
                    except Exception: pass
                elif item.is_dir() and not item.is_symlink():
                    stack.append((item, depth + 1))
        except PermissionError: pass
        
    return context_data