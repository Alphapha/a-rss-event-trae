#!/usr/bin/env python3
"""
GitHub Trending 爬虫 - 主入口
支持命令行调用和定时任务
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.crawler_task import main

if __name__ == "__main__":
    main()
