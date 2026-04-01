"""
配置工具模块
从环境变量加载配置
"""

import os
from typing import Optional
from dotenv import load_dotenv


def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    获取配置项
    
    Args:
        key: 配置项名称
        default: 默认值
        
    Returns:
        配置值
    """
    # 确保加载.env 文件
    load_dotenv()
    return os.getenv(key, default)


def get_database_url() -> str:
    """
    获取数据库连接 URL
    
    Returns:
        数据库连接 URL
    """
    db_type = get_config("DB_TYPE", "sqlite")
    
    if db_type == "sqlite":
        db_path = get_config("SQLITE_DB_PATH", "github_trending.db")
        return f"sqlite:///{db_path}"
    elif db_type == "postgresql":
        user = get_config("POSTGRES_USER", "postgres")
        password = get_config("POSTGRES_PASSWORD", "postgres")
        host = get_config("POSTGRES_HOST", "localhost")
        port = get_config("POSTGRES_PORT", "5432")
        database = get_config("POSTGRES_DB", "github_trending")
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    elif db_type == "mysql":
        user = get_config("MYSQL_USER", "root")
        password = get_config("MYSQL_PASSWORD", "root")
        host = get_config("MYSQL_HOST", "localhost")
        port = get_config("MYSQL_PORT", "3306")
        database = get_config("MYSQL_DB", "github_trending")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    else:
        raise ValueError(f"不支持的数据库类型：{db_type}")


def get_github_proxy() -> Optional[str]:
    """
    获取 GitHub 代理地址
    
    Returns:
        代理地址或 None
    """
    proxy = get_config("GITHUB_PROXY")
    return proxy if proxy else None


def get_crawl_timeout() -> int:
    """
    获取爬取超时时间
    
    Returns:
        超时时间（秒）
    """
    try:
        return int(get_config("CRAWL_TIMEOUT", "30"))
    except ValueError:
        return 30
