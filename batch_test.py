#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量股票分析测试程序
"""

import pandas as pd
import requests
import json

def test_csv_reading():
    """测试CSV文件读取"""
    print("=== 测试CSV文件读取 ===")
    try:
        df = pd.read_csv("list3.csv")
        print(f"CSV文件读取成功!")
        print(f"总行数: {len(df)}")
        print(f"列名: {list(df.columns)}")
        
        if 'secID' in df.columns:
            valid_stocks = df[df['secID'].notna() & (df['secID'] != '')]['secID'].tolist()
            print(f"有效股票代码: {len(valid_stocks)} 个")
            for code in valid_stocks:
                print(f"  {code}")
        else:
            print("未找到 secID 列!")
            
    except Exception as e:
        print(f"CSV文件读取失败: {str(e)}")

def test_code_conversion():
    """测试股票代码转换"""
    print("\n=== 测试股票代码转换 ===")
    
    def convert_stock_code(sec_id):
        if pd.isna(sec_id) or not isinstance(sec_id, str):
            return ""
            
        if sec_id.endswith('.XSHE'):
            return sec_id.replace('.XSHE', '.SZ')
        elif sec_id.endswith('.XSHG'):
            return sec_id.replace('.XSHG', '.SH')
        else:
            return sec_id
    
    test_codes = ["603316.XSHG", "601218.XSHG", "000001.XSHE"]
    for code in test_codes:
        converted = convert_stock_code(code)
        print(f"{code} -> {converted}")

def test_api_connection():
    """测试API连接"""
    print("\n=== 测试API连接 ===")
    
    API_URL = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
    API_KEY = "UZXJfw3YNX80DLfN"
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    
    payload = {
        "stock_code": "000001.SZ",
        "market_type": "A",
        "analysis_depth": "full",
        "include_ai_analysis": True
    }
    
    try:
        print("正在测试API连接...")
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("API调用成功!")
            print(f"响应键: {list(result.keys())}")
            if 'data' in result:
                data = result['data']
                print(f"数据键: {list(data.keys())}")
        else:
            print(f"API调用失败: {response.text}")
            
    except Exception as e:
        print(f"API调用异常: {str(e)}")

if __name__ == "__main__":
    print("批量股票分析测试程序")
    print("=" * 50)
    
    test_csv_reading()
    test_code_conversion()
    test_api_connection()
    
    print("\n测试完成!")
