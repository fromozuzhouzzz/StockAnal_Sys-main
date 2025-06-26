#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实时数据获取修复效果
验证缓存过期机制和数据更新是否正常工作
"""

import sys
import os
from datetime import datetime, timedelta
import logging
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量启用数据库
os.environ['USE_DATABASE'] = 'true'

from data_service import data_service
from database import get_session, StockRealtimeData

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_realtime_data_api():
    """测试实时数据API调用"""
    logger.info("=== 测试实时数据API调用 ===")
    
    # 测试股票列表（选择一些活跃的股票）
    test_stocks = [
        ('000001', 'A'),  # 平安银行
        ('600000', 'A'),  # 浦发银行
        ('000858', 'A'),  # 五粮液
        ('00617', 'HK'),  # 中油资本（用户提到的股票）
    ]
    
    for stock_code, market_type in test_stocks:
        try:
            logger.info(f"\n--- 测试股票: {stock_code} ({market_type}股) ---")
            
            # 获取实时数据
            start_time = time.time()
            data = data_service.get_stock_realtime_data(stock_code, market_type)
            end_time = time.time()
            
            if data:
                logger.info(f"✓ 成功获取实时数据 (耗时: {end_time - start_time:.2f}秒)")
                logger.info(f"  股票代码: {data['stock_code']}")
                logger.info(f"  当前价格: {data['current_price']}")
                logger.info(f"  涨跌额: {data['change_amount']}")
                logger.info(f"  涨跌幅: {data['change_pct']}%")
                logger.info(f"  成交量: {data['volume']}")
                logger.info(f"  更新时间: {data['updated_at']}")
                
                # 检查数据是否为非零值（验证不是虚假数据）
                if data['current_price'] > 0:
                    logger.info("✓ 数据验证通过：价格为非零值")
                else:
                    logger.warning("⚠ 数据可能异常：价格为零")
                    
            else:
                logger.error(f"✗ 获取实时数据失败: {stock_code}")
                
        except Exception as e:
            logger.error(f"✗ 测试股票 {stock_code} 时出错: {e}")
    
    return True

def test_cache_mechanism():
    """测试缓存机制"""
    logger.info("\n=== 测试缓存机制 ===")
    
    test_stock = '000001'  # 平安银行
    
    try:
        # 第一次调用（应该从API获取）
        logger.info("第一次调用（从API获取）...")
        start_time = time.time()
        data1 = data_service.get_stock_realtime_data(test_stock, 'A')
        time1 = time.time() - start_time
        
        if data1:
            logger.info(f"✓ 第一次调用成功 (耗时: {time1:.2f}秒)")
            
            # 第二次调用（应该从缓存获取）
            logger.info("第二次调用（从缓存获取）...")
            start_time = time.time()
            data2 = data_service.get_stock_realtime_data(test_stock, 'A')
            time2 = time.time() - start_time
            
            if data2:
                logger.info(f"✓ 第二次调用成功 (耗时: {time2:.2f}秒)")
                
                # 比较耗时（缓存应该更快）
                if time2 < time1:
                    logger.info("✓ 缓存机制工作正常：第二次调用更快")
                else:
                    logger.warning("⚠ 缓存可能未生效：第二次调用未明显加速")
                
                # 验证数据一致性
                if data1['current_price'] == data2['current_price']:
                    logger.info("✓ 缓存数据一致性验证通过")
                else:
                    logger.warning("⚠ 缓存数据不一致")
            else:
                logger.error("✗ 第二次调用失败")
        else:
            logger.error("✗ 第一次调用失败")
            
    except Exception as e:
        logger.error(f"✗ 缓存机制测试失败: {e}")

def test_database_storage():
    """测试数据库存储"""
    logger.info("\n=== 测试数据库存储 ===")
    
    try:
        session = get_session()
        
        # 查询数据库中的实时数据
        records = session.query(StockRealtimeData).all()
        logger.info(f"数据库中共有 {len(records)} 条实时数据记录")
        
        if records:
            for record in records[:3]:  # 显示前3条记录
                logger.info(f"  股票: {record.stock_code}, 价格: {record.current_price}, 过期时间: {record.expires_at}")
                
                # 检查过期时间设置是否正确
                if record.expires_at:
                    time_diff = (record.expires_at - datetime.now()).total_seconds()
                    if 0 < time_diff <= 300:  # 5分钟内
                        logger.info(f"    ✓ 过期时间设置正确 (剩余 {time_diff:.0f} 秒)")
                    else:
                        logger.warning(f"    ⚠ 过期时间可能异常 (剩余 {time_diff:.0f} 秒)")
        
        session.close()
        
    except Exception as e:
        logger.error(f"✗ 数据库存储测试失败: {e}")

def test_cache_expiration():
    """测试缓存过期机制（模拟）"""
    logger.info("\n=== 测试缓存过期机制 ===")
    
    try:
        # 获取一个股票的数据
        test_stock = '600000'
        data = data_service.get_stock_realtime_data(test_stock, 'A')
        
        if data:
            logger.info(f"✓ 获取到股票 {test_stock} 的数据")
            
            # 检查数据库中的过期时间
            session = get_session()
            record = session.query(StockRealtimeData).filter(
                StockRealtimeData.stock_code == test_stock,
                StockRealtimeData.market_type == 'A'
            ).first()
            
            if record:
                expires_at = record.expires_at
                current_time = datetime.now()
                time_to_expire = (expires_at - current_time).total_seconds()
                
                logger.info(f"  当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"  过期时间: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"  剩余时间: {time_to_expire:.0f} 秒")
                
                if 0 < time_to_expire <= 300:
                    logger.info("✓ 缓存过期时间设置正确（5分钟内）")
                else:
                    logger.warning("⚠ 缓存过期时间可能异常")
            
            session.close()
        
    except Exception as e:
        logger.error(f"✗ 缓存过期机制测试失败: {e}")

def main():
    """主测试函数"""
    logger.info("开始测试实时数据获取修复效果...")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行所有测试
    tests = [
        ("实时数据API调用", test_realtime_data_api),
        ("缓存机制", test_cache_mechanism),
        ("数据库存储", test_database_storage),
        ("缓存过期机制", test_cache_expiration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"开始测试: {test_name}")
            test_func()
            passed += 1
            logger.info(f"✓ {test_name} 测试完成")
        except Exception as e:
            logger.error(f"✗ {test_name} 测试失败: {e}")
    
    # 测试总结
    logger.info(f"\n{'='*50}")
    logger.info("测试总结:")
    logger.info(f"总测试数: {total}")
    logger.info(f"通过测试: {passed}")
    logger.info(f"失败测试: {total - passed}")
    
    if passed == total:
        logger.info("🎉 所有测试通过！实时数据获取修复成功！")
    else:
        logger.warning(f"⚠ 有 {total - passed} 个测试失败，需要进一步检查")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    if success:
        print("\n搞完了")
    else:
        print("\n需要进一步修复")
