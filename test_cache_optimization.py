#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存机制优化测试
"""

import time
import random
import json
from typing import List, Dict
from data_service import DataService
from stock_cache_manager import stock_cache_manager
from advanced_cache_manager import CacheStrategy

def test_cache_optimization():
    """测试缓存机制优化效果"""
    print('测试缓存机制优化...')
    print('=' * 60)
    
    data_service = DataService()
    test_stocks = ['000001', '000002', '600000', '600036', '000858', 
                   '002415', '000063', '600519', '000166', '600276']
    
    # 1. 测试传统缓存 vs 高级缓存性能对比
    print("1. 缓存性能对比测试...")
    
    # 传统缓存测试
    print("   传统缓存测试...")
    start_time = time.time()
    traditional_results = {}
    for stock_code in test_stocks:
        try:
            result = data_service.get_stock_basic_info(stock_code, use_advanced_cache=False)
            if result:
                traditional_results[stock_code] = result
        except Exception as e:
            print(f"   传统缓存查询 {stock_code} 失败: {e}")
    
    traditional_time = time.time() - start_time
    print(f"   传统缓存: {len(traditional_results)}/{len(test_stocks)} 成功，耗时: {traditional_time:.3f}秒")
    
    # 高级缓存测试
    print("   高级缓存测试...")
    start_time = time.time()
    advanced_results = {}
    for stock_code in test_stocks:
        try:
            result = data_service.get_stock_basic_info(stock_code, use_advanced_cache=True)
            if result:
                advanced_results[stock_code] = result
        except Exception as e:
            print(f"   高级缓存查询 {stock_code} 失败: {e}")
    
    advanced_time = time.time() - start_time
    print(f"   高级缓存: {len(advanced_results)}/{len(test_stocks)} 成功，耗时: {advanced_time:.3f}秒")
    
    if traditional_time > 0 and advanced_time > 0:
        speedup = traditional_time / advanced_time
        print(f"   性能提升: {speedup:.2f}x")
    
    # 2. 测试缓存命中率
    print("\n2. 缓存命中率测试...")
    
    # 重复查询相同数据测试命中率
    print("   重复查询测试...")
    hit_test_stocks = test_stocks[:5]
    
    # 第一轮查询（冷缓存）
    start_time = time.time()
    for stock_code in hit_test_stocks:
        stock_cache_manager.get_stock_basic_info(stock_code)
    cold_time = time.time() - start_time
    
    # 第二轮查询（热缓存）
    start_time = time.time()
    for stock_code in hit_test_stocks:
        stock_cache_manager.get_stock_basic_info(stock_code)
    hot_time = time.time() - start_time
    
    print(f"   冷缓存查询: {cold_time:.3f}秒")
    print(f"   热缓存查询: {hot_time:.3f}秒")
    if hot_time > 0:
        cache_speedup = cold_time / hot_time
        print(f"   缓存加速: {cache_speedup:.2f}x")
    
    # 3. 测试批量缓存操作
    print("\n3. 批量缓存操作测试...")
    
    # 批量获取测试
    start_time = time.time()
    batch_results, cache_misses = stock_cache_manager.batch_get_stock_basic_info(test_stocks)
    batch_time = time.time() - start_time
    
    print(f"   批量获取: {len(batch_results)}/{len(test_stocks)} 命中，耗时: {batch_time:.3f}秒")
    print(f"   缓存未命中: {len(cache_misses)} 只股票")
    
    # 批量设置测试
    test_data_list = []
    for i, stock_code in enumerate(test_stocks):
        test_data_list.append({
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
            'pb_ratio': random.uniform(1, 10)
        })
    
    start_time = time.time()
    batch_set_success = stock_cache_manager.batch_set_stock_basic_info(test_data_list)
    batch_set_time = time.time() - start_time
    
    print(f"   批量设置: {'成功' if batch_set_success else '失败'}，耗时: {batch_set_time:.3f}秒")
    
    # 4. 测试缓存策略效果
    print("\n4. 缓存策略测试...")
    
    # 模拟不同访问模式
    access_patterns = {
        'random': lambda: random.choice(test_stocks),
        'hot_data': lambda: random.choice(test_stocks[:3]),  # 前3只股票为热点数据
        'sequential': lambda: test_stocks[time.time() % len(test_stocks)]
    }
    
    for pattern_name, pattern_func in access_patterns.items():
        print(f"   测试 {pattern_name} 访问模式...")
        start_time = time.time()
        
        for _ in range(50):  # 50次访问
            stock_code = pattern_func()
            stock_cache_manager.get_stock_basic_info(stock_code)
        
        pattern_time = time.time() - start_time
        print(f"     {pattern_name}: {pattern_time:.3f}秒，平均每次: {pattern_time/50:.4f}秒")
    
    # 5. 测试缓存清理和失效
    print("\n5. 缓存清理测试...")
    
    # 获取清理前的缓存统计
    stats_before = stock_cache_manager.get_stats()
    l1_items_before = stats_before['cache_sizes']['l1_items']
    
    # 失效特定股票缓存
    test_stock = test_stocks[0]
    stock_cache_manager.invalidate_stock_data(stock_code=test_stock)
    print(f"   失效股票 {test_stock} 的缓存")
    
    # 失效特定类型缓存
    stock_cache_manager.invalidate_stock_data(data_type='basic_info')
    print(f"   失效所有基本信息缓存")
    
    # 获取清理后的缓存统计
    stats_after = stock_cache_manager.get_stats()
    l1_items_after = stats_after['cache_sizes']['l1_items']
    
    print(f"   缓存项数量: {l1_items_before} -> {l1_items_after}")
    
    # 6. 测试缓存压缩效果
    print("\n6. 缓存压缩测试...")
    
    # 创建大数据对象测试压缩
    large_data = {
        'stock_code': '000001',
        'large_field': 'x' * 5000,  # 5KB数据
        'repeated_data': ['test_data'] * 1000
    }
    
    start_time = time.time()
    stock_cache_manager.set('large_data_test', large_data, ttl=300, test_key='compression')
    set_time = time.time() - start_time
    
    start_time = time.time()
    retrieved_data = stock_cache_manager.get('large_data_test', ttl=300, test_key='compression')
    get_time = time.time() - start_time
    
    compression_success = retrieved_data is not None and retrieved_data == large_data
    print(f"   压缩测试: {'成功' if compression_success else '失败'}")
    print(f"   设置耗时: {set_time:.4f}秒，获取耗时: {get_time:.4f}秒")
    
    # 7. 获取详细性能报告
    print("\n7. 缓存性能报告...")
    
    performance_report = stock_cache_manager.get_cache_performance_report()
    
    print("   整体性能:")
    overall = performance_report['overall_performance']
    print(f"     总请求数: {overall['total_requests']}")
    print(f"     总命中数: {overall['total_hits']}")
    print(f"     整体命中率: {overall['overall_hit_rate']:.2%}")
    print(f"     缓存效率: {overall['cache_efficiency']}")
    
    print("   各级缓存性能:")
    level_perf = performance_report['level_performance']
    for level, stats in level_perf.items():
        if stats and level.endswith('_cache'):
            level_name = level.replace('_cache', '').upper()
            print(f"     {level_name}: 命中率 {stats['hit_rate']:.2%}, "
                  f"请求数 {stats['total_requests']}")
    
    print("   热点数据:")
    hot_stocks = performance_report.get('hot_stocks', [])
    if hot_stocks:
        print(f"     热点股票: {', '.join(hot_stocks[:5])}")
    else:
        print(f"     暂无热点数据")
    
    print("   优化建议:")
    recommendations = performance_report.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        print(f"     {i}. {rec}")
    
    # 8. 测试预加载功能
    print("\n8. 预加载功能测试...")
    
    preload_stocks = ['300001', '300002', '300003']
    start_time = time.time()
    
    # 启动预加载任务
    preload_future = stock_cache_manager.preload_market_data(preload_stocks)
    
    # 等待预加载完成
    try:
        preload_future.result(timeout=30)  # 最多等待30秒
        preload_time = time.time() - start_time
        print(f"   预加载完成: {len(preload_stocks)} 只股票，耗时: {preload_time:.3f}秒")
    except Exception as e:
        print(f"   预加载失败: {e}")
    
    print("\n" + "=" * 60)
    print("缓存机制优化测试完成！")
    
    # 9. 性能总结
    print("\n9. 性能优化总结:")
    
    if 'speedup' in locals() and speedup > 1:
        print(f"   ✓ 高级缓存性能提升: {speedup:.2f}x")
    else:
        print(f"   ⚠️  高级缓存性能提升不明显")
    
    if 'cache_speedup' in locals() and cache_speedup > 5:
        print(f"   ✓ 缓存命中加速: {cache_speedup:.2f}x")
    else:
        print(f"   ⚠️  缓存命中加速效果一般")
    
    if overall['overall_hit_rate'] > 0.8:
        print(f"   ✓ 缓存命中率优秀: {overall['overall_hit_rate']:.2%}")
    elif overall['overall_hit_rate'] > 0.6:
        print(f"   ✓ 缓存命中率良好: {overall['overall_hit_rate']:.2%}")
    else:
        print(f"   ⚠️  缓存命中率需要改进: {overall['overall_hit_rate']:.2%}")
    
    if compression_success:
        print(f"   ✓ 数据压缩功能正常")
    else:
        print(f"   ⚠️  数据压缩功能异常")
    
    print("\n缓存优化建议:")
    for rec in recommendations:
        print(f"   • {rec}")


if __name__ == "__main__":
    test_cache_optimization()
