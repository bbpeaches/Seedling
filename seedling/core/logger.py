import sys
import logging

logger = logging.getLogger("seedling") # 全局共享的日志实例

class CLIFormatter(logging.Formatter):
    """终端输出定制日志格式化器"""
    
    def format(self, record):
        if record.levelno == logging.INFO:
            self._style._fmt = "%(message)s"
        elif record.levelno == logging.DEBUG:
            self._style._fmt = "[DEBUG] %(message)s"
        elif record.levelno == logging.WARNING:
            self._style._fmt = "⚠️  %(message)s"
        elif record.levelno == logging.ERROR:
            self._style._fmt = "❌ %(message)s"
            
        return super().format(record)

def configure_logging(verbose=False, quiet=False):
    """初始化并配置全局logger"""
    level = logging.INFO
    
    if verbose: 
        level = logging.DEBUG
    elif quiet: 
        level = logging.ERROR
    
    # 清除残留的处理器
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CLIFormatter())
    
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False  # 保持终端输出纯净