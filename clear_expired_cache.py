#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理过期缓存数据脚本
用于清理数据库中的过期测试数据，确保修复后能够获取到最新的实时数据
"""

import sys
import os
from datetime import datetime, timedelta
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_session, USE_DATABASE,
    StockBasicInfo, StockPriceHistory, StockRealtimeData,
    FinancialData, CapitalFlowData,
    cleanup_expired_cache
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_all_realtime_cache():
    """清理所有实时数据缓存"""
    if not USE_DATABASE:
        logger.warning("数据库未启用，跳过缓存清理")
        return
    
    try:
        session = get_session()
        
        # 清理实时数据表
        realtime_count = session.query(StockRealtimeData).count()
        logger.info(f"发现 {realtime_count} 条实时数据记录")
        
        if realtime_count > 0:
            deleted_count = session.query(StockRealtimeData).delete()
            session.commit()
            logger.info(f"✓ 已清理 {deleted_count} 条实时数据缓存")
        
        session.close()
        
    except Exception as e:
        logger.error(f"清理实时数据缓存失败: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()

def clear_expired_cache_only():
    """只清理过期的缓存数据"""
    if not USE_DATABASE:
        logger.warning("数据库未启用，跳过缓存清理")
        return
    
    try:
        session = get_session()
        current_time = datetime.now()
        
        # 清理过期的实时数据
        expired_realtime = session.query(StockRealtimeData).filter(
            StockRealtimeData.expires_at < current_time
        ).count()
        
        if expired_realtime > 0:
            deleted_realtime = session.query(StockRealtimeData).filter(
                StockRealtimeData.expires_at < current_time
            ).delete(synchronize_session=False)
            logger.info(f"✓ 已清理 {deleted_realtime} 条过期实时数据")
        
        # 清理过期的基本信息
        expired_basic = session.query(StockBasicInfo).filter(
            StockBasicInfo.expires_at < current_time
        ).count()
        
        if expired_basic > 0:
            deleted_basic = session.query(StockBasicInfo).filter(
                StockBasicInfo.expires_at < current_time
            ).delete(synchronize_session=False)
            logger.info(f"✓ 已清理 {deleted_basic} 条过期基本信息")
        
        # 清理过期的资金流向数据
        expired_flow = session.query(CapitalFlowData).filter(
            CapitalFlowData.expires_at < current_time
        ).count()
        
        if expired_flow > 0:
            deleted_flow = session.query(CapitalFlowData).filter(
                CapitalFlowData.expires_at < current_time
            ).delete(synchronize_session=False)
            logger.info(f"✓ 已清理 {deleted_flow} 条过期资金流向数据")
        
        session.commit()
        session.close()
        
        logger.info("✓ 过期缓存清理完成")
        
    except Exception as e:
        logger.error(f"清理过期缓存失败: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()

def show_cache_stats():
    """显示缓存统计信息"""
    if not USE_DATABASE:
        logger.warning("数据库未启用，无法显示统计信息")
        return
    
    try:
        session = get_session()
        current_time = datetime.now()
        
        # 实时数据统计
        total_realtime = session.query(StockRealtimeData).count()
        expired_realtime = session.query(StockRealtimeData).filter(
            StockRealtimeData.expires_at < current_time
        ).count()
        valid_realtime = total_realtime - expired_realtime
        
        # 基本信息统计
        total_basic = session.query(StockBasicInfo).count()
        expired_basic = session.query(StockBasicInfo).filter(
            StockBasicInfo.expires_at < current_time
        ).count()
        valid_basic = total_basic - expired_basic
        
        # 资金流向统计
        total_flow = session.query(CapitalFlowData).count()
        expired_flow = session.query(CapitalFlowData).filter(
            CapitalFlowData.expires_at < current_time
        ).count()
        valid_flow = total_flow - expired_flow
        
        logger.info("=== 缓存统计信息 ===")
        logger.info(f"实时数据: 总计 {total_realtime}, 有效 {valid_realtime}, 过期 {expired_realtime}")
        logger.info(f"基本信息: 总计 {total_basic}, 有效 {valid_basic}, 过期 {expired_basic}")
        logger.info(f"资金流向: 总计 {total_flow}, 有效 {valid_flow}, 过期 {expired_flow}")
        
        session.close()
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        if 'session' in locals():
            session.close()

def main():
    """主函数"""
    logger.info("开始清理过期缓存数据...")
    
    # 显示清理前的统计信息
    logger.info("清理前的缓存状态:")
    show_cache_stats()
    
    # 选择清理策略
    print("\n请选择清理策略:")
    print("1. 只清理过期的缓存数据 (推荐)")
    print("2. 清理所有实时数据缓存 (强制刷新)")
    print("3. 只显示统计信息，不清理")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == '1':
        clear_expired_cache_only()
    elif choice == '2':
        confirm = input("确认要清理所有实时数据缓存吗? (y/N): ").strip().lower()
        if confirm == 'y':
            clear_all_realtime_cache()
        else:
            logger.info("取消清理操作")
    elif choice == '3':
        logger.info("只显示统计信息，不执行清理")
    else:
        logger.error("无效的选择")
        return
    
    # 显示清理后的统计信息
    logger.info("\n清理后的缓存状态:")
    show_cache_stats()
    
    logger.info("缓存清理操作完成!")

if __name__ == "__main__":
    main()
