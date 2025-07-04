#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量股票分析程序 - 测试版本
用于测试API连接和基本功能
"""

import pandas as pd
import requests
import json
from batch_stock_analyzer import BatchStockAnalyzer

def test_api_connection():
    """测试API连接"""
    API_URL = "https://fromozu-stock-analysis.hf.space:8888/api/v1/stock/analyze"
    API_KEY = "UZXJfw3YNX80DLfN"
    
    # 创建分析器
    analyzer = BatchStockAnalyzer(API_URL, API_KEY)
    
    # 测试股票代码转换
    print("=== 测试股票代码转换 ===")
    test_codes = ["603316.XSHG", "601218.XSHG", "000001.XSHE"]
    for code in test_codes:
        converted = analyzer.convert_stock_code(code)
        print(f"{code} -> {converted}")
    
    # 测试单只股票分析
    print("\n=== 测试API调用 ===")
    test_stock = "000001.SZ"  # 平安银行
    print(f"正在测试股票: {test_stock}")
    
    result = analyzer.analyze_single_stock(test_stock)
    if result:
        print("API调用成功!")
        print(f"返回数据键: {list(result.keys())}")
        
        # 提取关键指标
        metrics = analyzer.extract_key_metrics(result, "000001.XSHE", test_stock)
        print(f"提取的关键指标: {len(metrics)} 个")
        for key, value in list(metrics.items())[:10]:  # 显示前10个指标
            print(f"  {key}: {value}")
    else:
        print("API调用失败!")

def test_csv_reading():
    """测试CSV文件读取"""
    print("\n=== 测试CSV文件读取 ===")
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

if __name__ == "__main__":
    print("批量股票分析程序 - 测试模式")
    print("=" * 50)
    
    # 测试CSV读取
    test_csv_reading()
    
    # 测试API连接
    test_api_connection()
    
    print("\n测试完成!")
