from pathlib import Path
import sys
from seedling.core.logger import logger
from seedling.core.ui import ask_yes_no
from seedling.core.io import is_safe_path

def _read_ignore_rules(file_path: Path, rules_list: list):
    """读取并加入过滤规则列表"""
    logger.info(f"📄 Reading exclusion rules from: {file_path.name}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 统一为 POSIX 路径格式
                    clean_rule = line.replace('\\', '/').strip()
                    rules_list.append(clean_rule)
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")

def expand_excludes(raw_excludes: list) -> list:
    """智能解析 exclude 参数"""
    expanded_excludes = []
    current_work_dir = Path.cwd()
    
    for item in raw_excludes:
        item_path = Path(item)
        has_ignore_keyword = 'ignore' in item.lower()

        if item_path.is_file():
            # 执行安全拦截
            if not is_safe_path(item_path, current_work_dir):
                logger.warning(f"🚫 Security Block: Exclude file '{item}' is outside safe boundary. Skipping.")
                expanded_excludes.append(item)
                continue
            
            # 如果是 ignore 文件直接读，否则询问
            if has_ignore_keyword:
                _read_ignore_rules(item_path, expanded_excludes)
            else:
                prompt = f"❓ File '{item}' found. Read exclusion rules from it? (Select 'n' to treat as a glob string) [y/n]: "
                if ask_yes_no(prompt):
                    _read_ignore_rules(item_path, expanded_excludes)
                else:
                    expanded_excludes.append(item)
        else:
            # 处理不存在但带 ignore 的路径，猜测意图
            if has_ignore_keyword:
                possible_files = [
                    f for f in Path.cwd().iterdir() 
                    if f.is_file() and item.lower() in f.name.lower()
                ]
                if possible_files:
                    guess_file = possible_files[0] 
                    prompt = f"❓ Could not find '{item}', but found '{guess_file.name}'. Read rules from it? [y/n]: "
                    if ask_yes_no(prompt):
                        _read_ignore_rules(guess_file, expanded_excludes)
                    else:
                        expanded_excludes.append(item)
                else:
                    expanded_excludes.append(item)
            else:
                # 普通 glob 字符串处理
                clean_item = item.replace('\\', '/').strip()
                expanded_excludes.append(clean_item)
                
    return expanded_excludes