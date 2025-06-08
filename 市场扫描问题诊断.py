#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场扫描问题诊断脚本
帮助用户快速定位和解决市场扫描页面无响应的问题
"""

import requests
import json
import time
import os
from datetime import datetime

def check_server_status():
    """检查服务器状态"""
    print("=== 服务器状态检查 ===")
    
    base_urls = [
        "http://localhost:8888",
        "http://localhost:5000",
        "http://127.0.0.1:8888",
        "http://127.0.0.1:5000"
    ]
    
    working_url = None
    
    for url in base_urls:
        try:
            response = requests.get(f"{url}/", timeout=5)
            if response.status_code == 200:
                print(f"✓ 服务器运行正常: {url}")
                working_url = url
                break
        except Exception as e:
            print(f"✗ 无法连接到 {url}: {str(e)}")
    
    if not working_url:
        print("❌ 未找到运行中的服务器！")
        print("请确保运行了 python web_server.py")
        return None
    
    return working_url

def check_page_access(base_url):
    """检查页面访问"""
    print(f"\n=== 页面访问检查 ===")
    
    pages = [
        ("/market_scan", "市场扫描页面"),
        ("/test_scan", "测试页面"),
        ("/", "首页")
    ]
    
    for path, name in pages:
        try:
            response = requests.get(f"{base_url}{path}", timeout=10)
            if response.status_code == 200:
                print(f"✓ {name} 访问正常")
            else:
                print(f"✗ {name} 访问失败: {response.status_code}")
        except Exception as e:
            print(f"✗ {name} 访问出错: {str(e)}")

def check_api_endpoints(base_url):
    """检查API端点"""
    print(f"\n=== API端点检查 ===")
    
    # 检查指数股票API
    try:
        response = requests.get(f"{base_url}/api/index_stocks?index_code=000300", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stock_count = len(data.get('stock_list', []))
            print(f"✓ 指数股票API正常 (获取到 {stock_count} 只股票)")
        else:
            print(f"✗ 指数股票API失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 指数股票API出错: {str(e)}")
    
    # 检查扫描任务启动API
    test_data = {
        "stock_list": ["000001"],
        "min_score": 60,
        "market_type": "A"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/start_market_scan",
            json=test_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✓ 扫描任务启动API正常 (任务ID: {task_id})")
            
            # 检查状态查询API
            time.sleep(1)
            status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✓ 任务状态查询API正常 (状态: {status.get('status')})")
            else:
                print(f"✗ 任务状态查询API失败: {status_response.status_code}")
                
        else:
            print(f"✗ 扫描任务启动API失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
    except Exception as e:
        print(f"✗ 扫描任务启动API出错: {str(e)}")

def check_javascript_console():
    """检查JavaScript控制台"""
    print(f"\n=== JavaScript控制台检查 ===")
    print("请在浏览器中执行以下步骤:")
    print("1. 打开 http://localhost:8888/market_scan")
    print("2. 按F12打开开发者工具")
    print("3. 切换到Console(控制台)标签")
    print("4. 查看是否有红色错误信息")
    print("5. 尝试在控制台输入: typeof fetchIndexStocks")
    print("   应该返回 'function'")
    print("6. 尝试在控制台输入: typeof currentTaskId")
    print("   应该返回 'object' 或 'undefined'")

def check_file_integrity():
    """检查文件完整性"""
    print(f"\n=== 文件完整性检查 ===")
    
    files_to_check = [
        ("templates/market_scan.html", "市场扫描页面模板"),
        ("templates/layout.html", "布局模板"),
        ("web_server.py", "Web服务器"),
        ("stock_analyzer.py", "股票分析器")
    ]
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✓ {description} 存在 ({file_size} 字节)")
        else:
            print(f"✗ {description} 不存在: {file_path}")

def check_javascript_functions():
    """检查JavaScript函数定义"""
    print(f"\n=== JavaScript函数检查 ===")
    
    try:
        with open('templates/market_scan.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        functions = [
            'fetchIndexStocks',
            'fetchIndustryStocks',
            'scanMarket',
            'pollScanStatus',
            'cancelScan',
            'renderResults'
        ]
        
        for func in functions:
            if f'function {func}(' in content:
                print(f"✓ 函数 {func} 已定义")
            else:
                print(f"✗ 函数 {func} 未找到")
        
        # 检查关键变量
        if 'let currentTaskId = null' in content:
            print("✓ 全局变量 currentTaskId 已定义")
        else:
            print("✗ 全局变量 currentTaskId 未找到")
            
    except Exception as e:
        print(f"✗ 检查JavaScript函数时出错: {str(e)}")

def provide_solutions():
    """提供解决方案"""
    print(f"\n=== 常见问题解决方案 ===")
    
    solutions = [
        ("页面点击无响应", [
            "1. 检查浏览器控制台是否有JavaScript错误",
            "2. 尝试刷新页面(Ctrl+F5强制刷新)",
            "3. 清除浏览器缓存",
            "4. 尝试使用无痕模式打开页面"
        ]),
        ("扫描任务启动失败", [
            "1. 检查网络连接",
            "2. 确保选择了指数、行业或输入了自定义股票",
            "3. 检查服务器日志文件 flask_app.log",
            "4. 重启Flask服务器"
        ]),
        ("扫描进度卡住", [
            "1. 点击取消按钮停止当前任务",
            "2. 减少股票数量重新扫描",
            "3. 检查网络连接稳定性",
            "4. 等待一段时间后重试"
        ])
    ]
    
    for problem, steps in solutions:
        print(f"\n{problem}:")
        for step in steps:
            print(f"   {step}")

def main():
    """主函数"""
    print("市场扫描问题诊断工具")
    print("=" * 50)
    print(f"诊断时间: {datetime.now()}")
    
    # 检查服务器状态
    base_url = check_server_status()
    
    if base_url:
        # 检查页面访问
        check_page_access(base_url)
        
        # 检查API端点
        check_api_endpoints(base_url)
    
    # 检查文件完整性
    check_file_integrity()
    
    # 检查JavaScript函数
    check_javascript_functions()
    
    # 检查JavaScript控制台
    check_javascript_console()
    
    # 提供解决方案
    provide_solutions()
    
    print(f"\n=== 诊断完成 ===")
    print("如果问题仍然存在，请:")
    print("1. 将诊断结果截图保存")
    print("2. 查看浏览器控制台的错误信息")
    print("3. 检查 flask_app.log 日志文件")

if __name__ == "__main__":
    main()
