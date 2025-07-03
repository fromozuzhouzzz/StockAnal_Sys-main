#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统一评分API的脚本
用于验证投资组合页面和股票详情页面评分一致性
"""

import requests
import json
import sys

def test_score_consistency():
    """测试评分一致性"""
    base_url = "http://localhost:5000"
    test_stock = "000001"  # 平安银行
    market_type = "A"
    
    print(f"🔍 测试股票: {test_stock}")
    print("=" * 50)
    
    # 1. 测试投资组合页面使用的API (/analyze)
    print("📊 测试投资组合页面API (/analyze)...")
    try:
        response1 = requests.post(
            f"{base_url}/analyze",
            json={
                "stock_codes": [test_stock],
                "market_type": market_type
            },
            timeout=30
        )
        
        if response1.status_code == 200:
            data1 = response1.json()
            if data1.get('results') and len(data1['results']) > 0:
                portfolio_score = data1['results'][0].get('score', 'N/A')
                portfolio_name = data1['results'][0].get('stock_name', 'N/A')
                print(f"✅ 投资组合页面评分: {portfolio_score}")
                print(f"   股票名称: {portfolio_name}")
            else:
                print("❌ 投资组合API返回数据为空")
                return False
        else:
            print(f"❌ 投资组合API请求失败: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 投资组合API请求异常: {e}")
        return False
    
    # 2. 测试股票详情页面使用的新API (/api/stock_score)
    print("\n📈 测试股票详情页面API (/api/stock_score)...")
    try:
        response2 = requests.post(
            f"{base_url}/api/stock_score",
            json={
                "stock_code": test_stock,
                "market_type": market_type
            },
            timeout=30
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            detail_score = data2.get('score', 'N/A')
            detail_name = data2.get('stock_name', 'N/A')
            detail_recommendation = data2.get('recommendation', 'N/A')
            print(f"✅ 股票详情页面评分: {detail_score}")
            print(f"   股票名称: {detail_name}")
            print(f"   投资建议: {detail_recommendation}")
        else:
            print(f"❌ 股票详情API请求失败: {response2.status_code}")
            print(f"   错误信息: {response2.text}")
            return False
            
    except Exception as e:
        print(f"❌ 股票详情API请求异常: {e}")
        return False
    
    # 3. 比较评分一致性
    print("\n🔍 评分一致性检查...")
    print("=" * 50)
    
    if portfolio_score == detail_score:
        print(f"✅ 评分一致! 两个页面都显示: {portfolio_score}")
        print("🎉 修复成功！同一股票在不同页面显示相同评分")
        return True
    else:
        print(f"❌ 评分不一致!")
        print(f"   投资组合页面: {portfolio_score}")
        print(f"   股票详情页面: {detail_score}")
        print(f"   差异: {abs(float(portfolio_score) - float(detail_score)) if isinstance(portfolio_score, (int, float)) and isinstance(detail_score, (int, float)) else 'N/A'}")
        return False

def test_multiple_stocks():
    """测试多只股票的评分一致性"""
    test_stocks = ["000001", "000002", "600000"]
    
    print("\n🔄 测试多只股票评分一致性...")
    print("=" * 50)
    
    success_count = 0
    total_count = len(test_stocks)
    
    for stock in test_stocks:
        print(f"\n测试股票: {stock}")
        if test_score_consistency_for_stock(stock):
            success_count += 1
            print(f"✅ {stock} 评分一致")
        else:
            print(f"❌ {stock} 评分不一致")
    
    print(f"\n📊 测试结果: {success_count}/{total_count} 只股票评分一致")
    return success_count == total_count

def test_score_consistency_for_stock(stock_code):
    """测试单只股票的评分一致性"""
    base_url = "http://localhost:5000"
    market_type = "A"
    
    try:
        # 投资组合API
        response1 = requests.post(
            f"{base_url}/analyze",
            json={"stock_codes": [stock_code], "market_type": market_type},
            timeout=15
        )
        
        # 股票详情API
        response2 = requests.post(
            f"{base_url}/api/stock_score",
            json={"stock_code": stock_code, "market_type": market_type},
            timeout=15
        )
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            score1 = data1['results'][0]['score'] if data1.get('results') else None
            score2 = data2.get('score')
            
            return score1 == score2
        else:
            return False
            
    except Exception:
        return False

if __name__ == "__main__":
    print("🚀 开始测试股票评分一致性...")
    print("=" * 50)
    
    # 测试单只股票
    if test_score_consistency():
        print("\n🎯 单只股票测试通过!")
        
        # 测试多只股票
        if test_multiple_stocks():
            print("\n🏆 所有测试通过! 评分一致性修复成功!")
            sys.exit(0)
        else:
            print("\n⚠️  部分股票测试失败，需要进一步检查")
            sys.exit(1)
    else:
        print("\n❌ 单只股票测试失败，需要检查API实现")
        sys.exit(1)
