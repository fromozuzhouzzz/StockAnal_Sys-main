#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试rate_limiter修复
验证require_rate_limit装饰器参数修复是否成功
"""

import sys
import logging
import traceback

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rate_limiter_import():
    """测试rate_limiter模块导入"""
    try:
        from rate_limiter import require_rate_limit, rate_limiter
        logger.info("✅ rate_limiter模块导入成功")
        
        # 测试装饰器创建
        decorator = require_rate_limit('/api/v1/test')
        logger.info("✅ require_rate_limit装饰器创建成功")
        
        # 测试限流配置
        endpoint_limits = rate_limiter.endpoint_limits
        logger.info(f"✅ 端点限流配置: {len(endpoint_limits)} 个端点")
        
        # 检查批量更新相关的限流配置
        batch_endpoints = [
            '/api/v1/batch/update',
            '/api/v1/batch/progress', 
            '/api/v1/batch/cleanup'
        ]
        
        for endpoint in batch_endpoints:
            if endpoint in endpoint_limits:
                config = endpoint_limits[endpoint]
                logger.info(f"✅ {endpoint}: {config['requests']} 次/{config['window']}秒")
            else:
                logger.warning(f"⚠️  {endpoint}: 未配置限流")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ rate_limiter模块导入失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_api_endpoints_import():
    """测试api_endpoints模块导入"""
    try:
        # 模拟Flask应用环境
        from flask import Flask
        app = Flask(__name__)
        
        with app.app_context():
            # 创建请求上下文
            with app.test_request_context():
                from api_endpoints import api_v1
                logger.info("✅ api_endpoints模块导入成功")
                
                # 检查蓝图注册的路由
                rules = []
                for rule in app.url_map.iter_rules():
                    if rule.endpoint.startswith('api_v1.'):
                        rules.append(rule.rule)
                
                logger.info(f"✅ API路由注册成功: {len(rules)} 个路由")
                
                # 检查批量更新相关路由
                batch_routes = [
                    '/api/v1/batch/update',
                    '/api/v1/batch/progress/<session_id>',
                    '/api/v1/batch/cleanup'
                ]
                
                for route in batch_routes:
                    # 简化检查，只看是否包含关键路径
                    route_base = route.split('<')[0]  # 移除参数部分
                    found = any(route_base in rule for rule in rules)
                    if found:
                        logger.info(f"✅ 批量更新路由: {route}")
                    else:
                        logger.warning(f"⚠️  批量更新路由未找到: {route}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ api_endpoints模块导入失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_web_server_import():
    """测试web_server模块导入"""
    try:
        import web_server
        logger.info("✅ web_server模块导入成功")
        
        # 检查Flask应用是否创建成功
        if hasattr(web_server, 'app'):
            logger.info("✅ Flask应用创建成功")
        else:
            logger.warning("⚠️  Flask应用未找到")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ web_server模块导入失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_batch_updater_compatibility():
    """测试批量更新器兼容性"""
    try:
        from batch_data_updater import batch_updater
        logger.info("✅ batch_data_updater模块导入成功")
        
        # 测试基本功能
        if hasattr(batch_updater, 'start_batch_update'):
            logger.info("✅ start_batch_update方法存在")
        
        if hasattr(batch_updater, 'get_update_progress'):
            logger.info("✅ get_update_progress方法存在")
        
        if hasattr(batch_updater, 'cleanup_old_sessions'):
            logger.info("✅ cleanup_old_sessions方法存在")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ batch_data_updater模块导入失败: {e}")
        logger.error(traceback.format_exc())
        return False

def test_hf_spaces_compatibility():
    """测试Hugging Face Spaces兼容性"""
    try:
        # 模拟HF Spaces环境变量
        import os
        original_space = os.environ.get('SPACE_ID')
        os.environ['SPACE_ID'] = 'test-space'
        
        try:
            # 测试在HF Spaces环境下的导入
            from rate_limiter import require_rate_limit
            from api_endpoints import api_v1
            
            logger.info("✅ HF Spaces环境兼容性测试通过")
            return True
            
        finally:
            # 恢复环境变量
            if original_space is not None:
                os.environ['SPACE_ID'] = original_space
            elif 'SPACE_ID' in os.environ:
                del os.environ['SPACE_ID']
        
    except Exception as e:
        logger.error(f"❌ HF Spaces兼容性测试失败: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("Rate Limiter修复验证测试")
    print("=" * 60)
    
    tests = [
        ("Rate Limiter模块导入", test_rate_limiter_import),
        ("API Endpoints模块导入", test_api_endpoints_import),
        ("Web Server模块导入", test_web_server_import),
        ("批量更新器兼容性", test_batch_updater_compatibility),
        ("HF Spaces兼容性", test_hf_spaces_compatibility)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 测试: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
            
            if result:
                print(f"✅ {test_name}: 通过")
            else:
                print(f"❌ {test_name}: 失败")
                
        except Exception as e:
            logger.error(f"测试 {test_name} 执行异常: {e}")
            results[test_name] = False
            print(f"❌ {test_name}: 异常")
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过！Rate Limiter修复成功！")
        return True
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
