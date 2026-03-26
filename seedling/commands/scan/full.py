from seedling.core.config import ScanConfig
from seedling.core.traversal import TraversalResult
from seedling.core.io import get_dynamic_fence
from seedling.core.logger import logger

def run_full(args, target_path, config: ScanConfig, result: TraversalResult):
    """遍历缓存并提取所有纯文本"""
    logger.info(f"\n🚀 Power Mode Enabled! Gathering file contents...")
    
    if args.format == 'image':
        logger.warning("Power Mode cannot be exported as an image. Defaulting to Markdown (.md).")

    sections = ["\n\n" + "="*60, "📁 FULL PROJECT CONTENT", "="*60 + "\n"] 
    extracted_count = 0
    
    for item in result.text_files:
        content = result.get_content(item, quiet=config.quiet)
        if content:
            sections.append(f"### FILE: {item.relative_path}")
            lang = item.path.suffix.lstrip('.')
            
            fence = get_dynamic_fence(content)
            sections.append(f"{fence}{lang}\n{content}\n{fence}\n")
            extracted_count += 1
            
    logger.info(f"✅ Aggregated {extracted_count} files.")
    return "\n".join(sections)