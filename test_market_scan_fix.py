#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场扫描功能修复测试脚本
"""

import requests
import json
import time
import sys

def test_market_scan():
    """测试市场扫描功能"""
    base_url = 'http://localhost:8888'
    
    # 测试数据 - 使用少量股票进行快速测试
    test_data = {
        'stock_list': ['000001', '000002', '600000'],  # 平安银行、万科A、浦发银行
        'min_score': 50,
        'market_type': 'A'
    }
    
    print("=" * 50)
    print("开始测试市场扫描功能修复")
    print("=" * 50)
    
    try:
        # 1. 测试服务器连接
        print("1. 测试服务器连接...")
        response = requests.get(f'{base_url}/market_scan', timeout=5)
        if response.status_code == 200:
            print("   ✓ 服务器连接正常")
        else:
            print(f"   ✗ 服务器连接失败: {response.status_code}")
            return False
            
        # 2. 启动扫描任务
        print("\n2. 启动扫描任务...")
        response = requests.post(
            f'{base_url}/api/start_market_scan',
            json=test_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"   ✗ 启动扫描任务失败: {response.status_code} - {response.text}")
            return False
            
        result = response.json()
        task_id = result.get('task_id')
        
        if not task_id:
            print("   ✗ 未获取到任务ID")
            return False
            
        print(f"   ✓ 扫描任务启动成功，任务ID: {task_id}")
        
        # 3. 轮询任务状态
        print("\n3. 轮询任务状态...")
        max_polls = 20  # 最多轮询20次
        poll_count = 0
        last_status = None
        
        while poll_count < max_polls:
            try:
                status_response = requests.get(
                    f'{base_url}/api/scan_status/{task_id}',
                    timeout=5
                )
                
                if status_response.status_code != 200:
                    print(f"   ✗ 状态查询失败: {status_response.status_code} - {status_response.text}")
                    return False
                    
                status = status_response.json()
                current_status = status.get('status')
                progress = status.get('progress', 0)
                processed = status.get('processed', 0)
                found = status.get('found', 0)
                
                # 只在状态变化时打印
                if current_status != last_status or poll_count % 3 == 0:
                    print(f"   轮询 {poll_count + 1}: 状态={current_status}, 进度={progress}%, 已处理={processed}, 找到={found}")
                    last_status = current_status
                
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
                    else:
                        print("   注意: 未找到符合条件的股票")
                    
                    return True
                    
                elif current_status == 'failed':
                    error = status.get('error', '未知错误')
                    print(f"   ✗ 扫描失败: {error}")
                    return False
                    
                elif current_status == 'cancelled':
                    print("   ✗ 扫描被取消")
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
    success = test_market_scan()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 市场扫描功能测试通过！")
        print("前端应该能够正常显示扫描结果了。")
    else:
        print("✗ 市场扫描功能测试失败！")
        print("请检查服务器日志以获取更多信息。")
    print("=" * 50)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
