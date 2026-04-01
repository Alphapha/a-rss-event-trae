"""
数据库模型定义
按照研究文档设计，包含以下表：
- repository: GitHub 仓库信息
- repository_snapshot: 仓库历史快照（保留每次爬取的数据）
- crawl_jobs: 爬取任务记录
- articles: 生成的文章
- article_repos: 文章与仓库的关联
- push_logs: 推送日志
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Enum, Float, Boolean, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

Base = declarative_base()


class WindowType(enum.Enum):
    """时间窗口类型"""
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class Repository(Base):
    """
    GitHub 仓库基本信息表
    存储仓库的当前状态，会随每次爬取更新
    """
    __tablename__ = "repository"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_full_name = Column(String(255), unique=True, nullable=False, index=True)  # owner/name
    owner = Column(String(100), nullable=False)
    repo_name = Column(String(150), nullable=False)
    description = Column(Text)
    language = Column(String(50))
    homepage = Column(String(255))
    
    # 当前状态
    total_stars = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index('idx_repo_owner', 'owner', 'repo_name'),
        Index('idx_language', 'language'),
    )
    
    def __repr__(self):
        return f"<Repository {self.repo_full_name}>"


class RepositorySnapshot(Base):
    """
    仓库历史快照表
    每次爬取都会 insert 新记录，保留历史数据
    用于分析排名变化、stars 增长趋势
    """
    __tablename__ = "repository_snapshot"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, nullable=False, index=True)  # 关联 repository.id
    window_type = Column(Enum(WindowType), nullable=False, index=True)  # daily/weekly/monthly
    snapshot_date = Column(DateTime, nullable=False, index=True)  # 快照日期
    
    # 排名信息
    ranking = Column(Integer)  # 在榜单中的排名
    
    # Stars 信息
    stars_gained = Column(Integer, default=0)  # 增量（今日/本周/本月）
    total_stars = Column(Integer, default=0)  # 总 stars
    
    # 其他快照数据
    forks_count = Column(Integer, default=0)
    language = Column(String(50))
    description = Column(Text)
    
    # 原始 HTML 片段（用于 debug）
    raw_html_snippet = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 联合唯一索引：同一窗口类型 + 同一天 + 同一仓库只有一条记录
    __table_args__ = (
        UniqueConstraint('window_type', 'snapshot_date', 'repo_id', name='uix_window_date_repo'),
        Index('idx_snapshot_ranking', 'window_type', 'snapshot_date', 'ranking'),
    )
    
    def __repr__(self):
        return f"<RepositorySnapshot {self.repo_id} {self.window_type.value} {self.snapshot_date}>"


class CrawlJob(Base):
    """
    爬取任务记录表
    记录每次爬取任务的执行情况
    """
    __tablename__ = "crawl_jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    window_type = Column(Enum(WindowType), nullable=False, index=True)  # 任务类型
    status = Column(String(20), default="running")  # running/success/failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 统计信息
    repos_discovered = Column(Integer, default=0)  # 发现多少 repo
    new_repos_count = Column(Integer, default=0)  # 新增 repo 数量
    error_message = Column(Text)
    
    # 爬取的 URL
    crawled_url = Column(String(500))
    
    def __repr__(self):
        return f"<CrawlJob {self.window_type.value} {self.status}>"


class ArticleStatus(enum.Enum):
    """文章状态"""
    draft = "draft"
    reviewing = "reviewing"
    published = "published"
    failed = "failed"


class Article(Base):
    """
    生成的文章表
    存储 LLM 生成的文章内容
    """
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    window_type = Column(Enum(WindowType), nullable=False)
    
    # 内容
    content_md = Column(Text)  # Markdown 原始内容
    content_html = Column(Text)  # HTML 渲染后内容
    wechat_media_id = Column(String(100))  # 微信素材库 ID
    
    # 状态
    status = Column(Enum(ArticleStatus), default=ArticleStatus.draft)
    
    # 时间范围
    date_from = Column(DateTime)
    date_to = Column(DateTime)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Article {self.title}>"


class ArticleRepo(Base):
    """
    文章与仓库的关联表（多对多）
    记录每篇文章选了哪些 repo、排名第几
    """
    __tablename__ = "article_repos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, nullable=False, index=True)
    repo_id = Column(Integer, nullable=False, index=True)
    ranking_in_article = Column(Integer)  # 在文章中的排序
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint('article_id', 'repo_id', name='uix_article_repo'),
    )
    
    def __repr__(self):
        return f"<ArticleRepo article={self.article_id} repo={self.repo_id}>"


class PushLog(Base):
    """
    推送日志表
    记录每次推送的完整请求/响应
    """
    __tablename__ = "push_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, nullable=False, index=True)
    
    # 请求信息
    request_url = Column(String(500))
    request_body = Column(Text)
    
    # 响应信息
    response_status = Column(Integer)
    response_body = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PushLog article={self.article_id} status={self.response_status}>"


def init_db(database_url: str = "sqlite:///github_trending.db"):
    """
    初始化数据库，创建所有表
    
    Args:
        database_url: 数据库连接 URL，默认使用 SQLite
        
    Returns:
        engine: SQLAlchemy 引擎
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_db_session(engine):
    """
    获取数据库会话
    
    Args:
        engine: SQLAlchemy 引擎
        
    Returns:
        session: SQLAlchemy 会话
    """
    Session = sessionmaker(bind=engine)
    return Session()
