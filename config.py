# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - 配置文件
开发者：熊猫大侠
版本：v2.1.0
许可证：MIT License
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 数据库配置 ====================

# 数据库连接配置
DATABASE_CONFIG = {
    # 数据库URL - 支持MySQL、PostgreSQL、SQLite
    'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///data/stock_analyzer.db'),
    
    # 是否启用数据库缓存
    'USE_DATABASE': os.getenv('USE_DATABASE', 'False').lower() == 'true',
    
    # 连接池配置
    'POOL_SIZE': int(os.getenv('DATABASE_POOL_SIZE', '10')),
    'POOL_RECYCLE': int(os.getenv('DATABASE_POOL_RECYCLE', '3600')),  # 1小时
    'POOL_TIMEOUT': int(os.getenv('DATABASE_POOL_TIMEOUT', '30')),   # 30秒
    'POOL_PRE_PING': True,  # 验证连接有效性
    
    # 是否启用SQL日志
    'ECHO_SQL': os.getenv('ECHO_SQL', 'False').lower() == 'true',
}

# ==================== 缓存配置 ====================

CACHE_CONFIG = {
    # 默认缓存时间（秒）
    'DEFAULT_TTL': int(os.getenv('CACHE_DEFAULT_TTL', '900')),      # 15分钟
    
    # 不同数据类型的缓存时间
    'REALTIME_DATA_TTL': int(os.getenv('REALTIME_DATA_TTL', '300')),     # 5分钟
    'BASIC_INFO_TTL': int(os.getenv('BASIC_INFO_TTL', '604800')),        # 7天
    'FINANCIAL_DATA_TTL': int(os.getenv('FINANCIAL_DATA_TTL', '7776000')), # 90天
    'CAPITAL_FLOW_TTL': int(os.getenv('CAPITAL_FLOW_TTL', '86400')),     # 1天
    'PRICE_HISTORY_TTL': int(os.getenv('PRICE_HISTORY_TTL', '3600')),    # 1小时
    
    # 内存缓存配置
    'MEMORY_CACHE_SIZE': int(os.getenv('MEMORY_CACHE_SIZE', '1000')),    # 最大缓存条目数
    'MEMORY_CACHE_TTL': int(os.getenv('MEMORY_CACHE_TTL', '1800')),      # 30分钟
    
    # 缓存清理配置
    'CLEANUP_INTERVAL': int(os.getenv('CACHE_CLEANUP_INTERVAL', '3600')), # 1小时清理一次
}

# ==================== API配置 ====================

API_CONFIG = {
    # AKShare API配置 - 针对HF Spaces环境优化
    'AKSHARE_TIMEOUT': int(os.getenv('AKSHARE_TIMEOUT', '60')),          # 延长到60秒
    'AKSHARE_MAX_RETRIES': int(os.getenv('AKSHARE_MAX_RETRIES', '5')),   # 增加重试次数
    'AKSHARE_RETRY_DELAY': int(os.getenv('AKSHARE_RETRY_DELAY', '2')),   # 增加重试延迟
    
    # OpenAI API配置
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'OPENAI_API_URL': os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1'),
    'OPENAI_MODEL': os.getenv('OPENAI_API_MODEL', 'gemini-2.0-pro-exp-02-05'),
    'FUNCTION_CALL_MODEL': os.getenv('FUNCTION_CALL_MODEL', 'gpt-4o'),
    'NEWS_MODEL': os.getenv('NEWS_MODEL'),
}

# ==================== Redis配置 ====================

REDIS_CONFIG = {
    # 是否启用Redis缓存
    'USE_REDIS_CACHE': os.getenv('USE_REDIS_CACHE', 'False').lower() == 'true',
    
    # Redis连接配置
    'REDIS_URL': os.getenv('REDIS_URL'),
    'REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
    'REDIS_PORT': int(os.getenv('REDIS_PORT', '6379')),
    'REDIS_DB': int(os.getenv('REDIS_DB', '0')),
    'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
    
    # Redis缓存配置
    'REDIS_DEFAULT_TTL': int(os.getenv('REDIS_DEFAULT_TTL', '300')),  # 5分钟
}

# ==================== 应用配置 ====================

