#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断任务存储竞态条件脚本

专门测试任务创建和查询之间的时序问题，
分析为什么前端第一次轮询就收到404错误。
"""

import requests
import time
import json
import threading
from datetime import datetime


def test_task_creation_timing():
    """测试任务创建和查询的时序问题"""
    print("=== 测试任务创建和查询时序 ===")
    
    base_url = "http://localhost:8888"
    
    # 准备测试数据
    test_data = {
        "stock_list": ["000001", "000002"],  # 只用2只股票快速测试
        "min_score": 60,
        "market_type": "A"
    }
    
    try:
        print("1. 发送任务创建请求...")
        start_time = time.time()
        
        response = requests.post(
            f"{base_url}/api/start_market_scan",
            json=test_data,
            timeout=10
        )
        
        creation_time = time.time() - start_time
        print(f"   任务创建耗时: {creation_time:.3f}秒")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✓ 任务创建成功，任务ID: {task_id}")
            
            # 立即查询任务状态（模拟前端行为）
            print("\n2. 立即查询任务状态...")
            immediate_query_time = time.time()
            
            status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            query_time = time.time() - immediate_query_time
            print(f"   立即查询耗时: {query_time:.3f}秒")
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   ✓ 立即查询成功: 状态={status.get('status')}")
            else:
                print(f"   ✗ 立即查询失败: {status_response.status_code}")
                print(f"   响应内容: {status_response.text}")
                return False
            
            # 连续快速查询，模拟前端轮询
            print("\n3. 连续快速查询（模拟前端轮询）...")
            for i in range(5):
                query_start = time.time()
                status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
                query_duration = time.time() - query_start
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   查询 #{i+1}: ✓ 成功 ({query_duration:.3f}s) - 状态={status.get('status')}")
                else:
                    print(f"   查询 #{i+1}: ✗ 失败 ({query_duration:.3f}s) - {status_response.status_code}")
                    print(f"   错误响应: {status_response.text}")
                    return False
                
                time.sleep(0.5)  # 500ms间隔
            
            return True
            
        else:
            print(f"   ✗ 任务创建失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ 测试出错: {str(e)}")
        return False


def test_concurrent_task_creation():
    """测试并发任务创建"""
    print("\n=== 测试并发任务创建 ===")
    
    base_url = "http://localhost:8888"
    results = []
    
    def create_task(task_num):
        """创建单个任务"""
        test_data = {
            "stock_list": [f"00000{task_num}"],
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
                
                # 立即查询状态
                status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
                
                results.append({
                    'task_num': task_num,
                    'task_id': task_id,
                    'creation_success': True,
                    'query_success': status_response.status_code == 200,
                    'query_status_code': status_response.status_code
                })
                
                print(f"   任务 {task_num}: 创建✓ 查询{'✓' if status_response.status_code == 200 else '✗'}")
            else:
                results.append({
                    'task_num': task_num,
                    'creation_success': False,
                    'creation_status_code': response.status_code
                })
                print(f"   任务 {task_num}: 创建✗ ({response.status_code})")
                
        except Exception as e:
            results.append({
                'task_num': task_num,
                'creation_success': False,
                'error': str(e)
            })
            print(f"   任务 {task_num}: 异常 - {str(e)}")
    
    # 并发创建5个任务
    threads = []
    for i in range(5):
        thread = threading.Thread(target=create_task, args=(i+1,))
        threads.append(thread)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 分析结果
    successful_creations = sum(1 for r in results if r.get('creation_success', False))
    successful_queries = sum(1 for r in results if r.get('query_success', False))
    
    print(f"\n   并发测试结果:")
    print(f"   成功创建: {successful_creations}/5")
    print(f"   成功查询: {successful_queries}/5")
    
    return successful_creations == 5 and successful_queries == 5


def test_server_task_storage():
    """测试服务器任务存储状态"""
    print("\n=== 测试服务器任务存储状态 ===")
    
    base_url = "http://localhost:8888"
    
    # 创建一个任务
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
            print(f"   创建任务: {task_id}")
            
            # 等待不同时间间隔后查询
            intervals = [0, 0.1, 0.5, 1.0, 2.0, 5.0]
            
            for interval in intervals:
                time.sleep(interval)
                
                status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   {interval}s后查询: ✓ 状态={status.get('status')}")
                else:
                    print(f"   {interval}s后查询: ✗ {status_response.status_code}")
                    print(f"   错误响应: {status_response.text}")
                    break
            
            return True
        else:
            print(f"   任务创建失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   测试出错: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("任务存储竞态条件诊断")
    print("=" * 50)
    print(f"测试时间: {datetime.now()}")
    
    # 检查服务器连接
    try:
        response = requests.get("http://localhost:8888", timeout=5)
        if response.status_code != 200:
            print("服务器连接异常，退出测试")
            return
    except:
        print("服务器未启动，退出测试")
        return
    
    print("✓ 服务器连接正常\n")
    
    # 执行测试
    test1_result = test_task_creation_timing()
    test2_result = test_concurrent_task_creation()
    test3_result = test_server_task_storage()
    
    # 总结
    print(f"\n=== 诊断总结 ===")
    print(f"时序测试: {'✓ 通过' if test1_result else '✗ 失败'}")
    print(f"并发测试: {'✓ 通过' if test2_result else '✗ 失败'}")
    print(f"存储测试: {'✓ 通过' if test3_result else '✗ 失败'}")
    
    if not test1_result:
        print("\n⚠️  检测到时序问题！任务创建后立即查询失败。")
        print("   可能原因：")
        print("   1. 任务创建和存储之间存在竞态条件")
        print("   2. 线程安全问题")
        print("   3. 任务存储延迟")
    
    if not test2_result:
        print("\n⚠️  检测到并发问题！多个任务同时创建时出现问题。")
        print("   可能原因：")
        print("   1. 线程锁机制不完善")
        print("   2. 任务ID冲突")
        print("   3. 存储系统并发访问问题")
    
    if test1_result and test2_result and test3_result:
        print("\n🎉 所有测试通过！任务存储机制正常。")
        print("   问题可能在其他地方，建议检查：")
        print("   1. 任务清理机制的触发条件")
        print("   2. 前端轮询的URL路径")
        print("   3. 服务器日志中的详细错误信息")


if __name__ == "__main__":
    main()
