"""
仓库数据服务层
负责数据的增删改查操作
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Dict, Optional
from .models import Repository, RepositorySnapshot, CrawlJob, WindowType


class RepositoryService:
    """
    仓库数据服务类
    提供仓库相关的数据库操作
    """
    
    def __init__(self, session: Session):
        """
        初始化服务
        
        Args:
            session: SQLAlchemy 会话
        """
        self.session = session
    
    def get_or_create_repository(self, repo_data: Dict) -> Repository:
        """
        获取或创建仓库记录
        
        Args:
            repo_data: 仓库数据字典，包含 repo_full_name, owner, repo_name 等
            
        Returns:
            Repository: 仓库对象
        """
        repo = self.session.query(Repository).filter_by(
            repo_full_name=repo_data["repo_full_name"]
        ).first()
        
        if repo is None:
            repo = Repository(
                repo_full_name=repo_data["repo_full_name"],
                owner=repo_data["owner"],
                repo_name=repo_data["repo_name"],
                description=repo_data.get("description", ""),
                language=repo_data.get("language", ""),
                homepage=repo_data.get("homepage", ""),
                total_stars=repo_data.get("total_stars", 0),
                forks_count=repo_data.get("forks_count", 0)
            )
            self.session.add(repo)
            self.session.flush()  # 获取 ID
        else:
            # 更新现有记录
            repo.description = repo_data.get("description", repo.description)
            repo.language = repo_data.get("language", repo.language)
            repo.homepage = repo_data.get("homepage", repo.homepage)
            repo.total_stars = repo_data.get("total_stars", repo.total_stars)
            repo.forks_count = repo_data.get("forks_count", repo.forks_count)
            repo.updated_at = datetime.utcnow()
        
        return repo
    
    def create_snapshot(self, repo_id: int, snapshot_data: Dict, window_type: WindowType, snapshot_date: datetime) -> RepositorySnapshot:
        """
        创建仓库快照记录（不覆盖，总是 insert）
        
        Args:
            repo_id: 仓库 ID
            snapshot_data: 快照数据
            window_type: 窗口类型
            snapshot_date: 快照日期
            
        Returns:
            RepositorySnapshot: 快照对象
        """
        snapshot = RepositorySnapshot(
            repo_id=repo_id,
            window_type=window_type,
            snapshot_date=snapshot_date,
            ranking=snapshot_data.get("ranking"),
            stars_gained=snapshot_data.get("stars_gained", 0),
            total_stars=snapshot_data.get("total_stars", 0),
            forks_count=snapshot_data.get("forks_count", 0),
            language=snapshot_data.get("language", ""),
            description=snapshot_data.get("description", ""),
            raw_html_snippet=snapshot_data.get("raw_html_snippet", "")
        )
        self.session.add(snapshot)
        return snapshot
    
    def create_crawl_job(self, window_type: WindowType, crawled_url: str) -> CrawlJob:
        """
        创建爬取任务记录
        
        Args:
            window_type: 窗口类型
            crawled_url: 爬取的 URL
            
        Returns:
            CrawlJob: 任务对象
        """
        job = CrawlJob(
            window_type=window_type,
            status="running",
            crawled_url=crawled_url
        )
        self.session.add(job)
        self.session.flush()
        return job
    
    def update_crawl_job_success(self, job: CrawlJob, repos_discovered: int, new_repos_count: int):
        """
        更新爬取任务为成功状态
        
        Args:
            job: 任务对象
            repos_discovered: 发现的 repo 数量
            new_repos_count: 新增 repo 数量
        """
        job.status = "success"
        job.completed_at = datetime.utcnow()
        job.repos_discovered = repos_discovered
        job.new_repos_count = new_repos_count
    
    def update_crawl_job_failed(self, job: CrawlJob, error_message: str):
        """
        更新爬取任务为失败状态
        
        Args:
            job: 任务对象
            error_message: 错误信息
        """
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        job.error_message = error_message
    
    def get_recent_snapshots(self, window_type: WindowType, days: int = 7) -> List[RepositorySnapshot]:
        """
        获取最近 N 天的快照数据
        
        Args:
            window_type: 窗口类型
            days: 天数
            
        Returns:
            List[RepositorySnapshot]: 快照列表
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        snapshots = self.session.query(RepositorySnapshot).filter(
            and_(
                RepositorySnapshot.window_type == window_type,
                RepositorySnapshot.snapshot_date >= cutoff_date
            )
        ).order_by(RepositorySnapshot.snapshot_date.desc()).all()
        
        return snapshots
    
    def get_trending_repos(self, window_type: WindowType, date: datetime, limit: int = 25) -> List[RepositorySnapshot]:
        """
        获取指定日期的热门仓库
        
        Args:
            window_type: 窗口类型
            date: 日期
            limit: 数量限制
            
        Returns:
            List[RepositorySnapshot]: 快照列表
        """
        snapshots = self.session.query(RepositorySnapshot).filter(
            and_(
                RepositorySnapshot.window_type == window_type,
                RepositorySnapshot.snapshot_date >= date,
                RepositorySnapshot.snapshot_date < date
            )
        ).order_by(RepositorySnapshot.ranking).limit(limit).all()
        
        return snapshots
    
    def commit(self):
        """提交事务"""
        self.session.commit()
    
    def rollback(self):
        """回滚事务"""
        self.session.rollback()
