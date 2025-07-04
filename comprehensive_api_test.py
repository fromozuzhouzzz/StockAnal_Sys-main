#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合API测试脚本
验证所有修复和优化的效果
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class ComprehensiveAPITester:
    """综合API测试器"""
    
    def __init__(self, base_url="https://fromozu-stock-analysis.hf.space", api_key="UZXJfw3YNX80DLfN"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        self.test_results = {}
        
    def test_health_endpoints(self):
        """测试健康检查端点"""
        print("=== 测试健康检查端点 ===")
        
        endpoints = [
            ('/api/v1/health', '基础健康检查'),
            ('/api/v1/status', '详细状态检查')
        ]
        
        results = {}
        for endpoint, description in endpoints:
            try:
                print(f"\n测试 {description}: {endpoint}")
                response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {description} 成功")
                    print(f"   状态: {data.get('data', {}).get('status', 'unknown')}")
                    
                    if endpoint == '/api/v1/status':
                        analyzers = data.get('data', {}).get('analyzers', {})
                        features = data.get('data', {}).get('features', {})
                        print(f"   分析器状态: {analyzers}")
                        print(f"   功能状态: {features}")
                    
                    results[endpoint] = {'status': 'success', 'data': data}
                else:
                    print(f"❌ {description} 失败: {response.status_code}")
                    results[endpoint] = {'status': 'failed', 'status_code': response.status_code}
                    
            except Exception as e:
                print(f"❌ {description} 异常: {e}")
                results[endpoint] = {'status': 'error', 'error': str(e)}
        
        self.test_results['health_endpoints'] = results
        return results
    
    def test_stock_analysis_with_fallback(self):
        """测试股票分析的降级策略"""
        print("\n=== 测试股票分析降级策略 ===")
        
        test_stocks = [
            ('603316.SH', '诚邦股份'),
            ('601218.SH', '吉鑫科技'),
            ('000001.SZ', '平安银行'),
            ('600000.SH', '浦发银行'),
            ('invalid.XX', '无效股票')  # 测试错误处理
        ]
        
        results = {}
        for stock_code, stock_name in test_stocks:
            try:
                print(f"\n测试股票: {stock_code} ({stock_name})")
                
                payload = {
                    "stock_code": stock_code,
                    "market_type": "A",
                    "analysis_depth": "quick",
                    "include_ai_analysis": False
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/stock/analyze",
                    json=payload,
                    headers=self.headers,
                    timeout=60
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    fallback_info = data.get('data', {}).get('fallback_info', {})
                    
                    print(f"✅ 分析成功 ({duration:.2f}s)")
                    print(f"   使用策略: {fallback_info.get('level_used', 'unknown')}")
                    print(f"   是否降级: {fallback_info.get('is_fallback', False)}")
                    print(f"   股票名称: {data.get('data', {}).get('stock_info', {}).get('stock_name', 'unknown')}")
                    print(f"   综合评分: {data.get('data', {}).get('analysis_result', {}).get('overall_score', 0)}")
                    
                    results[stock_code] = {
                        'status': 'success',
                        'duration': duration,
                        'fallback_info': fallback_info,
                        'data': data.get('data', {})
                    }
                    
                else:
                    error_data = response.json() if response.headers.get('Content-Type', '').startswith('application/json') else {}
                    print(f"❌ 分析失败: {response.status_code}")
                    print(f"   错误信息: {error_data.get('error', {}).get('message', 'Unknown error')}")
                    
                    results[stock_code] = {
                        'status': 'failed',
                        'status_code': response.status_code,
                        'error': error_data
                    }
                
            except Exception as e:
                print(f"❌ 分析异常: {e}")
                results[stock_code] = {'status': 'error', 'error': str(e)}
            
            # 添加延迟避免限流
            time.sleep(2)
        
        self.test_results['stock_analysis'] = results
        return results
    
    def test_error_handling(self):
        """测试错误处理机制"""
        print("\n=== 测试错误处理机制 ===")
        
        error_tests = [
            {
                'name': '无API密钥',
                'headers': {'Content-Type': 'application/json'},
                'payload': {'stock_code': '603316.SH'},
                'expected_status': 401
            },
            {
                'name': '错误API密钥',
                'headers': {'Content-Type': 'application/json', 'X-API-Key': 'invalid_key'},
                'payload': {'stock_code': '603316.SH'},
                'expected_status': 403
            },
            {
                'name': '无效请求格式',
                'headers': self.headers,
                'payload': {'invalid_field': 'value'},
                'expected_status': 400
            },
            {
                'name': '无效股票代码',
                'headers': self.headers,
                'payload': {'stock_code': 'INVALID'},
                'expected_status': 400
            }
        ]
        
        results = {}
        for test in error_tests:
            try:
                print(f"\n测试 {test['name']}")
                
                response = requests.post(
                    f"{self.base_url}/api/v1/stock/analyze",
                    json=test['payload'],
                    headers=test['headers'],
                    timeout=30
                )
                
                if response.status_code == test['expected_status']:
                    print(f"✅ 错误处理正确: {response.status_code}")
                    
                    # 检查是否返回JSON格式
                    if response.headers.get('Content-Type', '').startswith('application/json'):
                        error_data = response.json()
                        print(f"   错误信息: {error_data.get('error', {}).get('message', 'No message')}")
                        results[test['name']] = {'status': 'success', 'response': error_data}
                    else:
                        print(f"⚠️ 响应不是JSON格式")
                        results[test['name']] = {'status': 'warning', 'message': 'Non-JSON response'}
                else:
                    print(f"❌ 错误状态码不匹配: 期望{test['expected_status']}, 实际{response.status_code}")
                    results[test['name']] = {
                        'status': 'failed',
                        'expected': test['expected_status'],
                        'actual': response.status_code
                    }
                    
            except Exception as e:
                print(f"❌ 测试异常: {e}")
                results[test['name']] = {'status': 'error', 'error': str(e)}
        
        self.test_results['error_handling'] = results
        return results
    
    def test_performance(self):
        """测试性能"""
        print("\n=== 测试性能 ===")
        
        # 测试单个请求的性能
        stock_code = '603316.SH'
        durations = []
        
        for i in range(3):
            try:
                print(f"性能测试 {i+1}/3")
                
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/stock/analyze",
                    json={'stock_code': stock_code, 'analysis_depth': 'quick'},
                    headers=self.headers,
                    timeout=60
                )
                duration = time.time() - start_time
                durations.append(duration)
                
                if response.status_code == 200:
                    print(f"✅ 请求成功: {duration:.2f}s")
                else:
                    print(f"❌ 请求失败: {response.status_code}")
                
                time.sleep(1)  # 避免限流
                
            except Exception as e:
                print(f"❌ 性能测试异常: {e}")
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            print(f"\n性能统计:")
            print(f"  平均响应时间: {avg_duration:.2f}s")
            print(f"  最快响应时间: {min_duration:.2f}s")
            print(f"  最慢响应时间: {max_duration:.2f}s")
            
            performance_result = {
                'average': avg_duration,
                'min': min_duration,
                'max': max_duration,
                'samples': len(durations)
            }
        else:
            performance_result = {'error': 'No successful requests'}
        
        self.test_results['performance'] = performance_result
        return performance_result
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("🎯 综合API测试报告")
        print("="*60)
        
        # 运行所有测试
        self.test_health_endpoints()
        self.test_stock_analysis_with_fallback()
        self.test_error_handling()
        self.test_performance()
        
        # 生成总结
        print(f"\n📊 测试总结")
        print(f"测试时间: {datetime.now()}")
        
        # 健康检查总结
        health_results = self.test_results.get('health_endpoints', {})
        health_success = sum(1 for r in health_results.values() if r.get('status') == 'success')
        print(f"健康检查: {health_success}/{len(health_results)} 通过")
        
        # 股票分析总结
        analysis_results = self.test_results.get('stock_analysis', {})
        analysis_success = sum(1 for r in analysis_results.values() if r.get('status') == 'success')
        print(f"股票分析: {analysis_success}/{len(analysis_results)} 成功")
        
        # 错误处理总结
        error_results = self.test_results.get('error_handling', {})
        error_success = sum(1 for r in error_results.values() if r.get('status') == 'success')
        print(f"错误处理: {error_success}/{len(error_results)} 正确")
        
        # 性能总结
        performance = self.test_results.get('performance', {})
        if 'average' in performance:
            print(f"平均响应时间: {performance['average']:.2f}s")
        
        # 整体评估
        total_tests = len(health_results) + len(analysis_results) + len(error_results)
        total_success = health_success + analysis_success + error_success
        success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎉 整体成功率: {success_rate:.1f}% ({total_success}/{total_tests})")
        
        if success_rate >= 80:
            print("✅ API修复效果良好！")
        elif success_rate >= 60:
            print("⚠️ API基本可用，但仍有改进空间")
        else:
            print("❌ API仍存在严重问题，需要进一步修复")
        
        # 保存详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"comprehensive_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 详细报告已保存: {report_file}")
        
        return self.test_results

def main():
    """主函数"""
    tester = ComprehensiveAPITester()
    results = tester.generate_test_report()
    
    return results

if __name__ == "__main__":
    main()
