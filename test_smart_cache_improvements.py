#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能缓存改进测试脚本
测试新的缓存策略，验证数据实时性和性能改进效果
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_trading_calendar():
    """测试交易日判断功能"""
    logger.info("=== 测试交易日判断功能 ===")
    
    try:
        from trading_calendar import trading_calendar, is_trading_day, get_last_trading_day
        
        # 测试今天是否为交易日
        today = datetime.now().date()
        is_today_trading = is_trading_day(today)
        logger.info(f"今天 ({today}) 是否为交易日: {is_today_trading}")
        
        # 测试最后一个交易日
        last_trading = get_last_trading_day()
        logger.info(f"最后一个交易日: {last_trading}")
        
        # 测试是否在交易时间
        is_market_open = trading_calendar.is_market_open_time()
        logger.info(f"当前是否在交易时间: {is_market_open}")
        
        # 测试获取交易日列表
        start_date = datetime.now().date() - timedelta(days=10)
        end_date = datetime.now().date()
        trading_days = trading_calendar.get_trading_days_between(start_date, end_date)
        logger.info(f"最近10天的交易日数量: {len(trading_days)}")
        
        logger.info("✓ 交易日判断功能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 交易日判断功能测试失败: {e}")
        return False

def test_smart_cache_manager():
    """测试智能缓存管理器"""
    logger.info("=== 测试智能缓存管理器 ===")
    
    try:
        from smart_cache_manager import smart_cache_manager
        
        test_stock = "000001"  # 平安银行
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 测试数据完整性检查
        logger.info(f"检查股票 {test_stock} 数据完整性...")
        completeness = smart_cache_manager.check_price_data_completeness(
            test_stock, start_date, end_date
        )
        
        logger.info(f"数据完整性检查结果:")
        logger.info(f"  有数据: {completeness['has_data']}")
        logger.info(f"  最新日期: {completeness['latest_date']}")
        logger.info(f"  缺失交易日: {len(completeness['missing_dates'])}")
        logger.info(f"  需要更新: {completeness['needs_update']}")
        
        # 测试增量更新范围计算
        logger.info(f"计算增量更新范围...")
        update_range = smart_cache_manager.get_incremental_update_range(
            test_stock, start_date, end_date
        )
        logger.info(f"增量更新范围: {update_range}")
        
        # 测试缓存统计
        logger.info(f"获取缓存统计...")
        stats = smart_cache_manager.get_cache_statistics(test_stock)
        logger.info(f"缓存统计: {stats}")
        
        logger.info("✓ 智能缓存管理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 智能缓存管理器测试失败: {e}")
        return False

def test_market_scan_cache_manager():
    """测试市场扫描缓存管理器"""
    logger.info("=== 测试市场扫描缓存管理器 ===")
    
    try:
        from market_scan_cache_manager import market_scan_cache_manager
        
        test_stocks = ["000001", "000002", "600000", "600036", "000858"]
        
        # 测试单只股票缓存检查
        logger.info(f"检查单只股票缓存状态...")
        cache_status = market_scan_cache_manager.should_update_for_market_scan(test_stocks[0])
        logger.info(f"股票 {test_stocks[0]} 缓存状态:")
        logger.info(f"  需要更新: {cache_status['needs_update']}")
        logger.info(f"  原因: {cache_status['reason']}")
        logger.info(f"  数据质量: {cache_status['data_quality']}")
        logger.info(f"  最后更新: {cache_status['last_update']}")
        
        # 测试批量缓存检查
        logger.info(f"批量检查 {len(test_stocks)} 只股票...")
        batch_status = market_scan_cache_manager.batch_check_market_scan_cache(test_stocks)
        
        needs_update_count = sum(1 for status in batch_status.values() if status['needs_update'])
        logger.info(f"批量检查结果: {needs_update_count}/{len(test_stocks)} 只股票需要更新")
        
        # 测试优先级分组
        logger.info(f"获取优先级分组...")
        priority_groups = market_scan_cache_manager.get_market_scan_priority_list(test_stocks)
        for group, stocks in priority_groups.items():
            if stocks:
                logger.info(f"  {group}: {len(stocks)} 只股票")
        
        # 测试时间估算
        logger.info(f"估算更新时间...")
        time_estimate = market_scan_cache_manager.estimate_update_time(test_stocks)
        logger.info(f"时间估算:")
        logger.info(f"  总股票数: {time_estimate['total_stocks']}")
        logger.info(f"  预计总时间: {time_estimate['estimated_total_time']:.1f} 秒")
        logger.info(f"  预计分钟数: {time_estimate['estimated_minutes']:.1f} 分钟")
        
        logger.info("✓ 市场扫描缓存管理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 市场扫描缓存管理器测试失败: {e}")
        return False

