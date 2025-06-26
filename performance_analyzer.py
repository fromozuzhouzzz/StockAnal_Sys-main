#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析系统性能分析工具
开发者：熊猫大侠
版本：v1.0.0
功能：分析系统性能瓶颈，包括缓存命中率、数据库查询效率、API调用时间等
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import json
import os
from contextlib import contextmanager

# 导入系统模块
from data_service import DataService
from database import get_session, USE_DATABASE, get_cache_stats
from stock_analyzer import StockAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.data_service = DataService()
        self.analyzer = StockAnalyzer()
        self.performance_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'db_queries': 0,
            'api_calls': 0,
            'total_query_time': 0,
            'api_call_times': [],
            'db_query_times': [],
            'cache_query_times': []
        }
        self.lock = threading.Lock()
        
    def reset_stats(self):
        """重置统计信息"""
        with self.lock:
            self.performance_stats = {
                'cache_hits': 0,
                'cache_misses': 0,
                'db_queries': 0,
                'api_calls': 0,
                'total_query_time': 0,
                'api_call_times': [],
                'db_query_times': [],
                'cache_query_times': []
            }
    
    @contextmanager
    def measure_time(self, operation_type: str):
        """测量操作时间的上下文管理器"""
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            with self.lock:
                self.performance_stats['total_query_time'] += elapsed
                if operation_type == 'api':
                    self.performance_stats['api_calls'] += 1
                    self.performance_stats['api_call_times'].append(elapsed)
                elif operation_type == 'db':
                    self.performance_stats['db_queries'] += 1
                    self.performance_stats['db_query_times'].append(elapsed)
                elif operation_type == 'cache':
                    self.performance_stats['cache_query_times'].append(elapsed)
    
    def test_cache_performance(self, test_stocks: List[str] = None) -> Dict:
        """测试缓存性能"""
        if test_stocks is None:
            test_stocks = ['000001', '000002', '600000', '600036', '000858']
        
        logger.info(f"开始测试缓存性能，测试股票: {test_stocks}")
        self.reset_stats()
        
        results = {
            'test_stocks': test_stocks,
            'cache_performance': {},
            'timing_analysis': {},
            'recommendations': []
        }
        
        # 第一轮：冷缓存测试
        logger.info("第一轮：冷缓存测试")
        cold_cache_times = []
        for stock_code in test_stocks:
            start_time = time.time()
            try:
                data = self.data_service.get_stock_basic_info(stock_code)
                elapsed = time.time() - start_time
                cold_cache_times.append(elapsed)
                logger.info(f"股票 {stock_code} 冷缓存查询耗时: {elapsed:.3f}秒")
            except Exception as e:
                logger.error(f"查询股票 {stock_code} 失败: {e}")
                cold_cache_times.append(None)
        
        # 等待一秒，然后进行热缓存测试
        time.sleep(1)
        
        # 第二轮：热缓存测试
        logger.info("第二轮：热缓存测试")
        hot_cache_times = []
        for stock_code in test_stocks:
            start_time = time.time()
            try:
                data = self.data_service.get_stock_basic_info(stock_code)
                elapsed = time.time() - start_time
                hot_cache_times.append(elapsed)
                logger.info(f"股票 {stock_code} 热缓存查询耗时: {elapsed:.3f}秒")
            except Exception as e:
                logger.error(f"查询股票 {stock_code} 失败: {e}")
                hot_cache_times.append(None)
        
        # 分析结果
        valid_cold = [t for t in cold_cache_times if t is not None]
        valid_hot = [t for t in hot_cache_times if t is not None]
        
        if valid_cold and valid_hot:
            avg_cold = sum(valid_cold) / len(valid_cold)
            avg_hot = sum(valid_hot) / len(valid_hot)
            speedup = avg_cold / avg_hot if avg_hot > 0 else 0
            
            results['cache_performance'] = {
                'avg_cold_cache_time': avg_cold,
                'avg_hot_cache_time': avg_hot,
                'cache_speedup': speedup,
                'cache_efficiency': (1 - avg_hot/avg_cold) * 100 if avg_cold > 0 else 0
            }
            
            logger.info(f"缓存性能分析:")
            logger.info(f"  平均冷缓存时间: {avg_cold:.3f}秒")
            logger.info(f"  平均热缓存时间: {avg_hot:.3f}秒")
            logger.info(f"  缓存加速比: {speedup:.2f}x")
            logger.info(f"  缓存效率: {results['cache_performance']['cache_efficiency']:.1f}%")
        
        return results
    
    def test_batch_performance(self, stock_list: List[str] = None, batch_sizes: List[int] = None) -> Dict:
        """测试批量处理性能"""
        if stock_list is None:
            stock_list = ['000001', '000002', '600000', '600036', '000858', '002415', '000063', '600519']
        
        if batch_sizes is None:
            batch_sizes = [1, 5, 10, 20]
        
        logger.info(f"开始测试批量处理性能，股票数量: {len(stock_list)}")
        
        results = {
            'stock_count': len(stock_list),
            'batch_tests': {},
            'optimal_batch_size': None,
            'recommendations': []
        }
        
        for batch_size in batch_sizes:
            logger.info(f"测试批次大小: {batch_size}")
            start_time = time.time()
            
            # 模拟批量处理
            processed = 0
            for i in range(0, len(stock_list), batch_size):
                batch = stock_list[i:i + batch_size]
                batch_start = time.time()
                
                for stock_code in batch:
                    try:
                        # 模拟快速分析
                        data = self.data_service.get_stock_basic_info(stock_code)
                        processed += 1
                    except Exception as e:
                        logger.error(f"处理股票 {stock_code} 失败: {e}")
                
                batch_time = time.time() - batch_start
                logger.debug(f"批次 {batch} 处理耗时: {batch_time:.3f}秒")
            
            total_time = time.time() - start_time
            avg_time_per_stock = total_time / processed if processed > 0 else 0
            
            results['batch_tests'][batch_size] = {
                'total_time': total_time,
                'processed_count': processed,
                'avg_time_per_stock': avg_time_per_stock,
                'throughput': processed / total_time if total_time > 0 else 0
            }
            
            logger.info(f"批次大小 {batch_size}: 总耗时 {total_time:.3f}秒, "
                       f"平均每股 {avg_time_per_stock:.3f}秒, "
                       f"吞吐量 {results['batch_tests'][batch_size]['throughput']:.2f}股/秒")
        
        # 找出最优批次大小
        best_batch_size = min(results['batch_tests'].keys(), 
                             key=lambda x: results['batch_tests'][x]['avg_time_per_stock'])
        results['optimal_batch_size'] = best_batch_size
        
        return results
    
    def analyze_database_performance(self) -> Dict:
        """分析数据库性能"""
        logger.info("开始分析数据库性能")
        
        results = {
            'database_enabled': USE_DATABASE,
            'connection_test': False,
            'cache_stats': {},
            'query_performance': {},
            'recommendations': []
        }
        
        if not USE_DATABASE:
            results['recommendations'].append("数据库未启用，建议启用数据库缓存以提高性能")
            return results
        
        try:
            # 测试数据库连接
            from sqlalchemy import text
            session = get_session()
            session.execute(text("SELECT 1"))
            session.close()
            results['connection_test'] = True
            logger.info("数据库连接测试成功")
            
            # 获取缓存统计
            cache_stats = get_cache_stats()
            results['cache_stats'] = cache_stats
            logger.info(f"数据库缓存统计: {cache_stats}")
            
            # 测试查询性能
            test_queries = [
                ("基本信息查询", "SELECT COUNT(*) FROM stock_basic_info"),
                ("实时数据查询", "SELECT COUNT(*) FROM stock_realtime_data"),
                ("历史价格查询", "SELECT COUNT(*) FROM stock_price_history"),
            ]
            
            query_times = {}
            session = get_session()
            
            for query_name, sql in test_queries:
                start_time = time.time()
                try:
                    result = session.execute(text(sql)).fetchone()
                    elapsed = time.time() - start_time
                    query_times[query_name] = {
                        'time': elapsed,
                        'count': result[0] if result else 0
                    }
                    logger.info(f"{query_name}: {elapsed:.3f}秒, 记录数: {result[0] if result else 0}")
                except Exception as e:
                    logger.error(f"{query_name} 失败: {e}")
                    query_times[query_name] = {'time': None, 'error': str(e)}
            
            session.close()
            results['query_performance'] = query_times
            
        except Exception as e:
            logger.error(f"数据库性能分析失败: {e}")
            results['error'] = str(e)
            results['recommendations'].append(f"数据库连接失败: {e}")
        
        return results
    
    def generate_performance_report(self) -> Dict:
        """生成完整的性能报告"""
        logger.info("开始生成性能报告")
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': {
                'database_enabled': USE_DATABASE,
                'cache_service_available': True
            },
            'cache_performance': {},
            'batch_performance': {},
            'database_performance': {},
            'overall_recommendations': []
        }
        
        try:
            # 缓存性能测试
            logger.info("执行缓存性能测试...")
            report['cache_performance'] = self.test_cache_performance()
            
            # 批量处理性能测试
            logger.info("执行批量处理性能测试...")
            report['batch_performance'] = self.test_batch_performance()
            
            # 数据库性能测试
            logger.info("执行数据库性能测试...")
            report['database_performance'] = self.analyze_database_performance()
            
            # 生成总体建议
            self._generate_recommendations(report)
            
        except Exception as e:
            logger.error(f"性能报告生成失败: {e}")
            report['error'] = str(e)
        
        return report
    
    def _generate_recommendations(self, report: Dict):
        """生成优化建议"""
        recommendations = []
        
        # 缓存性能建议
        cache_perf = report.get('cache_performance', {}).get('cache_performance', {})
        if cache_perf:
            speedup = cache_perf.get('cache_speedup', 0)
            if speedup < 2:
                recommendations.append("缓存加速比较低，建议优化缓存策略")
            if cache_perf.get('cache_efficiency', 0) < 50:
                recommendations.append("缓存效率较低，建议增加缓存TTL或优化缓存逻辑")
        
        # 批量处理建议
        batch_perf = report.get('batch_performance', {})
        if batch_perf.get('optimal_batch_size'):
            optimal_size = batch_perf['optimal_batch_size']
            recommendations.append(f"建议使用批次大小: {optimal_size}")
        
        # 数据库建议
        db_perf = report.get('database_performance', {})
        if not db_perf.get('database_enabled'):
            recommendations.append("强烈建议启用数据库缓存以提高性能")
        elif not db_perf.get('connection_test'):
            recommendations.append("数据库连接存在问题，需要检查配置")
        
        report['overall_recommendations'] = recommendations
    
    def save_report(self, report: Dict, filename: str = None):
        """保存性能报告"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_report_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"性能报告已保存到: {filename}")
            return filename
        except Exception as e:
            logger.error(f"保存性能报告失败: {e}")
            return None


def main():
    """主函数"""
    print("=" * 60)
    print("股票分析系统性能分析工具")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer()
    
    # 生成完整性能报告
    report = analyzer.generate_performance_report()
    
    # 保存报告
    filename = analyzer.save_report(report)
    
    # 打印摘要
    print("\n性能分析摘要:")
    print("-" * 40)
    
    if 'cache_performance' in report:
        cache_perf = report['cache_performance'].get('cache_performance', {})
        if cache_perf:
            print(f"缓存加速比: {cache_perf.get('cache_speedup', 0):.2f}x")
            print(f"缓存效率: {cache_perf.get('cache_efficiency', 0):.1f}%")
    
    if 'batch_performance' in report:
        optimal_batch = report['batch_performance'].get('optimal_batch_size')
        if optimal_batch:
            print(f"最优批次大小: {optimal_batch}")
    
    if 'database_performance' in report:
        db_enabled = report['database_performance'].get('database_enabled', False)
        print(f"数据库状态: {'启用' if db_enabled else '未启用'}")
    
    print(f"\n详细报告已保存到: {filename}")
    
    # 打印建议
    recommendations = report.get('overall_recommendations', [])
    if recommendations:
        print("\n优化建议:")
        print("-" * 40)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    print("\n分析完成！")


if __name__ == "__main__":
    main()
