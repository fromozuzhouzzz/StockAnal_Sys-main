#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API服务端Bug修复程序
修复 "'str' object has no attribute 'get'" 错误
"""

import os
import shutil
from datetime import datetime

def backup_file(file_path):
    """备份原文件"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"✅ 已备份文件: {backup_path}")
        return backup_path
    return None

def fix_stock_analyzer():
    """修复stock_analyzer.py中的bug"""
    file_path = "stock_analyzer.py"
    
    # 备份原文件
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找需要修复的代码段
        old_code = '''    def get_stock_info(self, stock_code, market_type='A'):
        """获取股票基本信息，使用新的数据访问层"""
        try:
            # 使用新的数据访问层获取数据
            info = data_service.get_stock_basic_info(stock_code, market_type)

            if info:
                # 转换为原有格式以保持兼容性
                result = {
                    '股票名称': info['stock_name'],
                    '行业': info['industry'],
                    '地区': info.get('sector', '未知'),
                    '总市值': info['market_cap'],
                    '市盈率': info['pe_ratio'],
                    '市净率': info['pb_ratio'],
                    '总股本': info['total_share'],
                    '流通股': info['float_share'],
                    '上市时间': info['list_date']
                }'''
        
        # 修复后的代码
        new_code = '''    def get_stock_info(self, stock_code, market_type='A'):
        """获取股票基本信息，使用新的数据访问层"""
        try:
            # 使用新的数据访问层获取数据
            info = data_service.get_stock_basic_info(stock_code, market_type)

            if info:
                # 检查info是否为字典类型，防止'str' object has no attribute 'get'错误
                if not isinstance(info, dict):
                    self.logger.error(f"获取到的股票信息不是字典格式: {type(info)}, 内容: {info}")
                    raise Exception(f"股票信息格式错误: 期望字典，实际为{type(info)}")
                
                # 转换为原有格式以保持兼容性
                result = {
                    '股票名称': info.get('stock_name', '未知'),
                    '行业': info.get('industry', '未知'),
                    '地区': info.get('sector', '未知'),
                    '总市值': info.get('market_cap', 0),
                    '市盈率': info.get('pe_ratio', 0),
                    '市净率': info.get('pb_ratio', 0),
                    '总股本': info.get('total_share', 0),
                    '流通股': info.get('float_share', 0),
                    '上市时间': info.get('list_date', '')
                }'''
        
        if old_code in content:
            content = content.replace(old_code, new_code)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已修复 {file_path}")
            return True
        else:
            print(f"⚠️ 在 {file_path} 中未找到需要修复的代码段")
            return False
            
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
    
    # 备份原文件
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找并修复get_stock_basic_info方法
        old_code = '''                # 获取股票名称
                try:
                    stock_name_df = ak.stock_info_a_code_name()
                    stock_name = stock_name_df[stock_name_df['code'] == stock_code]['name'].iloc[0]
                except:
                    stock_name = info_dict.get('股票简称', '')'''
        
        new_code = '''                # 获取股票名称
                try:
                    stock_name_df = ak.stock_info_a_code_name()
                    stock_name = stock_name_df[stock_name_df['code'] == stock_code]['name'].iloc[0]
                except Exception as e:
                    self.logger.warning(f"获取股票名称失败: {e}")
                    stock_name = info_dict.get('股票简称', '未知')'''
        
        if old_code in content:
            content = content.replace(old_code, new_code)
        
        # 添加数据验证
        validation_code = '''            # 验证返回数据的完整性
            if not isinstance(data, dict):
                self.logger.error(f"数据格式错误: 期望字典，实际为{type(data)}")
                return None
            
            # 确保必要字段存在
            required_fields = ['stock_code', 'stock_name', 'market_type']
            for field in required_fields:
                if field not in data:
                    self.logger.warning(f"缺少必要字段: {field}")
                    data[field] = '' if field != 'stock_code' else stock_code
            
            return data'''
        
        # 在return data之前插入验证代码
        if 'return data' in content and validation_code not in content:
            content = content.replace('            return data', validation_code)
        
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

def fix_api_endpoints():
    """修复api_endpoints.py中的错误处理"""
    file_path = "api_endpoints.py"
    
    # 备份原文件
    backup_path = backup_file(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在analyze_stock函数中添加更好的错误处理
        old_error_handling = '''        except Exception as e:
            logger.error(f"分析股票 {normalized_code} 时出错: {str(e)}")
            return APIResponse.error(
                code=ErrorCodes.ANALYSIS_FAILED,
                message=f'股票 {normalized_code} 分析失败',
                details={'error_message': str(e)},
                status_code=500
            )'''
        
        new_error_handling = '''        except Exception as e:
            logger.error(f"分析股票 {normalized_code} 时出错: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            
            return APIResponse.error(
                code=ErrorCodes.ANALYSIS_FAILED,
                message=f'股票 {normalized_code} 分析失败',
                details={
                    'error_message': str(e),
                    'error_type': type(e).__name__,
                    'stock_code': normalized_code
                },
                status_code=500
            )'''
        
        if old_error_handling in content:
            content = content.replace(old_error_handling, new_error_handling)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已修复 {file_path}")
            return True
        else:
            print(f"⚠️ 在 {file_path} 中未找到需要修复的代码段")
            return False
            
    except Exception as e:
        print(f"❌ 修复 {file_path} 失败: {e}")
        # 恢复备份
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"✅ 已恢复备份文件")
        return False

def main():
    """主函数"""
    print("=== API服务端Bug修复程序 ===")
    print(f"开始时间: {datetime.now()}")
    
    print("\n🔧 修复目标:")
    print("- 修复 'str' object has no attribute 'get' 错误")
    print("- 增强数据类型验证")
    print("- 改进错误处理和日志记录")
    
    success_count = 0
    total_fixes = 3
    
    print("\n📝 开始修复...")
    
    # 1. 修复stock_analyzer.py
    print("\n1. 修复 stock_analyzer.py...")
    if fix_stock_analyzer():
        success_count += 1
    
    # 2. 修复data_service.py
    print("\n2. 修复 data_service.py...")
    if fix_data_service():
        success_count += 1
    
    # 3. 修复api_endpoints.py
    print("\n3. 修复 api_endpoints.py...")
    if fix_api_endpoints():
        success_count += 1
    
    print(f"\n=== 修复完成 ===")
    print(f"成功修复: {success_count}/{total_fixes} 个文件")
    print(f"完成时间: {datetime.now()}")
    
    if success_count == total_fixes:
        print("\n🎉 所有修复都已完成！")
        print("\n📋 修复内容:")
        print("✅ 添加了数据类型检查，防止字符串被当作字典使用")
        print("✅ 使用.get()方法安全访问字典键，避免KeyError")
        print("✅ 增强了错误处理和日志记录")
        print("✅ 添加了数据验证和降级处理")
        
        print("\n🚀 下一步:")
        print("1. 重启API服务")
        print("2. 运行批量分析程序测试")
        print("3. 检查日志确认问题已解决")
    else:
        print(f"\n⚠️ 部分修复失败，请检查错误信息")

if __name__ == "__main__":
    main()
