# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - 统一数据访问层
开发者：熊猫大侠
版本：v2.1.0
许可证：MIT License
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import traceback
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time

# 导入数据库模型
from database import (
    get_session, USE_DATABASE, 
    StockBasicInfo, StockPriceHistory, StockRealtimeData, 
    FinancialData, CapitalFlowData,
    CACHE_DEFAULT_TTL, REALTIME_DATA_TTL, BASIC_INFO_TTL, FINANCIAL_DATA_TTL,
    cleanup_expired_cache, get_cache_stats
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 线程锁
data_lock = threading.Lock()

# 内存缓存作为降级方案
memory_cache = {}
MEMORY_CACHE_SIZE = 1000  # 最大缓存条目数


class DataService:
    """统一数据访问服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_timeout = 30  # API调用超时时间
        self.max_retries = 3   # 最大重试次数
        
        # 定期清理过期缓存
        self._schedule_cache_cleanup()
    
    def _schedule_cache_cleanup(self):
        """定期清理过期缓存"""
        def cleanup_task():
            while True:
                try:
                    time.sleep(3600)  # 每小时清理一次
                    cleanup_expired_cache()
                    self._cleanup_memory_cache()
                except Exception as e:
                    self.logger.error(f"缓存清理任务失败: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_memory_cache(self):
        """清理内存缓存"""
        with data_lock:
            if len(memory_cache) > MEMORY_CACHE_SIZE:
                # 删除最旧的缓存项
                sorted_items = sorted(memory_cache.items(), 
                                    key=lambda x: x[1].get('timestamp', 0))
                items_to_remove = len(memory_cache) - MEMORY_CACHE_SIZE + 100
                for i in range(items_to_remove):
                    del memory_cache[sorted_items[i][0]]
    
    def _get_cache_key(self, data_type: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [data_type]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "|".join(key_parts)
    
    def _check_memory_cache(self, cache_key: str, ttl: int) -> Optional[Any]:
        """检查内存缓存"""
        with data_lock:
            if cache_key in memory_cache:
                cache_item = memory_cache[cache_key]
                timestamp = cache_item.get('timestamp', 0)
                if time.time() - timestamp < ttl:
                    return cache_item.get('data')
                else:
                    del memory_cache[cache_key]
        return None
    
    def _set_memory_cache(self, cache_key: str, data: Any):
        """设置内存缓存"""
        with data_lock:
            memory_cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
    
    def _fetch_with_timeout(self, fetch_func, *args, **kwargs):
        """带超时的数据获取"""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fetch_func, *args, **kwargs)
            try:
                return future.result(timeout=self.api_timeout)
            except TimeoutError:
                self.logger.error(f"API调用超时 ({self.api_timeout}秒)")
                raise Exception("API调用超时，请稍后重试")
    
    def _retry_api_call(self, api_func, *args, **kwargs):
        """带重试机制的API调用"""
        for attempt in range(self.max_retries):
            try:
                return self._fetch_with_timeout(api_func, *args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                self.logger.warning(f"API调用第 {attempt + 1} 次尝试失败: {error_msg}")
                
                if attempt < self.max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise e
    
    def get_stock_basic_info(self, stock_code: str, market_type: str = 'A') -> Optional[Dict]:
        """获取股票基本信息"""
        cache_key = self._get_cache_key('basic_info', stock_code=stock_code, market_type=market_type)
        
        # 1. 检查内存缓存
        cached_data = self._check_memory_cache(cache_key, BASIC_INFO_TTL)
        if cached_data:
            return cached_data
        
        # 2. 检查数据库缓存
        if USE_DATABASE:
            try:
                session = get_session()
                db_record = session.query(StockBasicInfo).filter(
                    StockBasicInfo.stock_code == stock_code,
                    StockBasicInfo.market_type == market_type
                ).first()
                
                if db_record and not db_record.is_expired():
                    data = db_record.to_dict()
                    session.close()
                    self._set_memory_cache(cache_key, data)
                    return data
                
                session.close()
            except Exception as e:
                self.logger.error(f"数据库查询失败: {e}")
        
        # 3. 从API获取新数据
        try:
            self.logger.info(f"从API获取股票 {stock_code} 基本信息")
            
            if market_type == 'A':
                # 获取A股基本信息
                stock_info = self._retry_api_call(ak.stock_individual_info_em, symbol=stock_code)
                
                # 处理数据
                info_dict = {}
                for _, row in stock_info.iterrows():
                    if len(row) >= 2:
                        info_dict[row.iloc[0]] = row.iloc[1]
                
                # 获取股票名称
                try:
                    stock_name_df = ak.stock_info_a_code_name()
                    stock_name = stock_name_df[stock_name_df['code'] == stock_code]['name'].iloc[0]
                except:
                    stock_name = info_dict.get('股票简称', '')
                
                data = {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'market_type': market_type,
                    'industry': info_dict.get('行业', ''),
                    'sector': info_dict.get('板块', ''),
                    'list_date': info_dict.get('上市时间', ''),
                    'total_share': self._safe_float(info_dict.get('总股本', 0)),
                    'float_share': self._safe_float(info_dict.get('流通股', 0)),
                    'market_cap': self._safe_float(info_dict.get('总市值', 0)),
                    'pe_ratio': self._safe_float(info_dict.get('市盈率', 0)),
                    'pb_ratio': self._safe_float(info_dict.get('市净率', 0))
                }
            else:
                # 其他市场的处理逻辑
                data = {
                    'stock_code': stock_code,
                    'stock_name': '',
                    'market_type': market_type,
                    'industry': '',
                    'sector': '',
                    'list_date': '',
                    'total_share': 0,
                    'float_share': 0,
                    'market_cap': 0,
                    'pe_ratio': 0,
                    'pb_ratio': 0
                }
            
            # 4. 保存到数据库缓存
            if USE_DATABASE:
                try:
                    session = get_session()
                    
                    # 删除旧记录
                    session.query(StockBasicInfo).filter(
                        StockBasicInfo.stock_code == stock_code,
                        StockBasicInfo.market_type == market_type
                    ).delete()
                    
                    # 插入新记录
                    expires_at = datetime.now() + timedelta(seconds=BASIC_INFO_TTL)
                    db_record = StockBasicInfo(
                        stock_code=stock_code,
                        stock_name=data['stock_name'],
                        market_type=market_type,
                        industry=data['industry'],
                        sector=data['sector'],
                        list_date=data['list_date'],
                        total_share=data['total_share'],
                        float_share=data['float_share'],
                        market_cap=data['market_cap'],
                        pe_ratio=data['pe_ratio'],
                        pb_ratio=data['pb_ratio'],
                        expires_at=expires_at
                    )
                    session.add(db_record)
                    session.commit()
                    session.close()
                except Exception as e:
                    self.logger.error(f"保存基本信息到数据库失败: {e}")
            
            # 5. 保存到内存缓存
            self._set_memory_cache(cache_key, data)
            return data
            
        except Exception as e:
            self.logger.error(f"获取股票基本信息失败: {e}")
            return None
    
    def _safe_float(self, value) -> float:
        """安全转换为浮点数"""
        try:
            if isinstance(value, str):
                # 移除可能的单位和特殊字符
                value = value.replace('万', '').replace('亿', '').replace('%', '').replace(',', '')
            return float(value) if value else 0.0
        except:
            return 0.0
    
    def get_cache_statistics(self) -> Dict:
        """获取缓存统计信息"""
        stats = {
            'database_enabled': USE_DATABASE,
            'memory_cache_size': len(memory_cache)
        }
        
        if USE_DATABASE:
            db_stats = get_cache_stats()
            stats.update(db_stats)
        
        return stats


    def get_stock_price_history(self, stock_code: str, market_type: str = 'A',
                               start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """获取股票历史价格数据"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        cache_key = self._get_cache_key('price_history', stock_code=stock_code,
                                       market_type=market_type, start_date=start_date, end_date=end_date)

        # 1. 检查内存缓存
        cached_data = self._check_memory_cache(cache_key, 3600)  # 1小时缓存
        if cached_data is not None:
            return cached_data

        # 2. 检查数据库缓存
        if USE_DATABASE:
            try:
                session = get_session()
                db_records = session.query(StockPriceHistory).filter(
                    StockPriceHistory.stock_code == stock_code,
                    StockPriceHistory.market_type == market_type,
                    StockPriceHistory.trade_date >= start_date.replace('-', ''),
                    StockPriceHistory.trade_date <= end_date.replace('-', '')
                ).order_by(StockPriceHistory.trade_date).all()

                if db_records:
                    # 转换为DataFrame
                    data_list = [record.to_dict() for record in db_records]
                    df = pd.DataFrame(data_list)
                    df['date'] = pd.to_datetime(df['trade_date'])
                    df = df.drop('trade_date', axis=1)
                    session.close()
                    self._set_memory_cache(cache_key, df)
                    return df

                session.close()
            except Exception as e:
                self.logger.error(f"数据库查询历史价格失败: {e}")

        # 3. 从API获取新数据
        try:
            self.logger.info(f"从API获取股票 {stock_code} 历史价格数据")

            def fetch_price_data():
                if market_type == 'A':
                    return ak.stock_zh_a_hist(
                        symbol=stock_code,
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust="qfq"
                    )
                elif market_type == 'HK':
                    return ak.stock_hk_daily(symbol=stock_code, adjust="qfq")
                elif market_type == 'US':
                    return ak.stock_us_hist(
                        symbol=stock_code,
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust="qfq"
                    )
                else:
                    raise ValueError(f"不支持的市场类型: {market_type}")

            df = self._retry_api_call(fetch_price_data)

            if df is None or len(df) == 0:
                raise Exception("获取到的数据为空")

            # 重命名列名
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount"
            })

            # 确保日期格式正确
            df['date'] = pd.to_datetime(df['date'])

            # 数据类型转换
            numeric_columns = ['open', 'close', 'high', 'low', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 删除空值
            df = df.dropna()
            df = df.sort_values('date')

            # 4. 保存到数据库缓存
            if USE_DATABASE:
                try:
                    session = get_session()

                    for _, row in df.iterrows():
                        trade_date = row['date'].strftime('%Y-%m-%d')

                        # 检查是否已存在
                        existing = session.query(StockPriceHistory).filter(
                            StockPriceHistory.stock_code == stock_code,
                            StockPriceHistory.market_type == market_type,
                            StockPriceHistory.trade_date == trade_date.replace('-', '')
                        ).first()

                        if not existing:
                            db_record = StockPriceHistory(
                                stock_code=stock_code,
                                market_type=market_type,
                                trade_date=trade_date.replace('-', ''),
                                open_price=row['open'],
                                close_price=row['close'],
                                high_price=row['high'],
                                low_price=row['low'],
                                volume=row['volume'],
                                amount=row.get('amount', 0),
                                change_pct=row.get('change_pct', 0)
                            )
                            session.add(db_record)

                    session.commit()
                    session.close()
                except Exception as e:
                    self.logger.error(f"保存历史价格到数据库失败: {e}")

            # 5. 保存到内存缓存
            self._set_memory_cache(cache_key, df)
            return df

        except Exception as e:
            self.logger.error(f"获取股票历史价格失败: {e}")
            return None

    def get_stock_realtime_data(self, stock_code: str, market_type: str = 'A') -> Optional[Dict]:
        """获取股票实时数据"""
        cache_key = self._get_cache_key('realtime_data', stock_code=stock_code, market_type=market_type)

        # 1. 检查内存缓存
        cached_data = self._check_memory_cache(cache_key, REALTIME_DATA_TTL)
        if cached_data:
            return cached_data

        # 2. 检查数据库缓存
        if USE_DATABASE:
            try:
                session = get_session()
                db_record = session.query(StockRealtimeData).filter(
                    StockRealtimeData.stock_code == stock_code,
                    StockRealtimeData.market_type == market_type
                ).first()

                if db_record and not db_record.is_expired():
                    data = db_record.to_dict()
                    session.close()
                    self._set_memory_cache(cache_key, data)
                    return data

                session.close()
            except Exception as e:
                self.logger.error(f"数据库查询实时数据失败: {e}")

        # 3. 从API获取新数据
        try:
            self.logger.info(f"从API获取股票 {stock_code} 实时数据")

            # 这里可以根据需要调用相应的实时数据API
            # 暂时返回基础结构
            data = {
                'stock_code': stock_code,
                'market_type': market_type,
                'current_price': 0.0,
                'change_amount': 0.0,
                'change_pct': 0.0,
                'volume': 0.0,
                'amount': 0.0,
                'turnover_rate': 0.0,
                'pe_ratio': 0.0,
                'pb_ratio': 0.0,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # 4. 保存到数据库缓存
            if USE_DATABASE:
                try:
                    session = get_session()

                    # 删除旧记录
                    session.query(StockRealtimeData).filter(
                        StockRealtimeData.stock_code == stock_code,
                        StockRealtimeData.market_type == market_type
                    ).delete()

                    # 插入新记录
                    expires_at = datetime.now() + timedelta(seconds=REALTIME_DATA_TTL)
                    db_record = StockRealtimeData(
                        stock_code=stock_code,
                        market_type=market_type,
                        current_price=data['current_price'],
                        change_amount=data['change_amount'],
                        change_pct=data['change_pct'],
                        volume=data['volume'],
                        amount=data['amount'],
                        turnover_rate=data['turnover_rate'],
                        pe_ratio=data['pe_ratio'],
                        pb_ratio=data['pb_ratio'],
                        expires_at=expires_at
                    )
                    session.add(db_record)
                    session.commit()
                    session.close()
                except Exception as e:
                    self.logger.error(f"保存实时数据到数据库失败: {e}")

            # 5. 保存到内存缓存
            self._set_memory_cache(cache_key, data)
            return data

        except Exception as e:
            self.logger.error(f"获取股票实时数据失败: {e}")
            return None


# 全局数据服务实例
data_service = DataService()
