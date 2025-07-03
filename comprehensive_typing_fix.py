#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面修复类型注解导入问题
确保所有文件都正确导入了所需的typing模块
"""

import os
import re

def fix_typing_imports(filename):
    """修复单个文件的typing导入"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # 检查使用的类型注解
        uses_dict = bool(re.search(r':\s*Dict\b|-> *Dict\b|\bDict\[', content))
        uses_list = bool(re.search(r':\s*List\b|-> *List\b|\bList\[', content))
        uses_optional = bool(re.search(r':\s*Optional\b|-> *Optional\b|\bOptional\[', content))
        uses_any = bool(re.search(r':\s*Any\b|-> *Any\b|\bAny\b', content))
        uses_union = bool(re.search(r':\s*Union\b|-> *Union\b|\bUnion\[', content))
        uses_tuple = bool(re.search(r':\s*Tuple\b|-> *Tuple\b|\bTuple\[', content))
        uses_callable = bool(re.search(r':\s*Callable\b|-> *Callable\b|\bCallable\[', content))
        
        if not any([uses_dict, uses_list, uses_optional, uses_any, uses_union, uses_tuple, uses_callable]):
            return False  # 不需要typing导入
        
        # 检查现有的typing导入
        has_typing_import = False
        typing_import_line = -1
        imported_types = set()
        
        for i, line in enumerate(lines):
            if 'from typing import' in line:
                has_typing_import = True
                typing_import_line = i
                # 提取已导入的类型
                match = re.search(r'from typing import (.+)', line)
                if match:
                    imports = match.group(1)
                    # 处理多行导入
                    imports = imports.replace('(', '').replace(')', '').replace('\n', '')
                    for imp in imports.split(','):
                        imported_types.add(imp.strip())
                break
            elif 'import typing' in line:
                has_typing_import = True
                imported_types.add('typing')
                break
        
        # 确定需要导入的类型
        needed_types = []
        if uses_dict and 'Dict' not in imported_types and 'typing' not in imported_types:
            needed_types.append('Dict')
        if uses_list and 'List' not in imported_types and 'typing' not in imported_types:
            needed_types.append('List')
        if uses_optional and 'Optional' not in imported_types and 'typing' not in imported_types:
            needed_types.append('Optional')
        if uses_any and 'Any' not in imported_types and 'typing' not in imported_types:
            needed_types.append('Any')
        if uses_union and 'Union' not in imported_types and 'typing' not in imported_types:
            needed_types.append('Union')
        if uses_tuple and 'Tuple' not in imported_types and 'typing' not in imported_types:
            needed_types.append('Tuple')
        if uses_callable and 'Callable' not in imported_types and 'typing' not in imported_types:
            needed_types.append('Callable')
        
        if not needed_types:
            return False  # 不需要修复
        
        # 修复导入
        if has_typing_import and typing_import_line >= 0:
            # 添加到现有导入
            existing_line = lines[typing_import_line]
            for type_name in needed_types:
                if type_name not in existing_line:
                    if existing_line.endswith(')'):
                        existing_line = existing_line.replace(')', f', {type_name})')
                    else:
                        existing_line += f', {type_name}'
            lines[typing_import_line] = existing_line
        else:
            # 添加新的导入行
            import_line = f"from typing import {', '.join(needed_types)}"
            
            # 找到合适的位置插入
            insert_index = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'''"):
                    continue
                elif line.strip() == '':
                    continue
                elif line.startswith('import ') or line.startswith('from '):
                    insert_index = i
                    break
                else:
                    insert_index = i
                    break
            
            lines.insert(insert_index, import_line)
        
        # 写回文件
        new_content = '\n'.join(lines)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return True
        
    except Exception as e:
        print(f"修复 {filename} 时出错: {e}")
        return False

def main():
    """主函数"""
    print("🔧 全面修复类型注解导入问题")
    print("=" * 50)
    
    # 获取所有Python文件
    python_files = [f for f in os.listdir('.') if f.endswith('.py') and not f.startswith('__')]
    
    print(f"检查 {len(python_files)} 个Python文件...")
    
    fixed_count = 0
    
    for filename in python_files:
        if fix_typing_imports(filename):
            print(f"✅ 修复 {filename}")
            fixed_count += 1
    
    print(f"\n修复完成: {fixed_count} 个文件")
    
    # 特别检查关键文件
    key_files = [
        'api_integration.py',
        'api_endpoints.py', 
        'auth_middleware.py',
        'api_response.py',
        'api_cache_integration.py',
        'rate_limiter.py'
    ]
    
    print(f"\n检查关键API文件:")
    for filename in key_files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否有typing导入
                if 'from typing import' in content or 'import typing' in content:
                    print(f"✅ {filename}: 有typing导入")
                else:
                    print(f"⚠️ {filename}: 没有typing导入")
                    
                # 检查是否使用了Dict
                if re.search(r':\s*Dict\b|-> *Dict\b|\bDict\[', content):
                    if 'Dict' in content and ('from typing import' in content and 'Dict' in content):
                        print(f"✅ {filename}: Dict使用和导入正确")
                    else:
                        print(f"❌ {filename}: Dict使用但可能导入不正确")
                        
            except Exception as e:
                print(f"❌ {filename}: 检查出错 - {e}")
    
    print(f"\n🎉 类型注解导入修复完成！")

if __name__ == '__main__':
    main()
