#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务清理修复
"""

import requests
import time
import json
import sys

def test_scan_completion():
    """测试扫描任务完整流程"""
    base_url = 'http://localhost:8888'
    
    print("=" * 60)
    print("测试市场扫描任务清理修复")
    print("=" * 60)
    
    try:
        # 1. 获取保险行业股票
        print("1. 获取保险行业股票...")
        response = requests.get(f'{base_url}/api/industry_stocks?industry=保险', timeout=10)
        if response.status_code != 200:
            print(f"   ✗ 获取行业股票失败: {response.status_code}")
            return False
            
        data = response.json()
        stock_list = data.get('stock_list', [])
        print(f"   ✓ 获取到 {len(stock_list)} 只保险股票")
        
        if len(stock_list) == 0:
            print("   ✗ 股票列表为空")
            return False
            
        # 2. 启动扫描任务
        print("\n2. 启动扫描任务...")
        scan_data = {
            'stock_list': stock_list,
            'min_score': 50,
            'market_type': 'A'
        }
        
        response = requests.post(f'{base_url}/api/start_market_scan', json=scan_data, timeout=10)
        if response.status_code != 200:
            print(f"   ✗ 启动扫描失败: {response.status_code} - {response.text}")
            return False
            
        result = response.json()
        task_id = result.get('task_id')
        print(f"   ✓ 扫描任务启动成功，任务ID: {task_id}")
        
        # 3. 持续轮询任务状态
        print("\n3. 轮询任务状态...")
        max_polls = 60  # 最多轮询60次（约2分钟）
        poll_count = 0
        last_status = None
        last_progress = -1
        
        while poll_count < max_polls:
            try:
                status_response = requests.get(f'{base_url}/api/scan_status/{task_id}', timeout=5)
                
                if status_response.status_code == 404:
                    print(f"   ✗ 任务被意外删除！轮询次数: {poll_count}")
                    print(f"   ✗ 响应: {status_response.text}")
                    return False
                    
                if status_response.status_code != 200:
                    print(f"   ✗ 状态查询失败: {status_response.status_code} - {status_response.text}")
                    return False
                    
                status = status_response.json()
                current_status = status.get('status')
                progress = status.get('progress', 0)
                processed = status.get('processed', 0)
                found = status.get('found', 0)
                
                # 只在状态或进度变化时打印
                if current_status != last_status or progress != last_progress:
                    print(f"   轮询 {poll_count + 1}: 状态={current_status}, 进度={progress}%, 已处理={processed}, 找到={found}")
                    last_status = current_status
                    last_progress = progress
                
                # 检查任务完成状态
                if current_status == 'completed':
                    results = status.get('result', [])
                    print(f"\n   ✓ 扫描完成！找到 {len(results)} 只符合条件的股票")
                    
                    if results:
                        print("   前3个结果:")
                        for i, result in enumerate(results[:3]):
                            stock_code = result.get('stock_code', '未知')
                            stock_name = result.get('stock_name', '未知')
                            score = result.get('score', 0)
                            print(f"     {i+1}. {stock_code} {stock_name} 得分:{score}")
                    
                    # 4. 验证任务仍然存在
                    print("\n4. 验证任务完成后仍然存在...")
                    time.sleep(2)
                    final_check = requests.get(f'{base_url}/api/scan_status/{task_id}', timeout=5)
                    if final_check.status_code == 200:
                        print("   ✓ 任务完成后仍然存在，清理机制正常")
                        return True
                    else:
                        print(f"   ✗ 任务完成后立即被删除: {final_check.status_code}")
                        return False
                    
                elif current_status == 'failed':
                    error = status.get('error', '未知错误')
                    print(f"   ✗ 扫描失败: {error}")
                    return False
                    
            except Exception as e:
                print(f"   ✗ 轮询出错: {str(e)}")
                return False
                
            poll_count += 1
            time.sleep(2)  # 等待2秒后继续轮询
            
        print(f"   ✗ 轮询超时 (超过 {max_polls} 次)")
        return False
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        return False

def main():
    """主函数"""
    success = test_scan_completion()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ 任务清理修复测试通过！")
        print("任务在执行过程中不会被意外删除。")
    else:
        print("✗ 任务清理修复测试失败！")
        print("任务可能仍然会被意外删除。")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
