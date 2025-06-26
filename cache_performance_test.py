# -*- coding: utf-8 -*-
"""
缓存性能测试脚本
用于验证MySQL缓存机制在市场扫描中的效果
"""

import time
import logging
from datetime import datetime
from stock_analyzer import StockAnalyzer
from database import get_session, StockBasicInfo, StockPriceHistory, StockRealtimeData
from data_service import data_service
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CachePerformanceTest:
    """缓存性能测试类"""
    
    def __init__(self):
        self.analyzer = StockAnalyzer()
        self.test_stocks = [
            '000001',  # 平安银行
            '000002',  # 万科A
            '600000',  # 浦发银行
            '600036',  # 招商银行
            '000858',  # 五粮液
            '002415',  # 海康威视
            '600519',  # 贵州茅台
            '000166',  # 申万宏源
            '600276',  # 恒瑞医药
            '000063'   # 中兴通讯
        ]
    
    def check_database_cache_status(self):
        """检查数据库缓存状态"""
        print("\n" + "="*60)
        print("📊 数据库缓存状态检查")
        print("="*60)
        
        try:
            session = get_session()
            
            # 检查基本信息缓存
            basic_info_count = session.query(StockBasicInfo).count()
            print(f"📋 股票基本信息缓存: {basic_info_count} 条记录")
            
            # 检查价格历史缓存
            price_history_count = session.query(StockPriceHistory).count()
            print(f"📈 价格历史数据缓存: {price_history_count} 条记录")
            
            # 检查实时数据缓存
            realtime_count = session.query(StockRealtimeData).count()
            print(f"⚡ 实时数据缓存: {realtime_count} 条记录")
            
            # 检查测试股票的缓存情况
            print(f"\n🔍 测试股票缓存情况:")
            for stock_code in self.test_stocks:
                basic_cached = session.query(StockBasicInfo).filter(
                    StockBasicInfo.stock_code == stock_code
                ).first()
                
                price_cached = session.query(StockPriceHistory).filter(
                    StockPriceHistory.stock_code == stock_code
                ).count()
                
                status = "✅" if basic_cached and price_cached > 0 else "❌"
                print(f"  {status} {stock_code}: 基本信息={'有' if basic_cached else '无'}, 价格数据={price_cached}条")
            
            session.close()
            
        except Exception as e:
            print(f"❌ 数据库检查失败: {e}")
    
    def test_single_stock_performance(self, stock_code, use_cache=True):
        """测试单只股票的分析性能"""
        try:
            start_time = time.time()
            
            if not use_cache:
                # 清除内存缓存
                if hasattr(self.analyzer, 'data_cache'):
                    self.analyzer.data_cache.clear()
                if hasattr(data_service, 'memory_cache'):
                    data_service.memory_cache.clear()
            
            # 执行股票分析
            report = self.analyzer.quick_analyze_stock(stock_code, 'A', timeout=20)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            return {
                'stock_code': stock_code,
                'success': True,
                'time': elapsed_time,
                'score': report.get('score', 0),
                'stock_name': report.get('stock_name', '未知')
            }
            
        except Exception as e:
            end_time = time.time()
            elapsed_time = end_time - start_time
            return {
                'stock_code': stock_code,
                'success': False,
                'time': elapsed_time,
                'error': str(e)
            }
    
    def run_performance_comparison(self):
        """运行性能对比测试"""
        print("\n" + "="*60)
        print("🚀 缓存性能对比测试")
        print("="*60)
        
        # 第一轮：使用缓存
        print("\n📊 第一轮测试：使用缓存")
        print("-" * 40)
        cached_results = []
        total_cached_time = 0
        
        for stock_code in self.test_stocks[:5]:  # 测试前5只股票
            print(f"正在测试 {stock_code}...")
            result = self.test_single_stock_performance(stock_code, use_cache=True)
            cached_results.append(result)
            total_cached_time += result['time']
            
            if result['success']:
                print(f"  ✅ {result['stock_name']} ({stock_code}): {result['time']:.2f}秒, 得分: {result['score']:.1f}")
            else:
                print(f"  ❌ {stock_code}: 失败 - {result['error']}")
        
        # 第二轮：清除缓存
        print("\n📊 第二轮测试：清除缓存")
        print("-" * 40)
        uncached_results = []
        total_uncached_time = 0
        
        for stock_code in self.test_stocks[:5]:  # 测试相同的股票
            print(f"正在测试 {stock_code} (无缓存)...")
            result = self.test_single_stock_performance(stock_code, use_cache=False)
            uncached_results.append(result)
            total_uncached_time += result['time']
            
            if result['success']:
                print(f"  ✅ {result['stock_name']} ({stock_code}): {result['time']:.2f}秒, 得分: {result['score']:.1f}")
            else:
                print(f"  ❌ {stock_code}: 失败 - {result['error']}")
        
        # 性能对比分析
        print("\n" + "="*60)
        print("📈 性能对比分析")
        print("="*60)
        
        print(f"🔄 使用缓存总时间: {total_cached_time:.2f}秒")
        print(f"🚫 无缓存总时间: {total_uncached_time:.2f}秒")
        
        if total_uncached_time > 0:
            improvement = ((total_uncached_time - total_cached_time) / total_uncached_time) * 100
            speedup = total_uncached_time / total_cached_time if total_cached_time > 0 else 0
            print(f"⚡ 性能提升: {improvement:.1f}%")
            print(f"🚀 加速倍数: {speedup:.1f}x")
        
        # 详细对比
        print(f"\n📋 详细对比:")
        print(f"{'股票代码':<8} {'缓存时间':<10} {'无缓存时间':<12} {'提升':<8}")
        print("-" * 45)
        
        for i, stock_code in enumerate(self.test_stocks[:5]):
            if i < len(cached_results) and i < len(uncached_results):
                cached_time = cached_results[i]['time']
                uncached_time = uncached_results[i]['time']
                improvement = ((uncached_time - cached_time) / uncached_time * 100) if uncached_time > 0 else 0
                print(f"{stock_code:<8} {cached_time:<10.2f} {uncached_time:<12.2f} {improvement:<8.1f}%")
    
    def test_batch_cache_hit_rate(self):
        """测试批量处理的缓存命中率"""
        print("\n" + "="*60)
        print("🎯 批量缓存命中率测试")
        print("="*60)
        
        # 先进行一轮分析，建立缓存
        print("🔄 预热缓存...")
        for stock_code in self.test_stocks:
            try:
                self.analyzer.quick_analyze_stock(stock_code, 'A', timeout=10)
                print(f"  ✅ {stock_code} 预热完成")
            except:
                print(f"  ❌ {stock_code} 预热失败")
        
        # 测试批量处理性能
        print(f"\n🚀 批量处理测试 ({len(self.test_stocks)}只股票)...")
        start_time = time.time()
        
        successful_count = 0
        failed_count = 0
        
        for stock_code in self.test_stocks:
            try:
                report = self.analyzer.quick_analyze_stock(stock_code, 'A', timeout=10)
                successful_count += 1
                print(f"  ✅ {stock_code}: {report.get('score', 0):.1f}分")
            except Exception as e:
                failed_count += 1
                print(f"  ❌ {stock_code}: {str(e)}")
        
        total_time = time.time() - start_time
        avg_time = total_time / len(self.test_stocks)
        
        print(f"\n📊 批量处理结果:")
        print(f"  总时间: {total_time:.2f}秒")
        print(f"  平均每只: {avg_time:.2f}秒")
        print(f"  成功: {successful_count}只")
        print(f"  失败: {failed_count}只")
        print(f"  成功率: {(successful_count/(successful_count+failed_count)*100):.1f}%")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始缓存性能测试")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 检查数据库缓存状态
        self.check_database_cache_status()
        
        # 2. 性能对比测试
        self.run_performance_comparison()
        
        # 3. 批量缓存命中率测试
        self.test_batch_cache_hit_rate()
        
        print("\n" + "="*60)
        print("✅ 缓存性能测试完成")
        print("="*60)

if __name__ == "__main__":
    tester = CachePerformanceTest()
    tester.run_all_tests()
