import argparse
import sys
import textwrap
from pathlib import Path

from .utils import SmartArgumentParser, handle_empty_run, handle_path_error
from .builder import build_structure_from_file
from .scanner import scan_dir_lines, search_items
from .exporter import create_image_from_text

def build_entry():
    """
    Dedicated entry point for the 'build' command.
    Usage: build <tree_file> [target_dir]
    """
    if len(sys.argv) == 1:
        from .utils import handle_empty_build_run
        handle_empty_build_run()

    parser = argparse.ArgumentParser(
        description="🏗️ Build directory structure from a tree file (.txt or .md)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""\
            [ Examples ]
              1. Build in current directory:
                 build my_tree.txt
                 
              2. Build in a specific new directory:
                 build my_tree.md ~/Desktop/MyNewApp
            """)
    )
    parser.add_argument("file", help="The source tree file (.txt or .md)")
    parser.add_argument("target", nargs="?", default=".", help="Where to build the structure (default: current dir)")
        
    args = parser.parse_args()
    source_file = Path(args.file).resolve()
    target_dir = Path(args.target).resolve()
    
    if not source_file.exists():
        print(f"\n❌ ERROR: Source file '{args.file}' does not exist.")
        sys.exit(1)
        
    build_structure_from_file(source_file, target_dir)

def main():
    if len(sys.argv) == 1:
        handle_empty_run()
        # Notice: If count >= 2, handle_empty_run() adds '-h' to sys.argv and continues.
    
    # Use RawTextHelpFormatter to respect our newlines and spacing in the description and epilog
    parser = SmartArgumentParser(
        description="""
🌲 Directory Tree Scanner (v2.0.0)
====================================================================
A powerful CLI tool to Scan and Search file systems.

💡 Tip: To build a folder structure from a file, use the new 'build' command!
   (Try typing 'build -h' for more info)
====================================================================
        """,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""\
            [ Modes of Operation ]
              1. SCAN MODE (Default) : Exports a directory tree to a file.
              2. FIND MODE (-f)      : Searches for files/folders by name.

            [ Default Behaviors ]
              • Target Directory : Current working directory (.)
              • Output Format    : Markdown (.md)
              • Output Location  : Current working directory (.)
              • Hidden Files     : Ignored (unless -s is explicitly passed)

            [ Flag Conflicts & Limitations ]
              • When finding (-f) : -F (Format) and -d (Depth) are IGNORED.

            [ Examples ]
              1. Basic Scan (Outputs tree.md in current dir):
                 scan /path/to/project

              2. Search for files (Exact & Fuzzy match):
                 scan . -f "config"

              3. 🌟 THE MOST COMPLEX EXAMPLE (Advanced Scan):
                 scan /var/www/html -s -d 4 -e node_modules .git venv -F image -o ~/Desktop -n server_arch.png
                 
                 (Explanation: Scans '/var/www/html', includes hidden files (-s), 
                  limits recursion to 4 levels deep (-d 4), 
                  excludes heavy folders (-e), formats as a beautiful image (-F image), 
                  and saves it to the Desktop (-o) with a custom filename (-n).)
            """)
    )
    
    # Target directory is a positional argument, optional (defaults to current dir)
    parser.add_argument("target", nargs="?", default=".", help="Target directory for scanning or searching")
    
    parser.add_argument("-f", "--find", type=str, help="FIND MODE: Search items (Exact & Fuzzy)")
    parser.add_argument("-F", "--format", choices=["md", "txt", "image"], default="md", help="Output format (Scan mode only)")
    parser.add_argument("-n", "--name", help="Custom output filename")
    parser.add_argument("-o", "--outdir", help="Output directory path")
    parser.add_argument("-s", "--show-hidden", action="store_true", help="Include hidden files (starting with .)")
    parser.add_argument("-d", "--depth", type=int, default=None, help="Maximum recursion depth (Scan mode only)")
    parser.add_argument("-e", "--exclude", nargs="+", default=[], help="Files/directories to exclude (e.g., node_modules venv)")
    
    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    # Path Safety Check with smart suggestions
    if not target_path.exists() or not target_path.is_dir():
        handle_path_error(args.target)

    # ==========================
    # MODE 1: SEARCH (-f / --find)
    # ==========================
    if args.find:
        exact, fuzzy = search_items(target_path, args.find, args.show_hidden, args.exclude)
        
        def format_item(item):
            prefix = "[DIR] 📁" if item.is_dir() else "📄"
            rel = item.relative_to(target_path) if target_path in item.parents else item
            return f"{prefix} {rel}"

        if exact:
            print(f"\n🎯 Exact matches for '{args.find}':")
            print("-" * 40)
            for item in exact[:20]:
                print(f" {format_item(item)}")
            if len(exact) > 20:
                print(f" ... and {len(exact)-20} more.")
        else:
            print(f"\n❓ No exact matches found for '{args.find}'.")

        if fuzzy:
            print(f"\n💡 Did you mean one of these? (Fuzzy matches):")
            print("-" * 40)
            for item in fuzzy[:10]:
                print(f" {format_item(item)}")

        out_dir = Path(args.outdir).resolve() if args.outdir else Path.cwd()
        target_name = target_path.name or "root"
        search_filename = args.name or f"{target_name}_search_{args.find}.txt"
        final_search_file = out_dir / search_filename

        try:
            with open(final_search_file, 'w', encoding='utf-8') as f:
                f.write(f"Search Results for '{args.find}' in '{target_path}'\n")
                f.write("="*60 + "\n\n[ EXACT MATCHES ]\n")
                for item in exact: f.write(f"{item.resolve()}\n")
                f.write("\n[ FUZZY MATCHES ]\n")
                for item in fuzzy: f.write(f"{item.resolve()}\n")
            print(f"\n✅ Full results saved to:\n   👉 {final_search_file}\n")
        except Exception as e:
            print(f"\n❌ Failed to save search results: {e}")
                    
        return

    # ==========================
    # MODE 2: SCAN DIRECTORY
    # ==========================
    out_dir_path = Path(args.outdir).resolve() if args.outdir else Path.cwd()
    out_dir_path.mkdir(parents=True, exist_ok=True)
    target_name = target_path.name or "root_dir"

    ext_map = {'md': '.md', 'txt': '.txt', 'image': '.png'}
    out_name = args.name or f"{target_name}_tree{ext_map[args.format]}"
    
    if not any(out_name.endswith(ext) for ext in ext_map.values()):
        out_name += ext_map[args.format]
        
    final_file = out_dir_path / out_name
    
    stats = {"dirs": 0, "files": 0}
    lines = scan_dir_lines(target_path, max_depth=args.depth, show_hidden=args.show_hidden, excludes=args.exclude, stats=stats)
    
    sys.stdout.write(f"\r✅ Scan Complete! [ 📁 {stats['dirs']} dirs | 📄 {stats['files']} files ]           \n")
    sys.stdout.flush()
    
    root_name = target_path.name or str(target_path)
    tree_text = f"{root_name}/\n" + "\n".join(lines) + f"\n\n[ 📁 {stats['dirs']} directories, 📄 {stats['files']} files ]"
    
    success = False
    if args.format == 'md':
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(f"# 📁 Directory Structure Stats: `{target_path}`\n\n```text\n{tree_text}\n```\n")
        success = True
    elif args.format == 'txt':
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(tree_text + "\n")
        success = True
    elif args.format == 'image':
        success = create_image_from_text(tree_text, final_file, len(lines))
            
    if success:
        print(f"🎉 SUCCESS! Directory structure saved to:\n   👉 {final_file}\n")