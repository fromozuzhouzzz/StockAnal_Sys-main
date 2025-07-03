#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复Dict类型注解导入问题
"""

import os
import re

def check_and_fix_file(filename):
    """检查并修复单个文件的Dict导入问题"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        
        # 检查是否使用了Dict类型注解
        uses_dict = False
        dict_lines = []
        
        for i, line in enumerate(lines):
            # 查找Dict的使用（在类型注解中）
            if re.search(r':\s*Dict\b|-> *Dict\b|\bDict\[', line):
                uses_dict = True
                dict_lines.append(i + 1)
        
        if not uses_dict:
            return {'file': filename, 'status': 'no_dict_usage', 'changed': False}
        
        # 检查是否已经导入了Dict
        has_dict_import = False
        import_line_index = -1
        
        for i, line in enumerate(lines):
            if 'from typing import' in line and 'Dict' in line:
                has_dict_import = True
                break
            elif 'import typing' in line:
                has_dict_import = True
                break
            elif 'from typing import' in line:
                import_line_index = i
        
        if has_dict_import:
            return {'file': filename, 'status': 'already_imported', 'changed': False}
        
        # 需要添加Dict导入
        if import_line_index >= 0:
            # 已有typing导入，添加Dict
            import_line = lines[import_line_index]
            if 'Dict' not in import_line:
                # 添加Dict到现有导入
                if import_line.endswith(')'):
                    # 多行导入格式
                    lines[import_line_index] = import_line.replace(')', ', Dict)')
                else:
                    # 单行导入格式
                    lines[import_line_index] = import_line.rstrip() + ', Dict'
        else:
            # 没有typing导入，需要添加
            # 找到合适的位置插入导入
            insert_index = 0
            
            # 跳过文件头注释和编码声明
            for i, line in enumerate(lines):
                if line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'''"):
                    continue
                elif line.strip() == '':
                    continue
                else:
                    insert_index = i
                    break
            
            # 在其他导入之前插入typing导入
            lines.insert(insert_index, 'from typing import Dict')
        
        # 写回文件
        new_content = '\n'.join(lines)
        
        if new_content != original_content:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                'file': filename, 
                'status': 'fixed', 
                'changed': True,
                'dict_lines': dict_lines
            }
        else:
            return {'file': filename, 'status': 'no_change_needed', 'changed': False}
            
    except Exception as e:
        return {'file': filename, 'status': 'error', 'error': str(e), 'changed': False}

def main():
    """主函数"""
    print("🔧 修复Dict类型注解导入问题")
    print("=" * 50)
    
    # 获取所有Python文件
    python_files = [f for f in os.listdir('.') if f.endswith('.py') and not f.startswith('__')]
    
    print(f"检查 {len(python_files)} 个Python文件...")
    
    fixed_files = []
    error_files = []
    
    for filename in python_files:
        result = check_and_fix_file(filename)
        
        if result['status'] == 'fixed':
            fixed_files.append(result)
            print(f"✅ 修复 {filename}")
            print(f"   Dict使用位置: 第{', '.join(map(str, result['dict_lines']))}行")
        elif result['status'] == 'error':
            error_files.append(result)
            print(f"❌ 错误 {filename}: {result['error']}")
        elif result['status'] == 'no_dict_usage':
            pass  # 不输出，减少噪音
        elif result['status'] == 'already_imported':
            print(f"✓ {filename}: Dict已正确导入")
    
    print("\n" + "=" * 50)
    print(f"修复完成:")
    print(f"- 修复文件: {len(fixed_files)}")
    print(f"- 错误文件: {len(error_files)}")
    
    if fixed_files:
        print(f"\n修复的文件:")
        for result in fixed_files:
            print(f"- {result['file']}")
    
    if error_files:
        print(f"\n错误文件:")
        for result in error_files:
            print(f"- {result['file']}: {result['error']}")
    
    print(f"\n🎉 Dict导入问题修复完成！")

if __name__ == '__main__':
    main()
