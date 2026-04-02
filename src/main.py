"""
FastAPI 应用主模块
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import logging

from .database import init_db, get_db_session
from .utils.config import get_config, get_database_url
from .utils.logger import get_logger
from . import api
from .scheduler import setup_scheduler, shutdown_scheduler

# 配置日志
logger = get_logger(__name__)

# 全局变量存储 engine 和 scheduler
db_engine = None
scheduler = None


def get_db():
    """
    获取数据库会话的依赖注入函数
    Yields:
        Session: 数据库会话
    """
    global db_engine
    db = get_db_session(db_engine)
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    global db_engine, scheduler
    
    # 启动时初始化
    logger.info("正在启动 GitHub Trending 数据服务...")
    
    # 初始化数据库
    db_url = get_database_url()
    logger.info(f"使用数据库：{db_url}")
    db_engine = init_db(db_url)
    
    # 启动定时任务调度器
    scheduler = setup_scheduler(db_engine)
    
    # 设置 API 模块的 get_db 函数
    api.routes.get_db = get_db
    
    logger.info("GitHub Trending 数据服务启动完成")
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭 GitHub Trending 数据服务...")
    shutdown_scheduler(scheduler)
    logger.info("服务已关闭")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例
    
    Returns:
        FastAPI: 配置好的应用实例
    """
    app = FastAPI(
        title="GitHub Trending 数据服务",
        description="提供 GitHub Trending 数据爬取、存储和查询的 RESTful API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该配置具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(api.routes.router, prefix="/api/v1")
    
    @app.get("/health", tags=["健康检查"])
    async def health_check():
        """
        健康检查接口
        """
        return {
            "status": "healthy",
            "service": "github-trending-data-service"
        }
    
    @app.get("/", tags=["根路径"])
    async def root():
        """
        根路径欢迎信息
        """
        return {
            "message": "欢迎使用 GitHub Trending 数据服务",
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


# 创建应用实例
app = create_app()
