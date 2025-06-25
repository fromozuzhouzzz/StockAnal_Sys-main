#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试股票分析系统优化效果
"""

from data_service import DataService
from batch_optimizer import BatchOptimizer
from performance_monitor import performance_monitor
import time

def test_optimizations():
    """测试系统优化效果"""
    print('测试优化后的股票分析系统...')
    print('=' * 50)

    # 创建服务实例
    data_service = DataService()
    batch_optimizer = BatchOptimizer(data_service)

    # 测试单个股票查询
    print('1. 测试单个股票查询优化...')
    start_time = time.time()
    try:
        result = data_service.get_stock_basic_info('000001')
        elapsed = time.time() - start_time
        if result:
            print(f'✓ 股票000001查询成功，耗时: {elapsed:.3f}秒')
        else:
            print(f'✗ 股票000001查询失败，耗时: {elapsed:.3f}秒')
    except Exception as e:
        elapsed = time.time() - start_time
        print(f'✗ 股票000001查询异常: {e}，耗时: {elapsed:.3f}秒')

    # 测试批量处理
    print('\n2. 测试批量处理优化...')
    test_stocks = ['000001', '000002', '600000', '600036', '000858']
    start_time = time.time()
    try:
        results = batch_optimizer.process_stock_batch(test_stocks, 'basic_info', max_workers=5)
        elapsed = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        print(f'批量处理完成: {successful}/{len(results)} 成功，总耗时: {elapsed:.3f}秒')
        print(f'平均每股耗时: {elapsed/len(results):.3f}秒')
        print(f'吞吐量: {len(results)/elapsed:.2f}股/秒')
    except Exception as e:
        elapsed = time.time() - start_time
        print(f'✗ 批量处理异常: {e}，耗时: {elapsed:.3f}秒')

    # 获取性能统计
    print('\n3. 性能监控统计...')
    try:
        summary = performance_monitor.get_performance_summary()
        print(f'缓存命中率: {summary["rates"]["cache_hit_rate"]:.2%}')
        print(f'错误率: {summary["rates"]["error_rate"]:.2%}')
        print(f'平均API调用时间: {summary["avg_times"]["api_call_time"]:.3f}秒')
    except Exception as e:
        print(f'获取性能统计失败: {e}')

    print('\n测试完成！')

if __name__ == "__main__":
    test_optimizations()
