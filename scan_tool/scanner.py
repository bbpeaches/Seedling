import sys
import difflib
from pathlib import Path

def print_progress_bar(count, label="Processing", icon="⏳"):
    """
    A dynamic 'pulse' style progress indicator for tasks with unknown totals.
    """
    # Create a simple pulsing bar effect [ ###    ]
    pulse = ["#---", "-#--", "--#-", "---#", "--#-", "-#--"]
    idx = (count // 5) % len(pulse)
    sys.stdout.write(f"\r{icon} {label}... [{pulse[idx]}] Scanned: {count} items ")
    sys.stdout.flush()

def scan_dir_lines(dir_path, prefix="", max_depth=None, current_depth=0, show_hidden=False, excludes=None, stats=None):
    """
    Recursively generate each line of the directory tree and count files/directories.
    """
    if excludes is None:
        excludes = []
    if stats is None:
        stats = {"dirs": 0, "files": 0}
        
    lines = []
    if max_depth is not None and current_depth > max_depth:
        return lines

    path = Path(dir_path)
    
    try:
        items = list(path.iterdir())
        valid_items = [
            item for item in items 
            if not (not show_hidden and item.name.startswith('.')) and item.name not in excludes
        ]
        valid_items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError:
        lines.append(f"{prefix}└── [Permission Denied]")
        return lines
        
    for index, item in enumerate(valid_items):
        is_last = index == (len(valid_items) - 1)
        connector = "└── " if is_last else "├── "
        symlink_mark = " (symlink)" if item.is_symlink() else ""
        
        lines.append(f"{prefix}{connector}{item.name}{symlink_mark}")
        
        if item.is_dir():
            stats["dirs"] += 1
            if not item.is_symlink():
                extension = "    " if is_last else "│   "
                lines.extend(scan_dir_lines(
                    item, prefix=prefix + extension, max_depth=max_depth, 
                    current_depth=current_depth + 1, show_hidden=show_hidden,
                    excludes=excludes, stats=stats
                ))
        else:
            stats["files"] += 1
            
        # [ NEW ] Dynamic Progress Bar for Scan
        total_scanned = stats["dirs"] + stats["files"]
        if total_scanned % 15 == 0:
            print_progress_bar(total_scanned, label="Scanning", icon="⏳")
            
    return lines


def search_items(dir_path, keyword, show_hidden=False, excludes=None):
    """
    Search for files/directories using both Exact Match and Fuzzy Match (difflib).
    """
    if excludes is None:
        excludes = []
        
    exact_matches = []
    all_names = {} # Map name to Path object for fuzzy lookup
    keyword_lower = keyword.lower()
    
    # We use a mutable list for count so it can be modified inside the nested walk() function
    scan_stats = {"count": 0} 
    
    def walk(current_path):
        try:
            for item in current_path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                if item.name in excludes:
                    continue
                
                scan_stats["count"] += 1
                
                # Store for fuzzy backup
                all_names[item.name] = item
                
                # Exact substring match
                if keyword_lower in item.name.lower():
                    exact_matches.append(item)
                    
                # [ NEW ] Dynamic Progress Bar for Search
                if scan_stats["count"] % 10 == 0:
                    print_progress_bar(scan_stats["count"], label="Searching", icon="🔍")
                    
                if item.is_dir() and not item.is_symlink():
                    walk(item)
        except PermissionError:
            pass
            
    walk(Path(dir_path))
    
    # Clear the progress bar line when done
    sys.stdout.write(f"\r✅ Search complete! Scanned {scan_stats['count']} items.                \n")
    sys.stdout.flush()
    
    fuzzy_matches = []
    # Get names that are NOT in exact matches
    remaining_names = [name for name in all_names.keys() 
                       if not any(ex.name == name for ex in exact_matches)]
    
    # Use difflib to find close spellings
    close_names = difflib.get_close_matches(keyword, remaining_names, n=10, cutoff=0.4)
    fuzzy_matches = [all_names[name] for name in close_names]
    
    return exact_matches, fuzzy_matches