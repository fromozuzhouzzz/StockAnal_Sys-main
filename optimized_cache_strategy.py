#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化的缓存策略
专门针对CSV导出性能问题进行的缓存优化
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import sessionmaker

from database import StockPriceHistory, StockRealtimeData, StockBasicInfo, get_session
from database_optimizer import get_optimized_session
from trading_calendar import trading_calendar, get_last_trading_day

logger = logging.getLogger(__name__)

class OptimizedCacheStrategy:
    """优化的缓存策略，专门解决CSV导出性能问题"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 缓存策略配置
        self.batch_size = 50  # 批量查询大小
        self.cache_hit_threshold = 0.8  # 缓存命中率阈值
        self.slow_query_threshold = 5.0  # 慢查询阈值（秒）
        
        # 性能统计
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'batch_queries': 0,
            'slow_queries': 0,
            'total_query_time': 0.0
        }
    
    def batch_get_stock_data(self, stock_codes: List[str], market_type: str = 'A') -> Dict[str, Dict]:
        """
        批量获取股票数据，优化查询性能
        
        Args:
            stock_codes: 股票代码列表
            market_type: 市场类型
            
        Returns:
            Dict: 股票代码到数据的映射
        """
        start_time = time.time()
        result = {}
        
        try:
            # 分批处理，避免单次查询过大
            for i in range(0, len(stock_codes), self.batch_size):
                batch_codes = stock_codes[i:i + self.batch_size]
                batch_result = self._batch_query_stock_data(batch_codes, market_type)
                result.update(batch_result)
            
            # 记录性能统计
            query_time = time.time() - start_time
            self.stats['total_query_time'] += query_time
            self.stats['batch_queries'] += 1
            
            if query_time > self.slow_query_threshold:
                self.stats['slow_queries'] += 1
                self.logger.warning(f"慢查询检测: 批量查询 {len(stock_codes)} 只股票耗时 {query_time:.2f}秒")
            
            self.logger.info(f"批量获取 {len(stock_codes)} 只股票数据完成，耗时 {query_time:.2f}秒")
            return result
            
        except Exception as e:
            self.logger.error(f"批量获取股票数据失败: {e}")
            return {}
    
    def _batch_query_stock_data(self, stock_codes: List[str], market_type: str) -> Dict[str, Dict]:
        """执行批量查询"""
        result = {}
        
        try:
            with get_optimized_session() as session:
                # 1. 批量查询基本信息
                basic_info_map = self._batch_query_basic_info(session, stock_codes, market_type)
                
                # 2. 批量查询实时数据
                realtime_data_map = self._batch_query_realtime_data(session, stock_codes, market_type)
                
                # 3. 批量查询历史价格数据（最近30天）
                price_data_map = self._batch_query_price_data(session, stock_codes, market_type)
                
                # 4. 合并数据
                for code in stock_codes:
                    stock_data = {
                        'stock_code': code,
                        'basic_info': basic_info_map.get(code, {}),
                        'realtime_data': realtime_data_map.get(code, {}),
                        'price_data': price_data_map.get(code, []),
                        'cache_timestamp': datetime.now().isoformat()
                    }
                    result[code] = stock_data
                
                return result
                
        except Exception as e:
            self.logger.error(f"批量查询执行失败: {e}")
            return {}
    
    def _batch_query_basic_info(self, session, stock_codes: List[str], market_type: str) -> Dict[str, Dict]:
        """批量查询基本信息"""
        try:
            # 使用IN查询批量获取
            records = session.query(StockBasicInfo).filter(
                and_(
                    StockBasicInfo.stock_code.in_(stock_codes),
                    StockBasicInfo.market_type == market_type,
                    or_(
                        StockBasicInfo.expires_at.is_(None),
                        StockBasicInfo.expires_at > datetime.now()
                    )
                )
            ).all()
            
            # 转换为字典
            result = {}
            for record in records:
                result[record.stock_code] = {
                    'stock_name': record.stock_name,
                    'industry': record.industry,
                    'sector': record.sector,
                    'market_cap': record.market_cap,
                    'pe_ratio': record.pe_ratio,
                    'pb_ratio': record.pb_ratio,
                    'updated_at': record.updated_at.isoformat() if record.updated_at else None
                }
                self.stats['cache_hits'] += 1
            
            # 记录缓存未命中
            missing_codes = set(stock_codes) - set(result.keys())
            self.stats['cache_misses'] += len(missing_codes)
            
            return result
            
        except Exception as e:
            self.logger.error(f"批量查询基本信息失败: {e}")
            return {}
    
    def _batch_query_realtime_data(self, session, stock_codes: List[str], market_type: str) -> Dict[str, Dict]:
        """批量查询实时数据"""
        try:
            # 查询未过期的实时数据
            records = session.query(StockRealtimeData).filter(
                and_(
                    StockRealtimeData.stock_code.in_(stock_codes),
                    StockRealtimeData.market_type == market_type,
                    or_(
                        StockRealtimeData.expires_at.is_(None),
                        StockRealtimeData.expires_at > datetime.now()
                    )
                )
            ).all()
            
            # 转换为字典
            result = {}
            for record in records:
                result[record.stock_code] = {
                    'current_price': float(record.current_price) if record.current_price else None,
                    'change_amount': float(record.change_amount) if record.change_amount else None,
                    'change_pct': record.change_pct,
                    'volume': record.volume,
                    'amount': record.amount,
                    'turnover_rate': record.turnover_rate,
                    'pe_ratio': record.pe_ratio,
                    'pb_ratio': record.pb_ratio,
                    'updated_at': record.updated_at.isoformat() if record.updated_at else None
                }
                self.stats['cache_hits'] += 1
            
            # 记录缓存未命中
            missing_codes = set(stock_codes) - set(result.keys())
            self.stats['cache_misses'] += len(missing_codes)
            
            return result
            
        except Exception as e:
            self.logger.error(f"批量查询实时数据失败: {e}")
            return {}
    
    def _batch_query_price_data(self, session, stock_codes: List[str], market_type: str) -> Dict[str, List]:
        """批量查询历史价格数据"""
        try:
            # 计算查询日期范围（最近30天）
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            # 批量查询历史价格
            records = session.query(StockPriceHistory).filter(
                and_(
                    StockPriceHistory.stock_code.in_(stock_codes),
                    StockPriceHistory.market_type == market_type,
                    StockPriceHistory.trade_date >= start_date,
                    StockPriceHistory.trade_date <= end_date
                )
            ).order_by(StockPriceHistory.stock_code, StockPriceHistory.trade_date).all()
            
            # 按股票代码分组
            result = {}
            for record in records:
                if record.stock_code not in result:
                    result[record.stock_code] = []
                
                result[record.stock_code].append({
                    'trade_date': record.trade_date.strftime('%Y-%m-%d'),
                    'open': float(record.open_price) if record.open_price else None,
                    'close': float(record.close_price) if record.close_price else None,
                    'high': float(record.high_price) if record.high_price else None,
                    'low': float(record.low_price) if record.low_price else None,
                    'volume': record.volume,
                    'amount': record.amount
                })
            
            # 统计缓存命中情况
            for code in stock_codes:
                if code in result and len(result[code]) > 0:
                    self.stats['cache_hits'] += 1
                else:
                    self.stats['cache_misses'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"批量查询历史价格失败: {e}")
            return {}
    
    def check_cache_freshness(self, stock_codes: List[str], market_type: str = 'A') -> Dict[str, bool]:
        """
        检查缓存数据的新鲜度
        
        Args:
            stock_codes: 股票代码列表
            market_type: 市场类型
            
        Returns:
            Dict: 股票代码到是否需要更新的映射
        """
        result = {}
        
        try:
            with get_optimized_session() as session:
                # 检查实时数据的新鲜度
                current_time = datetime.now()
                
                # 查询所有股票的最新更新时间
                records = session.query(
                    StockRealtimeData.stock_code,
                    StockRealtimeData.updated_at,
                    StockRealtimeData.expires_at
                ).filter(
                    and_(
                        StockRealtimeData.stock_code.in_(stock_codes),
                        StockRealtimeData.market_type == market_type
                    )
                ).all()
                
                # 分析每只股票的更新需求
                existing_codes = set()
                for record in records:
                    existing_codes.add(record.stock_code)
                    
                    # 检查是否过期
                    if record.expires_at and current_time > record.expires_at:
                        result[record.stock_code] = True  # 需要更新
                    else:
                        # 检查更新时间
                        if record.updated_at:
                            time_since_update = current_time - record.updated_at
                            # 如果超过1小时未更新，建议更新
                            result[record.stock_code] = time_since_update > timedelta(hours=1)
                        else:
                            result[record.stock_code] = True
                
                # 没有缓存记录的股票需要更新
                for code in stock_codes:
                    if code not in existing_codes:
                        result[code] = True
                
                return result
                
        except Exception as e:
            self.logger.error(f"检查缓存新鲜度失败: {e}")
            # 出错时默认都需要更新
            return {code: True for code in stock_codes}
    
    def optimize_database_indexes(self) -> bool:
        """优化数据库索引以提升查询性能"""
        try:
            with get_optimized_session() as session:
                # 创建复合索引以优化批量查询
                index_sqls = [
                    # 股票基本信息优化索引
                    "CREATE INDEX IF NOT EXISTS idx_basic_info_batch ON stock_basic_info_cache(stock_code, market_type, expires_at)",
                    
                    # 实时数据优化索引
                    "CREATE INDEX IF NOT EXISTS idx_realtime_batch ON stock_realtime_data_cache(stock_code, market_type, expires_at)",
                    
                    # 历史价格优化索引
                    "CREATE INDEX IF NOT EXISTS idx_price_history_batch ON stock_price_history_cache(stock_code, market_type, trade_date)",
                    
                    # 覆盖索引，包含常用查询字段
                    "CREATE INDEX IF NOT EXISTS idx_realtime_covering ON stock_realtime_data_cache(stock_code, market_type, current_price, change_pct, updated_at)",
                ]
                
                for sql in index_sqls:
                    try:
                        session.execute(text(sql))
                        self.logger.debug(f"执行索引优化SQL: {sql}")
                    except Exception as e:
                        self.logger.warning(f"创建索引失败: {sql}, 错误: {e}")
                
                session.commit()
                self.logger.info("数据库索引优化完成")
                return True
                
        except Exception as e:
            self.logger.error(f"优化数据库索引失败: {e}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        avg_query_time = (self.stats['total_query_time'] / self.stats['batch_queries']) if self.stats['batch_queries'] > 0 else 0
        
        return {
            'cache_hit_rate': round(cache_hit_rate, 2),
            'total_requests': total_requests,
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'batch_queries': self.stats['batch_queries'],
            'slow_queries': self.stats['slow_queries'],
            'avg_query_time': round(avg_query_time, 3),
            'total_query_time': round(self.stats['total_query_time'], 3)
        }
    
    def reset_stats(self):
        """重置性能统计"""
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'batch_queries': 0,
            'slow_queries': 0,
            'total_query_time': 0.0
        }
        self.logger.info("缓存性能统计已重置")

# 全局实例
optimized_cache = OptimizedCacheStrategy()
