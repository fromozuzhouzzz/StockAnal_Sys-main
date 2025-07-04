# -*- coding: utf-8 -*-
"""
数据源备选方案
实现多个数据源的备选机制，确保在主要数据源不可用时仍能提供服务
"""

import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import random

logger = logging.getLogger(__name__)

class DataSourceFallback:
    """数据源备选管理器"""
    
    def __init__(self):
        self.data_sources = [
            'akshare_api',      # AKShare API
            'cached_data',      # 缓存数据
            'mock_data',        # 模拟数据
            'static_data'       # 静态数据
        ]
        self.current_source = 0
        self.failure_counts = {source: 0 for source in self.data_sources}
        self.last_success = {source: 0 for source in self.data_sources}
        
        # 初始化静态数据
        self.static_stock_data = self._load_static_data()
        
    def get_stock_data(self, stock_code: str, data_type: str = 'basic') -> Optional[Dict[str, Any]]:
        """获取股票数据，使用备选策略"""
        
        for source in self.data_sources:
            try:
                logger.info(f"尝试从 {source} 获取股票 {stock_code} 的数据")
                
                if source == 'akshare_api':
                    data = self._get_akshare_data(stock_code, data_type)
                elif source == 'cached_data':
                    data = self._get_cached_data(stock_code, data_type)
                elif source == 'mock_data':
                    data = self._get_mock_data(stock_code, data_type)
                else:  # static_data
                    data = self._get_static_data(stock_code, data_type)
                
                if data:
                    # 成功获取数据
                    self.failure_counts[source] = 0
                    self.last_success[source] = time.time()
                    
                    # 添加数据源信息
                    data['data_source'] = {
                        'source': source,
                        'timestamp': datetime.now().isoformat(),
                        'is_fallback': source != 'akshare_api'
                    }
                    
                    logger.info(f"成功从 {source} 获取股票 {stock_code} 的数据")
                    return data
                    
            except Exception as e:
                logger.warning(f"从 {source} 获取数据失败: {e}")
                self.failure_counts[source] += 1
                continue
        
        # 所有数据源都失败
        logger.error(f"所有数据源都无法获取股票 {stock_code} 的数据")
        return None
    
    def _get_akshare_data(self, stock_code: str, data_type: str) -> Optional[Dict[str, Any]]:
        """从AKShare API获取数据"""
        try:
            import akshare as ak
            
            # 标准化股票代码
            normalized_code = self._normalize_stock_code(stock_code)
            
            if data_type == 'basic':
                # 获取基本信息
                stock_info = ak.stock_individual_info_em(symbol=normalized_code)
                if stock_info is not None and not stock_info.empty:
                    return {
                        'stock_code': stock_code,
                        'stock_name': stock_info.iloc[0]['value'] if len(stock_info) > 0 else '未知',
                        'industry': '未知',
                        'price': 0,
                        'change': 0,
                        'volume': 0,
                        'market_cap': 0
                    }
            elif data_type == 'realtime':
                # 获取实时数据
                realtime_data = ak.stock_zh_a_spot_em()
                if realtime_data is not None and not realtime_data.empty:
                    stock_data = realtime_data[realtime_data['代码'] == normalized_code]
                    if not stock_data.empty:
                        row = stock_data.iloc[0]
                        return {
                            'stock_code': stock_code,
                            'stock_name': row.get('名称', '未知'),
                            'price': row.get('最新价', 0),
                            'change': row.get('涨跌幅', 0),
                            'volume': row.get('成交量', 0),
                            'turnover': row.get('成交额', 0)
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"AKShare API调用失败: {e}")
            raise
    
    def _get_cached_data(self, stock_code: str, data_type: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        try:
            # 尝试从文件缓存读取
            cache_file = f"cache/stock_{stock_code}_{data_type}.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # 检查缓存是否过期（1小时）
                cache_time = datetime.fromisoformat(cached_data.get('timestamp', '2000-01-01'))
                if datetime.now() - cache_time < timedelta(hours=1):
                    logger.info(f"使用缓存数据: {stock_code}")
                    return cached_data.get('data')
            
            return None
            
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
    
    def _get_mock_data(self, stock_code: str, data_type: str) -> Dict[str, Any]:
        """生成模拟数据"""
        # 基于股票代码生成确定性的模拟数据
        seed = hash(stock_code) % 10000
        random.seed(seed)
        
        base_price = 10 + (seed % 100)
        price_change = random.uniform(-10, 10)
        
        mock_data = {
            'stock_code': stock_code,
            'stock_name': f'模拟股票{stock_code[-4:]}',
            'industry': random.choice(['科技', '金融', '制造业', '医药', '消费', '能源']),
            'price': round(base_price + price_change, 2),
            'change': round(price_change, 2),
            'change_percent': round(price_change / base_price * 100, 2),
            'volume': random.randint(1000000, 100000000),
            'turnover': random.randint(10000000, 1000000000),
            'market_cap': random.randint(1000000000, 100000000000),
            'pe_ratio': round(random.uniform(5, 50), 2),
            'pb_ratio': round(random.uniform(0.5, 5), 2),
            'roe': round(random.uniform(0, 30), 2),
            'debt_ratio': round(random.uniform(10, 80), 2)
        }
        
        if data_type == 'historical':
            # 生成历史数据
            mock_data['historical_data'] = self._generate_historical_data(base_price, 30)
        
        return mock_data
    
    def _get_static_data(self, stock_code: str, data_type: str) -> Dict[str, Any]:
        """获取静态数据"""
        # 从预定义的静态数据中获取
        if stock_code in self.static_stock_data:
            return self.static_stock_data[stock_code].copy()
        
        # 如果没有预定义数据，返回基础静态数据
        return {
            'stock_code': stock_code,
            'stock_name': f'股票{stock_code[-4:]}',
            'industry': '未知',
            'price': 10.0,
            'change': 0.0,
            'change_percent': 0.0,
            'volume': 1000000,
            'turnover': 10000000,
            'market_cap': 1000000000,
            'pe_ratio': 15.0,
            'pb_ratio': 1.5,
            'roe': 10.0,
            'debt_ratio': 30.0
        }
    
    def _load_static_data(self) -> Dict[str, Dict[str, Any]]:
        """加载静态股票数据"""
        # 预定义一些常见股票的静态数据
        static_data = {
            '603316.SH': {
                'stock_code': '603316.SH',
                'stock_name': '诚邦股份',
                'industry': '建筑装饰',
                'price': 12.50,
                'change': 0.15,
                'change_percent': 1.22,
                'volume': 2500000,
                'turnover': 31250000,
                'market_cap': 2000000000,
                'pe_ratio': 18.5,
                'pb_ratio': 2.1,
                'roe': 8.5,
                'debt_ratio': 45.2
            },
            '601218.SH': {
                'stock_code': '601218.SH',
                'stock_name': '吉鑫科技',
                'industry': '电力设备',
                'price': 8.90,
                'change': -0.08,
                'change_percent': -0.89,
                'volume': 1800000,
                'turnover': 16020000,
                'market_cap': 1500000000,
                'pe_ratio': 22.3,
                'pb_ratio': 1.8,
                'roe': 6.2,
                'debt_ratio': 38.7
            },
            '000001.SZ': {
                'stock_code': '000001.SZ',
                'stock_name': '平安银行',
                'industry': '银行',
                'price': 15.20,
                'change': 0.25,
                'change_percent': 1.67,
                'volume': 50000000,
                'turnover': 760000000,
                'market_cap': 300000000000,
                'pe_ratio': 6.8,
                'pb_ratio': 0.9,
                'roe': 12.5,
                'debt_ratio': 85.2
            }
        }
        
        return static_data
    
    def _normalize_stock_code(self, stock_code: str) -> str:
        """标准化股票代码"""
        if '.' in stock_code:
            code, suffix = stock_code.split('.')
            if suffix in ['SH', 'XSHG']:
                return code
            elif suffix in ['SZ', 'XSHE']:
                return code
        return stock_code
    
    def _generate_historical_data(self, base_price: float, days: int) -> List[Dict[str, Any]]:
        """生成历史数据"""
        historical_data = []
        current_price = base_price
        
        for i in range(days):
            # 生成随机价格变动
            change = random.uniform(-0.1, 0.1) * current_price
            current_price = max(0.1, current_price + change)
            
            date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
            
            historical_data.append({
                'date': date,
                'open': round(current_price * random.uniform(0.98, 1.02), 2),
                'high': round(current_price * random.uniform(1.0, 1.05), 2),
                'low': round(current_price * random.uniform(0.95, 1.0), 2),
                'close': round(current_price, 2),
                'volume': random.randint(1000000, 10000000)
            })
        
        return historical_data
    
    def save_to_cache(self, stock_code: str, data_type: str, data: Dict[str, Any]):
        """保存数据到缓存"""
        try:
            os.makedirs('cache', exist_ok=True)
            cache_file = f"cache/stock_{stock_code}_{data_type}.json"
            
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"数据已缓存: {cache_file}")
            
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")
    
    def get_source_status(self) -> Dict[str, Any]:
        """获取数据源状态"""
        return {
            'available_sources': self.data_sources,
            'current_source': self.data_sources[self.current_source],
            'failure_counts': self.failure_counts,
            'last_success_times': {
                source: time.time() - timestamp if timestamp > 0 else -1
                for source, timestamp in self.last_success.items()
            }
        }

# 全局实例
data_source_fallback = DataSourceFallback()
