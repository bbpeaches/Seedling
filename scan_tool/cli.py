import argparse
import sys
import textwrap
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
from .exporter import create_image_from_text
from .utils import SmartArgumentParser, handle_empty_run, handle_path_error, ask_yes_no
from .builder import build_structure_from_file
from .scanner import scan_dir_lines, search_items, is_text_file

try:
    __version__ = version("Seedling") 
except PackageNotFoundError:
    __version__ = "dev" 

def build_entry():
    if len(sys.argv) == 1:
        from .utils import handle_empty_build_run
        handle_empty_build_run()

    parser = argparse.ArgumentParser(
        description="🏗️ Build directory structure from a tree blueprint",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("file", help="The source tree file (.txt or .md)")
    parser.add_argument("target", nargs="?", default=None, help="Where to build the structure (default: current dir)")
    parser.add_argument("-v", "--version", action="version", version=f"Seedling v{__version__}")
    parser.add_argument("-d", "--direct", action="store_true", help="Directly create the path without prompting (auto-detects file/folder)")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--check", action="store_true", help="Dry-run: Check what is missing before building")
    group.add_argument("-f", "--force", action="store_true", help="Force overwrite existing files")

    args = parser.parse_args()
    source_file = Path(args.file).resolve()
    
    if args.direct:
        if not source_file.suffix:
            source_file.mkdir(parents=True, exist_ok=True)
            print(f"✅ Successfully created directory: {source_file}")
        else:
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.touch(exist_ok=True)
            print(f"✅ Successfully created file: {source_file}")
        sys.exit(0)

    target_provided = args.target is not None
    target_dir = Path(args.target).resolve() if target_provided else Path(".").resolve()
    
    if not source_file.exists():
        print(f"\n❌ ERROR: Blueprint file '{args.file}' does not exist.")
        
        if target_provided:
            sys.exit(1)
            
        if ask_yes_no(f"👉 Did you mean to directly create this path as a file/folder instead? [y/n]: "):
            if not source_file.suffix:
                source_file.mkdir(parents=True, exist_ok=True)
                print(f"✅ Successfully created directory: {source_file}")
            else:
                source_file.parent.mkdir(parents=True, exist_ok=True)
                source_file.touch(exist_ok=True)
                print(f"✅ Successfully created file: {source_file}")
            sys.exit(0)
        else:
            sys.exit(1)
            
    build_structure_from_file(source_file, target_dir, check_mode=args.check, force_mode=args.force)
  
def main():
    if len(sys.argv) == 1:
        handle_empty_run()
    
    parser = SmartArgumentParser(
        description=f"🌲 Seedling (v{__version__})",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("target", nargs="?", default=".", help="Target directory for scanning or searching")
    parser.add_argument("-v", "--version", action="version", version=f"Seedling v{__version__}")
    parser.add_argument("-f", "--find", type=str, help="FIND MODE: Search items (Exact & Fuzzy)")
    parser.add_argument("-F", "--format", choices=["md", "txt", "image"], default="md", help="Output format")
    parser.add_argument("-n", "--name", help="Custom output filename")
    parser.add_argument("-o", "--outdir", help="Output directory path")
    parser.add_argument("-s", "--show-hidden", action="store_true", help="Include hidden files")
    parser.add_argument("-d", "--depth", type=int, default=None, help="Maximum recursion depth")
    parser.add_argument("-e", "--exclude", nargs="+", default=[], help="Files/directories to exclude")
    parser.add_argument("--full", action="store_true", help="POWER MODE: Gather full content")
    
    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    if not target_path.exists() or not target_path.is_dir():
        handle_path_error(args.target)

    # ==========================
    # MODE 1: SEARCH (-f / --find)
    # ==========================
    if args.find:
        exact, fuzzy = search_items(target_path, args.find, args.show_hidden, args.exclude)
        all_matches = exact + fuzzy
        
        def format_item(item):
            prefix = "[DIR] 📁" if item.is_dir() else "📄"
            rel = item.relative_to(target_path) if target_path in item.parents else item
            return f"{prefix} {rel}"

        if exact:
            print(f"\n🎯 Exact matches for '{args.find}':")
            for item in exact[:20]: print(f" {format_item(item)}")
        else:
            print(f"\n❓ No exact matches found for '{args.find}'.")

        if fuzzy:
            print(f"\n💡 Did you mean one of these? (Fuzzy matches):")
            for item in fuzzy[:10]: print(f" {format_item(item)}")

        if not all_matches:
            print("\n❌ No matches found. Aborting document generation.")
            return

        append_full = False
        if args.full:
            if ask_yes_no(f"\n🚀 Power Mode triggered! Do you want to append the full source code for these {len(all_matches)} matches? [y/n]: "):
                append_full = True
            else:
                print("Skipping full source code appending.")

        out_dir = Path(args.outdir).resolve() if args.outdir else Path.cwd()
        target_name = target_path.name or "root"
        search_filename = args.name or f"{target_name}_search_{args.find}.md"
        final_search_file = out_dir / search_filename

        highlights = set(all_matches)
        stats = {"dirs": 0, "files": 0}
        lines = scan_dir_lines(target_path, max_depth=args.depth, show_hidden=args.show_hidden, excludes=args.exclude, stats=stats, highlights=highlights)
        sys.stdout.write(f"\r✅ Tree generation complete!                      \n")
        
        tree_text = f"{target_path.name}/\n" + "\n".join(lines)

        try:
            with open(final_search_file, 'w', encoding='utf-8') as f:
                f.write(f"# Search Results for '{args.find}' in `{target_path}`\n\n")
                
                f.write("============================================================\n")
                f.write("📁 MATCHED SOURCE FILES (SUMMARY)\n")
                f.write("============================================================\n\n")
                for m in exact: f.write(f"- 🎯 [EXACT] {m.relative_to(target_path)}\n")
                for m in fuzzy: f.write(f"- 💡 [FUZZY] {m.relative_to(target_path)}\n")
                
                f.write("\n\n============================================================\n")
                f.write("🌲 PROJECT TREE (WITH HIGHLIGHTS)\n")
                f.write("============================================================\n\n")
                f.write(f"```text\n{tree_text}\n```\n\n")
                
                if append_full:
                    f.write("============================================================\n")
                    f.write("📁 MATCHED SOURCE FILES (FULL CONTEXT)\n")
                    f.write("============================================================\n\n")
                    for m in all_matches:
                        if m.is_file() and is_text_file(m):
                            f.write(f"### FILE: {m.relative_to(target_path)}\n")
                            lang = m.suffix.lstrip('.')
                            f.write(f"```{lang}\n{m.read_text(encoding='utf-8', errors='replace')}\n```\n\n")

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
    out_name = args.name or f"{target_name}{ext_map[args.format]}"
    
    if not any(out_name.endswith(ext) for ext in ext_map.values()):
        out_name += ext_map[args.format]
        
    final_file = out_dir_path / out_name
    
    stats = {"dirs": 0, "files": 0}
    lines = scan_dir_lines(target_path, max_depth=args.depth, show_hidden=args.show_hidden, excludes=args.exclude, stats=stats)
    
    sys.stdout.write(f"\r✅ Scan Complete! [ 📁 {stats['dirs']} dirs | 📄 {stats['files']} files ]           \n")
    sys.stdout.flush()
    
    root_name = target_path.name or str(target_path)
    tree_text = f"{root_name}/\n" + "\n".join(lines) + f"\n\n[ 📁 {stats['dirs']} directories, 📄 {stats['files']} files ]"
    
    full_content = ""
    if args.full:
        from .scanner import get_full_context
        print(f"\n🚀 Power Mode Enabled! Gathering file contents...")
        if args.format == 'image':
            print("⚠️  WARNING: Power Mode cannot be exported as an image. Defaulting to Markdown (.md).")
            args.format = 'md'
            final_file = final_file.with_suffix('.md')

        context_list = get_full_context(target_path, args.show_hidden, args.exclude)
        sections = ["\n\n" + "="*60, "📁 FULL PROJECT CONTENT", "="*60 + "\n"]
        for rel_path, content in context_list:
            sections.append(f"### FILE: {rel_path}")
            lang = rel_path.suffix.lstrip('.')
            sections.append(f"```{lang}\n{content}\n```\n")
        full_content = "\n".join(sections)
        print(f"\n✅ Aggregated {len(context_list)} files.")

    success = False
    if args.format == 'md':
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(f"# 📁 Directory Structure Stats: `{target_path}`\n\n```text\n{tree_text}\n```\n")
            f.write(full_content)
        success = True
    elif args.format == 'txt':
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(tree_text + "\n")
            f.write(full_content)
        success = True
    elif args.format == 'image':
        success = create_image_from_text(tree_text, final_file, len(lines))
            
    if success:
        print(f"🎉 SUCCESS! Directory structure saved to:\n   👉 {final_file}\n")