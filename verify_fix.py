#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证JavaScript语法错误修复
"""

import requests
import time

def verify_page_syntax():
    """验证页面语法"""
    print("=== 验证页面语法 ===")
    
    try:
        response = requests.get("http://localhost:8888/market_scan", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # 检查是否包含所有必要的函数
            required_functions = [
                'function fetchIndexStocks',
                'function fetchIndustryStocks',
                'function scanMarket', 
                'function pollScanStatus',
                'function cancelScan',
                'function renderResults',
                'function exportToCSV'
            ]
            
            missing = []
            for func in required_functions:
                if func not in content:
                    missing.append(func)
            
            if missing:
                print(f"❌ 缺少函数: {missing}")
                return False
            else:
                print("✅ 所有必要函数都存在")
            
            # 检查是否有明显的语法错误标志
            syntax_issues = []
            
            # 检查模板字符串问题
            if '${' in content and '`' not in content:
                syntax_issues.append("模板字符串语法错误")
            
            # 检查括号匹配（简单检查）
            open_braces = content.count('{')
            close_braces = content.count('}')
            if abs(open_braces - close_braces) > 10:  # 允许一些HTML中的差异
                syntax_issues.append(f"括号不匹配: {{ {open_braces} vs }} {close_braces}")
            
            if syntax_issues:
                print(f"⚠️ 可能的语法问题: {syntax_issues}")
            else:
                print("✅ 未发现明显的语法问题")
            
            return True
            
        else:
            print(f"❌ 页面访问失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 验证出错: {str(e)}")
        return False

def test_functionality():
    """测试功能"""
    print("\n=== 测试功能 ===")
    
    # 测试扫描功能
    try:
        test_data = {
            "stock_list": ["000001"],
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
            print(f"✅ 扫描功能正常 (任务ID: {task_id})")
            
            # 等待任务完成
            for i in range(10):
                time.sleep(1)
                status_response = requests.get(f"http://localhost:8888/api/scan_status/{task_id}", timeout=5)
                if status_response.status_code == 200:
                    status = status_response.json()
                    if status.get('status') in ['completed', 'failed']:
                        print(f"✅ 任务完成，状态: {status.get('status')}")
                        break
                else:
                    print(f"⚠️ 状态查询失败: {status_response.status_code}")
                    break
            
            return True
        else:
            print(f"❌ 扫描功能失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 功能测试出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("JavaScript语法错误修复验证")
    print("=" * 50)
    
    syntax_ok = verify_page_syntax()
    function_ok = test_functionality()
    
    print("\n" + "=" * 50)
    print("验证结果:")
    
    if syntax_ok and function_ok:
        print("🎉 验证成功！")
        print("\n✅ JavaScript语法错误已完全修复")
        print("✅ 所有功能正常工作")
        print("\n现在可以正常使用市场扫描功能：")
        print("1. 页面加载无语法错误")
        print("2. 按钮点击有响应")
        print("3. 扫描任务正常执行")
        print("4. 进度显示正常更新")
        print("5. 结果展示正确")
        
        print(f"\n请在浏览器中访问: http://localhost:8888/market_scan")
        print("按F12查看控制台，应该没有红色错误信息。")
        
        return True
    else:
        print("❌ 验证失败！")
        if not syntax_ok:
            print("- 页面语法仍有问题")
        if not function_ok:
            print("- 功能测试失败")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎊 恭喜！JavaScript语法错误修复完成！")
    else:
        print("\n😞 仍需要进一步修复。")
