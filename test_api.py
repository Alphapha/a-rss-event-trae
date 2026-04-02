#!/usr/bin/env python3
"""
测试 API 服务
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查接口"""
    print("📊 测试健康检查接口...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 健康检查通过：{data['status']}")
        return True
    else:
        print(f"❌ 健康检查失败：{response.status_code}")
        return False


def test_root():
    """测试根路径接口"""
    print("\n📊 测试根路径接口...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 根路径访问成功：{data['message']}")
        return True
    else:
        print(f"❌ 根路径访问失败：{response.status_code}")
        return False


def test_stats():
    """测试统计信息接口"""
    print("\n📊 测试统计信息接口...")
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 统计信息获取成功:")
        print(f"  - 仓库总数：{data['total_repos']}")
        print(f"  - 快照总数：{data['total_snapshots']}")
        print(f"  - 任务总数：{data['total_jobs']}")
        if data.get('last_crawl_time'):
            print(f"  - 最后爬取时间：{data['last_crawl_time']}")
        return True
    else:
        print(f"❌ 统计信息获取失败：{response.status_code}")
        return False


def test_repositories():
    """测试仓库列表接口"""
    print("\n📊 测试仓库列表接口...")
    response = requests.get(f"{BASE_URL}/api/v1/repositories", params={"limit": 5})
    if response.status_code == 200:
        repos = response.json()
        print(f"✅ 仓库列表获取成功：共 {len(repos)} 个")
        for repo in repos[:3]:
            print(f"  - {repo['repo_full_name']}: {repo['total_stars']} stars")
        return True
    else:
        print(f"❌ 仓库列表获取失败：{response.status_code}")
        return False


def test_docs():
    """测试 API 文档是否可访问"""
    print("\n📊 测试 API 文档...")
    response = requests.get(f"{BASE_URL}/docs")
    if response.status_code == 200:
        print(f"✅ API 文档可访问：{BASE_URL}/docs")
        return True
    else:
        print(f"❌ API 文档访问失败：{response.status_code}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("GitHub Trending 数据服务 - API 测试")
    print("=" * 60)
    
    # 等待服务启动
    print("\n⏳ 等待服务启动...")
    time.sleep(2)
    
    # 执行测试
    tests = [
        test_health,
        test_root,
        test_docs,
        test_stats,
        test_repositories,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ 测试失败：{e}")
            results.append(False)
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"通过：{passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！服务运行正常")
        print(f"\n📊 访问 API 文档：{BASE_URL}/docs")
        return 0
    else:
        print(f"\n❌ 有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
