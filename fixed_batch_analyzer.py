#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版批量股票分析程序
解决了API连接问题，增强了错误处理
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
import sys

def main():
    print("=== 修复版批量股票分析程序 ===")
    print(f"开始时间: {datetime.now()}")
    
    # 修复后的配置（移除了错误的端口号8888）
    API_URL = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
    API_KEY = "UZXJfw3YNX80DLfN"
    CSV_FILE = "list3.csv"
    
    print(f"API地址: {API_URL}")
    print(f"API密钥: {API_KEY[:10]}...")
    
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
    
    # 2. 股票代码转换
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
            response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            print(f"   HTTP状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ API连接成功!")
                
                if result.get('success'):
                    data = result.get('data', {})
                    print(f"   ✅ API分析成功!")
                    print(f"   响应数据键: {list(data.keys())}")
                else:
                    print(f"   ⚠️ API返回失败: {result.get('message', '未知错误')}")
                    print("   但连接正常，可以继续尝试其他股票")
                    
            elif response.status_code == 500:
                print("   ⚠️ API服务器内部错误 (500)")
                print("   这是服务端问题，不是客户端问题")
                print("   连接正常，但API服务可能有bug")
                
                # 尝试解析错误信息
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', '未知错误')
                    print(f"   错误详情: {error_msg}")
                except:
                    print(f"   原始响应: {response.text[:200]}...")
                    
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                print(f"   响应内容: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("   ❌ 请求超时")
            print("   建议: 增加超时时间或稍后重试")
            return
        except requests.exceptions.ConnectionError:
            print("   ❌ 连接错误")
            print("   建议: 检查网络连接")
            return
        except Exception as e:
            print(f"   ❌ API调用异常: {e}")
            return
    
    # 4. 批量分析决策
    print(f"\n4. 批量分析决策...")
    
    user_input = input(f"是否继续批量分析 {len(converted_stocks)} 只股票? (y/n): ").lower().strip()
    
    if user_input != 'y':
        print("用户取消批量分析")
        return
    
    # 5. 执行批量分析
    print(f"\n5. 开始批量分析...")
    
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
            response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    
                    # 尝试提取基本信息
                    try:
                        basic_info = data.get('basic_info', {})
                        scores = data.get('scores', {})
                        
                        record = {
                            'original_code': original,
                            'converted_code': converted,
                            'stock_name': basic_info.get('name', ''),
                            'current_price': basic_info.get('current_price', 0),
                            'overall_score': scores.get('overall_score', 0),
                            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'success'
                        }
                        
                        results.append(record)
                        print(f"   ✅ 成功 - 评分: {record['overall_score']}")
                        
                    except Exception as e:
                        # 如果数据解析失败，至少记录基本信息
                        record = {
                            'original_code': original,
                            'converted_code': converted,
                            'stock_name': 'API返回数据解析失败',
                            'current_price': 0,
                            'overall_score': 0,
                            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'data_parse_error',
                            'error': str(e)
                        }
                        results.append(record)
                        print(f"   ⚠️ 数据解析失败: {e}")
                        
                else:
                    failed.append({
                        'code': original, 
                        'error': result.get('message', '未知错误'),
                        'status_code': response.status_code
                    })
                    print(f"   ❌ 失败: {result.get('message', '未知错误')}")
                    
            else:
                failed.append({
                    'code': original, 
                    'error': f'HTTP {response.status_code}',
                    'status_code': response.status_code
                })
                print(f"   ❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            failed.append({
                'code': original, 
                'error': str(e),
                'status_code': 'exception'
            })
            print(f"   ❌ 异常: {e}")
        
        # 延迟避免限流
        if i < len(stocks):
            time.sleep(2)  # 增加延迟到2秒
    
    # 6. 保存结果
    print(f"\n6. 保存结果...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if results:
        output_file = f"batch_analysis_results_{timestamp}.csv"
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"   ✅ 结果已保存: {output_file}")
        print(f"   成功分析: {len(results)} 只股票")
        
        # 显示成功的结果
        success_results = [r for r in results if r.get('status') == 'success']
        if success_results:
            print(f"\n   成功分析的股票 ({len(success_results)} 只):")
            for r in success_results[:5]:  # 显示前5个
                print(f"   - {r['stock_name']} ({r['converted_code']}) 评分: {r['overall_score']}")
            if len(success_results) > 5:
                print(f"   ... 还有 {len(success_results) - 5} 只股票")
    
    if failed:
        failed_file = f"batch_analysis_failed_{timestamp}.csv"
        failed_df = pd.DataFrame(failed)
        failed_df.to_csv(failed_file, index=False, encoding='utf-8-sig')
        print(f"   ❌ 失败记录已保存: {failed_file}")
        print(f"   失败: {len(failed)} 只股票")
    
    # 7. 总结
    total = len(results) + len(failed)
    success_rate = (len(results) / total * 100) if total > 0 else 0
    
    print(f"\n=== 分析完成 ===")
    print(f"总股票数: {total}")
    print(f"成功: {len(results)}")
    print(f"失败: {len(failed)}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"结束时间: {datetime.now()}")
    
    if len(failed) > 0:
        print(f"\n💡 提示:")
        print(f"- 如果大部分失败是500错误，这是API服务端问题")
        print(f"- 建议联系API服务提供方修复服务端bug")
        print(f"- 或者稍后重试，服务可能会恢复正常")

if __name__ == "__main__":
    main()
