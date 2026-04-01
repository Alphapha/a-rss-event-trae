# GitHub 热点自动化系统

> 从数据爬取、AI 智能梳理、自动排版出文，到微信公众号矩阵推送的一站式解决方案

## 项目简介

本项目是一个全自动化 GitHub 热点内容运营系统，实现从 GitHub Trending 数据抓取到微信公众号推文发布的完整自动化流程。

### 核心特性

- 🕸️ **稳定数据获取**：模块化爬虫设计，支持每日/每周/每月数据抓取
- 📊 **历史数据追踪**：完整的快照机制，保留每次爬取的全部数据
- 🧠 **AI 智能处理**：自动梳理、总结、排版生成推文
- 🚀 **自动推送**：微信公众号自动发布
- 📈 **数据分析**：趋势分析、热度追踪、可视化报表

## 当前状态

✅ **数据获取模块已完成**

- 爬虫模块：支持 GitHub Trending 数据抓取
- 数据库模块：SQLite/PostgreSQL/MySQL 支持
- 定时任务：支持 daily/weekly/monthly 三种窗口
- 异常处理：自动重试、失败告警、详细日志

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件配置数据库和代理
```

### 3. 运行爬虫

```bash
# 爬取每日热门
python crawl.py daily

# 爬取每周热门
python crawl.py weekly

# 爬取每月热门
python crawl.py monthly
```

### 4. 配置定时任务

```bash
crontab -e
```

添加以下配置：

```cron
# 每天 07:15 爬取 daily 数据（为 08:00 推文做准备）
15 7 * * * cd /path/to/trae && python3 crawl.py daily

# 每天 07:20 爬取 weekly 数据
20 7 * * * cd /path/to/trae && python3 crawl.py weekly

# 每天 07:25 爬取 monthly 数据
25 7 * * * cd /path/to/trae && python3 crawl.py monthly
```

## 项目结构

```
trae/
├── src/                        # 源代码目录
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
│   └── crawler_task.py         # 爬虫调度脚本
├── crawl.py                    # 主入口
├── run_crawler.sh              # Cron 调度脚本
├── test_crawler.py             # 测试脚本
├── requirements.txt            # Python 依赖
├── .env.example                # 环境配置模板
├── DATA_CRAWLER_README.md      # 数据获取模块详细文档
└── README.md                   # 本文件
```

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

4. **articles** - 文章表（待实现）
   - 存储 LLM 生成的文章内容

5. **push_logs** - 推送日志表（待实现）
   - 记录每次推送的完整请求/响应

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

## 数据查询示例

### 查询今日热门 Top 10

```python
from sqlalchemy import create_engine, sessionmaker
from src.database.models import RepositorySnapshot, WindowType
from datetime import date

engine = create_engine("sqlite:///github_trending.db")
Session = sessionmaker(bind=engine)
session = Session()

today = date.today()
snapshots = session.query(RepositorySnapshot).filter(
    RepositorySnapshot.window_type == WindowType.daily,
    RepositorySnapshot.snapshot_date >= today
).order_by(RepositorySnapshot.ranking).limit(10).all()

for snap in snapshots:
    print(f"#{snap.ranking} - Repo {snap.repo_id} - Stars: +{snap.stars_gained}")
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

- **Debug 支持**：每次爬取都会保存原始 HTML 片段
- **异常处理**：如果解析失败，会生成 debug HTML 文件
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

### Q3: 国内服务器访问超时

**原因**：GitHub 在国内访问不稳定

**解决方法**：
1. **推荐**：使用海外云服务器（新加坡/香港）
2. 配置 HTTP 代理
3. 增加超时时间 `CRAWL_TIMEOUT=60`

## 路线图

- [x] 数据获取模块
  - [x] GitHub 爬虫实现
  - [x] 数据库模型设计
  - [x] 数据持久化服务
  - [x] 定时任务配置
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

- **爬虫**: requests, BeautifulSoup4
- **数据库**: SQLAlchemy (支持 SQLite/PostgreSQL/MySQL)
- **定时任务**: Cron
- **日志**: Python logging
- **配置管理**: python-dotenv

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
