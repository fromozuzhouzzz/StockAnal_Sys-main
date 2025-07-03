#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复Dict导入问题
"""

import os
import re

# 需要检查的关键文件
KEY_FILES = [
    'api_integration.py',
    'api_endpoints.py',
    'auth_middleware.py', 
    'api_response.py',
    'api_cache_integration.py',
    'rate_limiter.py'
]

def ensure_dict_import(filename):
    """确保文件正确导入Dict"""
    if not os.path.exists(filename):
        print(f"⚠️ 文件不存在: {filename}")
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否使用了Dict
        uses_dict = bool(re.search(r':\s*Dict\b|-> *Dict\b|\bDict\[', content))
        
        if not uses_dict:
            print(f"✓ {filename}: 不使用Dict")
            return True
        
        # 检查是否已经导入Dict
        has_dict_import = bool(re.search(r'from typing import.*Dict', content))
        
        if has_dict_import:
            print(f"✅ {filename}: Dict已正确导入")
            return True
        
        # 需要添加Dict导入
        lines = content.split('\n')
        
        # 查找现有的typing导入行
        typing_line_index = -1
        for i, line in enumerate(lines):
            if 'from typing import' in line:
                typing_line_index = i
                break
        
        if typing_line_index >= 0:
            # 添加Dict到现有导入
            old_line = lines[typing_line_index]
            if 'Dict' not in old_line:
                if old_line.endswith(')'):
                    new_line = old_line.replace(')', ', Dict)')
                else:
                    new_line = old_line + ', Dict'
                lines[typing_line_index] = new_line
        else:
            # 添加新的typing导入
            # 找到合适的位置
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_index = i + 1
                elif line.strip() and not line.startswith('#'):
                    break
            
            lines.insert(insert_index, 'from typing import Dict')
        
        # 写回文件
        new_content = '\n'.join(lines)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"🔧 {filename}: 已添加Dict导入")
        return True
        
    except Exception as e:
        print(f"❌ {filename}: 修复失败 - {e}")
        return False

def main():
    """主函数"""
    print("🔧 快速修复Dict导入问题")
    print("=" * 40)
    
    success_count = 0
    
    for filename in KEY_FILES:
        if ensure_dict_import(filename):
            success_count += 1
    
    print(f"\n修复完成: {success_count}/{len(KEY_FILES)} 个文件")
    
    # 验证修复结果
    print(f"\n验证修复结果:")
    for filename in KEY_FILES:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                uses_dict = bool(re.search(r':\s*Dict\b|-> *Dict\b|\bDict\[', content))
                has_dict_import = bool(re.search(r'from typing import.*Dict', content))
                
                if uses_dict and has_dict_import:
                    print(f"✅ {filename}: Dict使用和导入都正确")
                elif uses_dict and not has_dict_import:
                    print(f"❌ {filename}: 使用Dict但未导入")
                elif not uses_dict:
                    print(f"✓ {filename}: 不使用Dict")
                else:
                    print(f"✓ {filename}: 导入Dict但未使用")
                    
            except Exception as e:
                print(f"❌ {filename}: 验证失败 - {e}")

if __name__ == '__main__':
    main()
