#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终批量股票分析程序
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
import sys

def main():
    print("=== 批量股票分析程序 ===")
    print(f"开始时间: {datetime.now()}")
    
    # 配置
    API_URL = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
    API_KEY = "UZXJfw3YNX80DLfN"
    CSV_FILE = "list3.csv"
    
    # 1. 读取CSV文件
    print("\n1. 读取CSV文件...")
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"✅ 成功读取CSV文件")
        print(f"   总行数: {len(df)}")
        print(f"   列名: {list(df.columns)}")
        
        if 'secID' not in df.columns:
            print("❌ 错误: 未找到 'secID' 列")
            return
        
        # 获取有效股票代码
        stocks = df[df['secID'].notna() & (df['secID'] != '')]['secID'].tolist()
        print(f"   有效股票代码: {len(stocks)} 个")
        
        for i, stock in enumerate(stocks, 1):
            print(f"   {i}. {stock}")
            
    except Exception as e:
        print(f"❌ CSV文件读取失败: {e}")
        return
    
    # 2. 股票代码转换测试
    print("\n2. 股票代码转换...")
    
    def convert_code(sec_id):
        if sec_id.endswith('.XSHE'):
            return sec_id.replace('.XSHE', '.SZ')
        elif sec_id.endswith('.XSHG'):
            return sec_id.replace('.XSHG', '.SH')
        return sec_id
    
    converted_stocks = []
    for stock in stocks:
        converted = convert_code(stock)
        converted_stocks.append(converted)
        print(f"   {stock} → {converted}")
    
    # 3. API连接测试
    print("\n3. API连接测试...")
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    
    # 测试第一只股票
    if converted_stocks:
        test_stock = converted_stocks[0]
        print(f"   测试股票: {test_stock}")
        
        payload = {
            "stock_code": test_stock,
            "market_type": "A",
            "analysis_depth": "full",
            "include_ai_analysis": True
        }
        
        try:
            print("   发送API请求...")
            response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            print(f"   HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ API调用成功!")
                print(f"   响应键: {list(result.keys())}")
                
                if result.get('success'):
                    data = result.get('data', {})
                    print(f"   数据键: {list(data.keys())}")
                    
                    # 提取基本信息
                    basic_info = data.get('basic_info', {})
                    if basic_info:
                        print(f"   股票名称: {basic_info.get('name', 'N/A')}")
                        print(f"   当前价格: {basic_info.get('current_price', 'N/A')}")
                    
                    scores = data.get('scores', {})
                    if scores:
                        print(f"   综合评分: {scores.get('overall_score', 'N/A')}")
                else:
                    print(f"   ❌ API返回失败: {result.get('message', '未知错误')}")
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                print(f"   响应内容: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ API调用异常: {e}")
    
    # 4. 批量分析
    print(f"\n4. 开始批量分析 {len(converted_stocks)} 只股票...")
    
    results = []
    failed = []
    
    for i, (original, converted) in enumerate(zip(stocks, converted_stocks), 1):
        print(f"\n[{i}/{len(stocks)}] 分析: {original} ({converted})")
        
        payload = {
            "stock_code": converted,
            "market_type": "A",
            "analysis_depth": "full",
            "include_ai_analysis": True
        }
        
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    
                    # 提取关键信息
                    basic_info = data.get('basic_info', {})
                    scores = data.get('scores', {})
                    risk = data.get('risk_assessment', {})
                    
                    record = {
                        'original_code': original,
                        'converted_code': converted,
                        'stock_name': basic_info.get('name', ''),
                        'current_price': basic_info.get('current_price', 0),
                        'change_percent': basic_info.get('change_percent', 0),
                        'overall_score': scores.get('overall_score', 0),
                        'technical_score': scores.get('technical_score', 0),
                        'fundamental_score': scores.get('fundamental_score', 0),
                        'risk_score': scores.get('risk_score', 0),
                        'risk_level': risk.get('risk_level', ''),
                        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    results.append(record)
                    print(f"   ✅ 成功 - 评分: {record['overall_score']}")
                else:
                    failed.append({'code': original, 'error': result.get('message', '未知错误')})
                    print(f"   ❌ 失败: {result.get('message', '未知错误')}")
            else:
                failed.append({'code': original, 'error': f'HTTP {response.status_code}'})
                print(f"   ❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            failed.append({'code': original, 'error': str(e)})
            print(f"   ❌ 异常: {e}")
        
        # 延迟避免限流
        if i < len(stocks):
            time.sleep(1)
    
    # 5. 保存结果
    print(f"\n5. 保存结果...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if results:
        output_file = f"batch_analysis_results_{timestamp}.csv"
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✅ 结果已保存: {output_file}")
        print(f"   成功分析: {len(results)} 只股票")
        
        # 显示前几条结果
        print("\n   前3条结果预览:")
        for i, row in results_df.head(3).iterrows():
            print(f"   {i+1}. {row['stock_name']} ({row['converted_code']}) - 评分: {row['overall_score']}")
    
    if failed:
        failed_file = f"batch_analysis_failed_{timestamp}.csv"
        failed_df = pd.DataFrame(failed)
        failed_df.to_csv(failed_file, index=False, encoding='utf-8-sig')
        print(f"   ❌ 失败记录已保存: {failed_file}")
        print(f"   失败: {len(failed)} 只股票")
    
    # 6. 总结
    total = len(results) + len(failed)
    success_rate = (len(results) / total * 100) if total > 0 else 0
    
    print(f"\n=== 分析完成 ===")
    print(f"总股票数: {total}")
    print(f"成功: {len(results)}")
    print(f"失败: {len(failed)}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"结束时间: {datetime.now()}")

if __name__ == "__main__":
    main()
