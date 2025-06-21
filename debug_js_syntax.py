#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试JavaScript语法错误
"""

import re
import requests

def get_rendered_page():
    """获取渲染后的页面内容"""
    try:
        response = requests.get("http://localhost:8888/market_scan", timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ 无法获取页面: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 获取页面出错: {str(e)}")
        return None

def find_js_error_line(content, target_line=1337):
    """查找指定行的内容"""
    lines = content.split('\n')
    
    if target_line <= len(lines):
        print(f"第 {target_line} 行内容:")
        print(f"'{lines[target_line-1]}'")
        
        # 显示前后几行的上下文
        start = max(0, target_line - 5)
        end = min(len(lines), target_line + 5)
        
        print(f"\n上下文 (第 {start+1}-{end} 行):")
        for i in range(start, end):
            marker = ">>> " if i == target_line - 1 else "    "
            print(f"{marker}{i+1:4d}: {lines[i]}")
    else:
        print(f"❌ 文件只有 {len(lines)} 行，无法找到第 {target_line} 行")

def extract_js_blocks(content):
    """提取JavaScript代码块"""
    # 查找所有script标签
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, content, re.DOTALL)
    
    print(f"找到 {len(scripts)} 个JavaScript代码块")
    
    for i, script in enumerate(scripts):
        print(f"\n--- JavaScript代码块 {i+1} ---")
        lines = script.split('\n')
        
        # 检查每一行是否有明显的语法错误
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
                
            # 检查常见的语法错误
            if line.count('{') != line.count('}'):
                if line.endswith('}') and line.count('}') > line.count('{'):
                    print(f"⚠️ 第 {line_num} 行可能有多余的 '}': {line}")
            
            if line.endswith('};') and not any(keyword in line for keyword in ['function', 'var', 'let', 'const', '=']):
                print(f"⚠️ 第 {line_num} 行可能有语法问题: {line}")

def check_bracket_balance(content):
    """检查括号平衡"""
    # 提取JavaScript代码
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, content, re.DOTALL)
    
    for i, script in enumerate(scripts):
        print(f"\n检查JavaScript代码块 {i+1} 的括号平衡:")
        
        brace_count = 0
        paren_count = 0
        bracket_count = 0
        
        lines = script.split('\n')
        for line_num, line in enumerate(lines, 1):
            for char in line:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count < 0:
                        print(f"❌ 第 {line_num} 行: 多余的 '}}' - {line.strip()}")
                        return False
                elif char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    if paren_count < 0:
                        print(f"❌ 第 {line_num} 行: 多余的 ')' - {line.strip()}")
                        return False
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count < 0:
                        print(f"❌ 第 {line_num} 行: 多余的 ']' - {line.strip()}")
                        return False
        
        if brace_count != 0:
            print(f"❌ 大括号不平衡: {brace_count}")
            return False
        if paren_count != 0:
            print(f"❌ 小括号不平衡: {paren_count}")
            return False
        if bracket_count != 0:
            print(f"❌ 方括号不平衡: {bracket_count}")
            return False
            
        print("✅ 括号平衡正确")
    
    return True

def main():
    """主函数"""
    print("JavaScript语法错误调试工具")
    print("=" * 50)
    
    # 获取渲染后的页面
    content = get_rendered_page()
    if not content:
        return
    
    print(f"页面总行数: {len(content.split('\n'))}")
    
    # 查找第1337行的内容
    find_js_error_line(content, 1337)
    
    # 提取并检查JavaScript代码块
    extract_js_blocks(content)
    
    # 检查括号平衡
    check_bracket_balance(content)

if __name__ == "__main__":
    main()
