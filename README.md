# GitHub 热点自动化系统 - 数据服务

> 提供 GitHub Trending 数据爬取、存储和查询的 RESTful API 服务

## 项目简介

本项目是一个**独立的后台数据服务**，提供 GitHub Trending 数据的自动爬取、持久化存储和 RESTful API 查询功能。支持 Docker 一键部署，内置定时任务调度器，可自动执行爬取任务。

### 核心特性

- 🚀 **RESTful API**：提供完整的数据库操作接口
- ⏰ **自动定时任务**：内置 APScheduler，自动执行爬取任务
- 🐳 **Docker 部署**：一键启动，开箱即用
- 📊 **历史数据追踪**：完整的快照机制，保留每次爬取的全部数据
- 🕸️ **稳定爬虫**：自动重试、代理支持、详细日志
- 📈 **数据统计**：实时统计接口，支持多维度查询

## 快速开始

### 方式一：Docker 部署（推荐）

#### 1. 克隆项目

```bash
git clone https://github.com/Alphapha/a-rss-event-trae.git
cd a-rss-event-trae
```

#### 2. 启动服务

```bash
# 一键启动
./start.sh
```

#### 3. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

### 方式二：本地运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件配置
```

#### 3. 启动服务

```bash
# 开发模式
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 4. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

## 项目结构

```
trae/
├── src/                        # 源代码目录
│   ├── main.py                 # FastAPI 应用主模块
│   ├── api/                    # API 路由模块
│   │   ├── __init__.py
│   │   └── routes.py           # RESTful API 接口
│   ├── crawler/                # 爬虫模块
│   │   ├── __init__.py
│   │   └── github_crawler.py   # GitHub 爬虫实现
│   ├── database/               # 数据库模块
│   │   ├── __init__.py
│   │   ├── models.py           # 数据库模型
│   │   ├── repository_service.py # 数据服务层
│   │   └── persistence_service.py # 持久化服务
│   ├── utils/                  # 工具模块
│   │   ├── __init__.py
│   │   ├── logger.py           # 日志工具
│   │   └── config.py           # 配置工具
│   ├── scheduler.py            # 定时任务调度器
│   └── crawler_task.py         # 爬虫任务
├── Dockerfile                  # Docker 镜像构建文件
├── docker-compose.yml          # Docker Compose 配置
├── requirements.txt            # Python 依赖
├── .env.example                # 环境配置模板
├── start.sh                    # 启动脚本
├── stop.sh                     # 停止脚本
└── README.md                   # 本文件
```

## API 接口

### 主要接口

#### 1. 仓库查询

```bash
# 获取仓库列表
GET /api/v1/repositories?skip=0&limit=25&language=Python

# 获取单个仓库详情
GET /api/v1/repositories/{repo_id}

# 获取仓库历史快照
GET /api/v1/repositories/{repo_id}/snapshots?days=7
```

#### 2. 快照查询

```bash
# 查询快照数据
GET /api/v1/snapshots?window_type=daily&date_from=2024-01-01&limit=25
```

#### 3. 爬取任务

```bash
# 获取爬取任务列表
GET /api/v1/jobs?limit=20&status=success

# 手动触发爬取任务
POST /api/v1/crawl
{
  "window_type": "daily"
}
```

#### 4. 统计信息

```bash
# 获取数据库统计
GET /api/v1/stats
```

### API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 数据库设计

### 核心表

1. **repository** - 仓库基本信息表
   - 存储仓库当前状态，会随爬取更新

2. **repository_snapshot** - 历史快照表（核心）
   - 每次爬取都 insert 新记录，保留历史数据
   - 用于分析排名变化、stars 增长趋势

3. **crawl_jobs** - 爬取任务记录表
   - 记录每次爬取任务的执行情况
   - 便于运维和排查问题

## 配置说明

### 服务配置

```bash
# 服务端口
PORT=8000
HOST=0.0.0.0
```

### 数据库配置

#### SQLite（默认，推荐）
```bash
DB_TYPE=sqlite
SQLITE_DB_PATH=github_trending.db
```

#### PostgreSQL（生产环境）
```bash
DB_TYPE=postgresql
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=github_trending
```

### 定时任务配置

```bash
# 爬取时间（24 小时制，格式：HH:MM）
# 每天自动执行这三种类型的爬取
DAILY_CRAWL_TIME=07:15
WEEKLY_CRAWL_TIME=07:20
MONTHLY_CRAWL_TIME=07:25
```

### 网络配置

#### 使用代理（国内服务器推荐）
```bash
GITHUB_PROXY=http://username:password@proxy_host:proxy_port
```

