#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速API测试
"""

import requests

def test_api():
    print("快速API测试")
    print("=" * 30)
    
    # 正确的API地址（无端口号）
    api_url = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
    api_key = "UZXJfw3YNX80DLfN"
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key
    }
    
    payload = {
        "stock_code": "000001.SZ",
        "market_type": "A",
        "analysis_depth": "full",
        "include_ai_analysis": True
    }
    
    try:
        print("正在测试API连接...")
        print(f"URL: {api_url}")
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            if result.get('success'):
                print("✅ 分析成功!")
                data = result.get('data', {})
                basic_info = data.get('basic_info', {})
                print(f"股票名称: {basic_info.get('name', 'N/A')}")
            else:
                print(f"❌ 分析失败: {result.get('message', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    test_api()
