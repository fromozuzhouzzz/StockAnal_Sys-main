#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场扫描改进测试脚本
测试超时控制、错误处理和取消机制
"""

import sys
import time
import requests
import json
from datetime import datetime

def test_market_scan_improvements():
    """测试市场扫描改进功能"""
    base_url = "http://localhost:8888"
    
    print("=== 市场扫描改进功能测试 ===")
    print(f"测试时间: {datetime.now()}")
    print()
    
    # 测试数据 - 使用少量股票进行快速测试
    test_stocks = ["000001", "000002", "600000", "600036", "000858"]
    
    print(f"1. 测试启动扫描任务...")
    print(f"   测试股票: {test_stocks}")
    
    # 启动扫描任务
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
            print(f"   ✓ 任务启动成功，任务ID: {task_id}")
            
            # 测试状态轮询
            print(f"\n2. 测试状态轮询...")
            test_polling(base_url, task_id)
            
            # 测试取消功能
            print(f"\n3. 测试任务取消...")
            test_cancel_task(base_url, task_id)
            
        else:
            print(f"   ✗ 任务启动失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ✗ 请求失败: {str(e)}")

def test_polling(base_url, task_id):
    """测试状态轮询"""
    max_polls = 10
    poll_count = 0
    
    while poll_count < max_polls:
        try:
            response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            
            if response.status_code == 200:
                status = response.json()
                print(f"   轮询 {poll_count + 1}: 状态={status.get('status')}, "
                      f"进度={status.get('progress', 0)}%, "
                      f"已处理={status.get('processed', 0)}, "
                      f"找到={status.get('found', 0)}")
                
                # 检查任务是否完成
                if status.get('status') in ['completed', 'failed', 'cancelled']:
                    print(f"   ✓ 任务结束，最终状态: {status.get('status')}")
                    if status.get('status') == 'completed':
                        results = status.get('result', [])
                        print(f"   ✓ 找到 {len(results)} 只符合条件的股票")
                    break
                    
            else:
                print(f"   ✗ 状态查询失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ✗ 轮询出错: {str(e)}")
            
        poll_count += 1
        time.sleep(2)
    
    if poll_count >= max_polls:
        print(f"   ⚠ 轮询超时，任务可能仍在运行")

def test_cancel_task(base_url, task_id):
    """测试任务取消"""
    try:
        response = requests.post(f"{base_url}/api/cancel_scan/{task_id}", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ 取消请求成功: {result.get('message')}")
            
            # 验证任务状态
            time.sleep(1)
            status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   ✓ 任务状态已更新: {status.get('status')}")
            
        else:
            print(f"   ✗ 取消失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ✗ 取消请求出错: {str(e)}")

def test_timeout_handling():
    """测试超时处理"""
    print(f"\n4. 测试超时处理...")
    
    # 这里可以添加特定的超时测试
    # 比如使用大量股票列表或模拟网络延迟
    print(f"   ℹ 超时处理已集成到主要功能中")

def test_error_recovery():
    """测试错误恢复"""
    print(f"\n5. 测试错误恢复...")
    
    # 测试无效股票代码
    base_url = "http://localhost:8888"
    invalid_stocks = ["INVALID001", "INVALID002"]
    
    scan_data = {
        "stock_list": invalid_stocks,
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
            print(f"   ✓ 无效股票测试任务启动: {task_id}")
            
            # 等待一段时间查看结果
            time.sleep(5)
            status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   ✓ 错误处理结果: 状态={status.get('status')}, "
                      f"失败={status.get('failed', 0)}")
        
    except Exception as e:
        print(f"   ✗ 错误恢复测试失败: {str(e)}")

if __name__ == "__main__":
    print("请确保Flask服务器正在运行在 http://localhost:8888")
    print("按Enter键开始测试，或Ctrl+C退出...")
    
    try:
        input()
        test_market_scan_improvements()
        test_error_recovery()
        print(f"\n=== 测试完成 ===")
        
    except KeyboardInterrupt:
        print(f"\n测试被用户中断")
    except Exception as e:
        print(f"\n测试出错: {str(e)}")
