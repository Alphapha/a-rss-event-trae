# GitHub Trending 数据服务 - 使用说明

## 概述

本项目已改造为**独立的后台数据服务**，提供以下功能：

✅ **RESTful API** - 完整的数据库操作接口
✅ **自动定时任务** - 内置 APScheduler，自动执行爬取
✅ **Docker 部署** - 一键启动，开箱即用
✅ **历史数据追踪** - 快照机制保留完整历史

## 快速部署

### 1. Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/Alphapha/a-rss-event-trae.git
cd a-rss-event-trae

# 一键启动
./start.sh
```

### 2. 测试服务

```bash
# 运行测试脚本
python test_api.py
```

### 3. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

## 主要 API 接口

### 仓库查询

```bash
# 获取仓库列表
curl "http://localhost:8000/api/v1/repositories?limit=25&language=Python"

# 获取单个仓库详情
curl "http://localhost:8000/api/v1/repositories/1"

# 获取仓库历史快照（最近 7 天）
curl "http://localhost:8000/api/v1/repositories/1/snapshots?days=7"
```

### 快照查询

```bash
# 查询快照数据
curl "http://localhost:8000/api/v1/snapshots?window_type=daily&limit=25"
```

### 爬取任务

```bash
# 获取爬取任务列表
curl "http://localhost:8000/api/v1/jobs?limit=20"

# 手动触发爬取任务
curl -X POST "http://localhost:8000/api/v1/crawl" \
  -H "Content-Type: application/json" \
  -d '{"window_type": "daily"}'
```

### 统计信息

```bash
# 获取数据库统计
curl "http://localhost:8000/api/v1/stats"
```

## 定时任务配置

默认每天自动执行三次爬取：

- **07:15** - 爬取 daily 数据
- **07:20** - 爬取 weekly 数据
- **07:25** - 爬取 monthly 数据

修改 `.env` 文件可调整时间：

```bash
DAILY_CRAWL_TIME=07:15
WEEKLY_CRAWL_TIME=07:20
MONTHLY_CRAWL_TIME=07:25
```

## Docker 管理命令

```bash
# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps

# 重启服务
docker-compose restart

# 停止服务
./stop.sh

# 重新启动
./start.sh
```

## 数据持久化

- **数据库文件**: `./data/github_trending.db`
- **日志文件**: `./logs/`

Docker 会自动挂载这些目录到宿主机，确保数据安全。

## 使用 PostgreSQL（可选）

默认使用 SQLite，如需使用 PostgreSQL：

```bash
# 启动 PostgreSQL
docker-compose --profile postgres up -d

# 修改 .env 配置
DB_TYPE=postgresql
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=github_trending

# 重启服务
docker-compose restart
```

## 常见问题

### Q1: 服务启动失败

**解决方法**:
```bash
# 检查端口占用
lsof -i :8000

# 修改端口
PORT=8080

# 检查 Docker
docker --version
docker-compose --version
```

### Q2: 爬取失败，返回 429 错误

**解决方法**:
1. 配置代理：`GITHUB_PROXY=http://proxy:port`
2. 检查爬取频率
3. 等待一段时间后重试

### Q3: API 返回 500 错误

**解决方法**:
1. 查看详细错误日志：`docker-compose logs`
2. 检查数据库连接
3. 重启服务：`docker-compose restart`

## 技术栈

- **Web 框架**: FastAPI, Uvicorn
- **爬虫**: requests, BeautifulSoup4, lxml
- **数据库**: SQLAlchemy (SQLite/PostgreSQL/MySQL)
- **定时任务**: APScheduler
- **容器化**: Docker, Docker Compose

## 项目结构

```
trae/
├── src/
│   ├── main.py                 # FastAPI 应用主模块
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # RESTful API 接口
│   ├── crawler/
│   │   ├── __init__.py
│   │   └── github_crawler.py   # GitHub 爬虫实现
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # 数据库模型
│   │   ├── repository_service.py
│   │   └── persistence_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py           # 日志工具
│   │   └── config.py           # 配置工具
│   ├── scheduler.py            # 定时任务调度器
│   └── crawler_task.py         # 爬虫任务
├── Dockerfile                  # Docker 镜像构建
├── docker-compose.yml          # Docker Compose 配置
├── requirements.txt            # Python 依赖
├── .env.example                # 环境配置模板
├── start.sh                    # 启动脚本
├── stop.sh                     # 停止脚本
├── test_api.py                 # API 测试脚本
└── README.md                   # 项目文档
```

## 下一步

1. **监控告警** - 添加爬取失败告警功能
2. **性能优化** - 优化数据库查询性能
3. **AI 处理** - 集成 LLM 进行数据分析和总结
4. **推送模块** - 对接微信公众号等平台

## 支持

如有问题，请查看：
- 完整文档：[README.md](README.md)
- API 文档：http://localhost:8000/docs
- 项目仓库：https://github.com/Alphapha/a-rss-event-trae
