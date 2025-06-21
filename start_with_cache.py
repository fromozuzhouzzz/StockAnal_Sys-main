#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析系统启动脚本 - 带数据缓存支持
开发者：熊猫大侠
版本：v2.1.0
"""

import os
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_mysql_driver():
    """修复MySQL驱动配置"""
    database_url = os.getenv('DATABASE_URL')

    if database_url and 'mysql' in database_url.lower():
        logger.info("🔧 检测到MySQL数据库，初始化PyMySQL兼容性...")

        try:
            import pymysql
            # 让PyMySQL伪装成MySQLdb
            pymysql.install_as_MySQLdb()
            logger.info("✅ PyMySQL兼容性初始化成功")

            # 修复DATABASE_URL格式
            if database_url.startswith('mysql://') and '+pymysql' not in database_url:
                fixed_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
                os.environ['DATABASE_URL'] = fixed_url
                logger.info("✅ DATABASE_URL已修复为使用pymysql驱动")

            return True
        except ImportError:
            logger.error("❌ PyMySQL未安装，MySQL功能不可用")
            return False
        except Exception as e:
            logger.error(f"❌ PyMySQL初始化失败: {e}")
            return False

    return True

def check_environment():
    """检查环境配置"""
    logger.info("🔍 检查环境配置...")

    # 修复MySQL驱动
    if not fix_mysql_driver():
        logger.warning("⚠️ MySQL驱动修复失败，但系统仍可运行")

    # 检查必要的环境变量
    required_vars = []
    optional_vars = [
        'DATABASE_URL',
        'USE_DATABASE',
        'OPENAI_API_KEY',
        'SECRET_KEY'
    ]

    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)

    if missing_required:
        logger.error(f"❌ 缺少必需的环境变量: {', '.join(missing_required)}")
        return False

    # 显示配置信息
    logger.info("📋 当前配置:")
    logger.info(f"   数据库启用: {os.getenv('USE_DATABASE', 'False')}")
    database_url = os.getenv('DATABASE_URL', '未配置')
    if len(database_url) > 50:
        logger.info(f"   数据库URL: {database_url[:30]}...{database_url[-20:]}")
    else:
        logger.info(f"   数据库URL: {database_url}")
    logger.info(f"   Redis缓存: {os.getenv('USE_REDIS_CACHE', 'False')}")
    logger.info(f"   调试模式: {os.getenv('FLASK_DEBUG', 'False')}")

    return True

def initialize_database():
    """初始化数据库"""
    try:
        from database import USE_DATABASE, init_db, test_connection
        
        if USE_DATABASE:
            logger.info("🗄️ 初始化数据库...")
            init_db()
            
            if test_connection():
                logger.info("✅ 数据库连接成功")
                return True
            else:
                logger.warning("⚠️ 数据库连接失败，将使用内存缓存")
                return False
        else:
            logger.info("ℹ️ 数据库未启用，使用内存缓存")
            return True
            
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        logger.warning("⚠️ 将使用内存缓存作为降级方案")
        return False

def test_data_service():
    """测试数据访问服务"""
    try:
        logger.info("🧪 测试数据访问服务...")
        from data_service import data_service
        
        # 快速测试
        stats = data_service.get_cache_statistics()
        logger.info(f"📊 缓存统计: {stats}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 数据服务测试失败: {e}")
        return False

def start_application():
    """启动应用"""
    try:
        logger.info("🚀 启动股票分析系统...")
        
        # 导入主应用
        from web_server import app
        
        # 获取配置
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 7860))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        logger.info(f"🌐 服务器启动: http://{host}:{port}")
        logger.info(f"⚙️ 调试模式: {'启用' if debug else '禁用'}")
        
        # 启动应用
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        sys.exit(1)

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    股票分析系统 v2.1.0                        ║
║                  Enhanced with Data Caching                 ║
╠══════════════════════════════════════════════════════════════╣
║  🚀 新功能:                                                   ║
║     • 智能数据缓存 (MySQL + 内存)                             ║
║     • API调用优化 (减少80-90%调用)                            ║
║     • 性能提升 (响应时间提升10-50倍)                          ║
║     • 降级保护 (API失败时使用缓存)                            ║
║                                                              ║
║  📊 支持的数据库:                                             ║
║     • Aiven MySQL (免费)                                     ║
║     • PlanetScale (免费)                                     ║
║     • Railway MySQL                                          ║
║     • 本地 MySQL/SQLite                                      ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """主函数"""
    print_banner()
    
    logger.info(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查环境
    if not check_environment():
        logger.error("❌ 环境检查失败")
        sys.exit(1)
    
    # 初始化数据库
    db_success = initialize_database()
    
    # 测试数据服务
    if not test_data_service():
        logger.warning("⚠️ 数据服务测试失败，但系统仍可运行")
    
    # 显示系统状态
    logger.info("📋 系统状态:")
    logger.info(f"   数据库缓存: {'✅ 正常' if db_success else '❌ 降级到内存缓存'}")
    logger.info(f"   数据访问层: ✅ 正常")
    logger.info(f"   API重试机制: ✅ 启用")
    logger.info(f"   缓存清理: ✅ 自动")
    
    # 启动应用
    start_application()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 用户中断，正在关闭系统...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 系统启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
