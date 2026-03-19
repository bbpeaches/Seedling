from seedling.core.filesystem import get_full_context, ScanConfig
from seedling.core.io import get_dynamic_fence
from seedling.core.logger import logger

def run_full(args, target_path, config: ScanConfig):
    logger.info(f"\n🚀 Power Mode Enabled! Gathering file contents...")
    if args.format == 'image':
        logger.warning("Power Mode cannot be exported as an image. Defaulting to Markdown (.md).")

    context_list = get_full_context(target_path, config)
    
    sections = ["\n\n" + "="*60, "📁 FULL PROJECT CONTENT", "="*60 + "\n"]
    for rel_path, content in context_list:
        sections.append(f"### FILE: {rel_path}")
        lang = rel_path.suffix.lstrip('.')
        
        fence = get_dynamic_fence(content)
        sections.append(f"{fence}{lang}\n{content}\n{fence}\n")
        
    logger.info(f"✅ Aggregated {len(context_list)} files.")
    return "\n".join(sections)