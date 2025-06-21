#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署检查脚本 - 验证修复是否正确部署
"""

import os
import hashlib
import datetime
from pathlib import Path

def calculate_file_hash(file_path):
    """计算文件的MD5哈希值"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        return f"Error: {e}"

def check_file_modification(file_path):
    """检查文件的修改时间"""
    try:
        stat = os.stat(file_path)
        mod_time = datetime.datetime.fromtimestamp(stat.st_mtime)
        return mod_time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return f"Error: {e}"

def check_file_content(file_path, search_text):
    """检查文件是否包含特定内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return search_text in content
    except Exception as e:
        return False

def main():
    print("🔍 部署检查脚本")
    print("=" * 50)
    
    # 检查的文件列表
    files_to_check = [
        {
            'path': 'templates/capital_flow.html',
            'search_texts': [
                'cleanCode = String(item.code',  # 数据清理代码
                'white-space: nowrap',           # CSS样式
                'arrow_upward',                  # 新图标
                'color: #d32f2f'                 # 红色样式
            ]
        },
        {
            'path': 'static/md3-styles.css',
            'search_texts': [
                'color: #d32f2f',               # 红色上涨
                'color: #2e7d32',               # 绿色下跌
                'white-space: nowrap'           # 防换行
            ]
        },
        {
            'path': 'templates/layout.html',
            'search_texts': [
                'md3-styles.css?v=20241201-fix'  # 版本号
            ]
        }
    ]
    
    all_checks_passed = True
    
    for file_info in files_to_check:
        file_path = file_info['path']
        print(f"\n📁 检查文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"   ❌ 文件不存在")
            all_checks_passed = False
            continue
        
        # 检查修改时间
        mod_time = check_file_modification(file_path)
        print(f"   📅 修改时间: {mod_time}")
        
        # 检查文件哈希
        file_hash = calculate_file_hash(file_path)
        print(f"   🔐 文件哈希: {file_hash[:16]}...")
        
        # 检查内容
        content_checks = []
        for search_text in file_info['search_texts']:
            found = check_file_content(file_path, search_text)
            content_checks.append(found)
            status = "✅" if found else "❌"
            print(f"   {status} 包含: {search_text[:30]}...")
        
        if not all(content_checks):
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 所有检查通过！修复已正确部署。")
        print("\n📋 下一步操作:")
        print("1. 强制刷新浏览器缓存 (Ctrl+F5)")
        print("2. 访问 /test_fix 页面验证效果")
        print("3. 如果仍有问题，重启Web服务")
    else:
        print("⚠️  部分检查失败！请确认文件是否正确上传。")
        print("\n🔧 建议操作:")
        print("1. 重新上传失败的文件")
        print("2. 检查文件权限")
        print("3. 确认在正确的目录中")
    
    print(f"\n🕐 检查时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
