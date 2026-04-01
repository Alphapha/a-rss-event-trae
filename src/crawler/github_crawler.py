"""
GitHub Trending 爬虫
负责从 GitHub Trending 页面抓取热门仓库数据
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

from ..utils.logger import get_logger

logger = get_logger(__name__)


class GitHubCrawler:
    """
    GitHub Trending 爬虫类
    使用 requests + BeautifulSoup 爬取 GitHub Trending 页面
    """
    
    BASE_URL = "https://github.com/trending"
    
    def __init__(self, proxy: Optional[str] = None, timeout: int = 30):
        """
        初始化爬虫
        
        Args:
            proxy: 代理地址（可选），格式如 "http://proxy:port"
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.proxies = None
        if proxy:
            self.proxies = {
                "http": proxy,
                "https": proxy
            }
        
        # 配置重试策略
        self.session = self._create_session()
        
        # 请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
    
    def _create_session(self) -> requests.Session:
        """
        创建带重试策略的 Session
        
        Returns:
            requests.Session: 配置好的 Session 对象
        """
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 最多重试 3 次
            backoff_factor=1,  # 重试间隔：0s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],  # 对这些状态码重试
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _parse_stars(self, stars_text: str) -> int:
        """
        解析 stars 文本为数字
        
        Args:
            stars_text: stars 文本，如 "1.2k stars today" 或 "567 stars this week"
            
        Returns:
            int: stars 数量
        """
        if not stars_text:
            return 0
        
        # 提取数字部分
        stars_text = stars_text.strip().lower()
        
        # 匹配数字（支持 k 单位）
        match = re.search(r'([\d.]+)\s*(k)?', stars_text)
        if not match:
            return 0
        
        number = float(match.group(1))
        unit = match.group(2)
        
        if unit == 'k':
            return int(number * 1000)
        else:
            return int(number)
    
    def _extract_repo_data(self, article, ranking: int) -> Optional[Dict]:
        """
        从 article 标签中提取仓库数据
        
        Args:
            article: BeautifulSoup 的 article 标签
            ranking: 排名
            
        Returns:
            Dict: 仓库数据字典
        """
        try:
            # 仓库全名（owner/name）
            h2_el = article.find('h2')
            if not h2_el:
                return None
            
            a_el = h2_el.find('a')
            if not a_el:
                return None
            
            repo_full_name = a_el['href'].strip('/')
            parts = repo_full_name.split('/')
            if len(parts) != 2:
                return None
            
            owner, repo_name = parts
            
            # 描述
            desc_el = article.find('p', class_='col-9')
            description = desc_el.text.strip() if desc_el else ""
            
            # 主语言
            lang_el = article.find(itemprop='programmingLanguage')
            language = lang_el.text.strip() if lang_el else ""
            
            # Stars 增量
            stars_el = article.find('span', class_='d-inline-block float-sm-right')
            stars_text = stars_el.text.strip() if stars_el else ""
            stars_gained = self._parse_stars(stars_text)
            
            # 总 stars
            total_stars_el = article.find('a', href=lambda h: h and 'stargazers' in h)
            total_stars_text = total_stars_el.text.strip().replace(',', '') if total_stars_el else "0"
            try:
                total_stars = int(total_stars_text)
            except ValueError:
                total_stars = 0
            
            # Forks 数量
            forks_el = article.find('a', href=lambda h: h and 'forks' in h)
            forks_text = forks_el.text.strip().replace(',', '') if forks_el else "0"
            try:
                forks_count = int(forks_text)
            except ValueError:
                forks_count = 0
            
            # 构建数据字典
            repo_data = {
                "repo_full_name": repo_full_name,
                "owner": owner,
                "repo_name": repo_name,
                "description": description,
                "language": language,
                "ranking": ranking,
                "stars_gained": stars_gained,
                "total_stars": total_stars,
                "forks_count": forks_count,
                "raw_html_snippet": str(article)[:1000]  # 保存部分 HTML 用于 debug
            }
            
            return repo_data
            
        except Exception as e:
            logger.error(f"解析仓库数据失败：{e}")
            return None
    
    def crawl(self, window_type: str = "daily", since: Optional[str] = None, language: Optional[str] = None) -> List[Dict]:
        """
        爬取 GitHub Trending 数据
        
        Args:
            window_type: 时间窗口（daily/weekly/monthly）
            since: 时间范围（可选），如 "daily", "weekly", "monthly"
            language: 编程语言过滤（可选）
            
        Returns:
            List[Dict]: 仓库数据列表
        """
        # 构建 URL
        params = {}
        if since:
            params["since"] = since
        if language:
            params["language"] = language
        
        url = self.BASE_URL
        if params:
            url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
        
        logger.info(f"开始爬取：{url}")
        
        try:
            # 发送请求
            response = self.session.get(
                url,
                headers=self.headers,
                proxies=self.proxies,
                timeout=self.timeout
            )
            
            # 检查响应状态
            if response.status_code == 429:
                logger.error("触发 GitHub 限流，请稍后重试")
                raise Exception("GitHub 返回 429 限流错误")
            
            if response.status_code != 200:
                logger.error(f"爬取失败，状态码：{response.status_code}")
                raise Exception(f"HTTP {response.status_code}")
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有 repo 条目
            articles = soup.find_all('article', class_='Box-row')
            
            if not articles:
                logger.warning("未找到任何 repo 条目，HTML 结构可能已变化")
                # 保存原始 HTML 用于 debug
                with open(f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                raise Exception("未找到 repo 条目，请检查 HTML 结构")
            
            logger.info(f"找到 {len(articles)} 个 repo")
            
            # 提取数据
            repos = []
            for idx, article in enumerate(articles, start=1):
                repo_data = self._extract_repo_data(article, idx)
                if repo_data:
                    repos.append(repo_data)
            
            logger.info(f"成功解析 {len(repos)} 个 repo")
            return repos
            
        except requests.exceptions.Timeout:
            logger.error("请求超时")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败：{e}")
            raise
        except Exception as e:
            logger.error(f"爬取失败：{e}")
            raise
    
    def crawl_daily(self) -> List[Dict]:
        """
        爬取每日热门数据
        
        Returns:
            List[Dict]: 仓库数据列表
        """
        return self.crawl(window_type="daily", since="daily")
    
    def crawl_weekly(self) -> List[Dict]:
        """
        爬取每周热门数据
        
        Returns:
            List[Dict]: 仓库数据列表
        """
        return self.crawl(window_type="weekly", since="weekly")
    
    def crawl_monthly(self) -> List[Dict]:
        """
        爬取每月热门数据
        
        Returns:
            List[Dict]: 仓库数据列表
        """
        return self.crawl(window_type="monthly", since="monthly")
    
    def test_connection(self) -> bool:
        """
        测试 GitHub 连接
        
        Returns:
            bool: 是否连接成功
        """
        try:
            response = self.session.get(
                self.BASE_URL,
                headers=self.headers,
                proxies=self.proxies,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"连接测试失败：{e}")
            return False
