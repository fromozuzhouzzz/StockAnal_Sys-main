#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端修复后的功能
"""

import requests
import time
import sys

def test_basic_functionality():
    """测试基本功能"""
    base_url = 'http://localhost:8888'
    
    print("=" * 50)
    print("测试前端修复后的基本功能")
    print("=" * 50)
    
    try:
        # 1. 测试页面访问
        print("1. 测试页面访问...")
        response = requests.get(f'{base_url}/market_scan', timeout=5)
        if response.status_code == 200:
            print("   ✓ 市场扫描页面访问正常")
        else:
            print(f"   ✗ 页面访问失败: {response.status_code}")
            return False
            
        # 2. 测试指数API
        print("\n2. 测试指数API...")
        response = requests.get(f'{base_url}/api/index_stocks?index_code=000300', timeout=10)
        if response.status_code == 200:
            data = response.json()
            stock_list = data.get('stock_list', [])
            print(f"   ✓ 指数API正常，获取到 {len(stock_list)} 只股票")
            
            if len(stock_list) == 0:
                print("   ⚠ 警告：股票列表为空")
                return False
                
        else:
            print(f"   ✗ 指数API失败: {response.status_code} - {response.text}")
            return False
            
        # 3. 测试行业API
        print("\n3. 测试行业API...")
        response = requests.get(f'{base_url}/api/industry_stocks?industry=银行', timeout=10)
        if response.status_code == 200:
            data = response.json()
            industry_stocks = data.get('stock_list', [])
            print(f"   ✓ 行业API正常，获取到 {len(industry_stocks)} 只银行股")
        else:
            print(f"   ✗ 行业API失败: {response.status_code} - {response.text}")
            return False
            
        # 4. 测试扫描任务启动
        print("\n4. 测试扫描任务启动...")
        test_stocks = stock_list[:3] if len(stock_list) >= 3 else stock_list[:1]
        scan_data = {
            'stock_list': test_stocks,
            'min_score': 50,
            'market_type': 'A'
        }
        
        response = requests.post(f'{base_url}/api/start_market_scan', json=scan_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✓ 扫描任务启动成功，任务ID: {task_id}")
            
            # 5. 测试任务状态查询
            print("\n5. 测试任务状态查询...")
            time.sleep(1)
            
            status_response = requests.get(f'{base_url}/api/scan_status/{task_id}', timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   ✓ 任务状态查询成功，状态: {status.get('status')}")
                print(f"   ✓ 后端API完全正常")
                return True
            else:
                print(f"   ✗ 任务状态查询失败: {status_response.status_code} - {status_response.text}")
                return False
                
        else:
            print(f"   ✗ 扫描任务启动失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        return False

def main():
    """主函数"""
    success = test_basic_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 后端API测试全部通过！")
        print("\n现在请在浏览器中测试前端功能：")
        print("1. 打开 http://localhost:8888/market_scan")
        print("2. 选择一个指数（如沪深300）")
        print("3. 点击'开始扫描'按钮")
        print("4. 观察是否显示扫描进度")
        print("5. 检查浏览器控制台是否有错误（按F12）")
        print("\n如果前端仍有问题，请检查浏览器控制台的错误信息。")
    else:
        print("✗ 后端API测试失败！")
        print("请检查服务器日志以获取更多信息。")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
