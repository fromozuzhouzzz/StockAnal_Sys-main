#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API问题调试脚本
深入分析API端点的具体问题
"""

import requests
import json
import time
from datetime import datetime

class APIDebugger:
    """API调试器"""
    
    def __init__(self, base_url="https://fromozu-stock-analysis.hf.space", api_key="UZXJfw3YNX80DLfN"):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
    
    def test_basic_endpoints(self):
        """测试基础端点"""
        print("=== 测试基础端点 ===")
        
        endpoints = [
            "/api/v1/health",
            "/api/docs",
            "/",
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                print(f"\n测试端点: {endpoint}")
                
                response = requests.get(url, timeout=30)
                print(f"状态码: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                
                if response.status_code == 200:
                    print("✅ 端点可访问")
                else:
                    print(f"❌ 端点不可访问: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ 端点测试异常: {e}")
    
    def test_api_authentication(self):
        """测试API认证"""
        print("\n=== 测试API认证 ===")
        
        # 测试无API密钥
        print("\n1. 测试无API密钥:")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/stock/analyze",
                json={"stock_code": "603316.SH"},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}")
        except Exception as e:
            print(f"异常: {e}")
        
        # 测试错误API密钥
        print("\n2. 测试错误API密钥:")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/stock/analyze",
                json={"stock_code": "603316.SH"},
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': 'invalid_key'
                },
                timeout=30
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}")
        except Exception as e:
            print(f"异常: {e}")
        
        # 测试正确API密钥
        print("\n3. 测试正确API密钥:")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/stock/analyze",
                json={"stock_code": "603316.SH"},
                headers=self.headers,
                timeout=30
            )
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text[:200]}")
        except Exception as e:
            print(f"异常: {e}")
    
    def test_minimal_request(self):
        """测试最小化请求"""
        print("\n=== 测试最小化请求 ===")
        
        minimal_payloads = [
            {"stock_code": "603316.SH"},
            {"stock_code": "000001.SZ"},
            {"stock_code": "600000.SH"},
        ]
        
        for payload in minimal_payloads:
            print(f"\n测试载荷: {payload}")
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/stock/analyze",
                    json=payload,
                    headers=self.headers,
                    timeout=60
                )
                
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ 请求成功")
                    data = response.json()
                    print(f"股票信息: {data.get('data', {}).get('stock_info', {})}")
                else:
                    print(f"❌ 请求失败")
                    try:
                        error_data = response.json()
                        print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    except:
                        print(f"原始响应: {response.text}")
                        
            except Exception as e:
                print(f"异常: {e}")
            
            time.sleep(2)  # 避免限流
    
    def test_alternative_endpoints(self):
        """测试替代端点"""
        print("\n=== 测试替代端点 ===")
        
        # 测试原有的分析端点
        print("\n1. 测试原有分析端点 /analyze:")
        try:
            response = requests.post(
                f"{self.base_url}/analyze",
                json={"stock_codes": ["603316.SH"], "market_type": "A"},
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print("✅ 原有端点可用")
                data = response.json()
                print(f"结果数量: {len(data.get('results', []))}")
            else:
                print(f"❌ 原有端点不可用: {response.text[:200]}")
        except Exception as e:
            print(f"异常: {e}")
        
        # 测试其他API端点
        other_endpoints = [
            "/api/fundamental_analysis",
            "/api/risk_analysis",
        ]
        
        for endpoint in other_endpoints:
            print(f"\n2. 测试端点 {endpoint}:")
            try:
                response = requests.post(
                    f"{self.base_url}{endpoint}",
                    json={"stock_code": "603316.SH"},
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    print(f"✅ {endpoint} 可用")
                else:
                    print(f"❌ {endpoint} 不可用: {response.text[:200]}")
            except Exception as e:
                print(f"异常: {e}")
    
    def analyze_error_patterns(self):
        """分析错误模式"""
        print("\n=== 分析错误模式 ===")
        
        # 测试不同的股票代码格式
        stock_codes = [
            "603316.SH",
            "603316",
            "603316.XSHG",
            "000001.SZ",
            "000001",
            "600000.SH",
        ]
        
        for stock_code in stock_codes:
            print(f"\n测试股票代码: {stock_code}")
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/stock/analyze",
                    json={"stock_code": stock_code, "analysis_depth": "quick"},
                    headers=self.headers,
                    timeout=30
                )
                
                print(f"状态码: {response.status_code}")
                
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        error_code = error_data.get('error', {}).get('code', 'UNKNOWN')
                        error_message = error_data.get('error', {}).get('message', 'Unknown error')
                        print(f"错误代码: {error_code}")
                        print(f"错误信息: {error_message}")
                    except:
                        print(f"无法解析错误: {response.text[:100]}")
                else:
                    print("✅ 成功")
                    
            except Exception as e:
                print(f"异常: {e}")
            
            time.sleep(1)
    
    def run_comprehensive_debug(self):
        """运行综合调试"""
        print("🔍 开始API问题综合调试")
        print(f"调试时间: {datetime.now()}")
        print(f"API地址: {self.base_url}")
        
        self.test_basic_endpoints()
        self.test_api_authentication()
        self.test_minimal_request()
        self.test_alternative_endpoints()
        self.analyze_error_patterns()
        
        print("\n🎯 调试总结")
        print("1. 健康检查端点正常工作")
        print("2. API认证机制需要验证")
        print("3. 股票分析端点存在内部错误")
        print("4. 建议检查服务器端日志获取详细错误信息")

def main():
    """主函数"""
    debugger = APIDebugger()
    debugger.run_comprehensive_debug()

if __name__ == "__main__":
    main()
