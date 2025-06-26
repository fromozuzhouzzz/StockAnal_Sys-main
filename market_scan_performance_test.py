# -*- coding: utf-8 -*-
"""
市场扫描性能测试脚本
用于验证预缓存机制对市场扫描功能的性能提升效果
"""

import time
import logging
import requests
import json
from datetime import datetime
from stock_precache_scheduler import StockPrecacheScheduler

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketScanPerformanceTest:
    """市场扫描性能测试类"""
    
    def __init__(self, base_url="http://localhost:8888"):
        self.base_url = base_url
        self.precache_scheduler = StockPrecacheScheduler()
        
    def test_market_scan_performance(self, test_name="默认测试"):
        """测试市场扫描性能"""
        print(f"\n{'='*60}")
        print(f"🚀 开始 {test_name}")
        print(f"{'='*60}")
        
        try:
            # 启动市场扫描
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/market_scan",
                json={
                    "criteria": {
                        "min_score": 60,
                        "max_stocks": 20,
                        "sort_by": "score"
                    }
                },
                timeout=300  # 5分钟超时
            )
            
            if response.status_code != 200:
                print(f"❌ 市场扫描启动失败: {response.status_code}")
                return None
            
            task_data = response.json()
            task_id = task_data.get('task_id')
            
            if not task_id:
                print(f"❌ 未获取到任务ID")
                return None
            
            print(f"✅ 市场扫描任务已启动，任务ID: {task_id}")
            
            # 轮询任务状态
            completed = False
            last_progress = 0
            
            while not completed:
                time.sleep(5)  # 每5秒检查一次
                
                status_response = requests.get(f"{self.base_url}/api/task_status/{task_id}")
                if status_response.status_code != 200:
                    print(f"❌ 获取任务状态失败: {status_response.status_code}")
                    break
                
                status_data = status_response.json()
                status = status_data.get('status')
                progress = status_data.get('progress', 0)
                
                if progress != last_progress:
                    print(f"📊 进度: {progress}% - {status}")
                    last_progress = progress
                
                if status in ['completed', 'failed', 'error']:
                    completed = True
                    break
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 获取最终结果
            if status == 'completed':
                result_response = requests.get(f"{self.base_url}/api/task_result/{task_id}")
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    stocks_found = len(result_data.get('data', {}).get('stocks', []))
                    
                    print(f"\n📈 {test_name} 完成:")
                    print(f"  ⏱️  总耗时: {total_time:.1f}秒")
                    print(f"  📊 找到股票: {stocks_found}只")
                    print(f"  ⚡ 平均每只: {total_time/max(stocks_found, 1):.2f}秒")
                    
                    return {
                        'test_name': test_name,
                        'total_time': total_time,
                        'stocks_found': stocks_found,
                        'avg_time_per_stock': total_time/max(stocks_found, 1),
                        'status': 'success'
                    }
                else:
                    print(f"❌ 获取结果失败: {result_response.status_code}")
            else:
                print(f"❌ 任务失败，状态: {status}")
            
            return {
                'test_name': test_name,
                'total_time': total_time,
                'status': 'failed'
            }
            
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            return {
                'test_name': test_name,
                'status': 'error',
                'error': str(e)
            }
    
    def run_precache_and_test(self):
        """运行预缓存并测试性能"""
        print("🧪 市场扫描性能对比测试")
        print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = []
        
        # 第一轮：无预缓存测试
        print("\n🔄 第一轮：当前状态测试（可能有部分缓存）")
        result1 = self.test_market_scan_performance("当前状态测试")
        if result1:
            results.append(result1)
        
        # 执行预缓存
        print(f"\n{'='*60}")
        print("🔄 执行预缓存任务")
        print(f"{'='*60}")
        
        precache_start = time.time()
        self.precache_scheduler.manual_precache("000300", 50)  # 预缓存50只股票
        precache_time = time.time() - precache_start
        
        print(f"✅ 预缓存完成，耗时: {precache_time:.1f}秒")
        
        # 等待一段时间让缓存生效
        print("⏳ 等待5秒让缓存生效...")
        time.sleep(5)
        
        # 第二轮：预缓存后测试
        print("\n🚀 第二轮：预缓存后测试")
        result2 = self.test_market_scan_performance("预缓存后测试")
        if result2:
            results.append(result2)
        
        # 性能对比分析
        self.analyze_performance_results(results, precache_time)
        
        return results
    
    def analyze_performance_results(self, results, precache_time):
        """分析性能测试结果"""
        print(f"\n{'='*60}")
        print("📊 性能对比分析")
        print(f"{'='*60}")
        
        if len(results) < 2:
            print("❌ 测试结果不足，无法进行对比分析")
            return
        
        before = results[0]
        after = results[1]
        
        if before.get('status') != 'success' or after.get('status') != 'success':
            print("❌ 部分测试失败，无法进行准确对比")
            return
        
        before_time = before['total_time']
        after_time = after['total_time']
        
        improvement = ((before_time - after_time) / before_time) * 100
        speedup = before_time / after_time if after_time > 0 else 0
        
        print(f"📈 性能对比结果:")
        print(f"  🔄 预缓存前: {before_time:.1f}秒")
        print(f"  🚀 预缓存后: {after_time:.1f}秒")
        print(f"  ⚡ 性能提升: {improvement:.1f}%")
        print(f"  🚀 加速倍数: {speedup:.1f}x")
        print(f"  ⏱️  预缓存耗时: {precache_time:.1f}秒")
        
        # 计算投资回报率
        if improvement > 0:
            roi_threshold = precache_time / (before_time - after_time)
            print(f"  💰 投资回报: 预缓存执行{roi_threshold:.1f}次后开始盈利")
        
        # 给出建议
        print(f"\n💡 优化建议:")
        if improvement > 30:
            print("  ✅ 预缓存效果显著，建议启用定时预缓存")
        elif improvement > 10:
            print("  ⚠️  预缓存有一定效果，可考虑在低峰期启用")
        else:
            print("  ❌ 预缓存效果不明显，建议检查网络或API问题")
    
    def test_server_availability(self):
        """测试服务器可用性"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                print("✅ 服务器连接正常")
                return True
            else:
                print(f"❌ 服务器响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 服务器连接失败: {str(e)}")
            return False
    
    def run_full_test(self):
        """运行完整的性能测试"""
        print("🧪 开始市场扫描性能完整测试")
        
        # 检查服务器可用性
        if not self.test_server_availability():
            print("❌ 服务器不可用，测试终止")
            return
        
        # 运行性能对比测试
        results = self.run_precache_and_test()
        
        print(f"\n{'='*60}")
        print("✅ 性能测试完成")
        print(f"{'='*60}")
        
        return results

if __name__ == "__main__":
    # 创建测试实例
    tester = MarketScanPerformanceTest()
    
    # 运行完整测试
    results = tester.run_full_test()
    
    # 输出最终结果
    if results:
        print(f"\n📋 测试结果摘要:")
        for result in results:
            status = result.get('status', 'unknown')
            if status == 'success':
                print(f"  {result['test_name']}: {result['total_time']:.1f}秒 ({result['stocks_found']}只股票)")
            else:
                print(f"  {result['test_name']}: {status}")
    
    print("\n🎉 测试完成！")
