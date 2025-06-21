#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试页面功能
"""

import requests
import time

def test_basic_functionality():
    """测试基本功能"""
    base_url = "http://localhost:8888"
    
    print("=== 测试页面基本功能 ===")
    
    # 1. 测试页面访问
    try:
        response = requests.get(f"{base_url}/market_scan", timeout=5)
        if response.status_code == 200:
            print("✅ 页面访问正常")
            
            # 检查页面内容
            content = response.text
            if 'fetchIndexStocks' in content:
                print("✅ JavaScript函数已包含在页面中")
            else:
                print("❌ JavaScript函数未找到")
                
            if 'currentTaskId' in content:
                print("✅ 全局变量已定义")
            else:
                print("❌ 全局变量未找到")
                
        else:
            print(f"❌ 页面访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 页面访问出错: {str(e)}")
        return False
    
    # 2. 测试API端点
    print("\n=== 测试API端点 ===")
    
    # 测试指数股票API
    try:
        response = requests.get(f"{base_url}/api/index_stocks?index_code=000300", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stock_count = len(data.get('stock_list', []))
            print(f"✅ 指数股票API正常 (获取到 {stock_count} 只股票)")
        else:
            print(f"❌ 指数股票API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 指数股票API出错: {str(e)}")
    
    # 3. 测试扫描任务
    print("\n=== 测试扫描任务 ===")
    
    test_data = {
        "stock_list": ["000001", "000002"],
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
            print(f"✅ 扫描任务启动成功 (任务ID: {task_id})")
            
            # 等待一下然后检查状态
            time.sleep(2)
            status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✅ 任务状态查询成功 (状态: {status.get('status')})")
            else:
                print(f"❌ 任务状态查询失败: {status_response.status_code}")
                
        else:
            print(f"❌ 扫描任务启动失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 扫描任务测试出错: {str(e)}")
    
    return True

def main():
    """主函数"""
    print("页面功能测试")
    print("=" * 50)
    
    if test_basic_functionality():
        print("\n✅ 基本功能测试完成")
        print("\n请在浏览器中:")
        print("1. 打开 http://localhost:8888/market_scan")
        print("2. 按F12打开开发者工具")
        print("3. 查看Console标签是否有错误")
        print("4. 尝试选择一个指数，点击'开始扫描'")
        print("5. 观察是否显示加载状态")
    else:
        print("\n❌ 基本功能测试失败")

if __name__ == "__main__":
    main()
