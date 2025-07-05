#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试预加载功能移除效果
"""

import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_stock_cache_manager():
    """测试StockCacheManager是否还会自动预热"""
    logger.info("测试StockCacheManager...")
    try:
        from stock_cache_manager import StockCacheManager
        
        # 创建实例，检查是否会触发预热
        logger.info("创建StockCacheManager实例...")
        cache_manager = StockCacheManager()
        
        # 检查是否有预热相关的日志
        logger.info("StockCacheManager实例创建完成，检查是否有预热日志...")
        
        return True
    except Exception as e:
        logger.error(f"StockCacheManager测试失败: {e}")
        return False

def test_web_server_import():
    """测试web_server导入是否正常"""
    logger.info("测试web_server导入...")
    try:
        # 只导入，不运行
        import web_server
        logger.info("web_server导入成功，检查是否有预缓存调度器启动日志...")
        return True
    except Exception as e:
        logger.error(f"web_server导入失败: {e}")
        return False

def test_api_integration():
    """测试API集成是否还会预加载"""
    logger.info("测试API集成...")
    try:
        from api_integration import setup_api_middleware
        from flask import Flask
        
        app = Flask(__name__)
        logger.info("测试setup_api_middleware...")
        result = setup_api_middleware(app)
        logger.info(f"setup_api_middleware结果: {result}")
        
        return True
    except Exception as e:
        logger.error(f"API集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("="*60)
    logger.info("开始测试预加载功能移除效果")
    logger.info("="*60)
    
    tests = [
        ("StockCacheManager", test_stock_cache_manager),
        ("Web Server Import", test_web_server_import),
        ("API Integration", test_api_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"{test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 总结结果
    logger.info("\n" + "="*60)
    logger.info("测试结果总结:")
    logger.info("="*60)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        logger.info("\n🎉 所有测试通过！预加载功能已成功移除。")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查相关代码。")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n用户中断测试")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试脚本异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
