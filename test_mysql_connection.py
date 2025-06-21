#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL连接测试脚本
用于验证Railway部署中的MySQL配置
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pymysql_import():
    """测试PyMySQL导入"""
    print("🔍 测试PyMySQL导入...")
    try:
        import pymysql
        print(f"✅ PyMySQL版本: {pymysql.__version__}")
        return True
    except ImportError:
        print("❌ PyMySQL未安装")
        print("💡 解决方案: pip install pymysql")
        return False

def test_sqlalchemy_import():
    """测试SQLAlchemy导入"""
    print("\n🔍 测试SQLAlchemy导入...")
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy版本: {sqlalchemy.__version__}")
        return True
    except ImportError:
        print("❌ SQLAlchemy未安装")
        return False

def fix_database_url():
    """修复DATABASE_URL格式"""
    print("\n🔧 检查DATABASE_URL格式...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL环境变量未设置")
        return None
    
    print(f"原始URL: {database_url[:30]}...{database_url[-20:] if len(database_url) > 50 else database_url[30:]}")
    
    # 修复MySQL URL格式
    if database_url.startswith('mysql://') and '+pymysql' not in database_url:
        fixed_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
        os.environ['DATABASE_URL'] = fixed_url
        print("✅ DATABASE_URL已修复为使用pymysql驱动")
        return fixed_url
    elif 'mysql+pymysql://' in database_url:
        print("✅ DATABASE_URL格式正确")
        return database_url
    else:
        print("ℹ️ 非MySQL数据库或格式已正确")
        return database_url

def init_pymysql_compatibility():
    """初始化PyMySQL兼容性"""
    print("\n🔧 初始化PyMySQL兼容性...")
    
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
        print("✅ PyMySQL已配置为MySQLdb替代品")
        return True
    except Exception as e:
        print(f"❌ PyMySQL兼容性初始化失败: {e}")
        return False

def test_sqlalchemy_engine():
    """测试SQLAlchemy引擎创建"""
    print("\n🔍 测试SQLAlchemy引擎创建...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL未设置")
        return False
    
    try:
        from sqlalchemy import create_engine
        
        # 创建引擎（不实际连接）
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            echo=False
        )
        print("✅ SQLAlchemy引擎创建成功")
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy引擎创建失败: {e}")
        return False

def test_database_connection():
    """测试实际数据库连接"""
    print("\n🔍 测试数据库连接...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url or 'mysql' not in database_url.lower():
        print("ℹ️ 跳过MySQL连接测试（非MySQL数据库）")
        return True
    
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            echo=False
        )
        
        # 尝试连接并执行简单查询
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✅ 数据库连接成功")
                return True
            else:
                print("❌ 数据库查询结果异常")
                return False
                
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("💡 可能的原因:")
        print("   - 数据库服务未启动")
        print("   - 连接参数错误")
        print("   - 网络连接问题")
        print("   - 权限不足")
        return False

def print_environment_info():
    """打印环境信息"""
    print("\n📋 环境信息:")
    print(f"   Python版本: {sys.version}")
    print(f"   操作系统: {os.name}")
    print(f"   USE_DATABASE: {os.getenv('USE_DATABASE', '未设置')}")
    
    database_url = os.getenv('DATABASE_URL', '未设置')
    if database_url != '未设置' and len(database_url) > 50:
        print(f"   DATABASE_URL: {database_url[:30]}...{database_url[-20:]}")
    else:
        print(f"   DATABASE_URL: {database_url}")

def main():
    """主测试函数"""
    print("🚀 MySQL连接测试工具")
    print("=" * 50)
    
    print_environment_info()
    
    # 执行测试
    tests = [
        ("PyMySQL导入", test_pymysql_import),
        ("SQLAlchemy导入", test_sqlalchemy_import),
        ("DATABASE_URL修复", lambda: fix_database_url() is not None),
        ("PyMySQL兼容性", init_pymysql_compatibility),
        ("SQLAlchemy引擎", test_sqlalchemy_engine),
        ("数据库连接", test_database_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出结果摘要
    print("\n" + "=" * 50)
    print("📋 测试结果摘要:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！MySQL配置正确。")
        print("🚀 现在可以正常部署应用了。")
        return True
    else:
        print("⚠️ 部分测试失败，请检查配置。")
        print("📖 参考RAILWAY_MYSQL_SETUP.md获取详细指南。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
