import os
import argparse
import textwrap
from pathlib import Path

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
        
        # Filter hidden files and specified exclusions
        valid_items = []
        for item in items:
            if not show_hidden and item.name.startswith('.'):
                continue
            if item.name in excludes:
                continue
            valid_items.append(item)
            
        # Sort: directories first, then alphabetically
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
                    item, 
                    prefix=prefix + extension, 
                    max_depth=max_depth, 
                    current_depth=current_depth + 1,
                    show_hidden=show_hidden,
                    excludes=excludes,
                    stats=stats
                ))
        else:
            stats["files"] += 1
            
    return lines

def create_image_from_text(text, output_file, line_count):
    """
    Render the generated directory tree text as an image (with memory overflow protection).
    """
    if line_count > 1000:
        print(f"⚠️ WARNING: Directory too large ({line_count} lines). Generating an image may cause memory overflow.")
        print("👉 SUGGESTION: Use the -d flag to limit depth, or use -f md to export as text.")
        return False

    try:
        from PIL import Image, ImageDraw, ImageFont # type: ignore
    except ImportError:
        print("❌ ERROR: Exporting as image requires the Pillow library.")
        print("👉 Run in terminal: pip install Pillow")
        return False

    font = None
    font_size = 18
    font_paths = [
        "consola.ttf", "cour.ttf", "lucon.ttf",         
        "Menlo.ttc", "Monaco.ttf", "SFNSMono.ttf",      
        "DejaVuSansMono.ttf", "UbuntuMono-R.ttf"        
    ]
    
    for font_name in font_paths:
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except IOError:
            continue
            
    if font is None:
        font = ImageFont.load_default()

    lines = text.split('\n')
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
    for i, line in enumerate(lines):
        draw.text((40, y_offset), line, font=font, fill=text_color)
        y_offset += line_heights[i]
        
    try:
        image.save(output_file)
        return True
    except Exception as e:
        print(f"❌ ERROR saving image: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="🌲 Powerful directory tree export tool (Supports MD/TXT/Image)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""\
            💡 Examples:
              1. Basic scan (generates .md in the parent directory by default):
                 scan /path/to/your/dir
                 
              2. Export as image, limiting scan depth to 2 levels:
                 scan /path/to/your/dir -f image -d 2
                 
              3. Specify output directory (creates folder if it doesn't exist):
                 scan /path/to/your/dir --outdir ~/Desktop
                 
              4. Include hidden files, exclude node_modules, and customize filename:
                 scan . -s -e node_modules venv -o my_code.md
            """)
    )
    
    parser.add_argument("target", nargs="?", default=".", help="Target directory path to scan")
    parser.add_argument("-f", "--format", choices=["md", "txt", "image"], default="md", help="Output file format")
    parser.add_argument("-o", "--output", help="Custom output filename (Default: target_folder_name.ext)")
    parser.add_argument("-s", "--show-hidden", action="store_true", help="Include hidden files/directories (starting with .)")
    parser.add_argument("-d", "--depth", type=int, default=None, help="Maximum recursion depth")
    parser.add_argument("-e", "--exclude", nargs="+", default=[], help="Files/directories to exclude (e.g., node_modules venv)")
    parser.add_argument("--outdir", help="Directory to save the generated file (Default: parent directory of target)")
    
    args = parser.parse_args()
    target_path = Path(args.target).resolve()
    if not target_path.exists() or not target_path.is_dir():
        print(f"❌ ERROR: Directory '{args.target}' does not exist or is invalid.")
        return

    # Determine filename
    target_name = target_path.name or "root_dir"
    ext_map = {'md': '.md', 'txt': '.txt', 'image': '.png'}
    output_filename = args.output or f"{target_name}{ext_map[args.format]}"
    
    # Determine output directory
    if args.outdir:
        out_dir_path = Path(args.outdir).resolve()
        out_dir_path.mkdir(parents=True, exist_ok=True)
    else:
        out_dir_path = target_path.parent
        
    final_output_file = out_dir_path / output_filename
    
    print(f"⏳ Scanning directory ({target_path})...")
    
    stats = {"dirs": 0, "files": 0}
    lines = scan_dir_lines(
        target_path, 
        max_depth=args.depth, 
        show_hidden=args.show_hidden,
        excludes=args.exclude,
        stats=stats
    )
    
    root_name = target_path.name or str(target_path)
    stats_str = f"\n[ {stats['dirs']} directories, {stats['files']} files ]"
    tree_text = f"{root_name}/\n" + "\n".join(lines) + "\n" + stats_str
    
    success = False
    try:
        if args.format == 'md':
            with open(final_output_file, 'w', encoding='utf-8') as f:
                f.write(f"# 📁 Directory Structure Stats: `{target_path}`\n\n```text\n{tree_text}\n```\n")
            success = True
            
        elif args.format == 'txt':
            with open(final_output_file, 'w', encoding='utf-8') as f:
                f.write(tree_text + "\n")
            success = True
            
        elif args.format == 'image':
            print("🎨 Rendering image...")
            success = create_image_from_text(tree_text, final_output_file, len(lines))
            
    except Exception as e:
        print(f"❌ ERROR saving file: {e}")
        
    if success:
        print(f"✅ SUCCESS! Directory structure exported to: {final_output_file}")

if __name__ == "__main__":
    main()