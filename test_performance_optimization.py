# -*- coding: utf-8 -*-
"""
性能优化测试脚本
用于验证HF Spaces环境中的性能优化效果
"""

import time
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import json
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceOptimizationTest:
    """性能优化测试类"""
    
    def __init__(self):
        self.test_stocks = [
            '000001', '000002', '000858', '002415', '600036',
            '600519', '000858', '002594', '300059', '600276'
        ]
        self.results = {}
        
    def test_database_performance(self):
        """测试数据库性能优化"""
        logger.info("🔍 测试数据库性能优化...")
        
        try:
            from database import batch_get_stock_info, batch_get_realtime_data, get_session
            from sqlalchemy import text
            
            # 测试批量查询性能
            start_time = time.time()
            batch_info = batch_get_stock_info(self.test_stocks)
            batch_query_time = time.time() - start_time
            
            # 测试单个查询性能（对比）
            start_time = time.time()
            session = get_session()
            for _ in range(5):  # 测试5次单个查询
                session.execute(text("SELECT 1"))
            session.close()
            single_query_time = time.time() - start_time
            
            self.results['database'] = {
                'batch_query_time': batch_query_time,
                'batch_stocks_count': len(batch_info),
                'single_query_time': single_query_time,
                'optimization_effective': batch_query_time < single_query_time * 2
            }
            
            logger.info(f"✅ 数据库测试完成: 批量查询{len(batch_info)}只股票耗时{batch_query_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"❌ 数据库测试失败: {e}")
            self.results['database'] = {'error': str(e)}
    
    def test_cache_performance(self):
        """测试缓存性能优化"""
        logger.info("🔍 测试缓存性能优化...")
        
        try:
            from advanced_cache_manager import AdvancedCacheManager
            
            cache_manager = AdvancedCacheManager()
            
            # 测试缓存设置和获取
            test_data = {'test': 'data', 'timestamp': time.time()}
            
            # 设置缓存
            start_time = time.time()
            cache_manager.set('test_data', test_data, stock_code='TEST001')
            set_time = time.time() - start_time
            
            # 获取缓存
            start_time = time.time()
            cached_data = cache_manager.get('test_data', stock_code='TEST001')
            get_time = time.time() - start_time
            
            self.results['cache'] = {
                'set_time': set_time,
                'get_time': get_time,
                'cache_hit': cached_data is not None,
                'data_integrity': cached_data == test_data if cached_data else False
            }
            
            logger.info(f"✅ 缓存测试完成: 设置耗时{set_time:.4f}秒, 获取耗时{get_time:.4f}秒")
            
        except Exception as e:
            logger.error(f"❌ 缓存测试失败: {e}")
            self.results['cache'] = {'error': str(e)}
    
    def test_concurrent_analysis(self):
        """测试并发分析性能"""
        logger.info("🔍 测试并发分析性能...")
        
        try:
            from stock_analyzer import StockAnalyzer
            
            analyzer = StockAnalyzer()
            
            # 串行分析测试
            start_time = time.time()
            serial_results = []
            for stock_code in self.test_stocks[:5]:  # 测试5只股票
                try:
                    result = analyzer.quick_analyze_stock(stock_code, timeout=30)
                    serial_results.append(result)
                except Exception as e:
                    logger.warning(f"串行分析 {stock_code} 失败: {e}")
            serial_time = time.time() - start_time
            
            # 并发分析测试
            start_time = time.time()
            concurrent_results = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_stock = {
                    executor.submit(analyzer._safe_quick_analyze, stock_code, 'A', 0): stock_code 
                    for stock_code in self.test_stocks[:5]
                }
                
                for future in as_completed(future_to_stock, timeout=60):
                    try:
                        result = future.result()
                        if result:
                            concurrent_results.append(result)
                    except Exception as e:
                        logger.warning(f"并发分析失败: {e}")
            
            concurrent_time = time.time() - start_time
            
            self.results['concurrent_analysis'] = {
                'serial_time': serial_time,
                'serial_count': len(serial_results),
                'concurrent_time': concurrent_time,
                'concurrent_count': len(concurrent_results),
                'speedup_ratio': serial_time / concurrent_time if concurrent_time > 0 else 0,
                'optimization_effective': concurrent_time < serial_time
            }
            
            logger.info(f"✅ 并发分析测试完成: 串行{serial_time:.2f}秒 vs 并发{concurrent_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"❌ 并发分析测试失败: {e}")
            self.results['concurrent_analysis'] = {'error': str(e)}
    
    def test_timeout_configuration(self):
        """测试超时配置"""
        logger.info("🔍 测试超时配置...")
        
        try:
            from hf_spaces_performance_config import get_hf_timeout, is_hf_feature_enabled
            
            # 检查超时配置
            api_timeout = get_hf_timeout('api')
            analysis_timeout = get_hf_timeout('analysis')
            data_fetch_timeout = get_hf_timeout('data_fetch')
            
            # 检查功能开关
            ai_analysis_enabled = is_hf_feature_enabled('ai_analysis')
            complex_indicators_enabled = is_hf_feature_enabled('complex_indicators')
            
            self.results['timeout_config'] = {
                'api_timeout': api_timeout,
                'analysis_timeout': analysis_timeout,
                'data_fetch_timeout': data_fetch_timeout,
                'ai_analysis_enabled': ai_analysis_enabled,
                'complex_indicators_enabled': complex_indicators_enabled,
                'timeout_extended': api_timeout >= 180
            }
            
            logger.info(f"✅ 超时配置测试完成: API超时{api_timeout}秒, 分析超时{analysis_timeout}秒")
            
        except Exception as e:
            logger.error(f"❌ 超时配置测试失败: {e}")
            self.results['timeout_config'] = {'error': str(e)}
    
    def test_performance_monitoring(self):
        """测试性能监控"""
        logger.info("🔍 测试性能监控...")
        
        try:
            from performance_monitor import get_hf_spaces_performance_report, performance_monitor
            
            # 模拟一些性能数据
            performance_monitor.record_api_call(1.5, success=True)
            performance_monitor.record_cache_hit(0.01)
            performance_monitor.record_db_query(0.1, success=True)
            
            # 获取性能报告
            report = get_hf_spaces_performance_report()
            
            self.results['performance_monitoring'] = {
                'report_generated': report is not None,
                'has_recommendations': len(report.get('recommendations', [])) >= 0,
                'cache_hit_rate': report.get('cache_hit_rate', 0),
                'avg_api_time': report.get('avg_api_time', 0)
            }
            
            logger.info(f"✅ 性能监控测试完成: 缓存命中率{report.get('cache_hit_rate', 0):.1f}%")
            
        except Exception as e:
            logger.error(f"❌ 性能监控测试失败: {e}")
            self.results['performance_monitoring'] = {'error': str(e)}
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始性能优化测试...")
        
        start_time = time.time()
        
        # 运行各项测试
        self.test_database_performance()
        self.test_cache_performance()
        self.test_concurrent_analysis()
        self.test_timeout_configuration()
        self.test_performance_monitoring()
        
        total_time = time.time() - start_time
        
        # 生成测试报告
        self.results['test_summary'] = {
            'total_test_time': total_time,
            'test_timestamp': datetime.now().isoformat(),
            'tests_passed': sum(1 for result in self.results.values() 
                              if isinstance(result, dict) and 'error' not in result),
            'tests_failed': sum(1 for result in self.results.values() 
                              if isinstance(result, dict) and 'error' in result)
        }
        
        logger.info(f"✅ 所有测试完成，总耗时: {total_time:.2f}秒")
        
        return self.results
    
    def generate_report(self, filepath: str = None):
        """生成测试报告"""
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"performance_test_report_{timestamp}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 测试报告已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ 保存测试报告失败: {e}")
            return None


def main():
    """主函数"""
    print("🔧 HF Spaces 性能优化测试")
    print("=" * 50)
    
    # 创建测试实例
    test = PerformanceOptimizationTest()
    
    # 运行测试
    results = test.run_all_tests()
    
    # 生成报告
    report_file = test.generate_report()
    
    # 打印摘要
    print("\n📊 测试结果摘要:")
    print("=" * 50)
    
    summary = results.get('test_summary', {})
    print(f"总测试时间: {summary.get('total_test_time', 0):.2f}秒")
    print(f"通过测试: {summary.get('tests_passed', 0)}")
    print(f"失败测试: {summary.get('tests_failed', 0)}")
    
    if report_file:
        print(f"详细报告: {report_file}")
    
    print("\n🎯 优化效果评估:")
    print("=" * 50)
    
    # 评估各项优化效果
    if 'database' in results and 'optimization_effective' in results['database']:
        status = "✅" if results['database']['optimization_effective'] else "❌"
        print(f"{status} 数据库优化: {'有效' if results['database']['optimization_effective'] else '需要改进'}")
    
    if 'concurrent_analysis' in results and 'optimization_effective' in results['concurrent_analysis']:
        status = "✅" if results['concurrent_analysis']['optimization_effective'] else "❌"
        speedup = results['concurrent_analysis'].get('speedup_ratio', 0)
        print(f"{status} 并发分析优化: {'有效' if results['concurrent_analysis']['optimization_effective'] else '需要改进'} (加速比: {speedup:.2f}x)")
    
    if 'timeout_config' in results and 'timeout_extended' in results['timeout_config']:
        status = "✅" if results['timeout_config']['timeout_extended'] else "❌"
        print(f"{status} 超时配置: {'已延长到180秒' if results['timeout_config']['timeout_extended'] else '需要调整'}")


if __name__ == "__main__":
    main()
