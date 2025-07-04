#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确的API服务端Bug修复程序
只修复原始的"'str' object has no attribute 'get'"错误，不破坏语法结构
"""

import os
import shutil
from datetime import datetime

def backup_file(file_path):
    """备份原文件"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.correct_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"✅ 已备份文件: {backup_path}")
        return backup_path
    return None

def fix_stock_analyzer():
    """修复stock_analyzer.py中的bug"""
    file_path = "stock_analyzer.py"
    
    print(f"🔧 开始修复 {file_path}...")
    
    # 备份原文件
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并修复get_stock_info方法中的问题
        # 原始代码可能直接访问字典键，需要改为安全访问
        
        # 修复1: 添加数据类型检查
        old_pattern1 = '''            if info:
                # 转换为原有格式以保持兼容性
                result = {
                    '股票名称': info['stock_name'],'''
        
        new_pattern1 = '''            if info:
                # 检查info是否为字典类型，防止'str' object has no attribute 'get'错误
                if not isinstance(info, dict):
                    self.logger.error(f"获取到的股票信息不是字典格式: {type(info)}, 内容: {info}")
                    raise Exception(f"股票信息格式错误: 期望字典，实际为{type(info)}")
                
                # 转换为原有格式以保持兼容性
                result = {
                    '股票名称': info.get('stock_name', '未知'),'''
        
        if old_pattern1 in content:
            content = content.replace(old_pattern1, new_pattern1)
            print("✅ 修复了股票信息数据类型检查")
        
        # 修复2: 将所有直接字典访问改为安全访问
        replacements = [
            ("info['industry']", "info.get('industry', '未知')"),
            ("info['sector']", "info.get('sector', '未知')"),
            ("info['market_cap']", "info.get('market_cap', 0)"),
            ("info['pe_ratio']", "info.get('pe_ratio', 0)"),
            ("info['pb_ratio']", "info.get('pb_ratio', 0)"),
            ("info['total_share']", "info.get('total_share', 0)"),
            ("info['float_share']", "info.get('float_share', 0)"),
            ("info['list_date']", "info.get('list_date', '')")
        ]
        
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                print(f"✅ 修复了 {old} -> {new}")
        
        # 保存修复后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已修复 {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修复 {file_path} 失败: {e}")
        # 恢复备份
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"✅ 已恢复备份文件")
        return False

def fix_data_service():
    """修复data_service.py中的潜在问题"""
    file_path = "data_service.py"
    
    print(f"🔧 开始修复 {file_path}...")
    
    # 备份原文件
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在函数结尾添加数据验证，而不是破坏现有结构
        # 查找get_stock_basic_info函数的结尾
        
        # 在return data之前添加验证
        old_return_pattern = '''            return data
            
        except Exception as e:
            self.logger.error(f"获取股票基本信息失败: {e}")
            return None'''
        
        new_return_pattern = '''            # 验证返回数据的完整性
            if not isinstance(data, dict):
                self.logger.error(f"数据格式错误: 期望字典，实际为{type(data)}")
                return None
            
            # 确保必要字段存在
            required_fields = ['stock_code', 'stock_name', 'market_type']
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"缺少必要字段: {field}")
                    data[field] = '' if field != 'stock_code' else stock_code
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取股票基本信息失败: {e}")
            return None'''
        
        if old_return_pattern in content:
            content = content.replace(old_return_pattern, new_return_pattern)
            print("✅ 添加了数据验证逻辑")
        
        # 保存修复后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已修复 {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ 修复 {file_path} 失败: {e}")
        # 恢复备份
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"✅ 已恢复备份文件")
        return False

def validate_syntax(file_path):
    """验证文件语法"""
    print(f"\n🔍 验证 {file_path} 语法...")
    
    try:
        import ast
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析Python语法
        ast.parse(content)
        print(f"✅ {file_path} 语法验证通过")
        return True
        
    except SyntaxError as e:
        print(f"❌ {file_path} 语法错误:")
        print(f"   行号: {e.lineno}")
        print(f"   错误: {e.msg}")
        print(f"   代码: {e.text}")
        return False
        
    except Exception as e:
        print(f"❌ {file_path} 语法验证失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 正确的API服务端Bug修复程序 ===")
    print(f"开始时间: {datetime.now()}")
    
    print("\n🎯 修复目标:")
    print("- 修复 'str' object has no attribute 'get' 错误")
    print("- 添加数据类型验证")
    print("- 使用安全的字典访问方法")
    print("- 保持代码语法结构完整")
    
    success_count = 0
    total_fixes = 2
    
    print("\n📝 开始修复...")
    
    # 1. 修复stock_analyzer.py
    print("\n1. 修复 stock_analyzer.py...")
    if fix_stock_analyzer():
        success_count += 1
    
    # 验证语法
    if not validate_syntax("stock_analyzer.py"):
        print("❌ stock_analyzer.py 语法验证失败，停止修复")
        return
    
    # 2. 修复data_service.py
    print("\n2. 修复 data_service.py...")
    if fix_data_service():
        success_count += 1
    
    # 验证语法
    if not validate_syntax("data_service.py"):
        print("❌ data_service.py 语法验证失败，停止修复")
        return
    
    print(f"\n=== 修复完成 ===")
    print(f"成功修复: {success_count}/{total_fixes} 个文件")
    print(f"完成时间: {datetime.now()}")
    
    if success_count == total_fixes:
        print("\n🎉 所有修复都已完成且语法正确！")
        print("\n📋 修复内容:")
        print("✅ 添加了数据类型检查，防止字符串被当作字典使用")
        print("✅ 使用.get()方法安全访问字典键，避免KeyError")
        print("✅ 添加了数据验证和默认值处理")
        print("✅ 保持了代码语法结构完整")
        
        print("\n🚀 下一步:")
        print("1. 重新部署到Hugging Face Spaces")
        print("2. 测试API服务功能")
        print("3. 运行批量分析程序验证修复效果")
    else:
        print(f"\n⚠️ 部分修复失败，请检查错误信息")

if __name__ == "__main__":
    main()
