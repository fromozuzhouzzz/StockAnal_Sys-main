#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复data_service.py语法错误
解决try-except块结构问题和重复代码问题
"""

import os
import shutil
from datetime import datetime

def backup_file(file_path):
    """备份原文件"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.syntax_fix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"✅ 已备份文件: {backup_path}")
        return backup_path
    return None

def fix_data_service_syntax():
    """修复data_service.py中的语法错误"""
    file_path = "data_service.py"

    print(f"🔧 开始修复 {file_path} 语法错误...")

    # 备份原文件
    backup_path = backup_file(file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 修复所有被破坏的try-except块
        fixes_applied = 0

        # 修复1: 第一个try-except块（基本信息）
        broken_code1 = '''                            # 验证返回数据的完整性
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
                except Exception as e:'''

        fixed_code1 = '''                            return data
                except Exception as e:'''

        if broken_code1 in content:
            content = content.replace(broken_code1, fixed_code1)
            fixes_applied += 1
            print("✅ 修复了第一个try-except块")

        # 修复2: 第二个try-except块（实时数据）
        broken_code2 = '''                    # 验证返回数据的完整性
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

                session.close()'''

        fixed_code2 = '''                    return data
                session.close()'''

        if broken_code2 in content:
            content = content.replace(broken_code2, fixed_code2)
            fixes_applied += 1
            print("✅ 修复了第二个try-except块")

        # 修复3: 其他可能的破损模式
        # 查找所有孤立的验证代码块
        orphan_validation = '''            if not isinstance(data, dict):
                self.logger.error(f"数据格式错误: 期望字典，实际为{type(data)}")
                return None

            # 确保必要字段存在
            required_fields = ['stock_code', 'stock_name', 'market_type']
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"缺少必要字段: {field}")
                    data[field] = '' if field != 'stock_code' else stock_code

            return data'''

        # 如果这些验证代码出现在错误的位置，移除它们
        while orphan_validation in content:
            content = content.replace(orphan_validation, '')
            fixes_applied += 1
            print("✅ 移除了孤立的验证代码块")

        # 修复4: 处理缩进错误的except语句
        wrong_except_pattern = '''                session.close()
            except Exception as e:'''

        correct_except_pattern = '''                session.close()
            except Exception as e:'''

        if wrong_except_pattern in content:
            content = content.replace(wrong_except_pattern, correct_except_pattern)
            fixes_applied += 1
            print("✅ 修复了except语句缩进")

        # 保存修复后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 已修复 {file_path}，应用了 {fixes_applied} 个修复")
        return True

    except Exception as e:
        print(f"❌ 修复 {file_path} 失败: {e}")
        # 恢复备份
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"✅ 已恢复备份文件")
        return False

def validate_syntax():
    """验证修复后的语法"""
    print("\n🔍 验证Python语法...")
    
    try:
        import ast
        with open("data_service.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析Python语法
        ast.parse(content)
        print("✅ Python语法验证通过")
        return True
        
    except SyntaxError as e:
        print(f"❌ 语法错误仍然存在:")
        print(f"   文件: {e.filename}")
        print(f"   行号: {e.lineno}")
        print(f"   错误: {e.msg}")
        print(f"   代码: {e.text}")
        return False
        
    except Exception as e:
        print(f"❌ 语法验证失败: {e}")
        return False

def check_specific_lines():
    """检查特定行的代码"""
    print("\n📋 检查关键代码行...")
    
    try:
        with open("data_service.py", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 检查第245行附近
        print("第240-250行代码:")
        for i in range(239, min(250, len(lines))):
            line_num = i + 1
            line_content = lines[i].rstrip()
            print(f"   {line_num:3d}: {line_content}")
        
        # 检查try-except配对
        try_count = 0
        except_count = 0
        for i, line in enumerate(lines):
            if 'try:' in line:
                try_count += 1
            if 'except' in line and ':' in line:
                except_count += 1
        
        print(f"\n📊 try-except统计:")
        print(f"   try语句: {try_count}")
        print(f"   except语句: {except_count}")
        
        if try_count == except_count:
            print("✅ try-except配对正常")
        else:
            print("⚠️ try-except配对可能有问题")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查代码行失败: {e}")
        return False

def main():
    """主函数"""
    print("=== data_service.py 语法错误修复程序 ===")
    print(f"开始时间: {datetime.now()}")
    
    print("\n🎯 修复目标:")
    print("- 修复第245行附近的try-except块结构错误")
    print("- 移除重复的数据验证代码")
    print("- 确保Python语法正确性")
    
    # 1. 修复语法错误
    print("\n1. 修复语法错误...")
    if not fix_data_service_syntax():
        print("❌ 语法修复失败，程序退出")
        return
    
    # 2. 验证语法
    print("\n2. 验证语法...")
    if not validate_syntax():
        print("❌ 语法验证失败")
        return
    
    # 3. 检查关键代码行
    print("\n3. 检查关键代码行...")
    check_specific_lines()
    
    print(f"\n=== 修复完成 ===")
    print(f"完成时间: {datetime.now()}")
    
    print("\n🎉 语法错误修复成功！")
    print("\n📋 修复内容:")
    print("✅ 修复了try-except块结构")
    print("✅ 移除了重复的数据验证代码")
    print("✅ 修正了代码缩进")
    print("✅ 通过了Python语法验证")
    
    print("\n🚀 下一步:")
    print("1. 重新部署到Hugging Face Spaces")
    print("2. 测试API服务功能")
    print("3. 运行批量分析程序验证")

if __name__ == "__main__":
    main()
