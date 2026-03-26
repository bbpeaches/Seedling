import sys
from pathlib import Path
from seedling.core.config import ScanConfig
from seedling.core.traversal import TraversalResult, build_tree_lines
from seedling.core.io import create_image_from_text, check_overwrite_safely
from seedling.core.logger import logger
from .full import run_full
from .json_output import build_json_structure, write_json, build_json_with_contents

def run_explorer(args, target_path: Path, config: ScanConfig, result: TraversalResult):
    """默认探索命令"""
    if args.outdir:
        out_dir_path = Path(args.outdir).resolve()
    else:
        out_dir_path = Path.cwd()
    
    out_dir_path.mkdir(parents=True, exist_ok=True)
    target_name = target_path.name or "root_dir"

    ext_map = {'md': '.md', 'txt': '.txt', 'image': '.png', 'json': '.json'} # 格式到扩展名的映射字典
    out_name = args.name or f"{target_name}{ext_map[args.format]}"
    
    # 带有对应的扩展名后缀
    if not any(out_name.endswith(ext) for ext in ext_map.values()):
        out_name += ext_map[args.format]

    final_file = out_dir_path / out_name
    if not check_overwrite_safely(final_file): 
        return 

    lines = build_tree_lines(result, config, root_path=target_path)
    
    root_name = target_path.name or str(target_path)
    tree_text = f"{root_name}/\n" + "\n".join(lines) + f"\n\n[ {result.stats['dirs']} directories, {result.stats['files']} files ]"

    full_content = ""
    if args.full:
        # 追加全量源码
        full_content = run_full(args, target_path, config, result)
        if args.format == 'image':
            args.format = 'md'
            final_file = final_file.with_suffix('.md')

    success = False
    if args.format == 'json':
        if args.full:
            json_data = build_json_with_contents(target_path, config, result)
        else:
            json_data = build_json_structure(target_path, config, result)
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