#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试市场扫描页面功能
"""

import requests
import json
import time

def test_page_functionality():
    """测试页面基本功能"""
    base_url = "http://localhost:8888"
    
    print("=== 测试市场扫描页面功能 ===")
    
    # 1. 测试页面是否可以访问
    print("1. 测试页面访问...")
    try:
        response = requests.get(f"{base_url}/market_scan", timeout=10)
        if response.status_code == 200:
            print("   ✓ 页面访问正常")
        else:
            print(f"   ✗ 页面访问失败: {response.status_code}")
            return
    except Exception as e:
        print(f"   ✗ 页面访问出错: {str(e)}")
        return
    
    # 2. 测试指数股票API
    print("\n2. 测试指数股票API...")
    try:
        response = requests.get(f"{base_url}/api/index_stocks?index_code=000300", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stock_list = data.get('stock_list', [])
            print(f"   ✓ 指数股票API正常，获取到 {len(stock_list)} 只股票")
        else:
            print(f"   ✗ 指数股票API失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 指数股票API出错: {str(e)}")
    
    # 3. 测试行业股票API
    print("\n3. 测试行业股票API...")
    try:
        response = requests.get(f"{base_url}/api/industry_stocks?industry=银行", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stock_list = data.get('stock_list', [])
            print(f"   ✓ 行业股票API正常，获取到 {len(stock_list)} 只股票")
        else:
            print(f"   ✗ 行业股票API失败: {response.status_code}")
    except Exception as e:
        print(f"   ✗ 行业股票API出错: {str(e)}")
    
    # 4. 测试扫描任务启动
    print("\n4. 测试扫描任务启动...")
    test_stocks = ["000001", "000002"]
    scan_data = {
        "stock_list": test_stocks,
        "min_score": 60,
        "market_type": "A"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/start_market_scan",
            json=scan_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✓ 扫描任务启动成功，任务ID: {task_id}")
            
            # 5. 测试任务状态查询
            print("\n5. 测试任务状态查询...")
            time.sleep(2)  # 等待任务开始
            
            status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   ✓ 任务状态查询成功: {status.get('status')}")
            else:
                print(f"   ✗ 任务状态查询失败: {status_response.status_code}")
                
        else:
            print(f"   ✗ 扫描任务启动失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ✗ 扫描任务测试出错: {str(e)}")

def test_javascript_functions():
    """测试JavaScript函数是否正确定义"""
    print("\n=== 检查JavaScript函数定义 ===")
    
    # 读取HTML文件检查函数定义
    try:
        with open('templates/market_scan.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查关键函数是否存在
        functions_to_check = [
            'fetchIndexStocks',
            'fetchIndustryStocks', 
            'scanMarket',
            'pollScanStatus',
            'cancelScan',
            'cancelCurrentScan',
            'renderResults',
            'exportToCSV'
        ]
        
        for func in functions_to_check:
            if f'function {func}(' in content:
                print(f"   ✓ 函数 {func} 已定义")
            else:
                print(f"   ✗ 函数 {func} 未找到")
                
        # 检查全局变量
        if 'let currentTaskId = null' in content:
            print("   ✓ 全局变量 currentTaskId 已定义")
        else:
            print("   ✗ 全局变量 currentTaskId 未找到")
            
    except Exception as e:
        print(f"   ✗ 检查JavaScript函数时出错: {str(e)}")

if __name__ == "__main__":
    test_page_functionality()
    test_javascript_functions()
    print("\n=== 测试完成 ===")
    print("\n建议:")
    print("1. 在浏览器中打开 http://localhost:8888/market_scan")
    print("2. 打开浏览器开发者工具(F12)查看控制台是否有错误")
    print("3. 尝试选择一个指数或行业，点击'开始扫描'按钮")
    print("4. 观察是否显示加载状态和进度信息")
