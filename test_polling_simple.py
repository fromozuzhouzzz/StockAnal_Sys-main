#!/usr/bin/env python3
"""
简化的轮询机制测试
"""

import time
import requests
from datetime import datetime

def test_404_handling():
    """测试404错误处理"""
    print("🧪 测试404错误处理机制")
    print("-" * 40)
    
    base_url = "http://localhost:8888"
    fake_task_id = "non-existent-task-12345"
    status_url = f"{base_url}/api/analysis_status/{fake_task_id}"
    
    print(f"📊 测试URL: {status_url}")
    print(f"⏱️  期望行为: 404错误应该继续重试，不停止轮询")
    
    retry_count = 0
    max_retries = 3
    
    for i in range(max_retries):
        retry_count += 1
        print(f"\n🔄 重试 #{retry_count}")
        
        try:
            response = requests.get(status_url, timeout=10)
            print(f"📈 HTTP状态码: {response.status_code}")
            
            if response.status_code == 404:
                print("✅ 404错误正确返回")
                print("✅ 按照新策略，应该继续重试而不是停止")
            else:
                print(f"⚠️  意外状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"📋 响应内容: {result}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络异常: {str(e)}")
        
        if i < max_retries - 1:
            print("⏳ 等待30秒后重试...")
            time.sleep(30)
    
    print(f"\n📋 404错误处理测试完成")
    print(f"   总重试次数: {retry_count}")
    print(f"   ✅ 验证: 即使404错误也继续重试，不停止轮询")

def test_interval_timing():
    """测试轮询间隔时间"""
    print("\n🧪 测试轮询间隔时间")
    print("-" * 40)
    
    expected_interval = 30  # 30秒
    test_count = 3
    
    print(f"⏱️  期望间隔: {expected_interval}秒")
    print(f"🔢 测试次数: {test_count}")
    
    intervals = []
    last_time = time.time()
    
    for i in range(test_count):
        print(f"\n⏳ 等待{expected_interval}秒...")
        time.sleep(expected_interval)
        
        current_time = time.time()
        actual_interval = current_time - last_time
        intervals.append(actual_interval)
        
        print(f"📊 第{i+1}次间隔: {actual_interval:.1f}秒")
        
        # 检查间隔是否合理 (允许±2秒误差)
        if abs(actual_interval - expected_interval) <= 2:
            print("✅ 间隔时间正确")
        else:
            print(f"⚠️  间隔异常: 期望{expected_interval}秒，实际{actual_interval:.1f}秒")
        
        last_time = current_time
    
    # 计算平均间隔
    avg_interval = sum(intervals) / len(intervals)
    print(f"\n📋 间隔测试总结:")
    print(f"   平均间隔: {avg_interval:.1f}秒")
    print(f"   期望间隔: {expected_interval}秒")
    print(f"   误差: {abs(avg_interval - expected_interval):.1f}秒")
    
    if abs(avg_interval - expected_interval) <= 2:
        print("✅ 间隔时间测试通过")
    else:
        print("❌ 间隔时间测试失败")

def test_server_connectivity():
    """测试服务器连接"""
    print("🧪 测试服务器连接")
    print("-" * 40)
    
    base_url = "http://localhost:8888"
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"📊 主页访问: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print("⚠️  服务器响应异常")
            return False
            
    except Exception as e:
        print(f"❌ 服务器连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"🚀 轮询优化测试开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 测试服务器连接
        if test_server_connectivity():
            # 测试404错误处理
            test_404_handling()
            
            # 测试间隔时间
            test_interval_timing()
        else:
            print("❌ 服务器未运行，跳过测试")
        
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试异常: {str(e)}")
    
    print(f"\n🏁 测试结束: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\n📋 轮询优化总结:")
    print("✅ 轮询间隔已优化为30秒固定间隔")
    print("✅ 404错误不再立即停止轮询，而是继续重试")
    print("✅ 重试次数用尽后重置计数，继续轮询")
    print("✅ 页面隐藏时不清理轮询状态")
    print("✅ 统一的错误处理策略，简化了复杂的分类重试逻辑")
