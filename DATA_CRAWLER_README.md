# 数据获取模块使用说明

## 概述

数据获取模块是 GitHub 热点自动化系统的核心组件，负责从 GitHub Trending 页面稳定可靠地抓取热门仓库数据。

### 核心特性

- ✅ **模块化设计**：爬虫、数据库、工具分离，易于维护和扩展
- ✅ **历史快照**：保留每次爬取的完整数据，支持趋势分析
- ✅ **自动重试**：网络异常自动重试 3 次，提高稳定性
- ✅ **代理支持**：支持配置 HTTP 代理，解决国内访问问题
- ✅ **定时任务**：支持 daily/weekly/monthly 三种时间窗口
- ✅ **详细日志**：完整的爬取日志和错误追踪

## 快速开始

### 1. 安装依赖

```bash
cd /Users/ai/Documents/2026AI/a_github_event/trae
pip install -r requirements.txt
```

### 2. 配置环境

复制环境配置模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据需要配置：

```bash
# 数据库配置（默认使用 SQLite）
DB_TYPE=sqlite
SQLITE_DB_PATH=github_trending.db

# 代理配置（国内服务器建议配置）
# GITHUB_PROXY=http://127.0.0.1:7890

# 超时配置
CRAWL_TIMEOUT=30
```

### 3. 运行爬虫

#### 手动执行

```bash
# 爬取每日热门数据
python crawl.py daily

# 爬取每周热门数据
python crawl.py weekly

# 爬取每月热门数据
python crawl.py monthly
```

#### 使用定时任务

配置 crontab（推荐）：

```bash
crontab -e
```

添加以下配置：

```cron
# 每天 07:15 爬取 daily 数据
15 7 * * * cd /Users/ai/Documents/2026AI/a_github_event/trae && python3 crawl.py daily >> logs/crawler.log 2>&1

# 每天 07:20 爬取 weekly 数据
20 7 * * * cd /Users/ai/Documents/2026AI/a_github_event/trae && python3 crawl.py weekly >> logs/crawler.log 2>&1

# 每天 07:25 爬取 monthly 数据
25 7 * * * cd /Users/ai/Documents/2026AI/a_github_event/trae && python3 crawl.py monthly >> logs/crawler.log 2>&1
```

## 项目结构

```
trae/
├── src/
│   ├── __init__.py              # 包初始化
│   ├── crawler_task.py          # 爬虫调度主脚本
│   ├── crawler/
│   │   ├── __init__.py
│   │   └── github_crawler.py    # GitHub 爬虫实现
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py            # 数据库模型定义
│   │   ├── repository_service.py # 仓库数据服务
│   │   └── persistence_service.py # 数据持久化服务
│   └── utils/
│       ├── __init__.py
│       ├── logger.py            # 日志工具
│       └── config.py            # 配置工具
├── crawl.py                     # 主入口脚本
├── run_crawler.sh               # Cron 调度脚本
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境配置模板
└── .env                         # 环境配置（需创建）
```

## 数据库设计

### 核心表结构

#### 1. repository - 仓库基本信息表
存储仓库的当前状态，会随每次爬取更新

- `repo_full_name`: 仓库全名（owner/name）
- `owner`: 所有者
- `repo_name`: 仓库名
- `description`: 描述
- `language`: 编程语言
- `total_stars`: 总 stars 数
- `forks_count`: Fork 数量

#### 2. repository_snapshot - 仓库历史快照表
**核心表**：每次爬取都会 insert 新记录，保留历史数据

- `repo_id`: 关联 repository.id
- `window_type`: 窗口类型（daily/weekly/monthly）
- `snapshot_date`: 快照日期
- `ranking`: 排名
- `stars_gained`: stars 增量
- `total_stars`: 总 stars 数
- `raw_html_snippet`: 原始 HTML 片段（用于 debug）

**重要**：这张表使用联合唯一索引 `(window_type, snapshot_date, repo_id)`，确保同一窗口类型 + 同一天 + 同一仓库只有一条记录，但不会覆盖历史数据。

#### 3. crawl_jobs - 爬取任务记录表
记录每次爬取任务的执行情况

- `window_type`: 任务类型
- `status`: 状态（running/success/failed）
- `repos_discovered`: 发现的 repo 数量
- `new_repos_count`: 新增 repo 数量
- `error_message`: 错误信息

## 配置说明

### 数据库配置

#### SQLite（默认，推荐个人使用）
```bash
DB_TYPE=sqlite
SQLITE_DB_PATH=github_trending.db
```

#### PostgreSQL（推荐生产环境）
```bash
DB_TYPE=postgresql
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=github_trending
```

#### MySQL
```bash
DB_TYPE=mysql
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=github_trending
```

### 网络配置