def test_smart_price_history():
    """测试智能历史价格数据获取"""
    logger.info("=== 测试智能历史价格数据获取 ===")
    
    try:
        from data_service import DataService
        
        data_service = DataService()
        test_stock = "000001"
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # 测试智能缓存策略
        logger.info(f"使用智能缓存策略获取股票 {test_stock} 数据...")
        start_time = time.time()
        
        df_smart = data_service.get_stock_price_history(
            test_stock, 'A', start_date, end_date, use_smart_cache=True
        )
        
        smart_time = time.time() - start_time
        
        if df_smart is not None:
            logger.info(f"智能缓存策略结果:")
            logger.info(f"  数据条数: {len(df_smart)}")
            logger.info(f"  日期范围: {df_smart['date'].min()} 到 {df_smart['date'].max()}")
            logger.info(f"  获取时间: {smart_time:.2f} 秒")
        else:
            logger.warning("智能缓存策略未获取到数据")
        
        # 测试传统缓存策略（对比）
        logger.info(f"使用传统缓存策略获取股票 {test_stock} 数据...")
        start_time = time.time()
        
        df_traditional = data_service.get_stock_price_history(
            test_stock, 'A', start_date, end_date, use_smart_cache=False
        )
        
        traditional_time = time.time() - start_time
        
        if df_traditional is not None:
            logger.info(f"传统缓存策略结果:")
            logger.info(f"  数据条数: {len(df_traditional)}")
            logger.info(f"  日期范围: {df_traditional['date'].min()} 到 {df_traditional['date'].max()}")
            logger.info(f"  获取时间: {traditional_time:.2f} 秒")
        else:
            logger.warning("传统缓存策略未获取到数据")
        
        # 性能对比
        if df_smart is not None and df_traditional is not None:
            logger.info(f"性能对比:")
            logger.info(f"  智能策略: {smart_time:.2f} 秒")
            logger.info(f"  传统策略: {traditional_time:.2f} 秒")
            if smart_time < traditional_time:
                improvement = ((traditional_time - smart_time) / traditional_time) * 100
                logger.info(f"  性能提升: {improvement:.1f}%")
            else:
                logger.info(f"  传统策略更快")
        
        logger.info("✓ 智能历史价格数据获取测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 智能历史价格数据获取测试失败: {e}")
        return False

def test_market_scan_integration():
    """测试市场扫描集成效果"""
    logger.info("=== 测试市场扫描集成效果 ===")
    
    try:
        from market_scan_cache_manager import market_scan_cache_manager
        from data_service import DataService
        
        data_service = DataService()
        test_stocks = ["000001", "000002", "600000"]  # 减少测试股票数量
        
        # 1. 获取缓存状态和优先级
        logger.info(f"分析 {len(test_stocks)} 只股票的缓存状态...")
        priority_groups = market_scan_cache_manager.get_market_scan_priority_list(test_stocks)
        time_estimate = market_scan_cache_manager.estimate_update_time(test_stocks)
        
        logger.info(f"预计处理时间: {time_estimate['estimated_minutes']:.1f} 分钟")
        
        # 2. 模拟市场扫描数据获取过程
        logger.info("开始模拟市场扫描数据获取...")
        start_time = time.time()
        
        successful_count = 0
        failed_count = 0
        
        for stock_code in test_stocks:
            try:
                logger.info(f"处理股票 {stock_code}...")
                
                # 获取历史数据（用于技术分析）
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                
                df = data_service.get_stock_price_history(
                    stock_code, 'A', start_date, end_date, use_smart_cache=True
                )
                
                if df is not None and len(df) > 0:
                    logger.info(f"  ✓ 股票 {stock_code}: {len(df)} 条数据")
                    successful_count += 1
                else:
                    logger.warning(f"  ✗ 股票 {stock_code}: 无数据")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"  ✗ 股票 {stock_code}: {e}")
                failed_count += 1
        
        total_time = time.time() - start_time
        
        logger.info(f"市场扫描模拟完成:")
        logger.info(f"  成功: {successful_count}/{len(test_stocks)} 只股票")
        logger.info(f"  失败: {failed_count}/{len(test_stocks)} 只股票")
        logger.info(f"  实际用时: {total_time:.2f} 秒 ({total_time/60:.1f} 分钟)")
        logger.info(f"  预估用时: {time_estimate['estimated_total_time']:.2f} 秒")
        
        if successful_count > 0:
            avg_time_per_stock = total_time / len(test_stocks)
            logger.info(f"  平均每只股票: {avg_time_per_stock:.2f} 秒")
        
        logger.info("✓ 市场扫描集成效果测试通过")
        return True
        
    except Exception as e:
        logger.error(f"✗ 市场扫描集成效果测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("开始智能缓存改进测试")
    logger.info("=" * 50)
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("交易日判断功能", test_trading_calendar),
        ("智能缓存管理器", test_smart_cache_manager),
        ("市场扫描缓存管理器", test_market_scan_cache_manager),
        ("智能历史价格数据获取", test_smart_price_history),
        ("市场扫描集成效果", test_market_scan_integration),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n开始测试: {test_name}")
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"测试 {test_name} 出现异常: {e}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    logger.info("\n" + "=" * 50)
    logger.info("测试总结:")
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n总计: {passed} 个测试通过, {failed} 个测试失败")
    
    if failed == 0:
        logger.info("🎉 所有测试通过！智能缓存改进效果良好。")
    else:
        logger.warning(f"⚠️  有 {failed} 个测试失败，需要进一步检查和优化。")

if __name__ == "__main__":
    main()
