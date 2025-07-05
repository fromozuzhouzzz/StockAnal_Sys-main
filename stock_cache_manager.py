#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据缓存管理器
开发者：熊猫大侠
版本：v2.0.0
功能：专门针对股票数据的智能缓存管理
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd

from advanced_cache_manager import AdvancedCacheManager, CacheStrategy, CacheLevel
from database_optimizer import db_optimizer, get_optimized_session
from database import (
    USE_DATABASE, StockBasicInfo, StockRealtimeData, StockPriceHistory,
    BASIC_INFO_TTL, REALTIME_DATA_TTL, FINANCIAL_DATA_TTL
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockCacheManager(AdvancedCacheManager):
    """股票数据专用缓存管理器"""
    
    def __init__(self):
        super().__init__(
            l1_size=20000,  # 增大L1缓存
            l2_enabled=True,  # 启用Redis
            l3_enabled=USE_DATABASE,  # 根据配置启用数据库
            strategy=CacheStrategy.ADAPTIVE,
            compression_threshold=2048  # 2KB以上压缩
        )
        
        # 股票数据特定配置
        self.data_type_ttl = {
            'basic_info': BASIC_INFO_TTL,
            'realtime_data': REALTIME_DATA_TTL,
            'price_history': 3600,  # 1小时
            'financial_data': FINANCIAL_DATA_TTL,
            'capital_flow': 86400,  # 1天
            'market_scan': 300,     # 5分钟
            'industry_analysis': 1800,  # 30分钟
        }
        
        # 预热数据配置（保留配置但不自动启动）
        self.popular_stocks = [
            '000001', '000002', '600000', '600036', '000858',
            '002415', '000063', '600519', '000166', '600276'
        ]

        # 注释掉自动启动股票数据预热，改为手动调用
        # self._start_stock_preload()
    
    def _start_stock_preload(self):
        """启动股票数据预热"""
        def preload_popular_stocks():
            """预热热门股票数据"""
            try:
                logger.info("开始预热热门股票数据...")
                
                # 预热基本信息
                for stock_code in self.popular_stocks:
                    key = self._generate_key('basic_info', stock_code=stock_code, market_type='A')
                    if not self._get_from_l1(key, self.data_type_ttl['basic_info']):
                        # 从数据库预加载
                        data = self._get_stock_basic_info_from_db(stock_code)
                        if data:
                            self.set('basic_info', data, self.data_type_ttl['basic_info'], 
                                   stock_code=stock_code, market_type='A')
                
                logger.info(f"完成 {len(self.popular_stocks)} 只热门股票预热")
                
            except Exception as e:
                logger.error(f"股票数据预热失败: {e}")
        
        # 异步执行预热任务
        self.preload_executor.submit(preload_popular_stocks)
    
    def _get_from_l3(self, key: str, ttl: int, data_type: str, **kwargs) -> Optional[Any]:
        """从L3缓存（数据库）获取股票数据"""
        if not self.l3_enabled:
            return None
        
        try:
            if data_type == 'basic_info':
                return self._get_stock_basic_info_from_db(kwargs.get('stock_code'))
            elif data_type == 'realtime_data':
                return self._get_stock_realtime_data_from_db(kwargs.get('stock_code'))
            elif data_type == 'price_history':
                return self._get_stock_price_history_from_db(
                    kwargs.get('stock_code'),
                    kwargs.get('start_date'),
                    kwargs.get('end_date')
                )
            
            self.l3_stats.misses += 1
            return None
            
        except Exception as e:
            logger.error(f"L3缓存查询失败: {e}")
            self.l3_stats.misses += 1
            return None
    
    def _set_to_l3(self, key: str, data: Any, ttl: int, data_type: str, **kwargs) -> bool:
        """设置L3缓存（数据库）"""
        if not self.l3_enabled:
            return True
        
        try:
            if data_type == 'basic_info':
                return self._save_stock_basic_info_to_db(data, kwargs.get('stock_code'))
            elif data_type == 'realtime_data':
                return self._save_stock_realtime_data_to_db(data, kwargs.get('stock_code'))
            elif data_type == 'price_history':
                return self._save_stock_price_history_to_db(
                    data, kwargs.get('stock_code'),
                    kwargs.get('start_date'), kwargs.get('end_date')
                )
            
            return True
            
        except Exception as e:
            logger.error(f"L3缓存保存失败: {e}")
            return False
    
    def _get_stock_basic_info_from_db(self, stock_code: str) -> Optional[Dict]:
        """从数据库获取股票基本信息"""
        try:
            with get_optimized_session() as session:
                record = session.query(StockBasicInfo).filter(
                    StockBasicInfo.stock_code == stock_code,
                    StockBasicInfo.market_type == 'A'
                ).first()
                
                if record and not record.is_expired():
                    self.l3_stats.hits += 1
                    return record.to_dict()
                
                self.l3_stats.misses += 1
                return None
                
        except Exception as e:
            logger.error(f"数据库查询基本信息失败: {e}")
            return None
    
    def _save_stock_basic_info_to_db(self, data: Dict, stock_code: str) -> bool:
        """保存股票基本信息到数据库"""
        try:
            stock_data = data.copy()
            stock_data['ttl'] = self.data_type_ttl['basic_info']
            return db_optimizer.batch_save_stock_basic_info([stock_data])
        except Exception as e:
            logger.error(f"保存基本信息到数据库失败: {e}")
            return False
    
    def _get_stock_realtime_data_from_db(self, stock_code: str) -> Optional[Dict]:
        """从数据库获取股票实时数据"""
        try:
            with get_optimized_session() as session:
                record = session.query(StockRealtimeData).filter(
                    StockRealtimeData.stock_code == stock_code,
                    StockRealtimeData.market_type == 'A'
                ).first()
                
                if record and not record.is_expired():
                    self.l3_stats.hits += 1
                    return record.to_dict()
                
                self.l3_stats.misses += 1
                return None
                
        except Exception as e:
            logger.error(f"数据库查询实时数据失败: {e}")
            return None
    
    def _save_stock_realtime_data_to_db(self, data: Dict, stock_code: str) -> bool:
        """保存股票实时数据到数据库"""
        try:
            stock_data = data.copy()
            stock_data['ttl'] = self.data_type_ttl['realtime_data']
            return db_optimizer.batch_save_stock_realtime_data([stock_data])
        except Exception as e:
            logger.error(f"保存实时数据到数据库失败: {e}")
            return False
    
    def _get_stock_price_history_from_db(self, stock_code: str, 
                                        start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """从数据库获取股票历史价格"""
        try:
            with get_optimized_session() as session:
                records = session.query(StockPriceHistory).filter(
                    StockPriceHistory.stock_code == stock_code,
                    StockPriceHistory.market_type == 'A',
                    StockPriceHistory.trade_date >= start_date.replace('-', ''),
                    StockPriceHistory.trade_date <= end_date.replace('-', '')
                ).order_by(StockPriceHistory.trade_date).all()
                
                if records:
                    data_list = [record.to_dict() for record in records]
                    df = pd.DataFrame(data_list)
                    df['date'] = pd.to_datetime(df['trade_date'])
                    df = df.drop('trade_date', axis=1)
                    self.l3_stats.hits += 1
                    return df
                
                self.l3_stats.misses += 1
                return None
                
        except Exception as e:
            logger.error(f"数据库查询历史价格失败: {e}")
            return None
    
    def _save_stock_price_history_to_db(self, df: pd.DataFrame, stock_code: str,
                                       start_date: str, end_date: str) -> bool:
        """保存股票历史价格到数据库"""
        try:
            with get_optimized_session() as session:
                # 批量删除已存在的记录
                session.query(StockPriceHistory).filter(
                    StockPriceHistory.stock_code == stock_code,
                    StockPriceHistory.market_type == 'A',
                    StockPriceHistory.trade_date >= start_date.replace('-', ''),
                    StockPriceHistory.trade_date <= end_date.replace('-', '')
                ).delete(synchronize_session=False)
                
                # 批量插入新记录
                records = []
                for _, row in df.iterrows():
                    trade_date = row['date'].strftime('%Y%m%d')
                    record = StockPriceHistory(
                        stock_code=stock_code,
                        market_type='A',
                        trade_date=trade_date,
                        open_price=row['open'],
                        close_price=row['close'],
                        high_price=row['high'],
                        low_price=row['low'],
                        volume=row['volume'],
                        amount=row.get('amount', 0),
                        change_pct=row.get('change_pct', 0)
                    )
                    records.append(record)
                
                session.bulk_save_objects(records)
                return True
                
        except Exception as e:
            logger.error(f"保存历史价格到数据库失败: {e}")
            return False
    
    def get_stock_basic_info(self, stock_code: str, market_type: str = 'A') -> Optional[Dict]:
        """获取股票基本信息"""
        return self.get('basic_info', self.data_type_ttl['basic_info'],
                       stock_code=stock_code, market_type=market_type)
    
    def set_stock_basic_info(self, stock_code: str, data: Dict, market_type: str = 'A') -> bool:
        """设置股票基本信息"""
        return self.set('basic_info', data, self.data_type_ttl['basic_info'],
                       stock_code=stock_code, market_type=market_type)
    
    def get_stock_realtime_data(self, stock_code: str, market_type: str = 'A') -> Optional[Dict]:
        """获取股票实时数据"""
        return self.get('realtime_data', self.data_type_ttl['realtime_data'],
                       stock_code=stock_code, market_type=market_type)
    
    def set_stock_realtime_data(self, stock_code: str, data: Dict, market_type: str = 'A') -> bool:
        """设置股票实时数据"""
        return self.set('realtime_data', data, self.data_type_ttl['realtime_data'],
                       stock_code=stock_code, market_type=market_type)
    
    def get_stock_price_history(self, stock_code: str, start_date: str, 
                               end_date: str, market_type: str = 'A') -> Optional[pd.DataFrame]:
        """获取股票历史价格"""
        return self.get('price_history', self.data_type_ttl['price_history'],
                       stock_code=stock_code, market_type=market_type,
                       start_date=start_date, end_date=end_date)
    
    def set_stock_price_history(self, stock_code: str, df: pd.DataFrame,
                               start_date: str, end_date: str, market_type: str = 'A') -> bool:
        """设置股票历史价格"""
        return self.set('price_history', df, self.data_type_ttl['price_history'],
                       stock_code=stock_code, market_type=market_type,
                       start_date=start_date, end_date=end_date)
    
    def batch_get_stock_basic_info(self, stock_codes: List[str], 
                                  market_type: str = 'A') -> Tuple[Dict[str, Dict], List[str]]:
        """批量获取股票基本信息"""
        results = {}
        cache_misses = []
        
        for stock_code in stock_codes:
            data = self.get_stock_basic_info(stock_code, market_type)
            if data:
                results[stock_code] = data
            else:
                cache_misses.append(stock_code)
        
        logger.info(f"批量查询基本信息: {len(results)}/{len(stock_codes)} 命中缓存")
        return results, cache_misses
    
    def batch_set_stock_basic_info(self, stock_data_list: List[Dict], 
                                  market_type: str = 'A') -> bool:
        """批量设置股票基本信息"""
        success_count = 0
        
        for stock_data in stock_data_list:
            stock_code = stock_data.get('stock_code')
            if stock_code and self.set_stock_basic_info(stock_code, stock_data, market_type):
                success_count += 1
        
        logger.info(f"批量设置基本信息: {success_count}/{len(stock_data_list)} 成功")
        return success_count == len(stock_data_list)
    
    def invalidate_stock_data(self, stock_code: str = None, data_type: str = None):
        """失效股票数据缓存"""
        if stock_code:
            # 失效特定股票的所有数据
            pattern = f"stock_code={stock_code}"
            self.invalidate(pattern=pattern)
        elif data_type:
            # 失效特定类型的所有数据
            self.invalidate(data_type=data_type)
        else:
            # 失效所有股票数据
            for dt in self.data_type_ttl.keys():
                self.invalidate(data_type=dt)
    
    def preload_market_data(self, stock_codes: List[str]):
        """预加载市场数据"""
        def preload_task():
            logger.info(f"开始预加载 {len(stock_codes)} 只股票的市场数据...")
            
            # 预加载基本信息
            for stock_code in stock_codes:
                try:
                    # 尝试从数据库加载
                    data = self._get_stock_basic_info_from_db(stock_code)
                    if data:
                        self.set_stock_basic_info(stock_code, data)
                except Exception as e:
                    logger.error(f"预加载股票 {stock_code} 失败: {e}")
            
            logger.info("市场数据预加载完成")
        
        return self.preload_executor.submit(preload_task)
    
    def get_cache_performance_report(self) -> Dict:
        """获取缓存性能报告"""
        stats = self.get_stats()
        
        # 计算总体性能指标
        total_hits = 0
        total_requests = 0
        
        for level_stats in [stats['l1_cache'], stats['l2_cache'], stats['l3_cache']]:
            if level_stats:
                total_hits += level_stats['hits']
                total_requests += level_stats['total_requests']
        
        overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0
        
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_performance': {
                'total_requests': total_requests,
                'total_hits': total_hits,
                'overall_hit_rate': overall_hit_rate,
                'cache_efficiency': 'excellent' if overall_hit_rate > 0.8 else 
                                  'good' if overall_hit_rate > 0.6 else 'needs_improvement'
            },
            'level_performance': stats,
            'hot_stocks': list(self.hot_keys)[:10],  # 前10个热点股票
            'recommendations': self._generate_cache_recommendations(stats, overall_hit_rate)
        }
        
        return report
    
    def _generate_cache_recommendations(self, stats: Dict, hit_rate: float) -> List[str]:
        """生成缓存优化建议"""
        recommendations = []
        
        if hit_rate < 0.6:
            recommendations.append("缓存命中率较低，建议增加L1缓存大小或调整TTL策略")
        
        l1_stats = stats['l1_cache']
        if l1_stats['evictions'] > l1_stats['hits'] * 0.1:
            recommendations.append("L1缓存清理频繁，建议增加缓存容量")
        
        if not stats['levels_enabled']['l2']:
            recommendations.append("建议启用Redis L2缓存以提高性能")
        
        if len(self.hot_keys) > self.l1_size * 0.8:
            recommendations.append("热点数据过多，建议增加L1缓存容量")
        
        if not recommendations:
            recommendations.append("缓存性能良好，无需调整")
        
        return recommendations


# 全局股票缓存管理器实例
stock_cache_manager = StockCacheManager()


if __name__ == "__main__":
    # 测试股票缓存管理器
    cache = StockCacheManager()
    
    # 测试基本信息缓存
    test_data = {
        'stock_code': '000001',
        'stock_name': '平安银行',
        'market_type': 'A',
        'industry': '银行',
        'sector': '金融',
        'list_date': '19910403',
        'total_share': 19405918198.0,
        'float_share': 19405918198.0,
        'market_cap': 252077136574.0,
        'pe_ratio': 4.89,
        'pb_ratio': 0.59
    }
    
    # 设置缓存
    success = cache.set_stock_basic_info('000001', test_data)
    print(f"设置缓存: {'成功' if success else '失败'}")
    
    # 获取缓存
    result = cache.get_stock_basic_info('000001')
    print(f"获取缓存: {'成功' if result else '失败'}")
    
    # 获取性能报告
    report = cache.get_cache_performance_report()
    print(f"缓存性能报告: {report['overall_performance']}")
    
    print("股票缓存管理器测试完成！")
