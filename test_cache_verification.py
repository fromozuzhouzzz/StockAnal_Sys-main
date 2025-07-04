#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证缓存机制正常工作
确认修复后的数据能够正确缓存到MySQL数据库中
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_service import DataService
from database import get_session, StockPriceHistory, USE_DATABASE

def test_cache_mechanism():
    """测试缓存机制"""
    print("🗄️  验证MySQL缓存机制")
    print("=" * 50)
    
    if not USE_DATABASE:
        print("❌ 数据库未启用，跳过缓存测试")
        return False
    
    data_service = DataService()
    test_code = "000001.SZ"
    
    print(f"\n📊 测试股票: {test_code}")
    
    # 清除可能的旧缓存
    print("🧹 清理旧缓存数据...")
    try:
        with get_session() as session:
            session.query(StockPriceHistory).filter(
                StockPriceHistory.stock_code == test_code
            ).delete()
            session.commit()
            print("✅ 旧缓存数据已清理")
    except Exception as e:
        print(f"⚠️  清理缓存时出错: {e}")
    
    # 第一次获取数据（应该从API获取并缓存）
    print("\n🌐 第一次获取数据（从API）...")
    start_time = datetime.now()
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    try:
        df1 = data_service.get_stock_price_history(
            test_code, 
            market_type='A', 
            start_date=start_date, 
            end_date=end_date,
            use_smart_cache=True  # 启用智能缓存
        )
        first_duration = (datetime.now() - start_time).total_seconds()
        
        if df1 is not None and len(df1) > 0:
            print(f"✅ 成功获取 {len(df1)} 条数据，耗时 {first_duration:.2f} 秒")
        else:
            print("❌ 第一次获取失败")
            return False
    except Exception as e:
        print(f"❌ 第一次获取异常: {e}")
        return False
    
    # 检查数据是否已缓存到数据库
    print("\n🔍 检查数据库缓存...")
    try:
        with get_session() as session:
            cached_count = session.query(StockPriceHistory).filter(
                StockPriceHistory.stock_code == test_code
            ).count()
            print(f"📦 数据库中缓存了 {cached_count} 条记录")
            
            if cached_count > 0:
                print("✅ 数据成功缓存到MySQL数据库")
            else:
                print("❌ 数据未缓存到数据库")
                return False
    except Exception as e:
        print(f"❌ 检查缓存时出错: {e}")
        return False
    
    # 第二次获取数据（应该从缓存获取）
    print("\n💾 第二次获取数据（从缓存）...")
    start_time = datetime.now()
    
    try:
        df2 = data_service.get_stock_price_history(
            test_code, 
            market_type='A', 
            start_date=start_date, 
            end_date=end_date,
            use_smart_cache=True
        )
        second_duration = (datetime.now() - start_time).total_seconds()
        
        if df2 is not None and len(df2) > 0:
            print(f"✅ 成功获取 {len(df2)} 条数据，耗时 {second_duration:.2f} 秒")
            
            # 比较两次获取的数据
            if len(df1) == len(df2):
                print("✅ 两次获取的数据量一致")
            else:
                print(f"⚠️  数据量不一致: {len(df1)} vs {len(df2)}")
            
            # 比较获取速度
            if second_duration < first_duration:
                speedup = first_duration / second_duration
                print(f"🚀 缓存加速 {speedup:.1f}x")
            else:
                print("⚠️  缓存未显著提升速度")
                
        else:
            print("❌ 第二次获取失败")
            return False
    except Exception as e:
        print(f"❌ 第二次获取异常: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ 缓存机制验证完成")
    return True

if __name__ == "__main__":
    success = test_cache_mechanism()
    if success:
        print("🎉 缓存机制工作正常！")
    else:
        print("❌ 缓存机制存在问题")
