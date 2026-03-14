import sys
import difflib
from pathlib import Path
from .ui import print_progress_bar

TEXT_EXTENSIONS = {
    # --- C / C++ / CUDA ---
    '.c', '.h', 
    '.cpp', '.cc', '.cxx', '.c++', '.cp',          
    '.hpp', '.hxx', '.h++', '.hh', '.inc', '.inl', 
    '.cu', '.cuh',                                 # CUDA 
    
    # --- order ---
    '.py', '.js', '.ts', '.java', '.go', '.rs', '.cs',

    # --- config ---
    '.html', '.css', '.md', '.txt', 
    '.json', '.yaml', '.yml', '.toml', '.xml', 
    '.ini', '.cfg', '.csv',

    # --- bash ---
    '.sh', '.bat', '.ps1', '.sql'
}
SPECIAL_TEXT_NAMES = {'makefile', 'dockerfile', 'license', 'caddyfile', 'procfile'}

def is_text_file(file_path):
    if file_path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if file_path.name.lower() in SPECIAL_TEXT_NAMES:
        return True
    if file_path.name.startswith('.') and not file_path.suffix:
        return True
    return False

def scan_dir_lines(dir_path, prefix="", max_depth=None, current_depth=0, show_hidden=False, excludes=None, stats=None, highlights=None, text_only=False, quiet=False):
    if excludes is None: excludes = []
    if stats is None: stats = {"dirs": 0, "files": 0}
    if highlights is None: highlights = set()
        
    lines = []
    if max_depth is not None and current_depth > max_depth: return lines
    path = Path(dir_path)

    try:
        items = list(path.iterdir())
        valid_items = []
        for item in items:
            if not show_hidden and item.name.startswith('.'): continue
            if item.name in excludes: continue
            if text_only and item.is_file() and not is_text_file(item): continue 
            valid_items.append(item)
            
        valid_items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        lines.append(f"{prefix}[Permission Denied - Cannot read directory]")
        return lines
        
    for index, item in enumerate(valid_items):
        is_last = index == (len(valid_items) - 1)
        connector = "└── " if is_last else "├── "
        symlink_mark = " (symlink)" if item.is_symlink() else ""
        match_mark = " 🎯 [MATCHED]" if item in highlights else ""
        
        display_name = f"{item.name}/" if item.is_dir() else item.name
        
        lines.append(f"{prefix}{connector}{display_name}{symlink_mark}{match_mark}")
        
        if item.is_dir():
            stats["dirs"] += 1
            if not item.is_symlink():
                extension = "    " if is_last else "│   "
                lines.extend(scan_dir_lines(
                    item, prefix=prefix + extension, max_depth=max_depth, 
                    current_depth=current_depth + 1, show_hidden=show_hidden,
                    excludes=excludes, stats=stats, highlights=highlights, text_only=text_only, quiet=quiet
                ))
        else:
            stats["files"] += 1
            
        total_scanned = stats["dirs"] + stats["files"]
        if not quiet and total_scanned % 15 == 0:
            print_progress_bar(total_scanned, label="Scanning", icon="⏳")
            
    return lines

def search_items(dir_path, keyword, show_hidden=False, excludes=None, text_only=False, quiet=False):
    if excludes is None: excludes = []
        
    exact_matches = []
    all_names = []
    keyword_lower = keyword.lower()
    scan_stats = {"count": 0} 
    
    def walk(current_path):
        try:
            for item in current_path.iterdir():
                if not show_hidden and item.name.startswith('.'): continue
                if item.name in excludes: continue
                if text_only and item.is_file() and not is_text_file(item): continue 
                
                scan_stats["count"] += 1
                all_names.append((item.name, item)) 
                
                if keyword_lower in item.name.lower():
                    exact_matches.append(item)
                    
                if not quiet and scan_stats["count"] % 10 == 0:
                    print_progress_bar(scan_stats["count"], label="Searching", icon="🔍")
                    
                if item.is_dir() and not item.is_symlink():
                    walk(item)
        except PermissionError: pass
            
    walk(Path(dir_path))
    
    if not quiet:
        sys.stdout.write(f"\r✅ Search complete! Scanned {scan_stats['count']} items.                \n")
        sys.stdout.flush()
    
    exact_match_paths = {ex for ex in exact_matches}
    remaining_unique_names = list(set([name for name, item in all_names if item not in exact_match_paths]))
    
    close_names = difflib.get_close_matches(keyword, remaining_unique_names, n=10, cutoff=0.4)
    close_names_set = set(close_names)
    
    fuzzy_matches = [item for name, item in all_names if name in close_names_set and item not in exact_match_paths]
    
    return exact_matches, fuzzy_matches

def get_full_context(target_path, show_hidden=False, excludes=None, text_only=False, max_depth=None, quiet=False):
    if excludes is None: excludes = []
    context_data = []
    
    MAX_FILE_SIZE = 2 * 1024 * 1024  
    
    def walk(current_path, current_depth=0):
        if max_depth is not None and current_depth > max_depth:
            return
            
        try:
            items = sorted(list(current_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if not show_hidden and item.name.startswith('.'): continue
                if item.name in excludes: continue
                
                if item.is_file():
                    is_txt = is_text_file(item)
                    if (text_only and not is_txt) or not is_txt: 
                        continue

                    try:
                        if item.stat().st_size > MAX_FILE_SIZE:
                            continue
                        
                        if not quiet:
                            sys.stdout.write(f"\r📖 Reading: {item.name[:30]:<30}... ")
                            sys.stdout.flush()
                            
                        content = item.read_text(encoding='utf-8', errors='replace')
                        rel_path = item.relative_to(target_path)
                        context_data.append((rel_path, content))
                    except Exception: pass
                elif item.is_dir() and not item.is_symlink():
                    walk(item, current_depth + 1)
        except PermissionError: pass

    try:
        walk(target_path)
    except KeyboardInterrupt:
        if not quiet:
            sys.stdout.write("\n\n⚠️ [WARN] Read operation interrupted by user! Saving aggregated content so far...\n")
            sys.stdout.flush()
        
    return context_data