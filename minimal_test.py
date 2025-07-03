#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化测试 - 重现Dict导入问题
"""

def test_basic_typing():
    """测试基础typing导入"""
    try:
        from typing import Dict, List, Optional
        print("✅ 基础typing导入成功")
        return True
    except Exception as e:
        print(f"❌ 基础typing导入失败: {e}")
        return False

def test_dict_usage():
    """测试Dict使用"""
    try:
        from typing import Dict
        
        def test_func() -> Dict:
            return {'test': 'value'}
        
        result = test_func()
        print(f"✅ Dict使用成功: {result}")
        return True
    except Exception as e:
        print(f"❌ Dict使用失败: {e}")
        return False

def test_api_modules():
    """测试API模块导入"""
    modules = [
        'api_response',
        'rate_limiter',
        'auth_middleware'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module} 导入成功")
        except Exception as e:
            print(f"❌ {module} 导入失败: {e}")
            return False
    
    return True

def main():
    """主函数"""
    print("🔍 最小化测试 - Dict导入问题")
    print("=" * 40)
    
    tests = [
        ("基础typing导入", test_basic_typing),
        ("Dict使用", test_dict_usage),
        ("API模块导入", test_api_modules)
    ]
    
    for test_name, test_func in tests:
        print(f"\n测试: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")

if __name__ == '__main__':
    main()
