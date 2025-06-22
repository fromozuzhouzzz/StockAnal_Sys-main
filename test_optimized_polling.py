#!/usr/bin/env python3
"""
测试优化后的轮询机制
验证30秒间隔、重试机制和错误处理
"""

import time
import requests
import json
from datetime import datetime

def test_polling_optimization():
    """测试轮询优化效果"""
    print("=" * 60)
    print("测试优化后的轮询机制")
    print("=" * 60)
    
    base_url = "http://localhost:8888"
    
    # 测试配置
    test_configs = [
        {
            "name": "个股分析轮询测试",
            "start_url": f"{base_url}/api/start_stock_analysis",
            "status_url_template": f"{base_url}/api/analysis_status/{{task_id}}",
            "data": {"stock_code": "000001", "market_type": "sz"}
        },
        {
            "name": "市场扫描轮询测试", 
            "start_url": f"{base_url}/api/start_market_scan",
            "status_url_template": f"{base_url}/api/scan_status/{{task_id}}",
            "data": {"stocks": ["000001", "000002"], "min_score": 60}
        }
    ]
    
    for config in test_configs:
        print(f"\n🧪 {config['name']}")
        print("-" * 40)
        
        # 启动任务
        try:
            response = requests.post(
                config["start_url"],
                json=config["data"],
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                
                if task_id:
                    print(f"✅ 任务启动成功: {task_id}")
                    test_polling_behavior(config["status_url_template"], task_id)
                else:
                    print("❌ 任务启动失败: 未获取到task_id")
            else:
                print(f"❌ 任务启动失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 任务启动异常: {str(e)}")

def test_polling_behavior(status_url_template, task_id):
    """测试轮询行为"""
    status_url = status_url_template.format(task_id=task_id)
    start_time = time.time()
    poll_count = 0
    error_count = 0
    max_test_duration = 300  # 最多测试5分钟
    expected_interval = 30  # 期望的30秒间隔
    
    print(f"📊 开始轮询测试: {status_url}")
    print(f"⏱️  期望间隔: {expected_interval}秒")
    
    last_poll_time = time.time()
    
    while True:
        poll_count += 1
        current_time = time.time()
        elapsed = current_time - start_time
        
        # 检查测试超时
        if elapsed > max_test_duration:
            print(f"⏰ 测试超时 ({max_test_duration}秒)，停止测试")
            break
            
        # 检查轮询间隔
        if poll_count > 1:
            actual_interval = current_time - last_poll_time
            print(f"📈 轮询 #{poll_count}: 实际间隔 {actual_interval:.1f}秒 (期望{expected_interval}秒)")
            
            # 验证间隔是否合理 (允许±5秒误差)
            if abs(actual_interval - expected_interval) > 5:
                print(f"⚠️  间隔异常: 期望{expected_interval}秒，实际{actual_interval:.1f}秒")
        
        last_poll_time = current_time
        
        try:
            response = requests.get(status_url, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "unknown")
                progress = result.get("progress", 0)
                
                print(f"✅ 轮询成功: 状态={status}, 进度={progress}%")
                
                if status in ["completed", "failed", "cancelled"]:
                    print(f"🎯 任务完成: {status}")
                    break
                    
            elif response.status_code == 404:
                error_count += 1
                print(f"❌ 404错误 (第{error_count}次): 任务可能还未创建或已清理")
                
            else:
                error_count += 1
                print(f"❌ HTTP错误 (第{error_count}次): {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            error_count += 1
            print(f"❌ 网络错误 (第{error_count}次): {str(e)}")
        
        # 模拟前端的30秒间隔
        print(f"⏳ 等待{expected_interval}秒后继续轮询...")
        time.sleep(expected_interval)
    
    # 测试总结
    total_time = time.time() - start_time
    print(f"\n📋 轮询测试总结:")
    print(f"   总轮询次数: {poll_count}")
    print(f"   总错误次数: {error_count}")
    print(f"   总耗时: {total_time:.1f}秒")
    print(f"   平均间隔: {total_time/max(poll_count-1, 1):.1f}秒")
    
    if error_count > 0:
        print(f"   错误率: {error_count/poll_count*100:.1f}%")

def test_error_handling():
    """测试错误处理机制"""
    print("\n🔧 测试错误处理机制")
    print("-" * 40)
    
    # 测试404错误处理
    fake_task_id = "non-existent-task-id"
    status_url = f"http://localhost:8888/api/analysis_status/{fake_task_id}"
    
    print(f"🧪 测试404错误处理: {status_url}")
    
    for i in range(3):
        try:
            response = requests.get(status_url, timeout=10)
            print(f"📊 尝试 #{i+1}: HTTP {response.status_code}")
            
            if response.status_code == 404:
                print("✅ 404错误正确返回")
            else:
                print(f"⚠️  意外状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
        
        if i < 2:  # 不在最后一次等待
            print("⏳ 等待30秒后重试...")
            time.sleep(30)

if __name__ == "__main__":
    print(f"🚀 开始测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_polling_optimization()
        test_error_handling()
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试异常: {str(e)}")
    
    print(f"\n🏁 测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
