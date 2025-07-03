#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导入问题
"""

import sys

def test_import(module_name):
    """测试单个模块导入"""
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
        return True
    except Exception as e:
        print(f"❌ {module_name}: {e}")
        return False

def main():
    """主函数"""
    print("🔍 测试模块导入")
    print("=" * 40)
    
    # 测试基础模块
    modules_to_test = [
        'typing',
        'flask',
        'api_response',
        'rate_limiter', 
        'auth_middleware',
        'api_cache_integration',
        'api_endpoints',
        'api_integration'
    ]
    
    failed_modules = []
    
    for module in modules_to_test:
        if not test_import(module):
            failed_modules.append(module)
    
    print("\n" + "=" * 40)
    if failed_modules:
        print(f"❌ 失败模块: {', '.join(failed_modules)}")
    else:
        print("✅ 所有模块导入成功")

if __name__ == '__main__':
    main()
