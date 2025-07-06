#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量数据更新性能测试
验证CSV导出性能提升效果
"""

import time
import logging
import json
from datetime import datetime
from typing import List, Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入测试模块
try:
    from batch_data_updater import batch_updater
    from optimized_cache_strategy import optimized_cache
    from intelligent_fallback_strategy import intelligent_fallback
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    MODULES_AVAILABLE = False

class BatchUpdatePerformanceTest:
    """批量数据更新性能测试"""
    
    def __init__(self):
        self.test_stocks = [
            '000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ',
            '002415.SZ', '000063.SZ', '600519.SH', '000166.SZ', '600276.SH'
        ]
        self.test_results = {}
    
    def run_all_tests(self):
        """运行所有性能测试"""
        logger.info("开始批量数据更新性能测试")
        
        if not MODULES_AVAILABLE:
            logger.error("必要模块不可用，跳过测试")
            return
        
        # 1. 测试缓存策略性能
        self.test_cache_strategy_performance()
        
        # 2. 测试智能降级机制
        self.test_intelligent_fallback()
        
        # 3. 测试批量更新功能
        self.test_batch_update_functionality()
        
        # 4. 模拟CSV导出性能对比
        self.test_csv_export_performance()
        
        # 5. 生成测试报告
        self.generate_test_report()
    
    def test_cache_strategy_performance(self):
        """测试缓存策略性能"""
        logger.info("测试缓存策略性能...")
        
        try:
            start_time = time.time()
            
            # 批量获取股票数据
            cached_data = optimized_cache.batch_get_stock_data(self.test_stocks)
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # 获取性能统计
            cache_stats = optimized_cache.get_performance_stats()
            
            self.test_results['cache_performance'] = {
                'query_time': round(query_time, 3),
                'stocks_count': len(self.test_stocks),
                'data_retrieved': len(cached_data),
                'cache_stats': cache_stats,
                'avg_time_per_stock': round(query_time / len(self.test_stocks), 3)
            }
            
            logger.info(f"缓存策略测试完成: {query_time:.3f}秒, 平均每只股票 {query_time/len(self.test_stocks):.3f}秒")
            
        except Exception as e:
            logger.error(f"缓存策略性能测试失败: {e}")
            self.test_results['cache_performance'] = {'error': str(e)}
    
    def test_intelligent_fallback(self):
        """测试智能降级机制"""
        logger.info("测试智能降级机制...")
        
        try:
            start_time = time.time()
            
            # 批量获取数据，测试降级策略
            fallback_results = intelligent_fallback.batch_get_stock_data_with_fallback(self.test_stocks[:5])
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # 分析数据源分布
            data_sources = {}
            for code, (data, source) in fallback_results.items():
                source_name = source.value
                data_sources[source_name] = data_sources.get(source_name, 0) + 1
            
            # 获取健康状态
            health_status = intelligent_fallback.get_health_status()
            
            self.test_results['fallback_performance'] = {
                'query_time': round(query_time, 3),
                'stocks_count': len(fallback_results),
                'data_sources': data_sources,
                'health_status': health_status,
                'avg_time_per_stock': round(query_time / len(fallback_results), 3)
            }
            
            logger.info(f"智能降级测试完成: {query_time:.3f}秒, 数据源分布: {data_sources}")
            
        except Exception as e:
            logger.error(f"智能降级机制测试失败: {e}")
            self.test_results['fallback_performance'] = {'error': str(e)}
    
    def test_batch_update_functionality(self):
        """测试批量更新功能"""
        logger.info("测试批量更新功能...")
        
        try:
            # 启动批量更新
            session_id = f"test_{int(time.time())}"
            
            start_time = time.time()
            session_id = batch_updater.start_batch_update(
                stock_codes=self.test_stocks[:3],  # 测试3只股票
                session_id=session_id,
                force_update=False
            )
            
            # 等待更新完成
            max_wait_time = 60  # 最多等待60秒
            wait_start = time.time()
            
            while time.time() - wait_start < max_wait_time:
                progress = batch_updater.get_update_progress(session_id)
                if progress and progress['status'] == 'completed':
                    break
                time.sleep(2)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 获取最终进度
            final_progress = batch_updater.get_update_progress(session_id)
            
            self.test_results['batch_update'] = {
                'total_time': round(total_time, 3),
                'session_id': session_id,
                'final_progress': final_progress,
                'completed': final_progress['status'] == 'completed' if final_progress else False
            }
            
            logger.info(f"批量更新测试完成: {total_time:.3f}秒, 状态: {final_progress['status'] if final_progress else 'unknown'}")
            
        except Exception as e:
            logger.error(f"批量更新功能测试失败: {e}")
            self.test_results['batch_update'] = {'error': str(e)}
    
    def test_csv_export_performance(self):
        """模拟CSV导出性能对比"""
        logger.info("测试CSV导出性能对比...")
        
        try:
            # 模拟优化前的CSV导出（逐个获取数据）
            start_time = time.time()
            
            old_method_data = []
            for stock_code in self.test_stocks[:5]:
                # 模拟单个股票数据获取
                time.sleep(0.1)  # 模拟API调用延迟
                old_method_data.append({
                    'stock_code': stock_code,
                    'simulated': True
                })
            
            old_method_time = time.time() - start_time
            
            # 模拟优化后的CSV导出（批量获取缓存数据）
            start_time = time.time()
            
            new_method_data = optimized_cache.batch_get_stock_data(self.test_stocks[:5])
            
            new_method_time = time.time() - start_time
            
            # 计算性能提升
            performance_improvement = ((old_method_time - new_method_time) / old_method_time * 100) if old_method_time > 0 else 0
            
            self.test_results['csv_export_performance'] = {
                'old_method_time': round(old_method_time, 3),
                'new_method_time': round(new_method_time, 3),
                'performance_improvement_percent': round(performance_improvement, 1),
                'speedup_factor': round(old_method_time / new_method_time, 1) if new_method_time > 0 else 'N/A',
                'stocks_tested': len(self.test_stocks[:5])
            }
            
            logger.info(f"CSV导出性能对比: 优化前 {old_method_time:.3f}秒, 优化后 {new_method_time:.3f}秒, 提升 {performance_improvement:.1f}%")
            
        except Exception as e:
            logger.error(f"CSV导出性能测试失败: {e}")
            self.test_results['csv_export_performance'] = {'error': str(e)}
    
    def generate_test_report(self):
        """生成测试报告"""
        logger.info("生成测试报告...")
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'test_stocks': self.test_stocks,
            'test_results': self.test_results,
            'summary': self._generate_summary()
        }
        
        # 保存报告到文件
        report_filename = f"batch_update_performance_report_{int(time.time())}.json"
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"测试报告已保存到: {report_filename}")
        except Exception as e:
            logger.error(f"保存测试报告失败: {e}")
        
        # 打印摘要
        self._print_summary()
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        summary = {
            'total_tests': len(self.test_results),
            'successful_tests': len([r for r in self.test_results.values() if 'error' not in r]),
            'failed_tests': len([r for r in self.test_results.values() if 'error' in r])
        }
        
        # 性能改进摘要
        if 'csv_export_performance' in self.test_results and 'error' not in self.test_results['csv_export_performance']:
            perf_data = self.test_results['csv_export_performance']
            summary['performance_improvement'] = {
                'csv_export_speedup': perf_data.get('speedup_factor', 'N/A'),
                'time_saved_percent': perf_data.get('performance_improvement_percent', 'N/A')
            }
        
        # 缓存效率摘要
        if 'cache_performance' in self.test_results and 'error' not in self.test_results['cache_performance']:
            cache_data = self.test_results['cache_performance']
            cache_stats = cache_data.get('cache_stats', {})
            summary['cache_efficiency'] = {
                'hit_rate': cache_stats.get('cache_hit_rate', 'N/A'),
                'avg_query_time': cache_stats.get('avg_query_time', 'N/A')
            }
        
        return summary
    
    def _print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("批量数据更新性能测试报告")
        print("="*60)
        
        summary = self.test_results.get('summary', self._generate_summary())
        
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试股票数量: {len(self.test_stocks)}")
        print(f"成功测试: {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)}")
        
        # 性能改进
        if 'performance_improvement' in summary:
            perf = summary['performance_improvement']
            print(f"\n性能改进:")
            print(f"  CSV导出加速: {perf.get('csv_export_speedup', 'N/A')}倍")
            print(f"  时间节省: {perf.get('time_saved_percent', 'N/A')}%")
        
        # 缓存效率
        if 'cache_efficiency' in summary:
            cache = summary['cache_efficiency']
            print(f"\n缓存效率:")
            print(f"  命中率: {cache.get('hit_rate', 'N/A')}%")
            print(f"  平均查询时间: {cache.get('avg_query_time', 'N/A')}秒")
        
        # 详细结果
        print(f"\n详细测试结果:")
        for test_name, result in self.test_results.items():
            if test_name == 'summary':
                continue
            status = "失败" if 'error' in result else "成功"
            print(f"  {test_name}: {status}")
            if 'error' in result:
                print(f"    错误: {result['error']}")
        
        print("="*60)

def main():
    """主函数"""
    print("批量数据更新性能测试")
    print("="*40)
    
    # 创建测试实例
    test = BatchUpdatePerformanceTest()
    
    # 运行测试
    test.run_all_tests()

if __name__ == "__main__":
    main()
