#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找Dict类型注解导入问题
"""

import os
import re

def check_file(filename):
    """检查单个文件的Dict导入问题"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否使用了Dict类型注解
        dict_usage = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 查找Dict类型注解的使用
            if re.search(r':\s*Dict\b', line) or re.search(r'->\s*Dict\b', line):
                dict_usage.append((i, line.strip()))
        
        if not dict_usage:
            return None  # 没有使用Dict
        
        # 检查是否有typing导入
        has_dict_import = False
        
        # 检查各种导入方式
        if re.search(r'from typing import.*Dict', content):
            has_dict_import = True
        elif re.search(r'import typing', content):
            has_dict_import = True
        
        if not has_dict_import:
            return {
                'file': filename,
                'dict_usage': dict_usage,
                'has_import': False,
                'issue': 'Dict used but not imported'
            }
        
        return {
            'file': filename,
            'dict_usage': dict_usage,
            'has_import': True,
            'issue': None
        }
        
    except Exception as e:
        return {
            'file': filename,
            'error': str(e)
        }

def main():
    """主函数"""
    print("🔍 查找Dict类型注解导入问题")
    print("=" * 50)
    
    # 获取所有Python文件
    python_files = [f for f in os.listdir('.') if f.endswith('.py')]
    
    problem_files = []
    
    for filename in python_files:
        result = check_file(filename)
        
        if result and result.get('issue'):
            problem_files.append(result)
            print(f"\n❌ {filename}:")
            print(f"   问题: {result['issue']}")
            print("   Dict使用位置:")
            for line_num, line in result['dict_usage']:
                print(f"     第{line_num}行: {line}")
    
    if not problem_files:
        print("\n✅ 没有发现Dict导入问题！")
    else:
        print(f"\n发现 {len(problem_files)} 个问题文件")
        print("\n修复建议:")
        print("在文件开头添加: from typing import Dict")

if __name__ == '__main__':
    main()
