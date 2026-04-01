"""
数据持久化服务
负责将爬取的数据保存到数据库
"""

from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session

from ..database.models import WindowType
from ..database.repository_service import RepositoryService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataPersistenceService:
    """
    数据持久化服务类
    处理爬取数据的入库逻辑
    """
    
    def __init__(self, session: Session):
        """
        初始化服务
        
        Args:
            session: SQLAlchemy 会话
        """
        self.session = session
        self.repo_service = RepositoryService(session)
    
    def save_crawl_data(self, repos_data: List[Dict], window_type: WindowType, crawl_job) -> Dict:
        """
        保存爬取数据到数据库
        
        Args:
            repos_data: 爬取的仓库数据列表
            window_type: 窗口类型
            crawl_job: 爬取任务对象
            
        Returns:
            Dict: 统计信息
        """
        stats = {
            "total": len(repos_data),
            "new_repos": 0,
            "updated_repos": 0,
            "snapshots_created": 0
        }
        
        snapshot_date = datetime.utcnow()
        
        try:
            for idx, repo_data in enumerate(repos_data, start=1):
                logger.debug(f"处理 {idx}/{len(repos_data)}: {repo_data['repo_full_name']}")
                
                # 获取或创建仓库记录
                repo = self.repo_service.get_or_create_repository(repo_data)
                
                # 判断是否为新仓库
                if repo.id and repo.created_at == repo.updated_at:
                    stats["new_repos"] += 1
                else:
                    stats["updated_repos"] += 1
                
                # 创建快照记录（总是 insert，保留历史）
                snapshot_data = {
                    "ranking": repo_data.get("ranking"),
                    "stars_gained": repo_data.get("stars_gained", 0),
                    "total_stars": repo_data.get("total_stars", 0),
                    "forks_count": repo_data.get("forks_count", 0),
                    "language": repo_data.get("language", ""),
                    "description": repo_data.get("description", ""),
                    "raw_html_snippet": repo_data.get("raw_html_snippet", "")
                }
                
                snapshot = self.repo_service.create_snapshot(
                    repo_id=repo.id,
                    snapshot_data=snapshot_data,
                    window_type=window_type,
                    snapshot_date=snapshot_date
                )
                stats["snapshots_created"] += 1
                
                logger.debug(f"创建快照：{repo.repo_full_name} -> {snapshot.id}")
            
            # 更新爬取任务状态
            self.repo_service.update_crawl_job_success(
                job=crawl_job,
                repos_discovered=stats["total"],
                new_repos_count=stats["new_repos"]
            )
            
            # 提交事务
            self.session.commit()
            
            logger.info(f"数据持久化完成：总计{stats['total']}个，新增{stats['new_repos']}个，更新{stats['updated_repos']}个，快照{stats['snapshots_created']}条")
            
            return stats
            
        except Exception as e:
            logger.error(f"数据持久化失败：{e}")
            self.session.rollback()
            
            # 更新任务状态为失败
            self.repo_service.update_crawl_job_failed(crawl_job, str(e))
            self.session.commit()
            
            raise
