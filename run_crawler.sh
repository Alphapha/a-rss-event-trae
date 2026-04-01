#!/bin/bash
# GitHub Trending 爬虫 - Cron 调度脚本
# 按照研究文档设置的定时任务配置

# 设置项目根目录
PROJECT_DIR="/Users/ai/Documents/2026AI/a_github_event/trae"
PYTHON="python3"

# 切换到项目目录
cd "$PROJECT_DIR" || exit 1

# 获取当前时间
CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")

echo "=========================================="
echo "开始执行爬取任务 - $CURRENT_TIME"
echo "=========================================="

# 执行 daily 爬取（07:15）
if [ "$(date +%H:%M)" = "07:15" ]; then
    echo "[$CURRENT_TIME] 执行 daily 爬取..."
    $PYTHON crawl.py daily
    echo ""
fi

# 执行 weekly 爬取（07:20）
if [ "$(date +%H:%M)" = "07:20" ]; then
    echo "[$CURRENT_TIME] 执行 weekly 爬取..."
    $PYTHON crawl.py weekly
    echo ""
fi

# 执行 monthly 爬取（07:25）
if [ "$(date +%H:%M)" = "07:25" ]; then
    echo "[$CURRENT_TIME] 执行 monthly 爬取..."
    $PYTHON crawl.py monthly
    echo ""
fi

echo "=========================================="
echo "爬取任务执行完成"
echo "=========================================="