#### 不使用代理（海外服务器）
```bash
# 注释掉或不设置
# GITHUB_PROXY=
```

## Docker 部署

### 一键部署

```bash
# 启动服务
./start.sh

# 查看日志
docker-compose logs -f

# 停止服务
./stop.sh

# 重启服务
docker-compose restart
```

### 使用 PostgreSQL（可选）

默认使用 SQLite，如需使用 PostgreSQL：

```bash
# 启动服务（包括 PostgreSQL）
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

### 数据持久化

- **数据库文件**：`./data/github_trending.db`
- **日志文件**：`./logs/`

Docker 会自动挂载这些目录到宿主机，确保数据安全。

## 数据查询示例

### 使用 API 查询

```bash
# 查询今日热门 Top 10
curl "http://localhost:8000/api/v1/snapshots?window_type=daily&limit=10"

# 查询某个仓库的历史
curl "http://localhost:8000/api/v1/repositories/1/snapshots?days=7"

# 获取统计信息
curl "http://localhost:8000/api/v1/stats"
```

### 使用 Python SDK

```python
import requests

# 查询今日热门 Top 10
response = requests.get("http://localhost:8000/api/v1/snapshots", params={
    "window_type": "daily",
    "limit": 10
})
snapshots = response.json()

for snap in snapshots:
    print(f"#{snap['ranking']} - Repo {snap['repo_id']} - Stars: +{snap['stars_gained']}")
```

## 注意事项

### 1. 网络配置

- **国内服务器**：强烈建议使用海外节点或配置代理
- **代理配置**：在 `.env` 中设置 `GITHUB_PROXY`
- **超时设置**：根据网络情况调整 `CRAWL_TIMEOUT`

### 2. GitHub 限流

- **自动频率控制**：每天只爬取 3 次，不会触发限流
- **429 错误**：如遇限流，请检查代理或降低频率
- **重试机制**：内置 3 次自动重试

### 3. 数据备份

- **SQLite**：定期备份 `./data/github_trending.db`
- **PostgreSQL**：使用 pg_dump 定期备份
- **Docker 卷**：不要删除 `./data` 和 `./logs` 目录

### 4. 资源占用

- **内存**：约 200-300MB
- **CPU**：爬取时会有短暂 CPU 使用
- **磁盘**：根据数据量，约 100MB-1GB

## 常见问题

### Q1: 服务启动失败

**原因**：端口被占用或 Docker 未安装

**解决方法**：
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

**原因**：触发 GitHub 限流

**解决方法**：
1. 配置代理：`GITHUB_PROXY=http://proxy:port`
2. 检查爬取频率
3. 等待一段时间后重试

### Q3: 数据库连接失败

**原因**：数据库配置错误或权限问题

**解决方法**：
1. 检查 `.env` 配置
2. 查看日志：`docker-compose logs`
3. 确保数据目录有写权限

### Q4: 定时任务未执行

**原因**：调度器未启动或配置错误

**解决方法**：
1. 查看日志确认调度器启动
2. 检查时间配置格式（HH:MM）
3. 确认时区设置正确

### Q5: API 返回 500 错误

**原因**：数据库异常或爬虫错误

**解决方法**：
1. 查看详细错误日志
2. 检查数据库连接
3. 重启服务：`docker-compose restart`

## 路线图

- [x] 数据获取模块
  - [x] GitHub 爬虫实现
  - [x] 数据库模型设计
  - [x] 数据持久化服务
  - [x] RESTful API 接口
  - [x] 定时任务调度器
  - [x] Docker 部署
- [ ] 监控告警
  - [ ] 爬取失败告警
  - [ ] 性能指标监控
  - [ ] 健康检查优化
- [ ] AI 处理模块
  - [ ] 智能梳理和总结
  - [ ] 文章自动生成
  - [ ] 代码片段解读
- [ ] 推送模块
  - [ ] 微信公众号对接
  - [ ] 自动发布
  - [ ] 推送日志
- [ ] 管理后台
  - [ ] 数据可视化
  - [ ] 任务管理
  - [ ] 趋势分析

## 技术栈

- **Web 框架**: FastAPI, Uvicorn
- **爬虫**: requests, BeautifulSoup4, lxml
- **数据库**: SQLAlchemy (支持 SQLite/PostgreSQL/MySQL)
- **定时任务**: APScheduler
- **容器化**: Docker, Docker Compose
- **日志**: Python logging
- **配置管理**: python-dotenv, pydantic-settings

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues
- 邮件：[your-email@example.com]

---

**注意**：本项目仅供学习交流使用，请遵守 GitHub 的使用条款和相关法律法规。
