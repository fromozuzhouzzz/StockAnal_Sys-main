#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能降级策略
专门处理AKShare API不可用时的数据获取降级方案
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from optimized_cache_strategy import optimized_cache
from data_service import data_service
from trading_calendar import trading_calendar

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """数据源枚举"""
    API_FRESH = "api_fresh"          # 新鲜API数据
    CACHE_FRESH = "cache_fresh"      # 新鲜缓存数据
    CACHE_STALE = "cache_stale"      # 过期缓存数据
    FALLBACK = "fallback"            # 降级数据
    UNAVAILABLE = "unavailable"      # 数据不可用

class IntelligentFallbackStrategy:
    """智能降级策略"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 降级策略配置
        self.api_timeout = 10  # API超时时间（秒）
        self.max_api_failures = 3  # 最大API失败次数
        self.fallback_cache_age_limit = timedelta(days=7)  # 降级缓存数据最大年龄
        
        # API健康状态跟踪
        self.api_health = {
            'consecutive_failures': 0,
            'last_success_time': None,
            'last_failure_time': None,
            'is_degraded': False
        }
        
        # 性能统计
        self.stats = {
            'api_calls': 0,
            'api_successes': 0,
            'api_failures': 0,
            'cache_hits': 0,
            'fallback_uses': 0
        }
    
    def get_stock_data_with_fallback(self, stock_code: str, market_type: str = 'A') -> Tuple[Dict[str, Any], DataSource]:
        """
        使用智能降级策略获取股票数据
        
        Args:
            stock_code: 股票代码
            market_type: 市场类型
            
        Returns:
            Tuple[Dict, DataSource]: (数据, 数据源)
        """
        try:
            # 1. 检查API健康状态
            if self._should_skip_api():
                self.logger.info(f"API处于降级状态，直接使用缓存数据: {stock_code}")
                return self._get_cached_data_with_fallback(stock_code, market_type)
            
            # 2. 尝试获取新鲜API数据
            try:
                api_data = self._get_fresh_api_data(stock_code, market_type)
                if api_data:
                    self._record_api_success()
                    return api_data, DataSource.API_FRESH
            except Exception as e:
                self.logger.warning(f"API调用失败 {stock_code}: {e}")
                self._record_api_failure()
            
            # 3. API失败，使用缓存降级
            return self._get_cached_data_with_fallback(stock_code, market_type)
            
        except Exception as e:
            self.logger.error(f"获取股票数据异常 {stock_code}: {e}")
            return self._generate_fallback_data(stock_code), DataSource.FALLBACK
    
    def batch_get_stock_data_with_fallback(self, stock_codes: List[str], market_type: str = 'A') -> Dict[str, Tuple[Dict[str, Any], DataSource]]:
        """
        批量获取股票数据，使用智能降级策略
        
        Args:
            stock_codes: 股票代码列表
            market_type: 市场类型
            
        Returns:
            Dict: 股票代码到(数据, 数据源)的映射
        """
        result = {}
        
        try:
            # 1. 首先尝试批量获取缓存数据
            cached_data = optimized_cache.batch_get_stock_data(stock_codes, market_type)
            
            # 2. 分析缓存数据的新鲜度
            fresh_cached = {}
            stale_cached = {}
            missing_codes = []
            
            for code in stock_codes:
                if code in cached_data:
                    cache_age = self._calculate_cache_age(cached_data[code])
                    if cache_age < timedelta(hours=1):  # 1小时内的数据认为是新鲜的
                        fresh_cached[code] = cached_data[code]
                    else:
                        stale_cached[code] = cached_data[code]
                else:
                    missing_codes.append(code)
            
            # 3. 处理新鲜缓存数据
            for code, data in fresh_cached.items():
                result[code] = (self._format_cached_data(data), DataSource.CACHE_FRESH)
                self.stats['cache_hits'] += 1
            
            # 4. 处理需要API更新的股票
            codes_need_api = list(stale_cached.keys()) + missing_codes
            
            if codes_need_api and not self._should_skip_api():
                # 尝试API更新（限制并发数）
                api_results = self._batch_api_update(codes_need_api[:10], market_type)  # 限制最多10只
                
                for code in codes_need_api:
                    if code in api_results:
                        result[code] = (api_results[code], DataSource.API_FRESH)
                    elif code in stale_cached:
                        # API失败，使用过期缓存
                        result[code] = (self._format_cached_data(stale_cached[code]), DataSource.CACHE_STALE)
                        self.stats['fallback_uses'] += 1
                    else:
                        # 生成降级数据
                        result[code] = (self._generate_fallback_data(code), DataSource.FALLBACK)
                        self.stats['fallback_uses'] += 1
            else:
                # API不可用，使用现有缓存或生成降级数据
                for code in codes_need_api:
                    if code in stale_cached:
                        result[code] = (self._format_cached_data(stale_cached[code]), DataSource.CACHE_STALE)
                    else:
                        result[code] = (self._generate_fallback_data(code), DataSource.FALLBACK)
                    self.stats['fallback_uses'] += 1
            
            self.logger.info(f"批量获取完成: 新鲜缓存 {len(fresh_cached)}, API更新 {len([r for r in result.values() if r[1] == DataSource.API_FRESH])}, 降级 {len([r for r in result.values() if r[1] in [DataSource.CACHE_STALE, DataSource.FALLBACK]])}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"批量获取股票数据异常: {e}")
            # 全部使用降级数据
            return {code: (self._generate_fallback_data(code), DataSource.FALLBACK) for code in stock_codes}
    
    def _should_skip_api(self) -> bool:
        """判断是否应该跳过API调用"""
        # 如果连续失败次数过多，进入降级模式
        if self.api_health['consecutive_failures'] >= self.max_api_failures:
            # 检查是否应该尝试恢复
            if self.api_health['last_failure_time']:
                time_since_failure = datetime.now() - self.api_health['last_failure_time']
                # 5分钟后尝试恢复
                if time_since_failure > timedelta(minutes=5):
                    self.logger.info("尝试从API降级模式恢复")
                    self.api_health['consecutive_failures'] = 0
                    self.api_health['is_degraded'] = False
                    return False
                else:
                    return True
            return True
        
        return False
    
    def _get_fresh_api_data(self, stock_code: str, market_type: str) -> Optional[Dict[str, Any]]:
        """获取新鲜的API数据"""
        try:
            self.stats['api_calls'] += 1
            
            # 设置超时限制
            start_time = time.time()
            
            # 获取基本信息
            basic_info = data_service.get_stock_basic_info(stock_code, market_type, use_advanced_cache=False)
            
            # 检查超时
            if time.time() - start_time > self.api_timeout:
                raise TimeoutError(f"API调用超时: {stock_code}")
            
            # 获取实时数据
            realtime_data = data_service.get_stock_realtime_data(stock_code)
            
            if basic_info or realtime_data:
                return {
                    'stock_code': stock_code,
                    'stock_name': basic_info.get('股票名称', '未知') if basic_info else '未知',
                    'industry': basic_info.get('行业', '未知') if basic_info else '未知',
                    'price': realtime_data.get('current_price', 0) if realtime_data else 0,
                    'price_change': realtime_data.get('change_pct', 0) if realtime_data else 0,
                    'volume': realtime_data.get('volume', 0) if realtime_data else 0,
                    'data_source': 'api_fresh',
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取新鲜API数据失败 {stock_code}: {e}")
            raise
    
    def _get_cached_data_with_fallback(self, stock_code: str, market_type: str) -> Tuple[Dict[str, Any], DataSource]:
        """获取缓存数据，带降级处理"""
        try:
            # 获取缓存数据
            cached_data = optimized_cache.batch_get_stock_data([stock_code], market_type)
            
            if stock_code in cached_data:
                cache_age = self._calculate_cache_age(cached_data[stock_code])
                
                if cache_age < self.fallback_cache_age_limit:
                    # 缓存数据可用
                    data_source = DataSource.CACHE_FRESH if cache_age < timedelta(hours=1) else DataSource.CACHE_STALE
                    return self._format_cached_data(cached_data[stock_code]), data_source
            
            # 缓存不可用，生成降级数据
            return self._generate_fallback_data(stock_code), DataSource.FALLBACK
            
        except Exception as e:
            self.logger.error(f"获取缓存数据失败 {stock_code}: {e}")
            return self._generate_fallback_data(stock_code), DataSource.FALLBACK
    
    def _batch_api_update(self, stock_codes: List[str], market_type: str) -> Dict[str, Dict[str, Any]]:
        """批量API更新（限制并发）"""
        result = {}
        
        for code in stock_codes:
            try:
                api_data = self._get_fresh_api_data(code, market_type)
                if api_data:
                    result[code] = api_data
                    self._record_api_success()
                else:
                    self._record_api_failure()
            except Exception as e:
                self.logger.warning(f"批量API更新失败 {code}: {e}")
                self._record_api_failure()
                # 继续处理下一只股票
                continue
        
        return result
    
    def _calculate_cache_age(self, cached_data: Dict[str, Any]) -> timedelta:
        """计算缓存数据年龄"""
        try:
            timestamp_str = cached_data.get('cache_timestamp')
            if timestamp_str:
                cache_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return datetime.now() - cache_time.replace(tzinfo=None)
            
            # 如果没有时间戳，检查实时数据的更新时间
            realtime_data = cached_data.get('realtime_data', {})
            updated_at = realtime_data.get('updated_at')
            if updated_at:
                update_time = datetime.fromisoformat(updated_at)
                return datetime.now() - update_time
            
            # 默认认为很旧
            return timedelta(days=1)
            
        except Exception as e:
            self.logger.warning(f"计算缓存年龄失败: {e}")
            return timedelta(days=1)
    
    def _format_cached_data(self, cached_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化缓存数据"""
        basic_info = cached_data.get('basic_info', {})
        realtime_data = cached_data.get('realtime_data', {})
        
        return {
            'stock_code': cached_data.get('stock_code', ''),
            'stock_name': basic_info.get('stock_name', '未知'),
            'industry': basic_info.get('industry', '未知'),
            'price': realtime_data.get('current_price', 0),
            'price_change': realtime_data.get('change_pct', 0),
            'volume': realtime_data.get('volume', 0),
            'data_source': 'cache',
            'timestamp': cached_data.get('cache_timestamp', datetime.now().isoformat())
        }
    
    def _generate_fallback_data(self, stock_code: str) -> Dict[str, Any]:
        """生成降级数据"""
        return {
            'stock_code': stock_code,
            'stock_name': f'股票{stock_code}',
            'industry': '未知',
            'price': 0,
            'price_change': 0,
            'volume': 0,
            'data_source': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'fallback_reason': 'API不可用且无缓存数据'
        }
    
    def _record_api_success(self):
        """记录API成功"""
        self.api_health['consecutive_failures'] = 0
        self.api_health['last_success_time'] = datetime.now()
        self.api_health['is_degraded'] = False
        self.stats['api_successes'] += 1
    
    def _record_api_failure(self):
        """记录API失败"""
        self.api_health['consecutive_failures'] += 1
        self.api_health['last_failure_time'] = datetime.now()
        self.stats['api_failures'] += 1
        
        if self.api_health['consecutive_failures'] >= self.max_api_failures:
            self.api_health['is_degraded'] = True
            self.logger.warning(f"API进入降级模式，连续失败 {self.api_health['consecutive_failures']} 次")
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        total_calls = self.stats['api_calls']
        success_rate = (self.stats['api_successes'] / total_calls * 100) if total_calls > 0 else 0
        
        return {
            'api_health': self.api_health.copy(),
            'success_rate': round(success_rate, 2),
            'stats': self.stats.copy(),
            'is_degraded': self.api_health['is_degraded']
        }
    
    def reset_health_status(self):
        """重置健康状态"""
        self.api_health = {
            'consecutive_failures': 0,
            'last_success_time': None,
            'last_failure_time': None,
            'is_degraded': False
        }
        self.stats = {
            'api_calls': 0,
            'api_successes': 0,
            'api_failures': 0,
            'cache_hits': 0,
            'fallback_uses': 0
        }
        self.logger.info("API健康状态已重置")

# 全局实例
intelligent_fallback = IntelligentFallbackStrategy()
