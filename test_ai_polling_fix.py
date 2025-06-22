#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI分析任务前端轮询问题修复效果
验证轮询逻辑是否能正确处理长时间任务和404错误
"""

import requests
import time
import threading
from datetime import datetime

def test_ai_analysis_polling():
    """测试AI分析任务的轮询逻辑"""
    base_url = "http://localhost:8888"
    
    print("🧪 测试AI分析任务轮询修复效果")
    print("=" * 60)
    
    # 测试股票代码
    test_stock = "600547"
    
    try:
        print(f"\n1. 启动AI分析任务 - 股票代码: {test_stock}")
        
        # 启动AI分析任务
        response = requests.post(
            f"{base_url}/api/start_stock_analysis",
            json={
                "stock_code": test_stock,
                "market_type": "A"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✓ 任务创建成功: {task_id}")
            
            # 如果任务已完成，直接返回
            if result.get('status') == 'completed':
                print("   ✓ 任务已完成，无需轮询")
                return True
            
            # 开始轮询测试
            print(f"\n2. 开始轮询测试 - 模拟前端轮询逻辑")
            return test_polling_logic(base_url, task_id)
            
        else:
            print(f"   ✗ 任务创建失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ 测试出错: {str(e)}")
        return False

def test_polling_logic(base_url, task_id):
    """测试轮询逻辑"""
    start_time = time.time()
    poll_count = 0
    error_404_count = 0
    error_network_count = 0
    max_poll_duration = 600  # 10分钟
    
    # 模拟前端的动态轮询间隔
    def get_polling_interval():
        elapsed = time.time() - start_time
        if elapsed < 30:
            return 2  # 0-30秒：每2秒
        elif elapsed < 120:
            return 5  # 30秒-2分钟：每5秒
        elif elapsed < 300:
            return 10  # 2-5分钟：每10秒
        else:
            return 15  # 5分钟以上：每15秒
    
    print(f"   开始轮询任务 {task_id}")
    
    while True:
        poll_count += 1
        elapsed = time.time() - start_time
        
        # 检查超时
        if elapsed > max_poll_duration:
            print(f"   ✗ 轮询超时 ({max_poll_duration}秒)")
            return False
        
        print(f"   轮询 #{poll_count} ({int(elapsed)}s): ", end="")
        
        try:
            response = requests.get(
                f"{base_url}/api/analysis_status/{task_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                status = response.json()
                task_status = status.get('status')
                progress = status.get('progress', 0)
                
                print(f"状态={task_status}, 进度={progress}%")
                
                # 重置错误计数
                error_404_count = 0
                error_network_count = 0
                
                if task_status == 'completed':
                    print(f"   ✓ 任务完成！总耗时: {int(elapsed)}秒, 轮询次数: {poll_count}")
                    return True
                elif task_status == 'failed':
                    print(f"   ✗ 任务失败: {status.get('error', '未知错误')}")
                    return False
                
            elif response.status_code == 404:
                error_404_count += 1
                print(f"404错误 (第{error_404_count}次)")
                
                if error_404_count <= 3:  # 最多重试3次
                    retry_delay = 3 + (error_404_count * 2)  # 3秒、5秒、7秒
                    print(f"   → 404错误重试，{retry_delay}秒后重试")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"   ✗ 404错误重试次数用尽，停止轮询")
                    return False
            else:
                print(f"其他错误: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            error_network_count += 1
            print(f"网络错误 (第{error_network_count}次): {str(e)}")
            
            if error_network_count <= 5:  # 最多重试5次
                retry_delay = min(2 * (2 ** (error_network_count - 1)), 30)  # 指数退避，最大30秒
                print(f"   → 网络错误重试，{retry_delay}秒后重试")
                time.sleep(retry_delay)
                continue
            else:
                print(f"   ✗ 网络错误重试次数用尽，停止轮询")
                return False
        
        # 使用动态轮询间隔
        interval = get_polling_interval()
        time.sleep(interval)

def test_concurrent_requests():
    """测试并发请求是否会导致任务丢失"""
    base_url = "http://localhost:8888"
    
    print(f"\n🧪 测试并发请求处理")
    print("=" * 60)
    
    test_stock = "000001"
    
    try:
        # 启动任务
        response = requests.post(
            f"{base_url}/api/start_stock_analysis",
            json={
                "stock_code": test_stock,
                "market_type": "A"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✓ 任务创建成功: {task_id}")
            
            # 立即发送多个并发查询请求
            print(f"   发送5个并发状态查询请求...")
            
            results = []
            
            def query_status():
                try:
                    resp = requests.get(f"{base_url}/api/analysis_status/{task_id}", timeout=10)
                    results.append((resp.status_code, resp.json() if resp.status_code == 200 else resp.text))
                except Exception as e:
                    results.append((0, str(e)))
            
            # 创建并启动线程
            threads = []
            for i in range(5):
                thread = threading.Thread(target=query_status)
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 分析结果
            success_count = sum(1 for status_code, _ in results if status_code == 200)
            print(f"   ✓ 并发查询结果: {success_count}/5 个请求成功")
            
            if success_count >= 4:  # 允许1个失败
                print(f"   ✓ 并发处理测试通过")
                return True
            else:
                print(f"   ✗ 并发处理测试失败，成功率过低")
                return False
                
        else:
            print(f"   ✗ 任务创建失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ✗ 并发测试出错: {str(e)}")
        return False

def main():
    """主测试函数"""
    print(f"🚀 前端轮询问题修复测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 测试结果
    test_results = []
    
    # 测试1: AI分析轮询逻辑
    print(f"\n📋 测试1: AI分析轮询逻辑")
    result1 = test_ai_analysis_polling()
    test_results.append(("AI分析轮询逻辑", result1))
    
    # 测试2: 并发请求处理
    print(f"\n📋 测试2: 并发请求处理")
    result2 = test_concurrent_requests()
    test_results.append(("并发请求处理", result2))
    
    # 输出测试总结
    print(f"\n" + "=" * 80)
    print(f"📊 测试总结")
    print("=" * 80)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{len(test_results)} 个测试通过")
    
    if passed == len(test_results):
        print("🎉 所有测试通过！前端轮询问题修复成功！")
    else:
        print("⚠️  部分测试失败，需要进一步调试")

if __name__ == "__main__":
    main()
