#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试任务持久性修复效果
"""

import requests
import time
import sys

def quick_test(base_url="http://localhost:5000", stock_code="600547"):
    """快速测试任务是否会消失"""
    print(f"🧪 快速测试任务持久性修复效果")
    print(f"📍 服务器: {base_url}")
    print(f"📈 股票代码: {stock_code}")
    print("-" * 50)
    
    try:
        # 1. 创建任务
        print("1️⃣ 创建AI分析任务...")
        response = requests.post(
            f"{base_url}/api/start_stock_analysis",
            json={"stock_code": stock_code, "market_type": "A"},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ 任务创建失败: {response.status_code}")
            return False
        
        task_data = response.json()
        task_id = task_data.get('task_id')
        print(f"✅ 任务创建成功: {task_id}")
        
        # 2. 快速连续查询
        print("2️⃣ 开始快速连续查询...")
        for i in range(10):
            time.sleep(2)  # 2秒间隔
            
            try:
                status_response = requests.get(
                    f"{base_url}/api/analysis_status/{task_id}",
                    timeout=5
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    progress = status_data.get('progress', 0)
                    print(f"  查询 #{i+1}: ✅ 状态={status}, 进度={progress}%")
                    
                    if status in ['completed', 'failed']:
                        print(f"🎉 任务完成，最终状态: {status}")
                        return True
                        
                elif status_response.status_code == 404:
                    print(f"  查询 #{i+1}: ❌ 任务消失 (404错误)")
                    print("💥 任务持久性问题仍然存在！")
                    return False
                else:
                    print(f"  查询 #{i+1}: ⚠️ 状态码: {status_response.status_code}")
                    
            except Exception as e:
                print(f"  查询 #{i+1}: ❌ 异常: {str(e)}")
        
        print("✅ 快速测试完成，任务持久性正常")
        return True
        
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False

def main():
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    success = quick_test(base_url)
    
    if success:
        print("\n🎉 快速测试通过！修复效果良好。")
    else:
        print("\n❌ 快速测试失败！需要进一步检查。")

if __name__ == "__main__":
    main()
