#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的API接口
"""

import requests
import json
import time

def test_stock_analysis(stock_code, api_key="UZXJfw3YNX80DLfN"):
    """测试股票分析API"""
    url = "http://localhost:7860/api/v1/stock/analyze"
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key
    }
    
    payload = {
        "stock_code": stock_code,
        "market_type": "A",
        "analysis_depth": "full",
        "include_ai_analysis": True
    }
    
    try:
        print(f"正在测试股票: {stock_code}")
        print(f"请求URL: {url}")
        print(f"请求数据: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            print(f"响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ API调用失败: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=== 股票分析API修复效果测试 ===\n")
    
    # 测试问题股票代码
    test_stocks = ["603316.SH", "601218.SH"]
    
    results = {}
    
    for stock_code in test_stocks:
        print(f"\n{'='*50}")
        print(f"测试股票: {stock_code}")
        print('='*50)
        
        success = test_stock_analysis(stock_code)
        results[stock_code] = success
        
        # 等待一下避免请求过快
        time.sleep(2)
    
    # 总结测试结果
    print(f"\n{'='*50}")
    print("测试结果总结")
    print('='*50)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for stock_code, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{stock_code}: {status}")
    
    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 所有测试通过！API修复成功！")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")

if __name__ == "__main__":
    main()
