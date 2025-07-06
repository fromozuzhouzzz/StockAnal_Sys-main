#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的投资组合导出测试
"""

import requests
import json

def test_hf_export():
    """测试HF Spaces导出功能"""
    url = "https://fromozu-stock-analysis.hf.space/api/v1/portfolio/export"
    
    data = {
        "stocks": [
            {"stock_code": "000001.SZ", "weight": 50, "market_type": "A"},
            {"stock_code": "600000.SH", "weight": 50, "market_type": "A"}
        ],
        "portfolio_name": "测试组合",
        "export_format": "csv"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "UZXJfw3YNX80DLfN"
    }
    
    print("测试HF Spaces导出API...")
    print(f"URL: {url}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 成功！导出功能已修复")
            return True
        else:
            print(f"❌ 失败: {response.status_code}")
            try:
                error = response.json()
                print(f"错误: {error}")
            except:
                print(f"响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def test_simple_export():
    """测试简化导出API"""
    url = "https://fromozu-stock-analysis.hf.space/api/portfolio/export-simple"
    
    data = {
        "stocks": [
            {"stock_code": "000001.SZ", "weight": 50, "market_type": "A"},
            {"stock_code": "600000.SH", "weight": 50, "market_type": "A"}
        ],
        "portfolio_name": "测试组合"
    }
    
    headers = {"Content-Type": "application/json"}
    
    print("\n测试简化导出API...")
    print(f"URL: {url}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 简化导出成功！")
            return True
        else:
            print(f"❌ 失败: {response.status_code}")
            try:
                error = response.json()
                print(f"错误: {error}")
            except:
                print(f"响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试投资组合导出功能修复")
    
    # 测试主API
    main_success = test_hf_export()
    
    # 测试备用API
    simple_success = test_simple_export()
    
    print(f"\n📊 测试结果:")
    print(f"主导出API: {'✅ 成功' if main_success else '❌ 失败'}")
    print(f"简化导出API: {'✅ 成功' if simple_success else '❌ 失败'}")
    
    if main_success:
        print("🎉 主要问题已解决！403错误已修复")
    elif simple_success:
        print("🔧 备用方案可用，用户可以使用简化导出功能")
    else:
        print("⚠️  需要进一步调试")
