#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Python文件中的类型注解导入问题
"""

import os
import re
import sys

def check_file_typing_imports(file_path):
    """检查单个文件的类型注解导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # 检查是否使用了Dict类型注解
        uses_dict = False
        uses_list = False
        uses_optional = False
        uses_any = False
        uses_union = False
        
        # 检查类型注解使用
        for line in lines:
            if re.search(r':\s*Dict\b', line) or re.search(r'->\s*Dict\b', line):
                uses_dict = True
            if re.search(r':\s*List\b', line) or re.search(r'->\s*List\b', line):
                uses_list = True
            if re.search(r':\s*Optional\b', line) or re.search(r'->\s*Optional\b', line):
                uses_optional = True
            if re.search(r':\s*Any\b', line) or re.search(r'->\s*Any\b', line):
                uses_any = True
            if re.search(r':\s*Union\b', line) or re.search(r'->\s*Union\b', line):
                uses_union = True
        
        # 检查是否有typing导入
        has_typing_import = False
        imported_types = set()
        
        for line in lines:
            if 'from typing import' in line:
                has_typing_import = True
                # 提取导入的类型
                match = re.search(r'from typing import (.+)', line)
                if match:
                    imports = match.group(1)
                    # 处理多行导入和括号
                    imports = imports.replace('(', '').replace(')', '')
                    for imp in imports.split(','):
                        imported_types.add(imp.strip())
            elif 'import typing' in line:
                has_typing_import = True
                imported_types.add('typing')
        
        # 检查问题
        issues = []
        
        if uses_dict and 'Dict' not in imported_types and 'typing' not in imported_types:
            issues.append("使用了Dict但未导入")
        
        if uses_list and 'List' not in imported_types and 'typing' not in imported_types:
            issues.append("使用了List但未导入")
        
        if uses_optional and 'Optional' not in imported_types and 'typing' not in imported_types:
            issues.append("使用了Optional但未导入")
        
        if uses_any and 'Any' not in imported_types and 'typing' not in imported_types:
            issues.append("使用了Any但未导入")
        
        if uses_union and 'Union' not in imported_types and 'typing' not in imported_types:
            issues.append("使用了Union但未导入")
        
        return {
            'file': file_path,
            'has_typing_import': has_typing_import,
            'imported_types': imported_types,
            'uses_dict': uses_dict,
            'uses_list': uses_list,
            'uses_optional': uses_optional,
            'uses_any': uses_any,
            'uses_union': uses_union,
            'issues': issues
        }
        
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e),
            'issues': [f"读取文件出错: {e}"]
        }

def main():
    """主函数"""
    print("🔍 检查Python文件中的类型注解导入问题")
    print("=" * 60)
    
    # 获取所有Python文件
    python_files = []
    for file in os.listdir('.'):
        if file.endswith('.py') and not file.startswith('__'):
            python_files.append(file)
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 检查每个文件
    files_with_issues = []
    total_issues = 0
    
    for file_path in python_files:
        result = check_file_typing_imports(file_path)
        
        if result.get('issues'):
            files_with_issues.append(result)
            total_issues += len(result['issues'])
            
            print(f"\n❌ {file_path}:")
            for issue in result['issues']:
                print(f"   - {issue}")
            
            if result.get('imported_types'):
                print(f"   已导入: {', '.join(result['imported_types'])}")
        else:
            if result.get('uses_dict') or result.get('uses_list') or result.get('uses_optional'):
                print(f"✅ {file_path}: 类型注解导入正确")
    
    print("\n" + "=" * 60)
    print(f"检查完成: {len(files_with_issues)} 个文件有问题，共 {total_issues} 个问题")
    
    if files_with_issues:
        print("\n🔧 需要修复的文件:")
        for result in files_with_issues:
            print(f"- {result['file']}")
        
        print("\n💡 修复建议:")
        print("在文件开头添加适当的typing导入，例如:")
        print("from typing import Dict, List, Optional, Any, Union")
    else:
        print("\n🎉 所有文件的类型注解导入都正确！")

if __name__ == '__main__':
    main()
