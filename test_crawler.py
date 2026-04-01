#!/usr/bin/env python3
"""
数据获取模块测试脚本
验证爬虫和数据库功能是否正常
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Repository, RepositorySnapshot, CrawlJob, WindowType


def test_database():
    """测试数据库连接和数据"""
    print("=" * 60)
    print("数据库数据验证")
    print("=" * 60)
    
    try:
        engine = create_engine('sqlite:///github_trending.db')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 查询仓库
        repos = session.query(Repository).all()
        print(f"\n✅ 仓库总数：{len(repos)}")
        if repos:
            print("\n前 5 个仓库:")
            for repo in repos[:5]:
                print(f"  - {repo.repo_full_name}: {repo.total_stars} stars, {repo.language or 'N/A'}")
        
        # 查询快照
        snapshots = session.query(RepositorySnapshot).all()
        print(f"\n✅ 快照总数：{len(snapshots)}")
        if snapshots:
            print("\n前 5 条快照:")
            for snap in snapshots[:5]:
                print(f"  - Repo {snap.repo_id}: 排名#{snap.ranking}, +{snap.stars_gained} stars")
        
        # 查询爬取任务
        jobs = session.query(CrawlJob).all()
        print(f"\n✅ 爬取任务数：{len(jobs)}")
        if jobs:
            print("\n任务列表:")
            for job in jobs:
                print(f"  - {job.window_type.value}: {job.status}, 发现{job.repos_discovered}个，新增{job.new_repos_count}个")
        
        print("\n" + "=" * 60)
        print("✅ 数据库验证通过！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 数据库验证失败：{e}")
        return False


if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)
