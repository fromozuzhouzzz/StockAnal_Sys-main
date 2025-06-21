#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JavaScript语法检查脚本
"""

import re
import os

def check_js_syntax(file_path):
    """检查JavaScript语法"""
    print(f"检查文件: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取JavaScript代码
        js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        
        if not js_blocks:
            print("❌ 未找到JavaScript代码块")
            return False
        
        print(f"✅ 找到 {len(js_blocks)} 个JavaScript代码块")
        
        for i, js_code in enumerate(js_blocks):
            print(f"\n--- 检查代码块 {i+1} ---")
            check_single_js_block(js_code, i+1)
        
        return True
        
    except Exception as e:
        print(f"❌ 读取文件时出错: {str(e)}")
        return False

def check_single_js_block(js_code, block_num):
    """检查单个JavaScript代码块"""
    lines = js_code.split('\n')
    
    # 检查括号匹配
    bracket_stack = []
    brace_stack = []
    paren_stack = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('//'):
            continue
            
        for char_pos, char in enumerate(line):
            if char == '{':
                brace_stack.append((line_num, char_pos))
            elif char == '}':
                if not brace_stack:
                    print(f"❌ 第{line_num}行: 多余的 '}}' 在位置 {char_pos}")
                    return False
                brace_stack.pop()
            elif char == '[':
                bracket_stack.append((line_num, char_pos))
            elif char == ']':
                if not bracket_stack:
                    print(f"❌ 第{line_num}行: 多余的 ']' 在位置 {char_pos}")
                    return False
                bracket_stack.pop()
            elif char == '(':
                paren_stack.append((line_num, char_pos))
            elif char == ')':
                if not paren_stack:
                    print(f"❌ 第{line_num}行: 多余的 ')' 在位置 {char_pos}")
                    return False
                paren_stack.pop()
    
    # 检查未闭合的括号
    if brace_stack:
        line_num, pos = brace_stack[-1]
        print(f"❌ 第{line_num}行: 未闭合的 '{{' 在位置 {pos}")
        return False
    
    if bracket_stack:
        line_num, pos = bracket_stack[-1]
        print(f"❌ 第{line_num}行: 未闭合的 '[' 在位置 {pos}")
        return False
        
    if paren_stack:
        line_num, pos = paren_stack[-1]
        print(f"❌ 第{line_num}行: 未闭合的 '(' 在位置 {pos}")
        return False
    
    print(f"✅ 代码块 {block_num} 括号匹配正确")
    
    # 检查函数定义
    function_pattern = r'function\s+(\w+)\s*\('
    functions = re.findall(function_pattern, js_code)
    
    if functions:
        print(f"✅ 找到函数定义: {', '.join(functions)}")
    else:
        print("ℹ️ 未找到函数定义")
    
    # 检查常见语法错误
    common_errors = [
        (r'}\s*}', "可能的多余括号"),
        (r';\s*}', "分号后的括号"),
        (r'function\s+\w+\s*\(\s*\)\s*{[^}]*$', "函数未闭合"),
    ]
    
    for pattern, error_desc in common_errors:
        if re.search(pattern, js_code, re.MULTILINE):
            print(f"⚠️ 可能的语法问题: {error_desc}")
    
    return True

def check_function_calls(file_path):
    """检查函数调用"""
    print(f"\n--- 检查函数调用 ---")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取JavaScript代码
        js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        js_code = '\n'.join(js_blocks)
        
        # 查找函数定义
        function_defs = re.findall(r'function\s+(\w+)\s*\(', js_code)
        
        # 查找函数调用
        function_calls = re.findall(r'(\w+)\s*\(', js_code)
        
        print(f"定义的函数: {set(function_defs)}")
        print(f"调用的函数: {set(function_calls)}")
        
        # 检查未定义的函数调用
        undefined_calls = set(function_calls) - set(function_defs) - {
            'console', 'alert', 'confirm', 'setTimeout', 'setInterval', 'clearInterval',
            'parseInt', 'parseFloat', 'encodeURIComponent', 'JSON', 'Date', 'Blob', 'URL',
            'document', 'window', '$', 'jQuery', 'showError', 'showInfo', 'formatNumber', 
            'formatPercent', 'getMD3ScoreColorClass', 'getMD3TrendColorClass', 'getTrendIcon'
        }
        
        if undefined_calls:
            print(f"⚠️ 可能未定义的函数调用: {undefined_calls}")
        else:
            print("✅ 所有函数调用都有对应定义")
            
    except Exception as e:
        print(f"❌ 检查函数调用时出错: {str(e)}")

def main():
    """主函数"""
    print("JavaScript语法检查工具")
    print("=" * 50)
    
    file_path = "templates/market_scan.html"
    
    # 检查语法
    if check_js_syntax(file_path):
        print("\n✅ 语法检查通过")
    else:
        print("\n❌ 语法检查失败")
    
    # 检查函数调用
    check_function_calls(file_path)
    
    print("\n" + "=" * 50)
    print("检查完成")

if __name__ == "__main__":
    main()
