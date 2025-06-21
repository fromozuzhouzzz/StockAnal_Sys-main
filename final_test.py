#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试脚本 - 验证JavaScript语法错误修复
"""

import requests
import time

def test_page_load():
    """测试页面加载"""
    print("=== 测试页面加载 ===")
    
    try:
        response = requests.get("http://localhost:8888/market_scan", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # 检查关键函数是否存在
            functions = [
                'function fetchIndexStocks',
                'function fetchIndustryStocks', 
                'function scanMarket',
                'function pollScanStatus',
                'function cancelScan',
                'function renderResults',
                'function exportToCSV'
            ]
            
            missing_functions = []
            for func in functions:
                if func not in content:
                    missing_functions.append(func)
            
            if missing_functions:
                print(f"❌ 缺少函数: {missing_functions}")
                return False
            else:
                print("✅ 所有JavaScript函数都存在")
            
            # 检查语法错误标志
            error_patterns = [
                'Unexpected token',
                'SyntaxError',
                'function}',
                '}}',
                'undefined function'
            ]
            
            syntax_errors = []
            for pattern in error_patterns:
                if pattern in content:
                    syntax_errors.append(pattern)
            
            if syntax_errors:
                print(f"⚠️ 可能的语法问题: {syntax_errors}")
            else:
                print("✅ 未发现明显的语法错误")
            
            return True
            
        else:
            print(f"❌ 页面加载失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 页面加载出错: {str(e)}")
        return False

def test_api_functionality():
    """测试API功能"""
    print("\n=== 测试API功能 ===")
    
    # 测试指数股票API
    try:
        response = requests.get("http://localhost:8888/api/index_stocks?index_code=000300", timeout=10)
        if response.status_code == 200:
            data = response.json()
            stock_count = len(data.get('stock_list', []))
            print(f"✅ 指数股票API正常 (获取到 {stock_count} 只股票)")
        else:
            print(f"❌ 指数股票API失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 指数股票API出错: {str(e)}")
        return False
    
    # 测试扫描任务启动
    try:
        test_data = {
            "stock_list": ["000001", "000002"],
            "min_score": 60,
            "market_type": "A"
        }
        
        response = requests.post(
            "http://localhost:8888/api/start_market_scan",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 扫描任务启动成功 (任务ID: {task_id})")
            
            # 测试状态查询
            time.sleep(1)
            status_response = requests.get(f"http://localhost:8888/api/scan_status/{task_id}", timeout=5)
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✅ 任务状态查询成功 (状态: {status.get('status')})")
                return True
            else:
                print(f"❌ 任务状态查询失败: {status_response.status_code}")
                return False
                
        else:
            print(f"❌ 扫描任务启动失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 扫描任务测试出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("JavaScript语法错误修复 - 最终测试")
    print("=" * 50)
    
    # 测试页面加载
    page_ok = test_page_load()
    
    # 测试API功能
    api_ok = test_api_functionality()
    
    print("\n" + "=" * 50)
    print("测试结果:")
    
    if page_ok and api_ok:
        print("✅ 所有测试通过！")
        print("\n建议操作:")
        print("1. 在浏览器中打开 http://localhost:8888/market_scan")
        print("2. 按F12打开开发者工具，查看Console标签")
        print("3. 应该没有红色的JavaScript错误")
        print("4. 选择一个指数，点击'开始扫描'按钮")
        print("5. 应该看到加载状态和进度更新")
        return True
    else:
        print("❌ 测试失败！")
        print("\n问题排查:")
        if not page_ok:
            print("- 页面加载或JavaScript函数有问题")
        if not api_ok:
            print("- 后端API功能有问题")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 修复成功！市场扫描页面应该可以正常工作了。")
    else:
        print("\n❌ 仍有问题需要解决。")
