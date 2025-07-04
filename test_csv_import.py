#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试CSV批量导入功能
"""

import requests
import json

def test_csv_import():
    """测试CSV文件导入API"""
    url = "http://127.0.0.1:8888/api/portfolio/import_csv"
    
    # 打开CSV文件
    try:
        with open('list3.csv', 'rb') as f:
            files = {'file': ('list3.csv', f, 'text/csv')}
            
            print("正在测试CSV导入API...")
            print(f"URL: {url}")
            print(f"文件: list3.csv")
            
            response = requests.post(url, files=files)
            
            print(f"\n响应状态码: {response.status_code}")
            print(f"响应头: {response.headers}")
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ API调用成功!")
                print(f"响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 显示统计信息
                if result.get('success'):
                    print(f"\n📊 导入统计:")
                    print(f"总数: {result.get('total_count', 0)}")
                    print(f"成功: {result.get('converted_count', 0)}")
                    print(f"失败: {result.get('failed_count', 0)}")
                    
                    if result.get('converted_stocks'):
                        print(f"\n✅ 成功转换的股票:")
                        for stock in result['converted_stocks']:
                            print(f"  {stock['original_code']} -> {stock['converted_code']}")
                    
                    if result.get('failed_stocks'):
                        print(f"\n❌ 失败的股票:")
                        for stock in result['failed_stocks']:
                            print(f"  {stock['code']}: {stock['reason']}")
                else:
                    print(f"❌ 导入失败: {result}")
            else:
                print(f"\n❌ API调用失败!")
                print(f"错误信息: {response.text}")
                
    except FileNotFoundError:
        print("❌ 找不到list3.csv文件")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_csv_import()
