"""
爬虫调度脚本
支持 daily/weekly/monthly 三种窗口的数据爬取
"""

import argparse
import sys
from datetime import datetime
from typing import Optional

from .crawler import GitHubCrawler
from .database import init_db, get_db_session, RepositoryService
from .database.models import WindowType
from .database.persistence_service import DataPersistenceService
from .utils.config import get_database_url, get_github_proxy, get_crawl_timeout
from .utils.logger import get_logger

logger = get_logger(__name__)


def crawl(window_type: str, proxy: Optional[str] = None):
    """
    执行爬取任务
    
    Args:
        window_type: 窗口类型（daily/weekly/monthly）
        proxy: 代理地址
    """
    logger.info(f"开始执行爬取任务：{window_type}")
    
    try:
        # 初始化数据库
        db_url = get_database_url()
        logger.info(f"使用数据库：{db_url}")
        engine = init_db(db_url)
        session = get_db_session(engine)
        
        # 初始化服务
        repo_service = RepositoryService(session)
        persistence_service = DataPersistenceService(session)
        
        # 创建爬虫
        timeout = get_crawl_timeout()
        crawler = GitHubCrawler(proxy=proxy, timeout=timeout)
        
        # 测试连接
        logger.info("测试 GitHub 连接...")
        if not crawler.test_connection():
            raise Exception("无法连接到 GitHub，请检查网络或代理设置")
        logger.info("GitHub 连接正常")
        
        # 创建爬取任务记录
        if window_type == "daily":
            crawl_url = "https://github.com/trending?since=daily"
            repos_data = crawler.crawl_daily()
        elif window_type == "weekly":
            crawl_url = "https://github.com/trending?since=weekly"
            repos_data = crawler.crawl_weekly()
        elif window_type == "monthly":
            crawl_url = "https://github.com/trending?since=monthly"
            repos_data = crawler.crawl_monthly()
        else:
            raise ValueError(f"无效的窗口类型：{window_type}")
        
        # 创建任务记录
        window_enum = WindowType(window_type)
        crawl_job = repo_service.create_crawl_job(window_enum, crawl_url)
        session.commit()
        
        logger.info(f"爬取到 {len(repos_data)} 个仓库数据")
        
        # 保存数据
        stats = persistence_service.save_crawl_data(repos_data, window_enum, crawl_job)
        
        logger.info(f"爬取任务完成：{stats}")
        
        # 打印摘要
        print(f"\n{'='*60}")
        print(f"爬取任务完成 - {window_type.upper()}")
        print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"发现仓库：{stats['total']} 个")
        print(f"新增仓库：{stats['new_repos']} 个")
        print(f"更新仓库：{stats['updated_repos']} 个")
        print(f"创建快照：{stats['snapshots_created']} 条")
        print(f"{'='*60}\n")
        
    except Exception as e:
        logger.error(f"爬取任务失败：{e}", exc_info=True)
        print(f"\n❌ 爬取任务失败：{e}\n")
        sys.exit(1)
    finally:
        session.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GitHub Trending 爬虫")
    parser.add_argument(
        "window",
        type=str,
        choices=["daily", "weekly", "monthly"],
        help="时间窗口类型"
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="代理地址（可选）"
    )
    
    args = parser.parse_args()
    
    # 使用配置的代理（如果命令行未指定）
    proxy = args.proxy or get_github_proxy()
    
    crawl(args.window, proxy)


if __name__ == "__main__":
    main()
