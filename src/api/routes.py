"""
API 路由模块
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from ..database import get_db_session
from ..database.models import Repository, RepositorySnapshot, CrawlJob, WindowType
from ..database.repository_service import RepositoryService
from ..crawler_task import crawl as crawl_data

router = APIRouter()


# ============= Pydantic 模型 =============

class RepositoryBase(BaseModel):
    """仓库基础模型"""
    repo_full_name: str
    owner: str
    repo_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    total_stars: int = 0
    forks_count: int = 0


class RepositoryResponse(RepositoryBase):
    """仓库响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SnapshotBase(BaseModel):
    """快照基础模型"""
    repo_id: int
    window_type: str
    ranking: Optional[int] = None
    stars_gained: int = 0
    total_stars: int = 0


class SnapshotResponse(SnapshotBase):
    """快照响应模型"""
    id: int
    snapshot_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class CrawlJobResponse(BaseModel):
    """爬取任务响应模型"""
    id: int
    window_type: str
    status: str
    repos_discovered: int
    new_repos_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TriggerCrawlRequest(BaseModel):
    """触发爬取请求模型"""
    window_type: str  # daily, weekly, monthly


class StatsResponse(BaseModel):
    """统计信息响应模型"""
    total_repos: int
    total_snapshots: int
    total_jobs: int
    last_crawl_time: Optional[datetime] = None
    repos_by_language: dict = {}


# ============= 辅助函数 =============

# 这个变量会在 main.py 中被实际的 get_db 函数替换
get_db = None


# ============= API 接口 =============

@router.get("/repositories", response_model=List[RepositoryResponse], tags=["仓库"])
async def get_repositories(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(25, ge=1, le=100, description="返回数量限制"),
    language: Optional[str] = Query(None, description="按语言过滤"),
    db: Session = Depends(get_db)
):
    """
    获取仓库列表
    """
    query = db.query(Repository)
    
    if language:
        query = query.filter(Repository.language == language)
    
    repositories = query.offset(skip).limit(limit).all()
    return repositories


@router.get("/repositories/{repo_id}", response_model=RepositoryResponse, tags=["仓库"])
async def get_repository(
    repo_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个仓库详情
    """
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return repo


@router.get("/repositories/{repo_id}/snapshots", response_model=List[SnapshotResponse], tags=["仓库快照"])
async def get_repository_snapshots(
    repo_id: int,
    days: int = Query(7, ge=1, le=90, description="查询天数"),
    db: Session = Depends(get_db)
):
    """
    获取仓库的历史快照
    """
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    snapshots = db.query(RepositorySnapshot).filter(
        RepositorySnapshot.repo_id == repo_id,
        RepositorySnapshot.snapshot_date >= cutoff_date
    ).order_by(RepositorySnapshot.snapshot_date.desc()).all()
    
    return snapshots


@router.get("/snapshots", response_model=List[SnapshotResponse], tags=["仓库快照"])
async def get_snapshots(
    window_type: str = Query(..., description="窗口类型：daily, weekly, monthly"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    limit: int = Query(25, ge=1, le=100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    查询快照数据
    """
    query = db.query(RepositorySnapshot)
    
    # 转换 window_type 为枚举
    try:
        window_enum = WindowType(window_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的窗口类型")
    
    query = query.filter(RepositorySnapshot.window_type == window_enum)
    
    if date_from:
        query = query.filter(RepositorySnapshot.snapshot_date >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        query = query.filter(RepositorySnapshot.snapshot_date <= datetime.combine(date_to, datetime.max.time()))
    
    snapshots = query.order_by(RepositorySnapshot.ranking).limit(limit).all()
    return snapshots


@router.get("/jobs", response_model=List[CrawlJobResponse], tags=["爬取任务"])
async def get_crawl_jobs(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    status: Optional[str] = Query(None, description="按状态过滤"),
    db: Session = Depends(get_db)
):
    """
    获取爬取任务列表
    """
    query = db.query(CrawlJob)
    
    if status:
        query = query.filter(CrawlJob.status == status)
    
    jobs = query.order_by(CrawlJob.started_at.desc()).limit(limit).all()
    return jobs


@router.post("/crawl", tags=["爬取控制"])
async def trigger_crawl(
    request: TriggerCrawlRequest,
    db: Session = Depends(get_db)
):
    """
    手动触发爬取任务
    """
    window_type = request.window_type
    
    if window_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="无效的窗口类型")
    
    try:
        # 这里应该调用后台任务，而不是直接执行
        # 实际实现中应该使用 BackgroundTasks 或 Celery
        from ..crawler_task import crawl
        crawl(window_type)
        
        return {
            "message": f"已触发 {window_type} 爬取任务",
            "window_type": window_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬取失败：{str(e)}")


@router.get("/stats", response_model=StatsResponse, tags=["统计信息"])
async def get_stats(db: Session = Depends(get_db)):
    """
    获取数据库统计信息
    """
    # 统计仓库数量
    total_repos = db.query(Repository).count()
    
    # 统计快照数量
    total_snapshots = db.query(RepositorySnapshot).count()
    
    # 统计任务数量
    total_jobs = db.query(CrawlJob).count()
    
    # 最近一次爬取时间
    last_job = db.query(CrawlJob).order_by(CrawlJob.started_at.desc()).first()
    last_crawl_time = last_job.started_at if last_job else None
    
    # 按语言统计
    language_stats = db.query(
        Repository.language,
        db.func.count(Repository.id)
    ).filter(
        Repository.language.isnot(None)
    ).group_by(Repository.language).all()
    
    repos_by_language = {lang: count for lang, count in language_stats}
    
    return StatsResponse(
        total_repos=total_repos,
        total_snapshots=total_snapshots,
        total_jobs=total_jobs,
        last_crawl_time=last_crawl_time,
        repos_by_language=repos_by_language
    )


@router.delete("/repositories/{repo_id}", tags=["仓库"])
async def delete_repository(
    repo_id: int,
    db: Session = Depends(get_db)
):
    """
    删除仓库及其相关数据
    """
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    
    # 删除相关快照
    db.query(RepositorySnapshot).filter(RepositorySnapshot.repo_id == repo_id).delete()
    
    # 删除仓库
    db.delete(repo)
    db.commit()
    
    return {"message": f"仓库 {repo.repo_full_name} 已删除"}
