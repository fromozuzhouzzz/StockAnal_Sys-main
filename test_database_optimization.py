#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库优化效果测试
"""

import time
import random
from typing import List, Dict
from data_service import DataService
from database_optimizer import db_optimizer
from database import USE_DATABASE

def test_database_optimization():
    """测试数据库优化效果"""
    print('测试数据库连接和查询优化...')
    print('=' * 60)
    
    if not USE_DATABASE:
        print("❌ 数据库未启用，无法进行测试")
        return
    
    data_service = DataService()
    test_stocks = ['000001', '000002', '600000', '600036', '000858', 
                   '002415', '000063', '600519', '000166', '600276']
    
    # 1. 测试数据库索引优化
    print("1. 测试数据库索引优化...")
    start_time = time.time()
    success = db_optimizer.optimize_database_indexes()
    elapsed = time.time() - start_time
    print(f"   索引优化: {'✓' if success else '✗'} 耗时: {elapsed:.3f}秒")
    
    # 2. 测试单个查询 vs 批量查询性能
    print("\n2. 测试查询性能对比...")
    
    # 单个查询测试
    print("   单个查询测试...")
    start_time = time.time()
    single_results = {}
    for stock_code in test_stocks:
        try:
            result = data_service.get_stock_basic_info(stock_code)
            if result:
                single_results[stock_code] = result
        except Exception as e:
            print(f"   单个查询 {stock_code} 失败: {e}")
    
    single_time = time.time() - start_time
    print(f"   单个查询: {len(single_results)}/{len(test_stocks)} 成功，耗时: {single_time:.3f}秒")
    print(f"   平均每股: {single_time/len(test_stocks):.3f}秒")
    
    # 批量查询测试
    print("   批量查询测试...")
    start_time = time.time()
    try:
        batch_results, missing_stocks = data_service.batch_get_stock_basic_info(test_stocks)
        batch_time = time.time() - start_time
        print(f"   批量查询: {len(batch_results)}/{len(test_stocks)} 命中缓存，耗时: {batch_time:.3f}秒")
        print(f"   平均每股: {batch_time/len(test_stocks):.3f}秒")
        print(f"   性能提升: {single_time/batch_time:.1f}x" if batch_time > 0 else "   性能提升: ∞")
        
        if missing_stocks:
            print(f"   需要API查询: {missing_stocks}")
    except Exception as e:
        print(f"   批量查询失败: {e}")
    
    # 3. 测试数据库连接池性能
    print("\n3. 测试数据库连接池性能...")
    connection_times = []
    
    for i in range(10):
        start_time = time.time()
        try:
            from sqlalchemy import text
            with db_optimizer.get_optimized_session() as session:
                # 执行简单查询
                result = session.execute(text("SELECT 1")).fetchone()
            elapsed = time.time() - start_time
            connection_times.append(elapsed)
        except Exception as e:
            print(f"   连接测试 {i+1} 失败: {e}")
    
    if connection_times:
        avg_connection_time = sum(connection_times) / len(connection_times)
        print(f"   平均连接时间: {avg_connection_time:.4f}秒")
        print(f"   最快连接: {min(connection_times):.4f}秒")
        print(f"   最慢连接: {max(connection_times):.4f}秒")
    
    # 4. 测试缓存清理性能
    print("\n4. 测试缓存清理性能...")
    start_time = time.time()
    cleaned_count = db_optimizer.optimize_expired_cache_cleanup()
    cleanup_time = time.time() - start_time
    print(f"   清理过期缓存: {cleaned_count} 条记录，耗时: {cleanup_time:.3f}秒")
    
    # 5. 获取数据库统计信息
    print("\n5. 数据库统计信息...")
    try:
        stats = db_optimizer.get_database_stats()
        
        print("   连接统计:")
        conn_stats = stats['connection_stats']
        print(f"     总查询数: {conn_stats['total_queries']}")
        print(f"     慢查询数: {conn_stats['slow_queries']}")
        print(f"     失败查询数: {conn_stats['failed_queries']}")
        print(f"     平均查询时间: {conn_stats['avg_query_time']:.4f}秒")
        
        if conn_stats['total_queries'] > 0:
            print(f"     慢查询率: {conn_stats['slow_queries']/conn_stats['total_queries']*100:.1f}%")
            print(f"     失败率: {conn_stats['failed_queries']/conn_stats['total_queries']*100:.1f}%")
        
        print("   表统计:")
        for table_name, table_stats in stats['table_stats'].items():
            print(f"     {table_name}: {table_stats['record_count']} 条记录")
        
        if 'performance_metrics' in stats and stats['performance_metrics']:
            print("   性能指标:")
            perf = stats['performance_metrics']
            print(f"     慢查询率: {perf['slow_query_rate']*100:.1f}%")
            print(f"     错误率: {perf['error_rate']*100:.1f}%")
            print(f"     平均查询时间: {perf['avg_query_time']:.4f}秒")
            
    except Exception as e:
        print(f"   获取统计信息失败: {e}")
    
    # 6. 测试批量保存性能
    print("\n6. 测试批量保存性能...")
    test_data = []
    for i, stock_code in enumerate(test_stocks):
        test_data.append({
            'stock_code': stock_code,
            'stock_name': f'测试股票{i+1}',
            'market_type': 'A',
            'industry': '测试行业',
            'sector': '测试板块',
            'list_date': '20200101',
            'total_share': random.uniform(1000000, 10000000),
            'float_share': random.uniform(500000, 5000000),
            'market_cap': random.uniform(1000000000, 100000000000),
            'pe_ratio': random.uniform(10, 50),
            'pb_ratio': random.uniform(1, 10),
            'ttl': 604800  # 7天
        })
    
    start_time = time.time()
    try:
        success = db_optimizer.batch_save_stock_basic_info(test_data)
        save_time = time.time() - start_time
        print(f"   批量保存: {'✓' if success else '✗'} {len(test_data)} 条记录，耗时: {save_time:.3f}秒")
        print(f"   平均每条: {save_time/len(test_data):.4f}秒")
    except Exception as e:
        print(f"   批量保存失败: {e}")
    
    print("\n" + "=" * 60)
    print("数据库优化测试完成！")
    
    # 7. 性能建议
    print("\n7. 性能优化建议:")
    if conn_stats['total_queries'] > 0:
        if conn_stats['slow_queries'] / conn_stats['total_queries'] > 0.1:
            print("   ⚠️  慢查询率较高，建议检查索引和查询语句")
        else:
            print("   ✓ 查询性能良好")
        
        if conn_stats['failed_queries'] / conn_stats['total_queries'] > 0.05:
            print("   ⚠️  查询失败率较高，建议检查数据库连接")
        else:
            print("   ✓ 查询稳定性良好")
    
    if batch_time > 0 and single_time > 0:
        speedup = single_time / batch_time
        if speedup > 5:
            print("   ✓ 批量查询性能优秀")
        elif speedup > 2:
            print("   ✓ 批量查询性能良好")
        else:
            print("   ⚠️  批量查询优势不明显，建议检查缓存策略")


if __name__ == "__main__":
    test_database_optimization()
