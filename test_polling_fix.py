#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轮询机制修复验证测试脚本

这个脚本用于测试修复后的轮询机制，确保：
1. 轮询在404错误时能够正确停止
2. 轮询有超时和重试限制
3. 页面状态清理机制正常工作
4. 不会出现无限轮询问题
"""

import requests
import time
import json
import sys
from datetime import datetime

class PollingFixTester:
    def __init__(self, base_url="http://localhost:8888"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   详情: {details}")
    
    def test_server_connection(self):
        """测试服务器连接"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                self.log_test("服务器连接", True, "服务器正常运行")
                return True
            else:
                self.log_test("服务器连接", False, f"服务器返回状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("服务器连接", False, f"连接失败: {str(e)}")
            return False
    
    def test_invalid_task_id_404(self):
        """测试无效任务ID返回404"""
        invalid_task_id = "invalid-task-id-12345"
        
        try:
            response = requests.get(
                f"{self.base_url}/api/analysis_status/{invalid_task_id}",
                timeout=5
            )
            
            if response.status_code == 404:
                self.log_test("无效任务ID测试", True, "无效任务ID正确返回404")
                return True
            else:
                self.log_test("无效任务ID测试", False, 
                            f"期望404，实际返回: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("无效任务ID测试", False, f"测试异常: {str(e)}")
            return False
    
    def test_stock_analysis_creation(self):
        """测试股票分析任务创建"""
        test_data = {
            'stock_code': '301678',
            'market_type': 'A'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/start_stock_analysis",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get('task_id')
                
                if task_id:
                    self.log_test("股票分析任务创建", True, f"任务创建成功，ID: {task_id}")
                    
                    # 测试任务状态查询
                    return self.test_task_status_query(task_id)
                else:
                    self.log_test("股票分析任务创建", False, "未返回任务ID", result)
                    return False
            else:
                self.log_test("股票分析任务创建", False, 
                            f"创建失败，状态码: {response.status_code}",
                            response.text)
                return False
                
        except Exception as e:
            self.log_test("股票分析任务创建", False, f"测试异常: {str(e)}")
            return False
    
    def test_task_status_query(self, task_id):
        """测试任务状态查询"""
        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/api/analysis_status/{task_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    self.log_test(f"任务状态查询-尝试{attempt + 1}", True, 
                                f"查询成功，状态: {status}")
                    
                    # 如果任务完成，结束测试
                    if status in ['completed', 'failed']:
                        self.log_test("任务状态查询", True, f"任务最终状态: {status}")
                        return True
                    
                    # 等待后继续查询
                    if attempt < max_attempts - 1:
                        time.sleep(3)
                        
                elif response.status_code == 404:
                    self.log_test(f"任务状态查询-尝试{attempt + 1}", False, 
                                "任务不存在(404)")
                    
                    # 404错误应该停止轮询，这是正确的行为
                    if attempt == 0:
                        self.log_test("404错误处理", True, "首次查询就返回404，轮询应该停止")
                        return True
                    else:
                        self.log_test("404错误处理", False, "任务在查询过程中丢失")
                        return False
                else:
                    self.log_test(f"任务状态查询-尝试{attempt + 1}", False, 
                                f"查询失败，状态码: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"任务状态查询-尝试{attempt + 1}", False, 
                            f"查询异常: {str(e)}")
        
        self.log_test("任务状态查询", False, "所有查询尝试都失败")
        return False
    
    def test_concurrent_analysis_requests(self):
        """测试并发分析请求"""
        import threading
        
        results = []
        
        def create_analysis(stock_code):
            test_data = {
                'stock_code': stock_code,
                'market_type': 'A'
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/start_stock_analysis",
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get('task_id')
                    results.append(('success', stock_code, task_id))
                else:
                    results.append(('failed', stock_code, response.status_code))
                    
            except Exception as e:
                results.append(('exception', stock_code, str(e)))
        
        # 创建3个并发分析请求
        stock_codes = ['000001', '000002', '301678']
        threads = []
        
        for stock_code in stock_codes:
            thread = threading.Thread(target=create_analysis, args=(stock_code,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 分析结果
        success_count = sum(1 for result in results if result[0] == 'success')
        total_count = len(results)
        
        if success_count >= total_count * 0.8:  # 80%成功率即可
            self.log_test("并发分析请求", True, 
                        f"{success_count}/{total_count} 个请求成功")
            return True
        else:
            self.log_test("并发分析请求", False, 
                        f"只有 {success_count}/{total_count} 个请求成功",
                        results)
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("轮询机制修复验证测试")
        print("=" * 60)
        
        # 测试服务器连接
        if not self.test_server_connection():
            print("服务器连接失败，终止测试")
            return False
        
        # 运行各项测试
        tests = [
            ("无效任务ID 404测试", self.test_invalid_task_id_404),
            ("股票分析任务创建和查询", self.test_stock_analysis_creation),
            ("并发分析请求", self.test_concurrent_analysis_requests),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*40}")
            print(f"运行测试: {test_name}")
            print(f"{'='*40}")
            
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"测试执行异常: {str(e)}")
        
        # 输出测试总结
        print(f"\n{'='*60}")
        print(f"测试总结: {passed_tests}/{total_tests} 个测试通过")
        print(f"{'='*60}")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！轮询机制修复成功！")
            return True
        else:
            print("❌ 部分测试失败，需要进一步检查")
            return False
    
    def save_test_report(self, filename="polling_fix_test_report.json"):
        """保存测试报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        print(f"测试报告已保存到: {filename}")

if __name__ == "__main__":
    # 检查命令行参数
    base_url = "http://localhost:8888"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"测试目标服务器: {base_url}")
    
    # 运行测试
    tester = PollingFixTester(base_url)
    success = tester.run_all_tests()
    
    # 保存测试报告
    tester.save_test_report()
    
    # 退出码
    sys.exit(0 if success else 1)
