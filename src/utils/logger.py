"""
日志工具模块
提供统一的日志配置
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    获取配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别，默认为 INFO
        
    Returns:
        logging.Logger: 配置好的 Logger 对象
    """
    if level is None:
        level = logging.INFO
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 如果已经有处理器，不再添加
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    
    return logger
