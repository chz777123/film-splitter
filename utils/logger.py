import logging
import sys
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 日志文件存储目录：项目根目录下的 logs/ 文件夹
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

def setup_logger(name="film_splitter"):
    """
    配置并返回一个标准化的 logger。
    同时输出到控制台和日志文件。
    日志文件按日期命名，单个文件最大 5MB，最多保留 10 个历史文件。
    """
    logger = logging.getLogger(name)
    
    # 如果已经配置过，避免重复添加 handler
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s.%(module)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # ── 控制台输出 (INFO 及以上) ──
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # ── 文件输出 (DEBUG 全量记录) ──
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # 按日期命名日志文件
        today = datetime.now().strftime("%Y-%m-%d")
        log_filepath = os.path.join(LOG_DIR, f"film_splitter_{today}.log")
        
        # RotatingFileHandler: 单文件最大 5MB，保留最近 10 个备份
        file_handler = RotatingFileHandler(
            log_filepath,
            maxBytes=5 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Log file initialized: {log_filepath}")
        
    return logger

# 提供一个默认的全局 logger 实例
logger = setup_logger()
