#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行批量股票分析
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
import os

def convert_stock_code(sec_id):
    """转换股票代码格式"""
    if pd.isna(sec_id) or not isinstance(sec_id, str):
        return ""
        
    if sec_id.endswith('.XSHE'):
        return sec_id.replace('.XSHE', '.SZ')
    elif sec_id.endswith('.XSHG'):
        return sec_id.replace('.XSHG', '.SH')
    else:
        return sec_id

def analyze_stock(stock_code, api_url, api_key):
    """分析单只股票"""
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
        print(f"正在分析股票: {stock_code}")
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success', False):
                print(f"✅ {stock_code} 分析成功")
                return result.get('data', {})
            else:
                print(f"❌ {stock_code} 分析失败: {result.get('message', '未知错误')}")
                return None
        else:
            print(f"❌ {stock_code} HTTP错误: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ {stock_code} 异常: {str(e)}")
        return None

def extract_metrics(analysis_data, original_code, converted_code):
    """提取关键指标"""
    metrics = {
        'original_code': original_code,
        'converted_code': converted_code,
        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 基本信息
    basic_info = analysis_data.get('basic_info', {})
    metrics.update({
        'stock_name': basic_info.get('name', ''),
        'current_price': basic_info.get('current_price', 0),
        'change_percent': basic_info.get('change_percent', 0)
    })
    
    # 评分信息
    scores = analysis_data.get('scores', {})
    metrics.update({
        'overall_score': scores.get('overall_score', 0),
        'technical_score': scores.get('technical_score', 0),
        'fundamental_score': scores.get('fundamental_score', 0),
        'risk_score': scores.get('risk_score', 0)
    })
    
    # 风险评估
    risk_assessment = analysis_data.get('risk_assessment', {})
    metrics.update({
        'risk_level': risk_assessment.get('risk_level', ''),
        'volatility': risk_assessment.get('volatility', 0)
    })
    
    return metrics

def main():
    """主函数"""
    print("批量股票分析程序")
    print("=" * 50)
    
    # 配置
    API_URL = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
    API_KEY = "UZXJfw3YNX80DLfN"
    CSV_FILE = "list3.csv"
    
    # 读取CSV
    try:
        print("正在读取CSV文件...")
        df = pd.read_csv(CSV_FILE)
        print(f"✅ CSV读取成功，总行数: {len(df)}")
        
        if 'secID' not in df.columns:
            print("❌ 未找到secID列")
            return
        
        stocks = df[df['secID'].notna() & (df['secID'] != '')]['secID'].tolist()
        print(f"找到 {len(stocks)} 只有效股票")
        
        for stock in stocks:
            print(f"  - {stock}")
        
    except Exception as e:
        print(f"❌ CSV读取失败: {e}")
        return
    
    # 批量分析
    results = []
    failed = []
    
    for i, original_code in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] 处理股票: {original_code}")
        
        # 转换代码
        converted_code = convert_stock_code(original_code)
        print(f"转换后代码: {converted_code}")
        
        if not converted_code:
            print("❌ 代码转换失败")
            failed.append(original_code)
            continue
        
        # 分析股票
        analysis_data = analyze_stock(converted_code, API_URL, API_KEY)
        
        if analysis_data:
            metrics = extract_metrics(analysis_data, original_code, converted_code)
            results.append(metrics)
            print(f"✅ 分析完成，综合评分: {metrics.get('overall_score', 'N/A')}")
        else:
            failed.append(original_code)
        
        # 延迟避免限流
        if i < len(stocks):
            print("等待1秒...")
            time.sleep(1)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if results:
        output_file = f"batch_analysis_results_{timestamp}.csv"
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 分析结果已保存: {output_file}")
        print(f"成功分析: {len(results)} 只股票")
    
    if failed:
        print(f"❌ 失败股票: {len(failed)} 只")
        for code in failed:
            print(f"  - {code}")
    
    print(f"\n分析完成! 成功率: {len(results)/(len(results)+len(failed))*100:.1f}%")

if __name__ == "__main__":
    main()
