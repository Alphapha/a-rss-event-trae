"""
定时任务调度器模块
使用 APScheduler 实现后台定时任务
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import create_engine
import logging

from .utils.logger import get_logger
from .utils.config import get_config
from .crawler_task import crawl

logger = get_logger(__name__)


def crawl_daily_job():
    """
    每日爬取任务
    """
    logger.info("执行每日爬取任务 (daily)...")
    try:
        crawl("daily")
        logger.info("每日爬取任务完成")
    except Exception as e:
        logger.error(f"每日爬取任务失败：{e}")


def crawl_weekly_job():
    """
    每周爬取任务
    """
    logger.info("执行每周爬取任务 (weekly)...")
    try:
        crawl("weekly")
        logger.info("每周爬取任务完成")
    except Exception as e:
        logger.error(f"每周爬取任务失败：{e}")


def crawl_monthly_job():
    """
    每月爬取任务
    """
    logger.info("执行每月爬取任务 (monthly)...")
    try:
        crawl("monthly")
        logger.info("每月爬取任务完成")
    except Exception as e:
        logger.error(f"每月爬取任务失败：{e}")


def setup_scheduler(engine: create_engine) -> BackgroundScheduler:
    """
    设置并启动定时任务调度器
    
    Args:
        engine: SQLAlchemy 引擎
        
    Returns:
        BackgroundScheduler: 调度器实例
    """
    scheduler = BackgroundScheduler()
    
    # 获取配置（从环境变量或默认值）
    daily_time = get_config("DAILY_CRAWL_TIME", "07:15")
    weekly_time = get_config("WEEKLY_CRAWL_TIME", "07:20")
    monthly_time = get_config("MONTHLY_CRAWL_TIME", "07:25")
    
    # 解析时间
    daily_hour, daily_minute = map(int, daily_time.split(':'))
    weekly_hour, weekly_minute = map(int, weekly_time.split(':'))
    monthly_hour, monthly_minute = map(int, monthly_time.split(':'))
    
    # 添加定时任务
    # 每天执行 daily 爬取
    scheduler.add_job(
        crawl_daily_job,
        CronTrigger(hour=daily_hour, minute=daily_minute),
        id='daily_crawl',
        name='Daily Crawl Job',
        replace_existing=True
    )
    
    # 每天执行 weekly 爬取
    scheduler.add_job(
        crawl_weekly_job,
        CronTrigger(hour=weekly_hour, minute=weekly_minute),
        id='weekly_crawl',
        name='Weekly Crawl Job',
        replace_existing=True
    )
    
    # 每天执行 monthly 爬取
    scheduler.add_job(
        crawl_monthly_job,
        CronTrigger(hour=monthly_hour, minute=monthly_minute),
        id='monthly_crawl',
        name='Monthly Crawl Job',
        replace_existing=True
    )
    
    # 启动调度器
    scheduler.start()
    
    logger.info(f"定时任务调度器已启动")
    logger.info(f"  - Daily:   每天 {daily_time} 执行")
    logger.info(f"  - Weekly:  每天 {weekly_time} 执行")
    logger.info(f"  - Monthly: 每天 {monthly_time} 执行")
    
    return scheduler


def shutdown_scheduler(scheduler: BackgroundScheduler):
    """
    关闭定时任务调度器
    
    Args:
        scheduler: 调度器实例
    """
    if scheduler:
        logger.info("正在关闭定时任务调度器...")
        scheduler.shutdown(wait=True)
        logger.info("定时任务调度器已关闭")
