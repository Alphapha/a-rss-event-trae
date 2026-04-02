#!/bin/bash
# GitHub Trending 数据服务 - 启动脚本

set -e

echo "=========================================="
echo "GitHub Trending 数据服务"
echo "=========================================="

# 检查是否安装了 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误：未找到 Docker，请先安装 Docker"
    exit 1
fi

# 检查是否安装了 docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误：未找到 docker-compose，请先安装 docker-compose"
    exit 1
fi

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从模板复制..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请根据需要修改配置"
fi

# 创建必要的目录
mkdir -p data logs

# 启动服务
echo ""
echo "🚀 正在启动 Docker 服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ 服务启动成功！"
    echo ""
    echo "📊 服务信息:"
    echo "  - API 文档：http://localhost:8000/docs"
    echo "  - 健康检查：http://localhost:8000/health"
    echo "  - 数据目录：$(pwd)/data"
    echo "  - 日志目录：$(pwd)/logs"
    echo ""
    echo "📝 常用命令:"
    echo "  查看日志：docker-compose logs -f"
    echo "  停止服务：docker-compose down"
    echo "  重启服务：docker-compose restart"
    echo "  查看状态：docker-compose ps"
else
    echo ""
    echo "❌ 服务启动失败，请查看日志："
    docker-compose logs
    exit 1
fi
