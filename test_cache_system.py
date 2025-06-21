#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据缓存系统测试脚本
"""

import os
import sys

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        import database
        print("✅ database.py 导入成功")
    except Exception as e:
        print(f"❌ database.py 导入失败: {e}")
        return False
    
    try:
        import data_service
        print("✅ data_service.py 导入成功")
    except Exception as e:
        print(f"❌ data_service.py 导入失败: {e}")
        return False
    
    return True

def test_database_config():
    """测试数据库配置"""
    print("\n🗄️ 测试数据库配置...")
    
    try:
        from database import USE_DATABASE
        print(f"数据库启用状态: {USE_DATABASE}")
        return True
    except Exception as e:
        print(f"❌ 数据库配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 数据缓存系统测试")
    print("=" * 40)
    
    tests = [
        ("模块导入", test_imports),
        ("数据库配置", test_database_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出结果
    print("\n" + "=" * 40)
    print("📋 测试结果:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
