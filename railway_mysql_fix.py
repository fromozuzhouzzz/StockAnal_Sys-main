#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway MySQL驱动修复脚本
解决PyMySQL与SQLAlchemy的兼容性问题
"""

import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_railway_mysql_config():
    """修复Railway MySQL配置"""
    
    # 1. 初始化PyMySQL兼容性
    try:
        import pymysql
        # 让PyMySQL伪装成MySQLdb
        pymysql.install_as_MySQLdb()
        logger.info("✅ PyMySQL兼容性初始化成功")
    except ImportError:
        logger.error("❌ PyMySQL未安装，请检查requirements.txt")
        return False
    except Exception as e:
        logger.error(f"❌ PyMySQL初始化失败: {e}")
        return False
    
    # 2. 检查和修复DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        if database_url.startswith('mysql://') and '+pymysql' not in database_url:
            # 修复URL格式
            fixed_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
            os.environ['DATABASE_URL'] = fixed_url
            logger.info("✅ DATABASE_URL已修复为使用pymysql驱动")
            logger.info(f"   原URL: mysql://...")
            logger.info(f"   新URL: mysql+pymysql://...")
        else:
            logger.info("✅ DATABASE_URL格式正确")
    else:
        logger.warning("⚠️ 未找到DATABASE_URL环境变量")
    
    # 3. 验证MySQL连接配置
    try:
        from sqlalchemy import create_engine
        
        # 测试连接字符串
        if database_url and 'mysql' in database_url:
            # 创建测试引擎（不实际连接）
            test_engine = create_engine(
                os.getenv('DATABASE_URL'),
                pool_pre_ping=True,
                echo=False
            )
            logger.info("✅ SQLAlchemy引擎创建成功")
            return True
        else:
            logger.info("ℹ️ 非MySQL数据库，跳过MySQL特定配置")
            return True
            
    except Exception as e:
        logger.error(f"❌ SQLAlchemy引擎创建失败: {e}")
        return False

def print_railway_config_guide():
    """打印Railway配置指南"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                Railway MySQL配置指南                          ║
╚══════════════════════════════════════════════════════════════╝

🔧 方法1：修改环境变量（推荐）
在Railway项目设置中，将DATABASE_URL修改为：
mysql+pymysql://username:password@hostname:port/database

🔧 方法2：使用Railway MySQL服务变量
如果使用Railway的MySQL服务，设置：
DATABASE_URL=${{MySQL.DATABASE_URL}}
然后Railway会自动提供正确格式的连接字符串。

🔧 方法3：手动设置完整配置
USE_DATABASE=True
DATABASE_URL=mysql+pymysql://user:pass@host:port/db
DATABASE_POOL_SIZE=10
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_TIMEOUT=30

📋 验证步骤：
1. 确保requirements.txt包含pymysql>=1.0.0
2. 设置正确的DATABASE_URL格式
3. 重新部署应用
4. 检查部署日志确认连接成功

🚨 常见问题：
- 确保DATABASE_URL包含+pymysql
- 检查MySQL服务器是否允许外部连接
- 验证用户名密码是否正确
- 确认数据库名称存在

💡 测试连接：
运行此脚本验证配置：python railway_mysql_fix.py
""")

def main():
    """主函数"""
    print("🚀 Railway MySQL驱动修复工具")
    print("=" * 50)
    
    # 显示当前配置
    print("📋 当前配置:")
    print(f"   USE_DATABASE: {os.getenv('USE_DATABASE', 'False')}")
    database_url = os.getenv('DATABASE_URL', '未配置')
    if database_url != '未配置' and len(database_url) > 50:
        print(f"   DATABASE_URL: {database_url[:30]}...{database_url[-20:]}")
    else:
        print(f"   DATABASE_URL: {database_url}")
    
    # 执行修复
    print("\n🔧 执行修复...")
    success = fix_railway_mysql_config()
    
    if success:
        print("\n✅ MySQL驱动配置修复完成！")
        print("🚀 现在可以正常启动应用了")
    else:
        print("\n❌ MySQL驱动配置修复失败")
        print("📖 请查看下方配置指南")
        print_railway_config_guide()
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
