#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场扫描任务状态管理修复验证脚本

测试修复后的任务管理系统是否能够：
1. 正确创建和跟踪任务
2. 防止任务被意外清理
3. 提供稳定的状态查询
4. 处理长时间运行的任务
"""

import requests
import time
import json
from datetime import datetime


def test_server_connection():
    """测试服务器连接"""
    print("=== 测试服务器连接 ===")
    try:
        response = requests.get("http://localhost:8888", timeout=5)
        if response.status_code == 200:
            print("✓ 服务器连接正常")
            return True
        else:
            print(f"✗ 服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 服务器连接失败: {str(e)}")
        return False


def test_task_creation():
    """测试任务创建"""
    print("\n=== 测试任务创建 ===")
    
    test_data = {
        "stock_list": ["000001", "000002", "000858", "600036", "600519"],
        "min_score": 60,
        "market_type": "A"
    }
    
    try:
        response = requests.post(
            "http://localhost:8888/api/start_market_scan",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✓ 任务创建成功，任务ID: {task_id}")
            return task_id
        else:
            print(f"✗ 任务创建失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 任务创建出错: {str(e)}")
        return None


def test_task_status_tracking(task_id, max_duration=300):
    """测试任务状态跟踪"""
    print(f"\n=== 测试任务状态跟踪 (最长{max_duration}秒) ===")
    
    start_time = time.time()
    poll_count = 0
    last_progress = -1
    status_history = []
    
    while time.time() - start_time < max_duration:
        poll_count += 1
        elapsed = int(time.time() - start_time)
        
        try:
            response = requests.get(f"http://localhost:8888/api/scan_status/{task_id}", timeout=10)
            
            if response.status_code == 200:
                status = response.json()
                current_progress = status.get('progress', 0)
                task_status = status.get('status', 'unknown')
                
                # 记录状态变化
                status_info = {
                    'time': elapsed,
                    'poll': poll_count,
                    'status': task_status,
                    'progress': current_progress,
                    'processed': status.get('processed', 0),
                    'found': status.get('found', 0)
                }
                status_history.append(status_info)
                
                # 只在进度变化时打印
                if current_progress != last_progress or poll_count % 10 == 1:
                    print(f"轮询 #{poll_count} ({elapsed}s): 状态={task_status}, "
                          f"进度={current_progress}%, 已处理={status.get('processed', 0)}, "
                          f"找到={status.get('found', 0)}")
                    last_progress = current_progress
                
                # 检查任务是否完成
                if task_status in ['completed', 'failed', 'cancelled']:
                    print(f"✓ 任务结束，最终状态: {task_status}")
                    if task_status == 'completed':
                        results = status.get('result', [])
                        print(f"✓ 扫描完成，找到 {len(results)} 只符合条件的股票")
                    elif task_status == 'failed':
                        print(f"✗ 任务失败: {status.get('error', '未知错误')}")
                    
                    return True, status_history
                    
            elif response.status_code == 404:
                print(f"✗ 任务在第 {poll_count} 次轮询时消失 (404错误)")
                print(f"✗ 任务运行了 {elapsed} 秒后丢失")
                return False, status_history
            else:
                print(f"✗ 状态查询失败: {response.status_code}")
                
        except Exception as e:
            print(f"✗ 轮询出错: {str(e)}")
            
        time.sleep(2)  # 2秒间隔轮询
    
    print(f"✗ 任务在 {max_duration} 秒内未完成")
    return False, status_history


def test_task_persistence():
    """测试任务持久性 - 创建多个任务并检查是否会互相干扰"""
    print("\n=== 测试任务持久性 ===")
    
    tasks = []
    
    # 创建3个小任务
    for i in range(3):
        test_data = {
            "stock_list": [f"00000{i+1}"],
            "min_score": 60,
            "market_type": "A"
        }
        
        try:
            response = requests.post(
                "http://localhost:8888/api/start_market_scan",
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                tasks.append(task_id)
                print(f"✓ 任务 {i+1} 创建成功: {task_id}")
            else:
                print(f"✗ 任务 {i+1} 创建失败")
                
        except Exception as e:
            print(f"✗ 任务 {i+1} 创建出错: {str(e)}")
    
    # 检查所有任务是否都存在
    time.sleep(5)  # 等待5秒
    
    existing_tasks = 0
    for i, task_id in enumerate(tasks):
        try:
            response = requests.get(f"http://localhost:8888/api/scan_status/{task_id}", timeout=5)
            if response.status_code == 200:
                existing_tasks += 1
                print(f"✓ 任务 {i+1} 仍然存在")
            else:
                print(f"✗ 任务 {i+1} 已消失")
        except Exception as e:
            print(f"✗ 任务 {i+1} 查询出错: {str(e)}")
    
    print(f"任务持久性测试结果: {existing_tasks}/{len(tasks)} 个任务保持存在")
    return existing_tasks == len(tasks)


def generate_report(status_history):
    """生成测试报告"""
    print("\n=== 测试报告 ===")
    
    if not status_history:
        print("无状态历史记录")
        return
    
    total_time = status_history[-1]['time']
    total_polls = len(status_history)
    
    print(f"总测试时间: {total_time} 秒")
    print(f"总轮询次数: {total_polls}")
    print(f"平均轮询间隔: {total_time/total_polls:.1f} 秒")
    
    # 分析进度变化
    progress_changes = 0
    for i in range(1, len(status_history)):
        if status_history[i]['progress'] != status_history[i-1]['progress']:
            progress_changes += 1
    
    print(f"进度更新次数: {progress_changes}")
    
    # 检查是否有状态倒退
    max_progress = 0
    progress_regression = False
    for record in status_history:
        if record['progress'] < max_progress:
            progress_regression = True
            break
        max_progress = max(max_progress, record['progress'])
    
    if progress_regression:
        print("⚠️  检测到进度倒退")
    else:
        print("✓ 进度单调递增")


def main():
    """主测试函数"""
    print("市场扫描任务状态管理修复验证")
    print("=" * 50)
    print(f"测试时间: {datetime.now()}")
    
    # 1. 测试服务器连接
    if not test_server_connection():
        print("服务器连接失败，退出测试")
        return
    
    # 2. 测试任务持久性
    persistence_ok = test_task_persistence()
    
    # 3. 测试主要功能
    task_id = test_task_creation()
    if not task_id:
        print("任务创建失败，退出测试")
        return
    
    # 4. 测试任务状态跟踪
    success, history = test_task_status_tracking(task_id)
    
    # 5. 生成报告
    generate_report(history)
    
    # 6. 总结
    print(f"\n=== 测试总结 ===")
    print(f"任务持久性: {'✓ 通过' if persistence_ok else '✗ 失败'}")
    print(f"任务完成性: {'✓ 通过' if success else '✗ 失败'}")
    
    if success and persistence_ok:
        print("🎉 所有测试通过！任务状态管理修复成功。")
    else:
        print("❌ 部分测试失败，需要进一步调试。")


if __name__ == "__main__":
    main()
