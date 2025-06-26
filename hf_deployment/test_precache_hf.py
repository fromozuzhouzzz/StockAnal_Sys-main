# -*- coding: utf-8 -*-
"""
Hugging Face Spaces 预缓存功能测试脚本
用于在HF Spaces环境中测试预缓存API的可用性
"""

import requests
import json
import time
from datetime import datetime

class HFPrecacheTest:
    """Hugging Face Spaces 预缓存测试类"""
    
    def __init__(self, base_url="https://huggingface.co/spaces/fromozu/stock-analysis"):
        self.base_url = base_url.rstrip('/')
        
    def test_precache_status_api(self):
        """测试预缓存状态API"""
        print("🔍 测试预缓存状态API")
        print("-" * 40)
        
        try:
            url = f"{self.base_url}/api/precache/status"
            print(f"请求URL: {url}")
            
            response = requests.get(url, timeout=30)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API调用成功")
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            elif response.status_code == 404:
                print("❌ API路由不存在 (404)")
                print("可能原因：")
                print("  1. 预缓存API路由未正确配置")
                print("  2. web_server.py中缺少相关代码")
                print("  3. 部署版本不是最新的")
                return False
            elif response.status_code == 503:
                print("⚠️ 预缓存功能不可用 (503)")
                data = response.json()
                print(f"错误信息: {data.get('error', '未知错误')}")
                return False
            else:
                print(f"❌ API调用失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误，请检查URL是否正确")
            return False
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            return False
    
    def test_manual_precache_api(self):
        """测试手动预缓存API"""
        print("\n🚀 测试手动预缓存API")
        print("-" * 40)
        
        try:
            url = f"{self.base_url}/api/precache/manual"
            print(f"请求URL: {url}")
            
            payload = {
                "index_code": "000300",
                "max_stocks": 5  # 测试时只用5只股票
            }
            
            response = requests.post(
                url, 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 预缓存任务启动成功")
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            elif response.status_code == 404:
                print("❌ API路由不存在 (404)")
                return False
            elif response.status_code == 503:
                print("⚠️ 预缓存功能不可用 (503)")
                data = response.json()
                print(f"错误信息: {data.get('error', '未知错误')}")
                return False
            else:
                print(f"❌ API调用失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
            return False
    
    def test_app_availability(self):
        """测试应用可用性"""
        print("🌐 测试应用可用性")
        print("-" * 40)
        
        try:
            response = requests.get(self.base_url, timeout=30)
            print(f"主页状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 应用正常运行")
                return True
            else:
                print(f"❌ 应用访问异常，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 应用访问失败: {str(e)}")
            return False
    
    def test_other_apis(self):
        """测试其他相关API"""
        print("\n🔧 测试其他相关API")
        print("-" * 40)
        
        # 测试股票分析API
        try:
            url = f"{self.base_url}/api/analyze"
            payload = {
                "stock_code": "000001",
                "market_type": "A"
            }
            
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"股票分析API状态码: {response.status_code}")
            if response.status_code == 200:
                print("✅ 股票分析API正常")
            else:
                print("⚠️ 股票分析API异常")
                
        except Exception as e:
            print(f"⚠️ 股票分析API测试失败: {str(e)}")
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🧪 Hugging Face Spaces 预缓存功能综合测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试目标: {self.base_url}")
        print("=" * 60)
        
        results = {
            'app_available': False,
            'status_api': False,
            'manual_api': False,
            'other_apis': False
        }
        
        # 1. 测试应用可用性
        results['app_available'] = self.test_app_availability()
        
        if not results['app_available']:
            print("\n❌ 应用不可用，终止测试")
            return results
        
        # 2. 测试预缓存状态API
        results['status_api'] = self.test_precache_status_api()
        
        # 3. 测试手动预缓存API
        results['manual_api'] = self.test_manual_precache_api()
        
        # 4. 测试其他API
        try:
            self.test_other_apis()
            results['other_apis'] = True
        except:
            results['other_apis'] = False
        
        # 输出测试总结
        self.print_test_summary(results)
        
        return results
    
    def print_test_summary(self, results):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 测试结果总结")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        print(f"总测试项: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"通过率: {(passed_tests/total_tests*100):.1f}%")
        
        print("\n详细结果:")
        status_map = {True: "✅ 通过", False: "❌ 失败"}
        
        print(f"  应用可用性: {status_map[results['app_available']]}")
        print(f"  预缓存状态API: {status_map[results['status_api']]}")
        print(f"  手动预缓存API: {status_map[results['manual_api']]}")
        print(f"  其他API: {status_map[results['other_apis']]}")
        
        # 给出建议
        print("\n💡 建议:")
        if not results['status_api'] or not results['manual_api']:
            print("  1. 检查hf_deployment/web_server.py中是否包含预缓存API路由")
            print("  2. 确认hf_deployment/stock_precache_scheduler.py文件存在")
            print("  3. 重新部署到Hugging Face Spaces")
            print("  4. 检查部署日志中的错误信息")
        elif results['status_api'] and results['manual_api']:
            print("  ✅ 预缓存功能已正常部署，可以使用！")
    
    def get_correct_api_urls(self):
        """获取正确的API URL"""
        print("\n📋 正确的API访问方式:")
        print("-" * 40)
        print(f"预缓存状态: {self.base_url}/api/precache/status")
        print(f"手动预缓存: {self.base_url}/api/precache/manual")
        print("\n使用curl命令测试:")
        print(f"curl '{self.base_url}/api/precache/status'")
        print(f"curl -X POST '{self.base_url}/api/precache/manual' \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{\"index_code\": \"000300\", \"max_stocks\": 5}'")

def main():
    """主测试函数"""
    # 可以修改这个URL为你的实际HF Spaces URL
    base_url = "https://huggingface.co/spaces/fromozu/stock-analysis"
    
    tester = HFPrecacheTest(base_url)
    
    # 运行综合测试
    results = tester.run_comprehensive_test()
    
    # 显示正确的API URL
    tester.get_correct_api_urls()
    
    print("\n🎉 测试完成！")
    
    return results

if __name__ == "__main__":
    main()
