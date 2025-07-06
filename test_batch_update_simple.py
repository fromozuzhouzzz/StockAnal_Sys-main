# -*- coding: utf-8 -*-
"""
简化的批量数据更新功能测试
"""

import requests
import time
import json
from datetime import datetime

def test_batch_update_api():
    """测试批量更新API"""
    base_url = "http://localhost:5000"
    
    # 测试股票列表
    test_stocks = ["000001.SZ", "600000.SH", "000002.SZ"]
    
    print("🚀 测试批量数据更新API")
    print(f"测试股票: {', '.join(test_stocks)}")
    print("=" * 50)
    
    try:
        # 启动批量更新
        print("启动批量更新...")
        response = requests.post(
            f"{base_url}/api/portfolio/batch_update",
            json={
                "stock_codes": test_stocks,
                "market_type": "A",
                "force_update": False
            },
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                print(f"✅ 任务启动成功，ID: {task_id}")
                
                # 监控进度
                for i in range(30):  # 最多等待30秒
                    time.sleep(1)
                    
                    try:
                        status_response = requests.get(
                            f"{base_url}/api/portfolio/update_status/{task_id}",
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            progress = status.get('progress_percentage', 0)
                            print(f"进度: {progress}%")
                            
                            if status.get('status') in ['completed', 'failed']:
                                print(f"任务完成，状态: {status.get('status')}")
                                print(f"成功: {status.get('completed_stocks', 0)}")
                                print(f"失败: {status.get('failed_stocks', 0)}")
                                break
                        else:
                            print(f"获取状态失败: {status_response.status_code}")
                            
                    except Exception as e:
                        print(f"查询状态异常: {e}")
                        break
                
                print("✅ 批量更新测试完成")
            else:
                print("❌ 未获取到任务ID")
        else:
            print(f"❌ 启动批量更新失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def test_server_status():
    """测试服务器状态"""
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"服务器状态: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"服务器连接失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 简化批量更新测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查服务器状态
    if test_server_status():
        print("✅ 服务器连接正常")
        test_batch_update_api()
    else:
        print("❌ 服务器连接失败，请先启动服务器")
