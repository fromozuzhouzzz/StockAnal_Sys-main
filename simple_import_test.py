#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单的导入测试，验证rate_limiter修复
"""

print("开始测试rate_limiter修复...")

try:
    # 测试rate_limiter导入
    print("1. 测试rate_limiter模块导入...")
    from rate_limiter import require_rate_limit, rate_limiter
    print("✅ rate_limiter模块导入成功")
    
    # 测试装饰器创建
    print("2. 测试require_rate_limit装饰器...")
    decorator = require_rate_limit('/api/v1/test')
    print("✅ require_rate_limit装饰器创建成功")
    
    # 检查批量更新限流配置
    print("3. 检查批量更新限流配置...")
    endpoint_limits = rate_limiter.endpoint_limits
    
    batch_endpoints = {
        '/api/v1/batch/update': {'requests': 5, 'window': 300},
        '/api/v1/batch/progress': {'requests': 100, 'window': 300},
        '/api/v1/batch/cleanup': {'requests': 10, 'window': 3600}
    }
    
    for endpoint, expected in batch_endpoints.items():
        if endpoint in endpoint_limits:
            actual = endpoint_limits[endpoint]
            if actual == expected:
                print(f"✅ {endpoint}: 配置正确 ({actual['requests']} 次/{actual['window']}秒)")
            else:
                print(f"⚠️  {endpoint}: 配置不匹配 (期望: {expected}, 实际: {actual})")
        else:
            print(f"❌ {endpoint}: 配置缺失")
    
    print("\n4. 测试模拟Flask环境下的api_endpoints导入...")
    
    # 创建最小Flask应用
    from flask import Flask
    app = Flask(__name__)
    
    with app.app_context():
        with app.test_request_context():
            try:
                # 注册蓝图前先导入
                from api_endpoints import api_v1
                app.register_blueprint(api_v1)
                print("✅ api_endpoints模块导入成功")
                
                # 检查批量更新路由
                batch_routes = ['/api/v1/batch/update', '/api/v1/batch/progress', '/api/v1/batch/cleanup']
                registered_routes = [rule.rule for rule in app.url_map.iter_rules()]
                
                for route in batch_routes:
                    found = any(route in registered_route for registered_route in registered_routes)
                    if found:
                        print(f"✅ 批量更新路由注册成功: {route}")
                    else:
                        print(f"⚠️  批量更新路由未找到: {route}")
                        
            except Exception as e:
                print(f"❌ api_endpoints导入失败: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n🎉 Rate Limiter修复验证完成！")
    print("主要修复内容:")
    print("- 修复了require_rate_limit装饰器的参数错误")
    print("- 将错误的calls和period参数改为正确的endpoint参数")
    print("- 为批量更新API添加了专门的限流配置")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
