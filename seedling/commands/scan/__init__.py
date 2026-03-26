import sys
from pathlib import Path
from seedling import __version__
from seedling.core.ui import handle_empty_run, setup_ui_theme
from seedling.core.io import handle_path_error
from seedling.core.logger import configure_logging
from seedling.core.logger import logger
from seedling.core.config import ScanConfig
from seedling.core.traversal import traverse_directory
from .exclude import expand_excludes

def setup_scan_parser(parser):
    """配置CLI参数"""
    parser.add_argument("--version", action="version", version=f"Seedling v{__version__}")
    parser.add_argument("target", nargs="?", default=".", help="Target directory for scanning or searching")
    parser.add_argument("-f", "--find", type=str, help="FIND MODE: Search items (Exact & Fuzzy)")
    parser.add_argument("-F", "--format", choices=["md", "txt", "image", "json"], default="md", help="Output format")
    parser.add_argument("-n", "--name", help="Custom output filename")
    parser.add_argument("-o", "--outdir", help="Output directory path")
    parser.add_argument("-d", "--depth", type=int, default=None, help="Maximum recursion depth")
    parser.add_argument("-e", "--exclude", nargs="+", default=[], help="Files/directories to exclude")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only show errors")
    parser.add_argument("--showhidden", dest="show_hidden", action="store_true", help="Include hidden files")
    parser.add_argument("--text", dest="text_only", action="store_true", help="Only scan text files (ignore binary/media)")
    parser.add_argument("--delete", action="store_true", help="Delete matched items (FIND MODE ONLY)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true",help="Preview deletions without executing (use with --delete)")
    parser.add_argument("--noemoji", dest="no_emoji", action="store_true", help="Disable emojis for legacy terminals")
    parser.add_argument("--include", nargs="+", default=[], help="Only include files/directories matching patterns")
    parser.add_argument("-t", "--type", type=str, default=None,help="Filter by file type (py/js/ts/cpp/go/java/rs/web/json/yaml/md/shell/all)")
    parser.add_argument("--regex", action="store_true", help="Treat -f pattern as regular expression")
    grep_group = parser.add_argument_group("Grep Mode (Content Search)")
    grep_group.add_argument("-g", "--grep", type=str, default=None, dest="grep_pattern",help="Search inside file contents")
    grep_group.add_argument("-C", "--context", type=int, default=0,help="Show N lines of context around grep matches")
    grep_group.add_argument("-i", "--ignore-case", action="store_true",help="Case-insensitive search (default is case-sensitive)")
    parser.add_argument("--analyze", action="store_true", help="Analyze project structure and dependencies")

    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument("--full", action="store_true", help="POWER MODE: Gather full text content of scanned files.")
    output_mode.add_argument("--skeleton", action="store_true", help="[Experimental] AST Code Skeleton extraction.")
    
def handle_scan(args):
    """核心调度逻辑"""
    configure_logging(args.verbose, args.quiet)
    setup_ui_theme(args.no_emoji)

    # 拦截依赖缺失
    if args.format == "image":
        try:
            import PIL # type: ignore
        except ImportError:
            print("\nERROR: 'Pillow' is required for image export.\nFix: pip install Pillow")
            sys.exit(1)

    # 拦截无参调用
    if args.target == "." and len(sys.argv) <= 1:
        handle_empty_run()
        return

    # 校验目标路径
    target_path = Path(args.target).resolve()
    if not target_path.exists() or not target_path.is_dir():
        handle_path_error(args.target)

    if args.exclude:
        args.exclude = expand_excludes(args.exclude)

    # 参数组装
    config = ScanConfig(
        max_depth=args.depth,
        show_hidden=args.show_hidden,
        excludes=args.exclude,
        includes=getattr(args, 'include', []),
        file_type=getattr(args, 'type', None),
        text_only=args.text_only or getattr(args, 'grep_pattern', None) is not None, # 开启 Grep 时强制限制为纯文本模式
        quiet=args.quiet,
        use_regex=getattr(args, 'regex', False)
    )

    needs_content = args.full or getattr(args, 'grep_pattern', None) or args.analyze or getattr(args, 'skeleton', False)

    if not args.quiet:
        logger.info(f"\n🌲 Scanning directory structure in '{target_path.name}'...")

    # 统一DFS 
    traversal_result = traverse_directory(target_path, config, collect_content=needs_content)

    if not args.quiet:
        sys.stdout.write(f"\r✅ Scan Complete! [ {traversal_result.stats['dirs']} dirs | {traversal_result.stats['files']} files ]            \n")
        sys.stdout.flush()

    # 路由分发
    if args.analyze:
        from .analyzer import run_analyze
        run_analyze(args, target_path, config, traversal_result) 
        return

    if getattr(args, 'grep_pattern', None):
        from .grep import run_grep
        run_grep(args, target_path, config, traversal_result) 
        return

    if getattr(args, 'skeleton', False):
        from .skeleton import run_skeleton, check_skeleton_support
        if check_skeleton_support():
            run_skeleton(args, target_path, config, traversal_result) 
        return

    if args.find:
        from .search import run_search
        run_search(args, target_path, config, traversal_result) 
    else:
        from .explorer import run_explorer
        run_explorer(args, target_path, config, traversal_result)