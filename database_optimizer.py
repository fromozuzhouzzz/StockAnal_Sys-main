#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接和查询优化器
开发者：熊猫大侠
版本：v1.0.0
功能：优化数据库连接池、查询性能、批量操作等
"""

import time
import logging
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from datetime import datetime, timedelta
import threading

from database import (
    engine, get_session, USE_DATABASE,
    StockBasicInfo, StockPriceHistory, StockRealtimeData,
    FinancialData, CapitalFlowData
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_factory = sessionmaker(bind=engine)
        self.connection_stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'failed_queries': 0,
            'avg_query_time': 0.0,
            'connection_pool_hits': 0,
            'connection_pool_misses': 0
        }
        self.slow_query_threshold = 1.0  # 慢查询阈值（秒）
        self.lock = threading.Lock()
    
    @contextmanager
    def get_optimized_session(self):
        """获取优化的数据库会话"""
        session = None
        start_time = time.time()
        
        try:
            session = self.session_factory()
            yield session
            session.commit()
            
        except Exception as e:
            if session:
                session.rollback()
            self._record_failed_query()
            self.logger.error(f"数据库操作失败: {e}")
            raise
            
        finally:
            if session:
                session.close()
            
            # 记录查询统计
            query_time = time.time() - start_time
            self._record_query_stats(query_time)
    
    def _record_query_stats(self, query_time: float):
        """记录查询统计信息"""
        with self.lock:
            self.connection_stats['total_queries'] += 1
            
            if query_time > self.slow_query_threshold:
                self.connection_stats['slow_queries'] += 1
                self.logger.warning(f"慢查询检测: {query_time:.3f}秒")
            
            # 更新平均查询时间
            total = self.connection_stats['total_queries']
            current_avg = self.connection_stats['avg_query_time']
            self.connection_stats['avg_query_time'] = (current_avg * (total - 1) + query_time) / total
    
    def _record_failed_query(self):
        """记录失败查询"""
        with self.lock:
            self.connection_stats['failed_queries'] += 1
    
    def batch_get_stock_basic_info(self, stock_codes: List[str], 
                                  market_type: str = 'A') -> Dict[str, Dict]:
        """批量获取股票基本信息"""
        if not USE_DATABASE or not stock_codes:
            return {}
        
        results = {}
        
        try:
            with self.get_optimized_session() as session:
                # 使用IN查询批量获取
                records = session.query(StockBasicInfo).filter(
                    and_(
                        StockBasicInfo.stock_code.in_(stock_codes),
                        StockBasicInfo.market_type == market_type
                    )
                ).all()
                
                # 转换为字典
                for record in records:
                    if not record.is_expired():
                        results[record.stock_code] = record.to_dict()
                
                self.logger.info(f"批量查询基本信息: {len(results)}/{len(stock_codes)} 命中")
                
        except Exception as e:
            self.logger.error(f"批量查询股票基本信息失败: {e}")
        
        return results
    
    def batch_get_stock_realtime_data(self, stock_codes: List[str],
                                     market_type: str = 'A') -> Dict[str, Dict]:
        """批量获取股票实时数据"""
        if not USE_DATABASE or not stock_codes:
            return {}
        
        results = {}
        
        try:
            with self.get_optimized_session() as session:
                # 使用IN查询批量获取
                records = session.query(StockRealtimeData).filter(
                    and_(
                        StockRealtimeData.stock_code.in_(stock_codes),
                        StockRealtimeData.market_type == market_type
                    )
                ).all()
                
                # 转换为字典
                for record in records:
                    if not record.is_expired():
                        results[record.stock_code] = record.to_dict()
                
                self.logger.info(f"批量查询实时数据: {len(results)}/{len(stock_codes)} 命中")
                
        except Exception as e:
            self.logger.error(f"批量查询股票实时数据失败: {e}")
        
        return results
    
    def batch_save_stock_basic_info(self, stock_data_list: List[Dict]) -> bool:
        """批量保存股票基本信息"""
        if not USE_DATABASE or not stock_data_list:
            return False
        
        try:
            with self.get_optimized_session() as session:
                # 批量删除旧记录
                stock_codes = [data['stock_code'] for data in stock_data_list]
                session.query(StockBasicInfo).filter(
                    StockBasicInfo.stock_code.in_(stock_codes)
                ).delete(synchronize_session=False)
                
                # 批量插入新记录
                records = []
                for data in stock_data_list:
                    expires_at = datetime.now() + timedelta(seconds=data.get('ttl', 604800))
                    record = StockBasicInfo(
                        stock_code=data['stock_code'],
                        stock_name=data.get('stock_name', ''),
                        market_type=data.get('market_type', 'A'),
                        industry=data.get('industry', ''),
                        sector=data.get('sector', ''),
                        list_date=data.get('list_date', ''),
                        total_share=data.get('total_share', 0.0),
                        float_share=data.get('float_share', 0.0),
                        market_cap=data.get('market_cap', 0.0),
                        pe_ratio=data.get('pe_ratio', 0.0),
                        pb_ratio=data.get('pb_ratio', 0.0),
                        expires_at=expires_at
                    )
                    records.append(record)
                
                session.bulk_save_objects(records)
                self.logger.info(f"批量保存股票基本信息: {len(records)} 条记录")
                return True
                
        except Exception as e:
            self.logger.error(f"批量保存股票基本信息失败: {e}")
            return False
    
    def batch_save_stock_realtime_data(self, stock_data_list: List[Dict]) -> bool:
        """批量保存股票实时数据"""
        if not USE_DATABASE or not stock_data_list:
            return False
        
        try:
            with self.get_optimized_session() as session:
                # 批量删除旧记录
                stock_codes = [data['stock_code'] for data in stock_data_list]
                session.query(StockRealtimeData).filter(
                    StockRealtimeData.stock_code.in_(stock_codes)
                ).delete(synchronize_session=False)
                
                # 批量插入新记录
                records = []
                for data in stock_data_list:
                    expires_at = datetime.now() + timedelta(seconds=data.get('ttl', 300))
                    record = StockRealtimeData(
                        stock_code=data['stock_code'],
                        market_type=data.get('market_type', 'A'),
                        current_price=data.get('current_price', 0.0),
                        change_amount=data.get('change_amount', 0.0),
                        change_pct=data.get('change_pct', 0.0),
                        volume=data.get('volume', 0.0),
                        amount=data.get('amount', 0.0),
                        turnover_rate=data.get('turnover_rate', 0.0),
                        pe_ratio=data.get('pe_ratio', 0.0),
                        pb_ratio=data.get('pb_ratio', 0.0),
                        expires_at=expires_at
                    )
                    records.append(record)
                
                session.bulk_save_objects(records)
                self.logger.info(f"批量保存股票实时数据: {len(records)} 条记录")
                return True
                
        except Exception as e:
            self.logger.error(f"批量保存股票实时数据失败: {e}")
            return False
    
    def optimize_expired_cache_cleanup(self) -> int:
        """优化过期缓存清理"""
        if not USE_DATABASE:
            return 0
        
        cleaned_count = 0
        current_time = datetime.now()
        
        try:
            with self.get_optimized_session() as session:
                # 批量删除过期的基本信息缓存
                basic_deleted = session.query(StockBasicInfo).filter(
                    StockBasicInfo.expires_at < current_time
                ).delete(synchronize_session=False)
                
                # 批量删除过期的实时数据缓存
                realtime_deleted = session.query(StockRealtimeData).filter(
                    StockRealtimeData.expires_at < current_time
                ).delete(synchronize_session=False)
                
                # 批量删除过期的历史价格缓存（保留最近30天）
                cutoff_date = current_time - timedelta(days=30)
                price_deleted = session.query(StockPriceHistory).filter(
                    StockPriceHistory.created_at < cutoff_date
                ).delete(synchronize_session=False)
                
                cleaned_count = basic_deleted + realtime_deleted + price_deleted
                
                if cleaned_count > 0:
                    self.logger.info(f"清理过期缓存: {cleaned_count} 条记录")
                
        except Exception as e:
            self.logger.error(f"清理过期缓存失败: {e}")
        
        return cleaned_count
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        stats = {
            'connection_stats': self.connection_stats.copy(),
            'table_stats': {},
            'index_stats': {},
            'performance_metrics': {}
        }
        
        if not USE_DATABASE:
            return stats
        
        try:
            with self.get_optimized_session() as session:
                # 获取表统计信息
                tables = [
                    ('stock_basic_info', StockBasicInfo),
                    ('stock_realtime_data', StockRealtimeData),
                    ('stock_price_history', StockPriceHistory),
                    ('financial_data', FinancialData),
                    ('capital_flow_data', CapitalFlowData)
                ]
                
                for table_name, model_class in tables:
                    try:
                        count = session.query(model_class).count()
                        stats['table_stats'][table_name] = {
                            'record_count': count,
                            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                    except Exception as e:
                        self.logger.warning(f"获取表 {table_name} 统计失败: {e}")
                
                # 计算性能指标
                total_queries = self.connection_stats['total_queries']
                if total_queries > 0:
                    stats['performance_metrics'] = {
                        'slow_query_rate': self.connection_stats['slow_queries'] / total_queries,
                        'error_rate': self.connection_stats['failed_queries'] / total_queries,
                        'avg_query_time': self.connection_stats['avg_query_time']
                    }
                
        except Exception as e:
            self.logger.error(f"获取数据库统计失败: {e}")
        
        return stats
    
    def optimize_database_indexes(self) -> bool:
        """优化数据库索引"""
        if not USE_DATABASE:
            return False
        
        try:
            with self.get_optimized_session() as session:
                # 检查并创建复合索引
                index_sqls = [
                    # 股票基本信息复合索引
                    "CREATE INDEX IF NOT EXISTS idx_stock_basic_code_market ON stock_basic_info(stock_code, market_type)",
                    "CREATE INDEX IF NOT EXISTS idx_stock_basic_expires ON stock_basic_info(expires_at)",
                    
                    # 实时数据复合索引
                    "CREATE INDEX IF NOT EXISTS idx_stock_realtime_code_market ON stock_realtime_data(stock_code, market_type)",
                    "CREATE INDEX IF NOT EXISTS idx_stock_realtime_expires ON stock_realtime_data(expires_at)",
                    
                    # 历史价格复合索引
                    "CREATE INDEX IF NOT EXISTS idx_stock_price_code_date ON stock_price_history(stock_code, trade_date)",
                    "CREATE INDEX IF NOT EXISTS idx_stock_price_created ON stock_price_history(created_at)",
                    
                    # 财务数据索引
                    "CREATE INDEX IF NOT EXISTS idx_financial_code_period ON financial_data(stock_code, report_period)",
                    
                    # 资金流向索引
                    "CREATE INDEX IF NOT EXISTS idx_capital_flow_code_date ON capital_flow_data(stock_code, trade_date)"
                ]
                
                for sql in index_sqls:
                    try:
                        session.execute(text(sql))
                        self.logger.debug(f"执行索引SQL: {sql}")
                    except Exception as e:
                        self.logger.warning(f"创建索引失败: {sql}, 错误: {e}")
                
                self.logger.info("数据库索引优化完成")
                return True
                
        except Exception as e:
            self.logger.error(f"优化数据库索引失败: {e}")
            return False
    
    def reset_stats(self):
        """重置统计信息"""
        with self.lock:
            self.connection_stats = {
                'total_queries': 0,
                'slow_queries': 0,
                'failed_queries': 0,
                'avg_query_time': 0.0,
                'connection_pool_hits': 0,
                'connection_pool_misses': 0
            }
        self.logger.info("数据库统计信息已重置")


# 全局数据库优化器实例
db_optimizer = DatabaseOptimizer()


def get_optimized_session():
    """获取优化的数据库会话（便捷函数）"""
    return db_optimizer.get_optimized_session()


def batch_get_stock_data(stock_codes: List[str], data_type: str = 'basic_info') -> Dict[str, Dict]:
    """批量获取股票数据（便捷函数）"""
    if data_type == 'basic_info':
        return db_optimizer.batch_get_stock_basic_info(stock_codes)
    elif data_type == 'realtime_data':
        return db_optimizer.batch_get_stock_realtime_data(stock_codes)
    else:
        return {}


if __name__ == "__main__":
    # 测试数据库优化器
    optimizer = DatabaseOptimizer()
    
    # 优化索引
    print("优化数据库索引...")
    optimizer.optimize_database_indexes()
    
    # 清理过期缓存
    print("清理过期缓存...")
    cleaned = optimizer.optimize_expired_cache_cleanup()
    print(f"清理了 {cleaned} 条过期记录")
    
    # 获取统计信息
    print("数据库统计信息:")
    stats = optimizer.get_database_stats()
    print(f"连接统计: {stats['connection_stats']}")
    print(f"表统计: {stats['table_stats']}")
    
    print("数据库优化完成！")
