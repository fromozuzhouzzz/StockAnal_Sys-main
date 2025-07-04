#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心修复验证测试
专门测试AKShare API股票代码格式修复的效果
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_service import DataService

def test_core_fix():
    """测试核心修复效果"""
    print("🔍 验证AKShare API股票代码格式修复效果")
    print("=" * 60)
    
    data_service = DataService()
    
    # 测试用户报告的问题股票代码
    problem_codes = ["000001.SZ", "603316.SH", "601218.SH"]
    
    print("\n📋 测试股票代码转换:")
    for code in problem_codes:
        converted = data_service._convert_stock_code_for_akshare(code)
        print(f"  {code:12} -> {converted}")
    
    print("\n📈 测试历史价格数据获取:")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    success_count = 0
    total_count = len(problem_codes)
    
    for code in problem_codes:
        print(f"\n  测试 {code}:")
        try:
            df = data_service.get_stock_price_history(
                code, 
                market_type='A', 
                start_date=start_date, 
                end_date=end_date,
                use_smart_cache=False
            )
            if df is not None and len(df) > 0:
                success_count += 1
                print(f"    ✅ 成功获取 {len(df)} 条数据")
                print(f"    📊 最新价格: {df['close'].iloc[-1]:.2f}")
            else:
                print(f"    ❌ 返回空数据")
        except Exception as e:
            print(f"    ❌ 异常: {str(e)[:100]}...")
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    for i, code in enumerate(problem_codes):
        if i < success_count:
            print(f"{code}: ✅ 成功")
        else:
            print(f"{code}: ❌ 失败")
    
    success_rate = (success_count / total_count) * 100
    print(f"\n成功率: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_count == total_count:
        print("🎉 所有测试通过！API修复成功！")
    elif success_count > 0:
        print("⚠️  部分测试通过，修复基本有效")
    else:
        print("❌ 所有测试失败，需要进一步调试")
    
    return success_count == total_count

if __name__ == "__main__":
    test_core_fix()
