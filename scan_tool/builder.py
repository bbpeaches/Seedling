import re
import sys
from pathlib import Path

def extract_tree_block(file_path):
    """
    Intelligently find and extract the first tree structure block from a text/markdown file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        sys.stderr.write(f"\n❌ ERROR reading file: {e}\n")
        return []

    tree_lines = []
    in_tree = False
    
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if not stripped:
            if in_tree: 
                break # Empty line usually means end of the tree block
            continue
            
        # Detect if the current line or the immediately next line contains tree characters
        has_tree_chars = any(c in line for c in ['├──', '└──', '│'])
        next_has_tree_chars = False
        if i + 1 < len(lines):
            next_has_tree_chars = any(c in lines[i+1] for c in ['├──', '└──', '│'])
            
        # The root folder often doesn't have tree chars, but its children will.
        if has_tree_chars or (not in_tree and next_has_tree_chars):
            in_tree = True
            # Ignore markdown code block backticks
            if not stripped.startswith('```'):
                tree_lines.append(stripped)
        elif in_tree:
            # Stop if we hit a line that breaks the tree pattern (like markdown text)
            if stripped.startswith('```'):
                break
            # If no tree chars and we are inside, it might be a broken tree or end of block
            if not has_tree_chars:
                break
                
    return tree_lines

def build_structure_from_file(source_file, target_dir):
    """
    Parse the extracted tree lines and construct the actual file system hierarchy.
    """
    tree_lines = extract_tree_block(source_file)
    if not tree_lines:
        print(f"\n👻 ERROR: Could not find any valid tree structure in '{source_file}'.")
        return False

    target_path = Path(target_dir).resolve()
    print(f"\n🏗️  Building structure in: {target_path} ...")
    
    parsed_items = []
    
    for line in tree_lines:
        match = re.match(r'^([│├└─\s]*)(.+)$', line)
        if not match:
            continue
            
        prefix, content = match.groups()
        depth = len(prefix) 
        
        # Strip annotations/comments 
        clean_name = content.split('<-')[0].strip()
        clean_name = re.split(r'\s{2,}#', clean_name)[0].strip()
        clean_name = re.split(r'\s{2,}', clean_name)[0].strip() # Aggressive strip for right-aligned comments
        
        is_dir = clean_name.endswith('/')
        if is_dir:
            clean_name = clean_name.rstrip('/')
            
        if clean_name:
             parsed_items.append({'depth': depth, 'name': clean_name, 'is_dir': is_dir})
             
    for i, item in enumerate(parsed_items):
        if i + 1 < len(parsed_items):
            if parsed_items[i+1]['depth'] > item['depth']:
                item['is_dir'] = True

    stack = [(-1, target_path)]
    dirs_created, files_created = 0, 0
    
    for item in parsed_items:
        depth = item['depth']
        name = item['name']
        icons = ["🔨", "🔧", "🔩", "📐"]
        icon = icons[i % len(icons)]
        sys.stdout.write(f"\r{icon} Constructing... {i+1}/{len(parsed_items)}")
        sys.stdout.flush()

        while stack and stack[-1][0] >= depth:
            stack.pop()
            
        parent_path = stack[-1][1]
        current_path = parent_path / name
        
        try:
            if item['is_dir']:
                current_path.mkdir(parents=True, exist_ok=True)
                stack.append((depth, current_path))
                dirs_created += 1
                print(f" 📁 Created dir:  {current_path.relative_to(target_path)}")
            else:
                current_path.parent.mkdir(parents=True, exist_ok=True)
                current_path.touch(exist_ok=True)
                files_created += 1
                print(f" 📄 Created file: {current_path.relative_to(target_path)}")
        except Exception as e:
            print(f" ❌ Failed to create '{name}': {e}")
            
    print(f"\n✅ Build Complete! [ 📁 {dirs_created} dirs | 📄 {files_created} empty files ]\n")
    return True