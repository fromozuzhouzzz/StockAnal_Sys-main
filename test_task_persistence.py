#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务持久性测试脚本
用于验证AI分析任务不会意外消失的问题修复效果
"""

import requests
import time
import json
import sys
from datetime import datetime

class TaskPersistenceTest:
    """任务持久性测试类"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
    
    def log(self, message):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.test_results.append(log_message)
    
    def test_task_creation_and_persistence(self, stock_code="600547"):
        """测试任务创建和持久性"""
        self.log(f"开始测试股票 {stock_code} 的任务持久性")
        
        try:
            # 1. 创建分析任务
            self.log("步骤1: 创建AI分析任务")
            create_response = requests.post(
                f"{self.base_url}/api/start_stock_analysis",
                json={"stock_code": stock_code, "market_type": "A"},
                timeout=10
            )
            
            if create_response.status_code != 200:
                self.log(f"❌ 任务创建失败: {create_response.status_code} - {create_response.text}")
                return False
            
            task_data = create_response.json()
            task_id = task_data.get('task_id')
            
            if not task_id:
                self.log("❌ 任务创建响应中没有task_id")
                return False
            
            self.log(f"✅ 任务创建成功，task_id: {task_id}")
            
            # 2. 立即查询任务状态
            self.log("步骤2: 立即查询任务状态")
            immediate_response = requests.get(
                f"{self.base_url}/api/analysis_status/{task_id}",
                timeout=5
            )
            
            if immediate_response.status_code != 200:
                self.log(f"❌ 立即查询失败: {immediate_response.status_code}")
                return False
            
            immediate_status = immediate_response.json()
            self.log(f"✅ 立即查询成功，状态: {immediate_status.get('status')}")
            
            # 3. 连续轮询测试
            self.log("步骤3: 开始连续轮询测试（模拟前端行为）")
            poll_count = 0
            max_polls = 30  # 最多轮询30次
            poll_interval = 2  # 每2秒轮询一次
            
            consecutive_failures = 0
            max_consecutive_failures = 3
            
            while poll_count < max_polls:
                poll_count += 1
                time.sleep(poll_interval)
                
                try:
                    poll_response = requests.get(
                        f"{self.base_url}/api/analysis_status/{task_id}",
                        timeout=5
                    )
                    
                    if poll_response.status_code == 200:
                        status_data = poll_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        
                        self.log(f"轮询 #{poll_count}: ✅ 状态={status}, 进度={progress}%")
                        consecutive_failures = 0
                        
                        # 如果任务完成，结束测试
                        if status in ['completed', 'failed']:
                            self.log(f"✅ 任务结束，最终状态: {status}")
                            return True
                            
                    elif poll_response.status_code == 404:
                        consecutive_failures += 1
                        self.log(f"轮询 #{poll_count}: ❌ 任务消失 (404错误) - 连续失败次数: {consecutive_failures}")
                        
                        if consecutive_failures >= max_consecutive_failures:
                            self.log(f"❌ 连续{max_consecutive_failures}次404错误，任务确实消失了")
                            return False
                    else:
                        self.log(f"轮询 #{poll_count}: ⚠️ 意外状态码: {poll_response.status_code}")
                        
                except requests.RequestException as e:
                    self.log(f"轮询 #{poll_count}: ❌ 网络错误: {str(e)}")
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_consecutive_failures:
                        self.log(f"❌ 连续{max_consecutive_failures}次网络错误")
                        return False
            
            self.log(f"⚠️ 轮询达到最大次数({max_polls})，测试结束")
            return True
            
        except Exception as e:
            self.log(f"❌ 测试过程中发生异常: {str(e)}")
            return False
    
    def test_multiple_tasks(self, stock_codes=["600547", "000001", "000002"]):
        """测试多个任务的并发持久性"""
        self.log("开始多任务并发持久性测试")
        
        task_ids = []
        
        # 创建多个任务
        for stock_code in stock_codes:
            try:
                response = requests.post(
                    f"{self.base_url}/api/start_stock_analysis",
                    json={"stock_code": stock_code, "market_type": "A"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    task_data = response.json()
                    task_id = task_data.get('task_id')
                    if task_id:
                        task_ids.append((stock_code, task_id))
                        self.log(f"✅ 创建任务成功: {stock_code} -> {task_id}")
                    else:
                        self.log(f"❌ 创建任务失败: {stock_code} - 无task_id")
                else:
                    self.log(f"❌ 创建任务失败: {stock_code} - {response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ 创建任务异常: {stock_code} - {str(e)}")
        
        if not task_ids:
            self.log("❌ 没有成功创建任何任务")
            return False
        
        # 并发查询所有任务
        self.log(f"开始并发查询 {len(task_ids)} 个任务")
        
        for round_num in range(10):  # 查询10轮
            time.sleep(3)
            self.log(f"--- 第 {round_num + 1} 轮查询 ---")
            
            for stock_code, task_id in task_ids:
                try:
                    response = requests.get(
                        f"{self.base_url}/api/analysis_status/{task_id}",
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        status_data = response.json()
                        status = status_data.get('status')
                        self.log(f"  {stock_code}({task_id[:8]}): ✅ {status}")
                    else:
                        self.log(f"  {stock_code}({task_id[:8]}): ❌ {response.status_code}")
                        
                except Exception as e:
                    self.log(f"  {stock_code}({task_id[:8]}): ❌ 异常: {str(e)}")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 60)
        self.log("开始任务持久性测试套件")
        self.log("=" * 60)
        
        # 测试1: 单任务持久性
        test1_result = self.test_task_creation_and_persistence()
        
        # 等待一段时间
        time.sleep(5)
        
        # 测试2: 多任务并发持久性
        test2_result = self.test_multiple_tasks()
        
        # 输出测试结果
        self.log("=" * 60)
        self.log("测试结果汇总:")
        self.log(f"单任务持久性测试: {'✅ 通过' if test1_result else '❌ 失败'}")
        self.log(f"多任务并发测试: {'✅ 通过' if test2_result else '❌ 失败'}")
        self.log("=" * 60)
        
        return test1_result and test2_result

def main():
    """主函数"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    print(f"使用服务器地址: {base_url}")
    
    tester = TaskPersistenceTest(base_url)
    success = tester.run_all_tests()
    
    # 保存测试结果到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"task_persistence_test_{timestamp}.log"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        for result in tester.test_results:
            f.write(result + '\n')
    
    print(f"\n测试日志已保存到: {log_file}")
    
    if success:
        print("🎉 所有测试通过！任务持久性问题已修复。")
        sys.exit(0)
    else:
        print("❌ 测试失败！任务持久性问题仍然存在。")
        sys.exit(1)

if __name__ == "__main__":
    main()
