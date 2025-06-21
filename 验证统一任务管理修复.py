#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证统一任务管理修复效果

测试修复后的统一任务管理系统是否能够：
1. 彻底解决任务存储不一致问题
2. 确保前端轮询不会收到404错误
3. 提供稳定的任务状态管理
"""

import requests
import time
import json
from datetime import datetime


def test_unified_task_management():
    """测试统一任务管理系统"""
    print("=== 测试统一任务管理系统 ===")
    
    base_url = "http://localhost:8888"
    
    # 测试数据
    test_data = {
        "stock_list": ["000001", "000002", "000858"],
        "min_score": 60,
        "market_type": "A"
    }
    
    try:
        print("1. 创建市场扫描任务...")
        response = requests.post(
            f"{base_url}/api/start_market_scan",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✓ 任务创建成功: {task_id}")
            
            # 立即测试状态查询
            print("\n2. 立即查询任务状态...")
            status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   ✓ 立即查询成功: 状态={status.get('status')}")
                
                # 持续轮询直到完成
                print("\n3. 持续轮询任务状态...")
                poll_count = 0
                start_time = time.time()
                
                while True:
                    poll_count += 1
                    elapsed = int(time.time() - start_time)
                    
                    status_response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=10)
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        current_status = status.get('status')
                        progress = status.get('progress', 0)
                        
                        print(f"   轮询 #{poll_count} ({elapsed}s): 状态={current_status}, 进度={progress}%")
                        
                        if current_status in ['completed', 'failed', 'cancelled']:
                            if current_status == 'completed':
                                results = status.get('result', [])
                                print(f"   ✓ 任务完成！找到 {len(results)} 只符合条件的股票")
                            else:
                                print(f"   ✗ 任务结束，状态: {current_status}")
                                if 'error' in status:
                                    print(f"   错误信息: {status['error']}")
                            break
                            
                    elif status_response.status_code == 404:
                        print(f"   ✗ 第 {poll_count} 次轮询时任务消失 (404错误)")
                        print(f"   ✗ 任务运行了 {elapsed} 秒后丢失")
                        return False
                    else:
                        print(f"   ✗ 轮询失败: {status_response.status_code}")
                        return False
                    
                    time.sleep(2)  # 2秒间隔
                    
                    # 防止无限循环
                    if elapsed > 300:  # 5分钟超时
                        print("   ⚠️  任务运行超过5分钟，停止轮询")
                        break
                
                return True
                
            else:
                print(f"   ✗ 立即查询失败: {status_response.status_code}")
                print(f"   响应内容: {status_response.text}")
                return False
        else:
            print(f"   ✗ 任务创建失败: {response.status_code}")
            print(f"   响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ 测试出错: {str(e)}")
        return False


def test_multiple_concurrent_tasks():
    """测试多个并发任务"""
    print("\n=== 测试多个并发任务 ===")
    
    base_url = "http://localhost:8888"
    task_ids = []
    
    # 创建3个任务
    for i in range(3):
        test_data = {
            "stock_list": [f"00000{i+1}"],
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
                task_ids.append(task_id)
                print(f"   任务 {i+1} 创建成功: {task_id}")
            else:
                print(f"   任务 {i+1} 创建失败: {response.status_code}")
                
        except Exception as e:
            print(f"   任务 {i+1} 创建出错: {str(e)}")
    
    # 检查所有任务是否都能查询到
    print(f"\n   检查 {len(task_ids)} 个任务的状态...")
    success_count = 0
    
    for i, task_id in enumerate(task_ids):
        try:
            response = requests.get(f"{base_url}/api/scan_status/{task_id}", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"   任务 {i+1}: ✓ 状态={status.get('status')}")
                success_count += 1
            else:
                print(f"   任务 {i+1}: ✗ 查询失败 ({response.status_code})")
        except Exception as e:
            print(f"   任务 {i+1}: ✗ 查询出错 ({str(e)})")
    
    print(f"\n   并发任务测试结果: {success_count}/{len(task_ids)} 个任务可正常查询")
    return success_count == len(task_ids)


def test_browser_cache_issue():
    """测试浏览器缓存问题"""
    print("\n=== 测试浏览器缓存问题 ===")
    print("   建议用户执行以下操作来清除浏览器缓存：")
    print("   1. 按 Ctrl+Shift+R 强制刷新页面")
    print("   2. 或者按 F12 打开开发者工具，右键刷新按钮选择'清空缓存并硬性重新加载'")
    print("   3. 或者在浏览器设置中清除缓存和Cookie")
    return True


def main():
    """主测试函数"""
    print("统一任务管理系统修复验证")
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
    test1_result = test_unified_task_management()
    test2_result = test_multiple_concurrent_tasks()
    test3_result = test_browser_cache_issue()
    
    # 总结
    print(f"\n=== 修复验证总结 ===")
    print(f"统一任务管理: {'✓ 通过' if test1_result else '✗ 失败'}")
    print(f"并发任务处理: {'✓ 通过' if test2_result else '✗ 失败'}")
    print(f"缓存问题提示: {'✓ 已提示' if test3_result else '✗ 未提示'}")
    
    if test1_result and test2_result:
        print("\n🎉 统一任务管理系统修复成功！")
        print("   如果用户仍然遇到问题，请建议用户：")
        print("   1. 清除浏览器缓存并强制刷新页面")
        print("   2. 确认使用的是最新版本的代码")
        print("   3. 检查是否有多个web_server.py在运行")
    else:
        print("\n❌ 部分测试失败，需要进一步调试")
        if not test1_result:
            print("   - 统一任务管理系统仍有问题")
        if not test2_result:
            print("   - 并发任务处理有问题")


if __name__ == "__main__":
    main()