APP_CONFIG = {
    # Flask配置
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
    'DEBUG': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
    'HOST': os.getenv('HOST', '0.0.0.0'),
    'PORT': int(os.getenv('PORT', '7860')),
    
    # 日志配置
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'LOG_FILE': os.getenv('LOG_FILE', 'flask_app.log'),
    'LOG_MAX_BYTES': int(os.getenv('LOG_MAX_BYTES', '10000000')),  # 10MB
    'LOG_BACKUP_COUNT': int(os.getenv('LOG_BACKUP_COUNT', '5')),
    
    # 性能配置 - 针对HF Spaces环境优化
    'MAX_WORKERS': int(os.getenv('MAX_WORKERS', '4')),
    'REQUEST_TIMEOUT': int(os.getenv('REQUEST_TIMEOUT', '180')),    # 延长到180秒
}

# ==================== 数据库连接字符串示例 ====================

DATABASE_EXAMPLES = {
    # Aiven MySQL (免费层)
    'aiven_mysql': 'mysql://[USER]:[PASS]@[HOST]:[PORT]/[DB]?ssl-mode=REQUIRED',

    # PlanetScale MySQL
    'planetscale': 'mysql://[USER]:[PASS]@[HOST]:[PORT]/[DB]?ssl-mode=REQUIRED',

    # Railway MySQL
    'railway_mysql': 'mysql://[USER]:[PASS]@[HOST]:[PORT]/[DB]',

    # Railway PostgreSQL
    'railway_postgres': 'postgresql://[USER]:[PASS]@[HOST]:[PORT]/[DB]',

    # 本地SQLite
    'sqlite': 'sqlite:///data/stock_analyzer.db',

    # 本地MySQL
    'local_mysql': 'mysql://[USER]:[PASS]@localhost:3306/stock_analyzer',

    # 本地PostgreSQL
    'local_postgres': 'postgresql://[USER]:[PASS]@localhost:5432/stock_analyzer',
}

# ==================== 环境变量模板 ====================

ENV_TEMPLATE = """
# 数据库配置
DATABASE_URL=sqlite:///data/stock_analyzer.db
USE_DATABASE=True
DATABASE_POOL_SIZE=10
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_TIMEOUT=30

# 缓存配置
CACHE_DEFAULT_TTL=900
REALTIME_DATA_TTL=300
BASIC_INFO_TTL=604800
FINANCIAL_DATA_TTL=7776000
CAPITAL_FLOW_TTL=86400

# API配置
AKSHARE_TIMEOUT=30
AKSHARE_MAX_RETRIES=3
OPENAI_API_KEY=[YOUR_OPENAI_API_KEY]

# Redis配置（可选）
USE_REDIS_CACHE=False
REDIS_URL=redis://localhost:6379/0

# 应用配置
SECRET_KEY=[YOUR_SECRET_KEY]
FLASK_DEBUG=False
HOST=0.0.0.0
PORT=7860
LOG_LEVEL=INFO
"""

def get_database_url():
    """获取数据库连接URL"""
    return DATABASE_CONFIG['DATABASE_URL']

def is_database_enabled():
    """检查是否启用数据库"""
    return DATABASE_CONFIG['USE_DATABASE']

def get_cache_ttl(data_type: str) -> int:
    """获取指定数据类型的缓存时间"""
    ttl_map = {
        'realtime': CACHE_CONFIG['REALTIME_DATA_TTL'],
        'basic_info': CACHE_CONFIG['BASIC_INFO_TTL'],
        'financial': CACHE_CONFIG['FINANCIAL_DATA_TTL'],
        'capital_flow': CACHE_CONFIG['CAPITAL_FLOW_TTL'],
        'price_history': CACHE_CONFIG['PRICE_HISTORY_TTL'],
    }
    return ttl_map.get(data_type, CACHE_CONFIG['DEFAULT_TTL'])

def print_config_summary():
    """打印配置摘要"""
    print("=== 股票分析系统配置摘要 ===")
    print(f"数据库: {'启用' if DATABASE_CONFIG['USE_DATABASE'] else '禁用'}")
    print(f"数据库URL: {DATABASE_CONFIG['DATABASE_URL']}")
    print(f"Redis缓存: {'启用' if REDIS_CONFIG['USE_REDIS_CACHE'] else '禁用'}")
    print(f"默认缓存时间: {CACHE_CONFIG['DEFAULT_TTL']}秒")
    print(f"应用端口: {APP_CONFIG['PORT']}")
    print(f"调试模式: {'启用' if APP_CONFIG['DEBUG'] else '禁用'}")
    print("=" * 30)

if __name__ == "__main__":
    print_config_summary()
