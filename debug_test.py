#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("开始测试...")

try:
    import pandas as pd
    print("✅ pandas 导入成功")
except Exception as e:
    print(f"❌ pandas 导入失败: {e}")

try:
    import requests
    print("✅ requests 导入成功")
except Exception as e:
    print(f"❌ requests 导入失败: {e}")

try:
    df = pd.read_csv("list3.csv")
    print(f"✅ CSV文件读取成功，行数: {len(df)}")
    print(f"列名: {list(df.columns)}")
    
    if 'secID' in df.columns:
        stocks = df['secID'].dropna().tolist()
        print(f"股票代码: {stocks}")
    
except Exception as e:
    print(f"❌ CSV读取失败: {e}")

print("测试完成!")
