#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API连接测试程序
验证股票分析API是否正常工作
"""

import requests
import json
from datetime import datetime

def test_api_health():
    """测试API健康状态"""
    print("=== 测试API健康状态 ===")
    
    health_url = "https://fromozu-stock-analysis.hf.space/api/v1/health"
    
    try:
        response = requests.get(health_url, timeout=30)
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API服务正常运行")
            print(f"API版本: {result.get('data', {}).get('api_version', 'N/A')}")
            print(f"服务状态: {result.get('data', {}).get('status', 'N/A')}")
            return True
        else:
            print(f"❌ API健康检查失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API健康检查异常: {e}")
        return False

def test_stock_analysis_api():
    """测试股票分析API"""
    print("\n=== 测试股票分析API ===")
    
    api_url = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
    api_key = "UZXJfw3YNX80DLfN"
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key
    }
    
    # 测试数据
    test_stocks = [
        {"code": "000001.SZ", "name": "平安银行"},
        {"code": "600000.SH", "name": "浦发银行"}
    ]
    
    for stock in test_stocks:
        print(f"\n测试股票: {stock['name']} ({stock['code']})")
        
        payload = {
            "stock_code": stock['code'],
            "market_type": "A",
            "analysis_depth": "full",
            "include_ai_analysis": True
        }
        
        try:
            print("发送API请求...")
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            print(f"HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    basic_info = data.get('basic_info', {})
                    scores = data.get('scores', {})
                    
                    print("✅ API调用成功!")
                    print(f"股票名称: {basic_info.get('name', 'N/A')}")
                    print(f"当前价格: {basic_info.get('current_price', 'N/A')}")
                    print(f"综合评分: {scores.get('overall_score', 'N/A')}")
                    print(f"技术评分: {scores.get('technical_score', 'N/A')}")
                    print(f"基本面评分: {scores.get('fundamental_score', 'N/A')}")
                    return True
                else:
                    print(f"❌ API返回失败: {result.get('message', '未知错误')}")
                    return False
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"响应内容: {response.text[:200]}...")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误")
            return False
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            return False

def test_batch_analysis_simulation():
    """模拟批量分析测试"""
    print("\n=== 模拟批量分析测试 ===")
    
    # 模拟CSV数据
    test_codes = ["603316.XSHG", "601218.XSHG"]
    
    print(f"模拟处理 {len(test_codes)} 只股票:")
    for code in test_codes:
        print(f"  - {code}")
    
    # 代码转换测试
    print("\n代码转换测试:")
    for original in test_codes:
        if original.endswith('.XSHE'):
            converted = original.replace('.XSHE', '.SZ')
        elif original.endswith('.XSHG'):
            converted = original.replace('.XSHG', '.SH')
        else:
            converted = original
        print(f"  {original} → {converted}")
    
    print("\n✅ 批量分析模拟完成")

def main():
    """主函数"""
    print("股票分析API连接测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now()}")
    
    # 1. 测试API健康状态
    health_ok = test_api_health()
    
    # 2. 测试股票分析API
    if health_ok:
        api_ok = test_stock_analysis_api()
        
        # 3. 模拟批量分析
        if api_ok:
            test_batch_analysis_simulation()
            print("\n🎉 所有测试通过！批量分析程序应该可以正常工作。")
        else:
            print("\n❌ 股票分析API测试失败，请检查API密钥或服务状态。")
    else:
        print("\n❌ API服务不可用，请检查网络连接或服务状态。")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()
