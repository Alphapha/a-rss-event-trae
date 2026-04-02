#!/bin/bash
# GitHub Trending 数据服务 - 停止脚本

set -e

echo "=========================================="
echo "停止 GitHub Trending 数据服务"
echo "=========================================="

# 检查 docker-compose 是否运行
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  服务未运行"
    exit 0
fi

# 停止服务
echo "🛑 正在停止服务..."
docker-compose down

echo ""
echo "✅ 服务已停止"
echo ""
echo "📝 提示:"
echo "  - 数据文件保存在 ./data 目录"
echo "  - 日志文件保存在 ./logs 目录"
echo "  - 重新启动：./start.sh"
