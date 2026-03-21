import sys
from pathlib import Path
from seedling.core.filesystem import scan_dir_lines, ScanConfig
from seedling.core.io import create_image_from_text
from seedling.core.ui import ask_yes_no
from seedling.core.logger import logger
from .full import run_full
from .json_output import build_json_structure, write_json, build_json_with_contents

def run_explorer(args, target_path):
    out_dir_path = Path(args.outdir).resolve() if args.outdir else Path.cwd()
    out_dir_path.mkdir(parents=True, exist_ok=True)
    target_name = target_path.name or "root_dir"

    ext_map = {'md': '.md', 'txt': '.txt', 'image': '.png', 'json': '.json'}
    out_name = args.name or f"{target_name}{ext_map[args.format]}"

    if not any(out_name.endswith(ext) for ext in ext_map.values()):
        out_name += ext_map[args.format]

    final_file = out_dir_path / out_name

    if final_file.exists():
        logger.warning(f"NOTICE: Output file already exists:\n   {final_file}")
        if not ask_yes_no("Do you want to overwrite it? [y/n]: "):
            logger.info("Aborted. No changes were made.")
            return

    stats = {"dirs": 0, "files": 0}
    config = ScanConfig(
        max_depth=args.depth,
        show_hidden=args.show_hidden,
        excludes=args.exclude,
        includes=getattr(args, 'include', []),
        file_type=getattr(args, 'type', None),
        text_only=args.text_only,
        quiet=args.quiet
    )
    lines = scan_dir_lines(target_path, config, stats)
    
    if not args.quiet:
        sys.stdout.write(f"\rScan Complete! [ {stats['dirs']} dirs | {stats['files']} files ]            \n")
        sys.stdout.flush()

    root_name = target_path.name or str(target_path)
    tree_text = f"{root_name}/\n" + "\n".join(lines) + f"\n\n[ {stats['dirs']} directories, {stats['files']} files ]"

    full_content = ""
    if args.full:
        full_content = run_full(args, target_path, config)
        if args.format == 'image':
            args.format = 'md'
            final_file = final_file.with_suffix('.md')

    success = False
    if args.format == 'json':
        # NEW: JSON output mode
        if args.full and full_content:
            # Include file contents in JSON
            from seedling.core.filesystem import get_full_context
            contents = {str(p): c for p, c in get_full_context(target_path, config)}
            json_data = build_json_with_contents(target_path, config, stats, contents)
        else:
            json_data = build_json_structure(target_path, config, stats)
        success = write_json(json_data, final_file)
    elif args.format == 'md':
        with open(final_file, 'w', encoding='utf-8') as f:
            f.write(f"# Directory Structure Stats: `{target_path}`\n\n```text\n{tree_text}\n```\n")
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
        logger.info(f"SUCCESS! Directory structure saved to:\n   {final_file}\n")