#### 使用代理（国内服务器推荐）
```bash
#  HTTP 代理
GITHUB_PROXY=http://username:password@proxy_host:proxy_port

# SOCKS 代理
GITHUB_PROXY=socks5://username:password@proxy_host:proxy_port
```

#### 不使用代理（海外服务器）
```bash
# 注释掉或不设置 GITHUB_PROXY
# GITHUB_PROXY=
```

### 超时配置

```bash
# 请求超时时间（秒），默认 30 秒
CRAWL_TIMEOUT=30
```

## 数据查询示例

### 查询今日热门 Top 10

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import RepositorySnapshot, WindowType
from datetime import datetime, date

# 连接数据库
engine = create_engine("sqlite:///github_trending.db")
Session = sessionmaker(bind=engine)
session = Session()

# 获取今天的快照
today = date.today()
snapshots = session.query(RepositorySnapshot).filter(
    RepositorySnapshot.window_type == WindowType.daily,
    RepositorySnapshot.snapshot_date >= today
).order_by(RepositorySnapshot.ranking).limit(10).all()

# 打印结果
for snap in snapshots:
    print(f"#{snap.ranking} - {snap.repo_id} - Stars: +{snap.stars_gained}")
```

### 查询某仓库的历史排名变化

```python
from sqlalchemy import and_

repo_id = 1  # 仓库 ID
snapshots = session.query(RepositorySnapshot).filter(
    and_(
        RepositorySnapshot.repo_id == repo_id,
        RepositorySnapshot.window_type == WindowType.daily
    )
).order_by(RepositorySnapshot.snapshot_date.desc()).limit(30).all()

for snap in snapshots:
    print(f"{snap.snapshot_date}: 排名#{snap.ranking}, Stars: +{snap.stars_gained}")
```

## 注意事项

### 1. 网络稳定性

- **国内服务器**：强烈建议使用海外节点（新加坡/香港）或配置代理
- **重试机制**：已内置 3 次重试，但网络问题仍可能导致失败
- **失败告警**：建议配置监控，当爬取失败时及时通知

### 2. GitHub 限流

- **频率控制**：每天只爬取 3 次（07:15/07:20/07:25），不会触发限流
- **429 错误**：如果返回 429，说明触发限流，请降低爬取频率
- **User-Agent**：已配置标准浏览器 UA，不要随意修改

### 3. 数据存储

- **SQLite**：适合个人使用，单文件易备份
- **PostgreSQL/MySQL**：适合生产环境，支持高并发
- **定期备份**：建议每天备份数据库文件

### 4. HTML 结构变化

- **Debug 支持**：每次爬取都会保存原始 HTML 片段到 `raw_html_snippet` 字段
- **异常处理**：如果解析失败，会生成 `debug_YYYYMMDD_HHMMSS.html` 文件
- **及时更新**：关注 GitHub 页面结构变化，及时更新爬虫代码

## 常见问题

### Q1: 爬取失败，返回 429 错误

**原因**：触发 GitHub 限流

**解决方法**：
1. 检查爬取频率，不要过于频繁
2. 使用代理 IP
3. 等待一段时间后再试

### Q2: 爬取成功但解析失败

**原因**：GitHub 页面 HTML 结构变化

**解决方法**：
1. 查看生成的 `debug_*.html` 文件
2. 对比 HTML 结构和代码中的选择器
3. 更新 `_extract_repo_data` 方法中的选择器

### Q3: 数据库连接失败

**原因**：数据库配置错误或数据库服务未启动

**解决方法**：
1. 检查 `.env` 文件中的数据库配置
2. 确认数据库服务已启动
3. 检查数据库用户权限

### Q4: 国内服务器访问超时

**原因**：GitHub 在国内访问不稳定

**解决方法**：
1. **推荐**：使用海外云服务器（新加坡/香港）
2. 配置 HTTP 代理
3. 增加超时时间 `CRAWL_TIMEOUT=60`

### Q5: 如何查看爬取日志

**方法 1**：查看控制台输出
```bash
python crawl.py daily
```

**方法 2**：查看日志文件（如果使用 cron）
```bash
tail -f logs/crawler.log
```

**方法 3**：查询数据库中的 `crawl_jobs` 表
```sql
SELECT * FROM crawl_jobs ORDER BY created_at DESC LIMIT 10;
```

## 下一步

数据获取模块已完成，后续可以实现：

1. **AI 处理模块**：对爬取的数据进行智能梳理和总结
2. **文章生成模块**：自动生成微信公众号推文
3. **定时推送模块**：自动推送到微信公众号
4. **管理后台**：数据可视化和任务管理

## 技术支持

如有问题，请查看：
- 研究文档：`research/` 目录
- 日志文件：`logs/crawler.log`
- 数据库：使用 DB Browser for SQLite 查看数据
