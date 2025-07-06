#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能缓存管理器
支持数据完整性检查、增量更新和交易日感知的缓存策略
"""

import logging
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Tuple
import pandas as pd
from sqlalchemy import func, desc

from database import StockPriceHistory, StockRealtimeData, StockBasicInfo
from database_optimizer import get_optimized_session
from trading_calendar import trading_calendar, get_last_trading_day, get_trading_days_between

logger = logging.getLogger(__name__)

class SmartCacheManager:
    """智能缓存管理器，支持数据完整性检查和增量更新"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def check_price_data_completeness(self, stock_code: str, 
                                    start_date: str, end_date: str,
                                    market_type: str = 'A') -> Dict:
        """
        检查股票历史价格数据的完整性
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            market_type: 市场类型
            
        Returns:
            Dict: {
                'has_data': bool,           # 是否有数据
                'latest_date': str,         # 数据库中最新日期
                'missing_dates': List[str], # 缺失的交易日
                'needs_update': bool,       # 是否需要更新
                'cached_data': DataFrame    # 已缓存的数据
            }
        """
        try:
            with get_optimized_session() as session:
                # 查询数据库中该股票的价格数据
                records = session.query(StockPriceHistory).filter(
                    StockPriceHistory.stock_code == stock_code,
                    StockPriceHistory.market_type == market_type,
                    StockPriceHistory.trade_date >= start_date.replace('-', ''),
                    StockPriceHistory.trade_date <= end_date.replace('-', '')
                ).order_by(StockPriceHistory.trade_date).all()
                
                result = {
                    'has_data': len(records) > 0,
                    'latest_date': None,
                    'missing_dates': [],
                    'needs_update': False,
                    'cached_data': None
                }
                
                if not records:
                    # 没有任何数据，需要全量获取
                    result['needs_update'] = True
                    result['missing_dates'] = [d.strftime('%Y-%m-%d') 
                                             for d in get_trading_days_between(
                                                 datetime.strptime(start_date, '%Y-%m-%d').date(),
                                                 datetime.strptime(end_date, '%Y-%m-%d').date()
                                             )]
                    return result
                
                # 转换为DataFrame
                data_list = [record.to_dict() for record in records]
                df = pd.DataFrame(data_list)
                df['date'] = pd.to_datetime(df['trade_date'])
                df = df.drop('trade_date', axis=1)
                result['cached_data'] = df
                
                # 获取数据库中的最新日期
                latest_record = max(records, key=lambda x: x.trade_date)
                latest_date_str = latest_record.trade_date
                result['latest_date'] = f"{latest_date_str[:4]}-{latest_date_str[4:6]}-{latest_date_str[6:8]}"
                
                # 检查数据完整性
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                latest_dt = datetime.strptime(result['latest_date'], '%Y-%m-%d').date()
                
                # 获取应该有的所有交易日
                expected_trading_days = get_trading_days_between(start_dt, end_dt)
                
                # 获取数据库中已有的交易日
                existing_dates = set()
                for record in records:
                    date_str = record.trade_date
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    existing_dates.add(formatted_date)
                
                # 找出缺失的交易日
                missing_dates = []
                for trading_day in expected_trading_days:
                    if trading_day.strftime('%Y-%m-%d') not in existing_dates:
                        missing_dates.append(trading_day.strftime('%Y-%m-%d'))
                
                result['missing_dates'] = missing_dates
                result['needs_update'] = len(missing_dates) > 0
                
                self.logger.info(f"股票 {stock_code} 数据完整性检查: "
                               f"最新日期={result['latest_date']}, "
                               f"缺失{len(missing_dates)}个交易日")
                
                return result
                
        except Exception as e:
            self.logger.error(f"检查数据完整性失败: {e}")
            return {
                'has_data': False,
                'latest_date': None,
                'missing_dates': [],
                'needs_update': True,
                'cached_data': None
            }
    
    def get_incremental_update_range(self, stock_code: str, 
                                   requested_start: str, requested_end: str,
                                   market_type: str = 'A') -> Tuple[Optional[str], Optional[str]]:
        """
        计算需要增量更新的日期范围
        
        Args:
            stock_code: 股票代码
            requested_start: 请求的开始日期
            requested_end: 请求的结束日期
            market_type: 市场类型
            
        Returns:
            Tuple[start_date, end_date]: 需要从API获取的日期范围，None表示不需要更新
        """
        try:
            with get_optimized_session() as session:
                # 查询数据库中该股票的最新数据日期
                latest_record = session.query(StockPriceHistory).filter(
                    StockPriceHistory.stock_code == stock_code,
                    StockPriceHistory.market_type == market_type
                ).order_by(desc(StockPriceHistory.trade_date)).first()
                
                if not latest_record:
                    # 没有任何数据，需要全量获取
                    return requested_start, requested_end
                
                # 获取数据库中的最新日期
                latest_date_str = latest_record.trade_date
                latest_date = datetime.strptime(latest_date_str, '%Y%m%d').date()
                
                # 获取请求的结束日期
                requested_end_date = datetime.strptime(requested_end, '%Y-%m-%d').date()
                
                # 如果数据库中的最新日期已经包含或超过请求的结束日期
                if latest_date >= requested_end_date:
                    # 检查是否为最新的交易日
                    last_trading_day = get_last_trading_day()
                    if latest_date >= last_trading_day:
                        self.logger.info(f"股票 {stock_code} 数据已是最新，无需更新")
                        return None, None
                
                # 计算需要更新的开始日期（从数据库最新日期的下一个交易日开始）
                update_start_date = latest_date + timedelta(days=1)
                
                # 确保更新开始日期不早于请求的开始日期
                requested_start_date = datetime.strptime(requested_start, '%Y-%m-%d').date()
                if update_start_date < requested_start_date:
                    update_start_date = requested_start_date
                
                # 如果更新开始日期超过了请求的结束日期，则不需要更新
                if update_start_date > requested_end_date:
                    return None, None
                
                update_start_str = update_start_date.strftime('%Y-%m-%d')
                update_end_str = requested_end
                
                self.logger.info(f"股票 {stock_code} 需要增量更新: {update_start_str} 到 {update_end_str}")
                return update_start_str, update_end_str
                
        except Exception as e:
            self.logger.error(f"计算增量更新范围失败: {e}")
            return requested_start, requested_end
    
    def should_update_realtime_data(self, stock_code: str, market_type: str = 'A') -> bool:
        """
        判断是否需要更新实时数据
        
        Args:
            stock_code: 股票代码
            market_type: 市场类型
            
        Returns:
            bool: 是否需要更新
        """
        try:
            # 如果不是交易时间，且已有当日数据，则不需要更新
            if not trading_calendar.is_market_open_time():
                # 检查是否有当日的实时数据
                with get_optimized_session() as session:
                    today = datetime.now().date()
                    record = session.query(StockRealtimeData).filter(
                        StockRealtimeData.stock_code == stock_code,
                        StockRealtimeData.market_type == market_type,
                        func.date(StockRealtimeData.updated_at) == today
                    ).first()
                    
                    if record and not record.is_expired():
                        self.logger.debug(f"股票 {stock_code} 非交易时间且有当日数据，无需更新")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"判断实时数据更新需求失败: {e}")
            return True  # 出错时默认需要更新

    def get_last_update_time(self, stock_code: str, market_type: str = 'A') -> Optional[datetime]:
        """
        获取股票数据的最后更新时间

        Args:
            stock_code: 股票代码
            market_type: 市场类型

        Returns:
            Optional[datetime]: 最后更新时间
        """
        try:
            with get_optimized_session() as session:
                # 检查实时数据的更新时间
                realtime_record = session.query(StockRealtimeData).filter(
                    StockRealtimeData.stock_code == stock_code,
                    StockRealtimeData.market_type == market_type
                ).first()

                if realtime_record:
                    return realtime_record.updated_at

                return None

        except Exception as e:
            self.logger.error(f"获取最后更新时间失败: {e}")
            return None

    def has_today_data(self, stock_code: str, market_type: str = 'A') -> bool:
        """
        检查是否有当日数据

        Args:
            stock_code: 股票代码
            market_type: 市场类型

        Returns:
            bool: 是否有当日数据
        """
        try:
            with get_optimized_session() as session:
                today = datetime.now().date()

                # 检查实时数据
                realtime_record = session.query(StockRealtimeData).filter(
                    StockRealtimeData.stock_code == stock_code,
                    StockRealtimeData.market_type == market_type,
                    func.date(StockRealtimeData.updated_at) == today
                ).first()

                return realtime_record is not None

        except Exception as e:
            self.logger.error(f"检查当日数据失败: {e}")
            return False

    def cache_score_result(self, stock_code: str, score_result: Dict, market_type: str = 'A'):
        """
        缓存评分结果

        Args:
            stock_code: 股票代码
            score_result: 评分结果
            market_type: 市场类型
        """
        try:
            # 这里可以将评分结果缓存到内存或数据库
            # 暂时使用日志记录
            self.logger.info(f"缓存股票 {stock_code} 的评分结果: {score_result.get('score', 'N/A')}")

        except Exception as e:
            self.logger.error(f"缓存评分结果失败: {e}")
    
    def get_cache_statistics(self, stock_code: str, market_type: str = 'A') -> Dict:
        """
        获取指定股票的缓存统计信息
        
        Args:
            stock_code: 股票代码
            market_type: 市场类型
            
        Returns:
            Dict: 缓存统计信息
        """
        try:
            with get_optimized_session() as session:
                stats = {}
                
                # 历史价格数据统计
                price_count = session.query(StockPriceHistory).filter(
                    StockPriceHistory.stock_code == stock_code,
                    StockPriceHistory.market_type == market_type
                ).count()
                
                if price_count > 0:
                    # 最早和最新日期
                    earliest = session.query(func.min(StockPriceHistory.trade_date)).filter(
                        StockPriceHistory.stock_code == stock_code,
                        StockPriceHistory.market_type == market_type
                    ).scalar()
                    
                    latest = session.query(func.max(StockPriceHistory.trade_date)).filter(
                        StockPriceHistory.stock_code == stock_code,
                        StockPriceHistory.market_type == market_type
                    ).scalar()
                    
                    stats['price_data'] = {
                        'count': price_count,
                        'earliest_date': f"{earliest[:4]}-{earliest[4:6]}-{earliest[6:8]}" if earliest else None,
                        'latest_date': f"{latest[:4]}-{latest[4:6]}-{latest[6:8]}" if latest else None
                    }
                
                # 实时数据统计
                realtime_record = session.query(StockRealtimeData).filter(
                    StockRealtimeData.stock_code == stock_code,
                    StockRealtimeData.market_type == market_type
                ).first()
                
                if realtime_record:
                    stats['realtime_data'] = {
                        'last_updated': realtime_record.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'expires_at': realtime_record.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'is_expired': realtime_record.is_expired()
                    }
                
                # 基本信息统计
                basic_record = session.query(StockBasicInfo).filter(
                    StockBasicInfo.stock_code == stock_code,
                    StockBasicInfo.market_type == market_type
                ).first()
                
                if basic_record:
                    stats['basic_info'] = {
                        'last_updated': basic_record.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'expires_at': basic_record.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'is_expired': basic_record.is_expired()
                    }
                
                return stats
                
        except Exception as e:
            self.logger.error(f"获取缓存统计失败: {e}")
            return {}


# 创建全局实例
smart_cache_manager = SmartCacheManager()
