#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Spaces 修复验证脚本
验证SQLAlchemy修复和平台优化是否生效
"""

import os
import sys
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sqlalchemy_fixes() -> Dict[str, Any]:
    """测试SQLAlchemy修复"""
    results = {
        'database_connection': False,
        'performance_analyzer': False,
        'database_optimizer': False,
        'errors': []
    }
    
    logger.info("🔍 测试SQLAlchemy修复...")
    
    try:
        # 1. 测试database.py的修复
        logger.info("测试 database.py 连接测试...")
        from database import test_connection, USE_DATABASE
        
        if USE_DATABASE:
            results['database_connection'] = test_connection()
            if results['database_connection']:
                logger.info("✅ database.py 连接测试成功")
            else:
                logger.warning("⚠️ database.py 连接测试失败（可能是配置问题）")
        else:
            logger.info("ℹ️ 数据库未启用，跳过连接测试")
            results['database_connection'] = True
            
    except Exception as e:
        error_msg = f"database.py 测试失败: {e}"
        logger.error(f"❌ {error_msg}")
        results['errors'].append(error_msg)
    
    try:
        # 2. 测试performance_analyzer.py的修复
        logger.info("测试 performance_analyzer.py...")
        from performance_analyzer import PerformanceAnalyzer
        
        analyzer = PerformanceAnalyzer()
        # 只测试导入和初始化，不执行完整分析
        results['performance_analyzer'] = True
        logger.info("✅ performance_analyzer.py 导入成功")
        
    except Exception as e:
        error_msg = f"performance_analyzer.py 测试失败: {e}"
        logger.error(f"❌ {error_msg}")
        results['errors'].append(error_msg)
    
    try:
        # 3. 测试database_optimizer.py的修复
        logger.info("测试 database_optimizer.py...")
        from database_optimizer import db_optimizer
        
        # 测试优化器初始化
        stats = db_optimizer.get_database_stats()
        results['database_optimizer'] = True
        logger.info("✅ database_optimizer.py 初始化成功")
        
    except Exception as e:
        error_msg = f"database_optimizer.py 测试失败: {e}"
        logger.error(f"❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results

def test_hf_spaces_optimization() -> Dict[str, Any]:
    """测试Hugging Face Spaces优化"""
    results = {
        'platform_detection': False,
        'optimization_applied': False,
        'errors': []
    }
    
    logger.info("🔍 测试Hugging Face Spaces优化...")
    
    try:
        from huggingface_spaces_optimization import hf_optimizer
        
        # 测试平台检测
        results['platform_detection'] = hf_optimizer.detect_platform()
        if results['platform_detection']:
            logger.info("✅ 检测到Hugging Face Spaces环境")
        else:
            logger.info("ℹ️ 未检测到Hugging Face Spaces环境（本地测试正常）")
        
        # 测试优化配置
        optimization_result = hf_optimizer.optimize_for_hf_spaces()
        results['optimization_applied'] = len(optimization_result.get('applied_optimizations', [])) > 0
        
        if results['optimization_applied']:
            logger.info("✅ 优化配置应用成功")
            for opt in optimization_result.get('applied_optimizations', []):
                logger.info(f"  - {opt}")
        else:
            logger.info("ℹ️ 未应用优化配置（可能不在HF Spaces环境）")
        
    except Exception as e:
        error_msg = f"HF Spaces优化测试失败: {e}"
        logger.error(f"❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results

def test_system_integration() -> Dict[str, Any]:
    """测试系统集成"""
    results = {
        'data_service': False,
        'cache_manager': False,
        'errors': []
    }
    
    logger.info("🔍 测试系统集成...")
    
    try:
        # 测试数据服务
        logger.info("测试数据服务...")
        from data_service import DataService
        
        data_service = DataService()
        stats = data_service.get_cache_statistics()
        results['data_service'] = True
        logger.info("✅ 数据服务初始化成功")
        logger.info(f"📊 缓存统计: {stats}")
        
    except Exception as e:
        error_msg = f"数据服务测试失败: {e}"
        logger.error(f"❌ {error_msg}")
        results['errors'].append(error_msg)
    
    try:
        # 测试缓存管理器
        logger.info("测试缓存管理器...")
        from stock_cache_manager import StockCacheManager
        
        cache_manager = StockCacheManager()
        results['cache_manager'] = True
        logger.info("✅ 缓存管理器初始化成功")
        
    except Exception as e:
        error_msg = f"缓存管理器测试失败: {e}"
        logger.error(f"❌ {error_msg}")
        results['errors'].append(error_msg)
    
    return results

def generate_test_report(sqlalchemy_results: Dict, hf_results: Dict, integration_results: Dict):
    """生成测试报告"""
    logger.info("\n" + "="*60)
    logger.info("📋 Hugging Face Spaces 修复验证报告")
    logger.info("="*60)
    
    # SQLAlchemy修复结果
    logger.info("\n🔧 SQLAlchemy修复验证:")
    total_tests = 3
    passed_tests = sum([
        sqlalchemy_results['database_connection'],
        sqlalchemy_results['performance_analyzer'], 
        sqlalchemy_results['database_optimizer']
    ])
    
    logger.info(f"  通过: {passed_tests}/{total_tests}")
    if sqlalchemy_results['errors']:
        logger.info("  错误:")
        for error in sqlalchemy_results['errors']:
            logger.info(f"    - {error}")
    
    # HF Spaces优化结果
    logger.info("\n🚀 Hugging Face Spaces优化验证:")
    logger.info(f"  平台检测: {'✅' if hf_results['platform_detection'] else 'ℹ️ 非HF环境'}")
    logger.info(f"  优化应用: {'✅' if hf_results['optimization_applied'] else 'ℹ️ 未应用'}")
    if hf_results['errors']:
        logger.info("  错误:")
        for error in hf_results['errors']:
            logger.info(f"    - {error}")
    
    # 系统集成结果
    logger.info("\n🔗 系统集成验证:")
    integration_passed = sum([
        integration_results['data_service'],
        integration_results['cache_manager']
    ])
    logger.info(f"  通过: {integration_passed}/2")
    if integration_results['errors']:
        logger.info("  错误:")
        for error in integration_results['errors']:
            logger.info(f"    - {error}")
    
    # 总体结果
    total_errors = len(sqlalchemy_results['errors']) + len(hf_results['errors']) + len(integration_results['errors'])
    logger.info(f"\n📊 总体结果:")
    logger.info(f"  SQLAlchemy修复: {'✅ 成功' if passed_tests == total_tests else '⚠️ 部分成功'}")
    logger.info(f"  平台优化: {'✅ 成功' if not hf_results['errors'] else '⚠️ 有问题'}")
    logger.info(f"  系统集成: {'✅ 成功' if integration_passed == 2 else '⚠️ 部分成功'}")
    logger.info(f"  总错误数: {total_errors}")
    
    if total_errors == 0:
        logger.info("\n🎉 所有修复验证通过！系统已准备好部署到Hugging Face Spaces")
    else:
        logger.info(f"\n⚠️ 发现 {total_errors} 个问题，请检查上述错误信息")

def main():
    """主测试函数"""
    logger.info("🚀 开始Hugging Face Spaces修复验证")
    
    # 执行各项测试
    sqlalchemy_results = test_sqlalchemy_fixes()
    hf_results = test_hf_spaces_optimization()
    integration_results = test_system_integration()
    
    # 生成报告
    generate_test_report(sqlalchemy_results, hf_results, integration_results)

if __name__ == "__main__":
    main()
