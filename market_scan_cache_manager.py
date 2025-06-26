#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
市场扫描专用缓存管理器
针对市场扫描功能的特殊需求，实现智能的缓存时效性管理
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Set
import pandas as pd

from database import StockPriceHistory, USE_DATABASE
from database_optimizer import get_optimized_session
from trading_calendar import trading_calendar, is_trading_day, get_last_trading_day
from smart_cache_manager import smart_cache_manager

logger = logging.getLogger(__name__)

class MarketScanCacheManager:
    """市场扫描专用缓存管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 市场扫描缓存策略配置
        self.cache_config = {
            'market_scan_ttl': 300,  # 5分钟缓存
            'price_data_days': 365,  # 默认获取1年历史数据
            'min_data_days': 60,     # 最少需要60天数据进行技术分析
            'update_threshold_hours': 6,  # 6小时内的数据认为是新鲜的
        }
        
    def should_update_for_market_scan(self, stock_code: str, market_type: str = 'A') -> Dict:
        """
        判断股票数据是否需要为市场扫描更新
        
        Args:
            stock_code: 股票代码
            market_type: 市场类型
            
        Returns:
            Dict: {
                'needs_update': bool,
                'reason': str,
                'last_update': str,
                'missing_days': int,
                'data_quality': str
            }
        """
        try:
            result = {
                'needs_update': False,
                'reason': '数据充足',
                'last_update': None,
                'missing_days': 0,
                'data_quality': 'good'
            }
            
            # 1. 检查当前是否为交易时间
            current_time = datetime.now()
            is_trading_time = trading_calendar.is_market_open_time(current_time)
            is_trading_day_today = is_trading_day(current_time.date())
            
            # 2. 获取数据完整性信息
            end_date = current_time.strftime('%Y-%m-%d')
            start_date = (current_time - timedelta(days=self.cache_config['price_data_days'])).strftime('%Y-%m-%d')
            
            completeness = smart_cache_manager.check_price_data_completeness(
                stock_code, start_date, end_date, market_type
            )
            
            # 3. 如果没有任何数据，必须更新
            if not completeness['has_data']:
                result.update({
                    'needs_update': True,
                    'reason': '无历史数据',
                    'data_quality': 'none'
                })
                return result
            
            # 4. 检查数据的最新日期
            latest_date_str = completeness['latest_date']
            if latest_date_str:
                latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d').date()
                result['last_update'] = latest_date_str
                
                # 获取最后一个交易日
                last_trading_day = get_last_trading_day()
                
                # 计算数据滞后天数
                days_behind = (last_trading_day - latest_date).days
                result['missing_days'] = days_behind
                
                # 5. 判断数据质量和更新需求
                if days_behind > 5:
                    result.update({
                        'needs_update': True,
                        'reason': f'数据滞后{days_behind}个交易日',
                        'data_quality': 'stale'
                    })
                elif days_behind > 2:
                    result.update({
                        'needs_update': True,
                        'reason': f'数据滞后{days_behind}个交易日',
                        'data_quality': 'outdated'
                    })
                elif days_behind > 0:
                    # 如果是交易日且在交易时间，需要更新
                    if is_trading_day_today and is_trading_time:
                        result.update({
                            'needs_update': True,
                            'reason': '交易时间内需要最新数据',
                            'data_quality': 'acceptable'
                        })
                    # 如果是交易日但非交易时间，检查是否有当日数据
                    elif is_trading_day_today:
                        result.update({
                            'needs_update': True,
                            'reason': '缺少当日交易数据',
                            'data_quality': 'acceptable'
                        })
                
                # 6. 检查数据量是否足够进行技术分析
                if completeness['cached_data'] is not None:
                    data_days = len(completeness['cached_data'])
                    if data_days < self.cache_config['min_data_days']:
                        result.update({
                            'needs_update': True,
                            'reason': f'数据量不足({data_days}天，需要至少{self.cache_config["min_data_days"]}天)',
                            'data_quality': 'insufficient'
                        })
            
            self.logger.debug(f"股票 {stock_code} 市场扫描缓存检查: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"检查市场扫描缓存需求失败: {e}")
            return {
                'needs_update': True,
                'reason': f'检查失败: {str(e)}',
                'last_update': None,
                'missing_days': 0,
                'data_quality': 'unknown'
            }
    
    def batch_check_market_scan_cache(self, stock_codes: List[str], 
                                    market_type: str = 'A') -> Dict[str, Dict]:
        """
        批量检查多只股票的市场扫描缓存状态
        
        Args:
            stock_codes: 股票代码列表
            market_type: 市场类型
            
        Returns:
            Dict: {stock_code: cache_status}
        """
        results = {}
        
        self.logger.info(f"批量检查 {len(stock_codes)} 只股票的市场扫描缓存状态")
        
        for stock_code in stock_codes:
            try:
                results[stock_code] = self.should_update_for_market_scan(stock_code, market_type)
            except Exception as e:
                self.logger.error(f"检查股票 {stock_code} 缓存状态失败: {e}")
                results[stock_code] = {
                    'needs_update': True,
                    'reason': f'检查失败: {str(e)}',
                    'last_update': None,
                    'missing_days': 0,
                    'data_quality': 'error'
                }
        
        # 统计结果
        needs_update = sum(1 for r in results.values() if r['needs_update'])
        self.logger.info(f"批量检查完成: {needs_update}/{len(stock_codes)} 只股票需要更新")
        
        return results
    
    def get_market_scan_priority_list(self, stock_codes: List[str], 
                                    market_type: str = 'A') -> Dict[str, List[str]]:
        """
        根据缓存状态对股票进行优先级分组
        
        Args:
            stock_codes: 股票代码列表
            market_type: 市场类型
            
        Returns:
            Dict: {
                'no_data': [],      # 无数据，最高优先级
                'stale': [],        # 数据过时，高优先级
                'outdated': [],     # 数据滞后，中优先级
                'acceptable': [],   # 数据可接受，低优先级
                'good': []          # 数据良好，无需更新
            }
        """
        cache_status = self.batch_check_market_scan_cache(stock_codes, market_type)
        
        priority_groups = {
            'no_data': [],
            'stale': [],
            'outdated': [],
            'acceptable': [],
            'good': []
        }
        
        for stock_code, status in cache_status.items():
            quality = status['data_quality']
            if quality == 'none':
                priority_groups['no_data'].append(stock_code)
            elif quality == 'stale':
                priority_groups['stale'].append(stock_code)
            elif quality == 'outdated':
                priority_groups['outdated'].append(stock_code)
            elif quality == 'acceptable':
                priority_groups['acceptable'].append(stock_code)
            else:
                priority_groups['good'].append(stock_code)
        
        self.logger.info(f"优先级分组: 无数据={len(priority_groups['no_data'])}, "
                        f"过时={len(priority_groups['stale'])}, "
                        f"滞后={len(priority_groups['outdated'])}, "
                        f"可接受={len(priority_groups['acceptable'])}, "
                        f"良好={len(priority_groups['good'])}")
        
        return priority_groups
    
    def estimate_update_time(self, stock_codes: List[str], market_type: str = 'A') -> Dict:
        """
        估算市场扫描数据更新所需时间
        
        Args:
            stock_codes: 股票代码列表
            market_type: 市场类型
            
        Returns:
            Dict: 时间估算信息
        """
        priority_groups = self.get_market_scan_priority_list(stock_codes, market_type)
        
        # 估算每种操作的时间（秒）
        time_estimates = {
            'full_fetch': 3,      # 全量获取
            'incremental': 1.5,   # 增量更新
            'cache_hit': 0.1,     # 缓存命中
            'analysis': 2         # 技术分析
        }
        
        total_time = 0
        details = {}
        
        # 无数据股票需要全量获取
        no_data_count = len(priority_groups['no_data'])
        no_data_time = no_data_count * (time_estimates['full_fetch'] + time_estimates['analysis'])
        total_time += no_data_time
        details['no_data'] = {'count': no_data_count, 'time': no_data_time}
        
        # 过时和滞后数据需要增量更新
        update_count = len(priority_groups['stale']) + len(priority_groups['outdated']) + len(priority_groups['acceptable'])
        update_time = update_count * (time_estimates['incremental'] + time_estimates['analysis'])
        total_time += update_time
        details['incremental'] = {'count': update_count, 'time': update_time}
        
        # 良好数据直接使用缓存
        cache_count = len(priority_groups['good'])
        cache_time = cache_count * (time_estimates['cache_hit'] + time_estimates['analysis'])
        total_time += cache_time
        details['cache_hit'] = {'count': cache_count, 'time': cache_time}
        
        return {
            'total_stocks': len(stock_codes),
            'estimated_total_time': total_time,
            'estimated_minutes': total_time / 60,
            'details': details,
            'priority_groups': priority_groups
        }


# 创建全局实例
market_scan_cache_manager = MarketScanCacheManager()
