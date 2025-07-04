#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API修复测试脚本
用于测试修复后的API端点是否正常工作
"""

import requests
import json
import time
from datetime import datetime

class APITester:
    """API测试器"""
    
    def __init__(self, base_url="https://fromozu-stock-analysis.hf.space", api_key="UZXJfw3YNX80DLfN"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
    def test_health_check(self):
        """测试健康检查端点"""
        print("=== 测试API健康检查 ===")
        try:
            url = f"{self.base_url}/api/v1/health"
            response = requests.get(url, timeout=30)
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    return True
                except json.JSONDecodeError:
                    print(f"响应不是JSON格式: {response.text}")
                    return False
            else:
                print(f"健康检查失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"健康检查异常: {e}")
            return False
    
    def test_stock_analysis(self, stock_code="603316.SH"):
        """测试股票分析端点"""
        print(f"\n=== 测试股票分析: {stock_code} ===")
        try:
            url = f"{self.base_url}/api/v1/stock/analyze"
            payload = {
                "stock_code": stock_code,
                "market_type": "A",
                "analysis_depth": "full",
                "include_ai_analysis": True
            }
            
            print(f"请求URL: {url}")
            print(f"请求数据: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=60
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"分析成功!")
                    print(f"股票信息: {data.get('data', {}).get('stock_info', {})}")
                    print(f"分析结果: {data.get('data', {}).get('analysis_result', {})}")
                    return True
                except json.JSONDecodeError:
                    print(f"响应不是JSON格式: {response.text}")
                    return False
            else:
                print(f"分析失败，状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"错误响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"股票分析异常: {e}")
            return False
    
    def test_multiple_stocks(self, stock_codes=["603316.SH", "601218.SH"]):
        """测试多只股票分析"""
        print(f"\n=== 测试多只股票分析 ===")
        results = []
        
        for stock_code in stock_codes:
            print(f"\n--- 测试股票: {stock_code} ---")
            success = self.test_stock_analysis(stock_code)
            results.append({
                'stock_code': stock_code,
                'success': success,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # 添加延迟避免限流
            time.sleep(2)
        
        # 统计结果
        total = len(results)
        success_count = sum(1 for r in results if r['success'])
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        print(f"\n=== 测试结果统计 ===")
        print(f"总测试数: {total}")
        print(f"成功数: {success_count}")
        print(f"失败数: {total - success_count}")
        print(f"成功率: {success_rate:.1f}%")
        
        return results
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始API修复效果测试")
        print(f"测试时间: {datetime.now()}")
        print(f"API地址: {self.base_url}")
        
        # 1. 健康检查
        health_ok = self.test_health_check()
        
        # 2. 单股票测试
        single_ok = self.test_stock_analysis("603316.SH")
        
        # 3. 多股票测试
        multi_results = self.test_multiple_stocks(["603316.SH", "601218.SH"])
        
        # 总结
        print(f"\n🎯 测试总结")
        print(f"健康检查: {'✅ 通过' if health_ok else '❌ 失败'}")
        print(f"单股票测试: {'✅ 通过' if single_ok else '❌ 失败'}")
        
        success_count = sum(1 for r in multi_results if r['success'])
        total_count = len(multi_results)
        print(f"多股票测试: {success_count}/{total_count} 成功")
        
        if health_ok and success_count > 0:
            print("🎉 API修复效果良好！")
        else:
            print("⚠️ API仍存在问题，需要进一步调试")
        
        return {
            'health_check': health_ok,
            'single_stock': single_ok,
            'multi_stock_results': multi_results,
            'overall_success': health_ok and success_count > 0
        }

def main():
    """主函数"""
    tester = APITester()
    results = tester.run_comprehensive_test()
    
    # 保存测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"api_test_results_{timestamp}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n📄 测试结果已保存到: {result_file}")

if __name__ == "__main__":
    main()
