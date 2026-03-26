import re
from pathlib import Path
from typing import List, Callable
from dataclasses import dataclass
from seedling.core.config import ScanConfig
from seedling.core.traversal import TraversalResult
from seedling.core.logger import logger
from seedling.core.io import check_overwrite_safely

@dataclass
class GrepMatch:
    """记录单次文本搜索命中"""
    file_path: Path              # 绝对路径
    relative_path: Path          # 相对路径
    line_number: int             # 具体行号
    line_content: str            # 命中行的完整文本内容
    context_before: List[str]    # 命中行上方的前置上下文文本
    context_after: List[str]     # 命中行下方的后置上下文文本

def grep_files(
    result: TraversalResult,
    pattern: str,
    config: ScanConfig,
    context: int = 0,
    ignore_case: bool = False
) -> List[GrepMatch]:
    """搜索关键词或正则"""
    matches: List[GrepMatch] = []
    
    if ignore_case:
        regex_flags = re.IGNORECASE
    else:
        regex_flags = 0

    if config.use_regex:
        try:
            compiled = re.compile(pattern, regex_flags)
            matcher: Callable[[str], bool] = lambda line: bool(compiled.search(line))
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return []
    else:
        if ignore_case:
            pattern_lower = pattern.lower()
            matcher = lambda line: pattern_lower in line.lower()
        else:
            matcher = lambda line: pattern in line

    for item in result.text_files:
        content = result.get_content(item, quiet=config.quiet)
        if not content:
            continue
            
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if matcher(line):
                # 动态计算上下文的截取边界
                start = max(0, i - context)
                end = min(len(lines), i + context + 1)
                
                matches.append(GrepMatch(
                    file_path=item.path,
                    relative_path=item.relative_path,
                    line_number=i + 1,
                    line_content=line,
                    context_before=lines[start:i],
                    context_after=lines[i + 1:end]
                ))

    return matches

def format_grep_output(matches: List[GrepMatch], show_context: bool) -> str:
    """格式化为纯文本"""
    lines = []
    for m in matches:
        if show_context:
            if m.context_before:
                for i, ctx in enumerate(m.context_before):
                    lines.append(f"  {m.line_number - len(m.context_before) + i}-\t{ctx}")
                
        lines.append(f">>> {m.relative_path}:{m.line_number}\t{m.line_content}")
        
        if show_context:
            if m.context_after:
                for i, ctx in enumerate(m.context_after):
                    lines.append(f"  {m.line_number + i + 1}-\t{ctx}")
    return "\n".join(lines)

def run_grep(args, target_path: Path, config: ScanConfig, result: TraversalResult):
    """Grep主控逻辑"""
    ignore_case = getattr(args, 'ignore_case', False)
    
    if ignore_case:
        case_mode = "case-insensitive"
    else:
        case_mode = "case-sensitive"
    
    logger.info(f"Searching for '{args.grep_pattern}' ({case_mode})...")
    matches = grep_files(result, args.grep_pattern, config, args.context, ignore_case)

    if not matches:
        logger.error("No matches found.")
        return

    # 统计命中的去重文件数
    unique_files = len(set(m.file_path for m in matches))
    logger.info(f"\nFound {len(matches)} matches in {unique_files} files:\n")
    print(format_grep_output(matches, args.context > 0))

    if args.full or args.format != 'md':
        if args.outdir:
            out_dir = Path(args.outdir).resolve()
        else:
            out_dir = Path.cwd()
            
        out_dir.mkdir(parents=True, exist_ok=True)
        
        if args.format == 'json':
            ext = '.json'
        else:
            ext = '.md'
            
        out_file = out_dir / f"{target_path.name}_grep{ext}"

        if not check_overwrite_safely(out_file):
            return

        if args.format == 'json':
            import json
            json_data = {
                "pattern": args.grep_pattern,
                "case_sensitive": not ignore_case,
                "target": str(target_path),
                "total_matches": len(matches),
                "files_matched": unique_files,
                "matches": [
                    {
                        "file": str(m.relative_path),
                        "line": m.line_number,
                        "content": m.line_content,
                        "context_before": m.context_before,
                        "context_after": m.context_after
                    }
                    for m in matches
                ]
            }
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        else:
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(f"# Grep Results: `{args.grep_pattern}`\n\n")
                f.write(f"**Target**: `{target_path}`\n\n")
                
                if ignore_case:
                    mode_str = 'Case-insensitive'
                else:
                    mode_str = 'Case-sensitive'
                    
                f.write(f"**Mode**: {mode_str}\n\n")
                f.write(f"**Stats**: {len(matches)} matches in {unique_files} files\n\n")
                f.write("```\n")
                f.write(format_grep_output(matches, args.context > 0))
                f.write("\n```\n")

        logger.info(f"\nResults saved to: {out_file}")