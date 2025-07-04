#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AKShare API修复效果
验证股票代码格式转换和数据获取是否正常工作
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_service import DataService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_stock_code_conversion():
    """测试股票代码转换功能"""
    print("\n=== 测试股票代码转换功能 ===")
    
    data_service = DataService()
    
    test_codes = [
        "000001.SZ",  # 平安银行
        "603316.SH",  # 诚邦股份
        "601218.SH",  # 吉鑫科技
        "000001",     # 纯数字格式
        "invalid.XX"  # 无效格式
    ]
    
    for code in test_codes:
        converted = data_service._convert_stock_code_for_akshare(code)
        print(f"{code:12} -> {converted}")

def test_stock_basic_info():
    """测试股票基本信息获取"""
    print("\n=== 测试股票基本信息获取 ===")
    
    data_service = DataService()
    
    test_codes = ["000001.SZ", "603316.SH", "601218.SH"]
    
    for code in test_codes:
        print(f"\n测试股票: {code}")
        try:
            info = data_service.get_stock_basic_info(code, market_type='A', use_advanced_cache=False)
            if info:
                print(f"  ✅ 成功获取基本信息")
                print(f"  股票名称: {info.get('stock_name', 'N/A')}")
                print(f"  行业: {info.get('industry', 'N/A')}")
                print(f"  市盈率: {info.get('pe_ratio', 'N/A')}")
                print(f"  市净率: {info.get('pb_ratio', 'N/A')}")
            else:
                print(f"  ❌ 获取基本信息失败")
        except Exception as e:
            print(f"  ❌ 异常: {e}")

def test_stock_price_history():
    """测试股票历史价格数据获取"""
    print("\n=== 测试股票历史价格数据获取 ===")
    
    data_service = DataService()
    
    # 设置较短的时间范围以减少测试时间
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    test_codes = ["000001.SZ", "603316.SH", "601218.SH"]
    
    for code in test_codes:
        print(f"\n测试股票: {code}")
        try:
            df = data_service.get_stock_price_history(
                code, 
                market_type='A', 
                start_date=start_date, 
                end_date=end_date,
                use_smart_cache=False
            )
            if df is not None and len(df) > 0:
                print(f"  ✅ 成功获取历史数据，共 {len(df)} 条记录")
                print(f"  日期范围: {df['date'].min()} 到 {df['date'].max()}")
                print(f"  最新收盘价: {df['close'].iloc[-1]:.2f}")
            else:
                print(f"  ❌ 获取历史数据失败：返回空数据")
        except Exception as e:
            print(f"  ❌ 异常: {e}")

def test_stock_realtime_data():
    """测试股票实时数据获取"""
    print("\n=== 测试股票实时数据获取 ===")
    
    data_service = DataService()
    
    test_codes = ["000001.SZ", "603316.SH", "601218.SH"]
    
    for code in test_codes:
        print(f"\n测试股票: {code}")
        try:
            data = data_service.get_stock_realtime_data(code, market_type='A')
            if data:
                print(f"  ✅ 成功获取实时数据")
                print(f"  当前价格: {data.get('current_price', 'N/A')}")
                print(f"  涨跌幅: {data.get('change_pct', 'N/A')}%")
                print(f"  成交量: {data.get('volume', 'N/A')}")
            else:
                print(f"  ❌ 获取实时数据失败")
        except Exception as e:
            print(f"  ❌ 异常: {e}")

def main():
    """主测试函数"""
    print("开始测试AKShare API修复效果...")
    print("=" * 50)
    
    try:
        # 测试股票代码转换
        test_stock_code_conversion()
        
        # 测试基本信息获取
        test_stock_basic_info()
        
        # 测试历史价格数据获取
        test_stock_price_history()
        
        # 测试实时数据获取
        test_stock_realtime_data()
        
        print("\n" + "=" * 50)
        print("测试完成！")
        
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
