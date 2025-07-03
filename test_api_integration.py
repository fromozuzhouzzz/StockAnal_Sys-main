#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API集成测试脚本
验证API功能是否正确集成到系统中
"""

import requests
import json
import time
import sys

def test_api_health():
    """测试API健康检查"""
    print("🔍 测试API健康检查...")
    
    try:
        response = requests.get(
            "http://localhost:8888/api/v1/health",
            headers={"X-API-Key": "UZXJfw3YNX80DLfN"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API健康检查通过")
            print(f"   API版本: {data.get('data', {}).get('api_version', 'unknown')}")
            print(f"   状态: {data.get('data', {}).get('status', 'unknown')}")
            return True
        else:
            print(f"❌ API健康检查失败: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用正在运行")
        return False
    except Exception as e:
        print(f"❌ API健康检查出错: {e}")
        return False


def test_stock_analysis_api():
    """测试个股分析API"""
    print("\n🔍 测试个股分析API...")
    
    try:
        data = {
            "stock_code": "000001.SZ",
            "market_type": "A",
            "analysis_depth": "quick",
            "include_ai_analysis": False
        }
        
        response = requests.post(
            "http://localhost:8888/api/v1/stock/analyze",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "UZXJfw3YNX80DLfN"
            },
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 个股分析API测试通过")
                stock_data = result.get('data', {})
                stock_info = stock_data.get('stock_info', {})
                analysis_result = stock_data.get('analysis_result', {})
                
                print(f"   股票: {stock_info.get('stock_name', 'unknown')} ({stock_info.get('stock_code', 'unknown')})")
                print(f"   综合评分: {analysis_result.get('overall_score', 0)}")
                return True
            else:
                print(f"❌ API返回失败: {result.get('error', {}).get('message', 'unknown')}")
                return False
        else:
            print(f"❌ 个股分析API测试失败: HTTP {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                error_data = response.json()
                print(f"   错误: {error_data.get('error', {}).get('message', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ 个股分析API测试出错: {e}")
        return False


def test_portfolio_analysis_api():
    """测试投资组合分析API"""
    print("\n🔍 测试投资组合分析API...")
    
    try:
        data = {
            "stocks": [
                {
                    "stock_code": "000001.SZ",
                    "weight": 0.6,
                    "market_type": "A"
                },
                {
                    "stock_code": "600000.SH",
                    "weight": 0.4,
                    "market_type": "A"
                }
            ],
            "analysis_params": {
                "risk_preference": "moderate"
            }
        }
        
        response = requests.post(
            "http://localhost:8888/api/v1/portfolio/analyze",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "UZXJfw3YNX80DLfN"
            },
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 投资组合分析API测试通过")
                portfolio_data = result.get('data', {})
                
                print(f"   组合评分: {portfolio_data.get('portfolio_score', 0)}")
                print(f"   风险等级: {portfolio_data.get('risk_level', 'unknown')}")
                print(f"   个股数量: {len(portfolio_data.get('individual_stocks', []))}")
                return True
            else:
                print(f"❌ API返回失败: {result.get('error', {}).get('message', 'unknown')}")
                return False
        else:
            print(f"❌ 投资组合分析API测试失败: HTTP {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                error_data = response.json()
                print(f"   错误: {error_data.get('error', {}).get('message', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ 投资组合分析API测试出错: {e}")
        return False


def test_batch_score_api():
    """测试批量评分API"""
    print("\n🔍 测试批量评分API...")
    
    try:
        data = {
            "stock_codes": ["000001.SZ", "600000.SH"],
            "market_type": "A",
            "min_score": 0,
            "sort_by": "score",
            "sort_order": "desc"
        }
        
        response = requests.post(
            "http://localhost:8888/api/v1/stocks/batch-score",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "UZXJfw3YNX80DLfN"
            },
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 批量评分API测试通过")
                batch_data = result.get('data', {})
                
                print(f"   分析数量: {batch_data.get('total_analyzed', 0)}")
                print(f"   成功数量: {batch_data.get('successful_count', 0)}")
                print(f"   结果数量: {len(batch_data.get('results', []))}")
                return True
            else:
                print(f"❌ API返回失败: {result.get('error', {}).get('message', 'unknown')}")
                return False
        else:
            print(f"❌ 批量评分API测试失败: HTTP {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                error_data = response.json()
                print(f"   错误: {error_data.get('error', {}).get('message', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ 批量评分API测试出错: {e}")
        return False


def test_authentication():
    """测试认证功能"""
    print("\n🔍 测试API认证...")
    
    # 测试缺少API密钥
    try:
        response = requests.post(
            "http://localhost:8888/api/v1/stock/analyze",
            headers={"Content-Type": "application/json"},
            json={"stock_code": "000001.SZ"},
            timeout=10
        )
        
        if response.status_code == 401:
            print("✅ 缺少API密钥时正确返回401")
        else:
            print(f"❌ 缺少API密钥时应返回401，实际返回{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 认证测试出错: {e}")
        return False
    
    # 测试无效API密钥
    try:
        response = requests.post(
            "http://localhost:8888/api/v1/stock/analyze",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "invalid_key"
            },
            json={"stock_code": "000001.SZ"},
            timeout=10
        )
        
        if response.status_code == 403:
            print("✅ 无效API密钥时正确返回403")
            return True
        else:
            print(f"❌ 无效API密钥时应返回403，实际返回{response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 认证测试出错: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("股票分析系统 API 集成测试")
    print("=" * 60)
    
    print("\n⚠️  请确保股票分析系统正在运行 (python web_server.py)")
    print("   默认地址: http://localhost:8888")
    
    input("\n按回车键开始测试...")
    
    tests = [
        ("API健康检查", test_api_health),
        ("API认证功能", test_authentication),
        ("个股分析API", test_stock_analysis_api),
        ("投资组合分析API", test_portfolio_analysis_api),
        ("批量评分API", test_batch_score_api)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            time.sleep(1)  # 避免请求过快
        except KeyboardInterrupt:
            print("\n\n⚠️  测试被用户中断")
            break
        except Exception as e:
            print(f"❌ 测试 {test_name} 出现异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有API功能测试通过！")
        print("\n📖 接下来您可以：")
        print("1. 查看 API_USAGE_GUIDE.md 了解详细使用方法")
        print("2. 访问 http://localhost:8888/api/docs 查看Swagger文档")
        print("3. 使用 Postman 或其他工具进行更详细的测试")
    else:
        print("⚠️  部分测试失败，请检查系统配置和日志")
    
    print("=" * 60)


if __name__ == '__main__':
    main()
