#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
交易日历工具
用于判断A股市场的交易日，支持节假日和特殊休市日的识别
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Set, Optional
import akshare as ak

logger = logging.getLogger(__name__)

class TradingCalendar:
    """A股交易日历管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._trading_days_cache = {}  # 缓存交易日数据
        self._cache_expiry = {}  # 缓存过期时间
        
        # 固定节假日（每年相同的日期）
        self.fixed_holidays = {
            (1, 1): "元旦",
            (5, 1): "劳动节", 
            (10, 1): "国庆节",
            (10, 2): "国庆节",
            (10, 3): "国庆节"
        }
        
        # 2024年特殊休市安排（示例，实际应从官方获取）
        self.special_holidays_2024 = {
            # 春节
            "2024-02-09", "2024-02-10", "2024-02-11", "2024-02-12", 
            "2024-02-13", "2024-02-14", "2024-02-15", "2024-02-16", "2024-02-17",
            # 清明节
            "2024-04-04", "2024-04-05", "2024-04-06",
            # 端午节
            "2024-06-10",
            # 中秋节
            "2024-09-15", "2024-09-16", "2024-09-17"
        }
        
    def is_trading_day(self, check_date: Optional[date] = None) -> bool:
        """
        判断指定日期是否为交易日
        
        Args:
            check_date: 要检查的日期，默认为今天
            
        Returns:
            bool: True表示是交易日，False表示非交易日
        """
        if check_date is None:
            check_date = date.today()
        elif isinstance(check_date, str):
            check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        elif isinstance(check_date, datetime):
            check_date = check_date.date()
            
        # 1. 检查是否为周末
        if check_date.weekday() >= 5:  # 周六=5, 周日=6
            return False
            
        # 2. 检查是否为固定节假日
        month_day = (check_date.month, check_date.day)
        if month_day in self.fixed_holidays:
            self.logger.debug(f"{check_date} 是{self.fixed_holidays[month_day]}，非交易日")
            return False
            
        # 3. 检查是否为特殊节假日
        date_str = check_date.strftime('%Y-%m-%d')
        if date_str in self.special_holidays_2024:
            self.logger.debug(f"{check_date} 是特殊节假日，非交易日")
            return False
            
        # 4. 尝试从AKShare获取官方交易日历（带缓存）
        try:
            if self._is_trading_day_from_akshare(check_date):
                return True
        except Exception as e:
            self.logger.warning(f"无法从AKShare获取交易日历: {e}")
            
        # 5. 默认认为是交易日（工作日且不在已知节假日列表中）
        return True
        
    def _is_trading_day_from_akshare(self, check_date: date) -> bool:
        """从AKShare获取官方交易日历"""
        year = check_date.year
        cache_key = f"trading_days_{year}"
        
        # 检查缓存
        if cache_key in self._trading_days_cache:
            cache_time = self._cache_expiry.get(cache_key)
            if cache_time and datetime.now() < cache_time:
                trading_days = self._trading_days_cache[cache_key]
                return check_date.strftime('%Y-%m-%d') in trading_days
                
        # 从API获取交易日历
        try:
            # 尝试获取A股交易日历（使用工具日历接口）
            df = ak.tool_trade_date_hist_sina()
            if df is not None and len(df) > 0:
                # 过滤指定年份的数据
                df['trade_date'] = df['trade_date'].astype(str)
                year_data = df[df['trade_date'].str.startswith(str(year))]
                trading_days = set(year_data['trade_date'].tolist())

                # 缓存数据（缓存1天）
                self._trading_days_cache[cache_key] = trading_days
                self._cache_expiry[cache_key] = datetime.now() + timedelta(days=1)

                return check_date.strftime('%Y-%m-%d') in trading_days
                
        except Exception as e:
            self.logger.error(f"获取AKShare交易日历失败: {e}")
            
        return True  # 默认返回True
        
    def get_trading_days_between(self, start_date: date, end_date: date) -> List[date]:
        """
        获取两个日期之间的所有交易日
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[date]: 交易日列表
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if self.is_trading_day(current_date):
                trading_days.append(current_date)
            current_date += timedelta(days=1)
            
        return trading_days
        
    def get_last_trading_day(self, before_date: Optional[date] = None) -> date:
        """
        获取指定日期之前的最后一个交易日
        
        Args:
            before_date: 参考日期，默认为今天
            
        Returns:
            date: 最后一个交易日
        """
        if before_date is None:
            before_date = date.today()
        elif isinstance(before_date, str):
            before_date = datetime.strptime(before_date, '%Y-%m-%d').date()
        elif isinstance(before_date, datetime):
            before_date = before_date.date()
            
        # 从前一天开始往前查找
        check_date = before_date - timedelta(days=1)
        
        # 最多查找30天
        for _ in range(30):
            if self.is_trading_day(check_date):
                return check_date
            check_date -= timedelta(days=1)
            
        # 如果30天内都没有交易日，返回30天前的日期
        self.logger.warning(f"30天内未找到交易日，返回 {check_date}")
        return check_date
        
    def get_next_trading_day(self, after_date: Optional[date] = None) -> date:
        """
        获取指定日期之后的下一个交易日
        
        Args:
            after_date: 参考日期，默认为今天
            
        Returns:
            date: 下一个交易日
        """
        if after_date is None:
            after_date = date.today()
        elif isinstance(after_date, str):
            after_date = datetime.strptime(after_date, '%Y-%m-%d').date()
        elif isinstance(after_date, datetime):
            after_date = after_date.date()
            
        # 从后一天开始往后查找
        check_date = after_date + timedelta(days=1)
        
        # 最多查找30天
        for _ in range(30):
            if self.is_trading_day(check_date):
                return check_date
            check_date += timedelta(days=1)
            
        # 如果30天内都没有交易日，返回30天后的日期
        self.logger.warning(f"30天内未找到交易日，返回 {check_date}")
        return check_date
        
    def is_market_open_time(self, check_time: Optional[datetime] = None) -> bool:
        """
        判断指定时间是否在交易时间内
        A股交易时间：9:30-11:30, 13:00-15:00
        
        Args:
            check_time: 要检查的时间，默认为当前时间
            
        Returns:
            bool: True表示在交易时间内
        """
        if check_time is None:
            check_time = datetime.now()
            
        # 首先检查是否为交易日
        if not self.is_trading_day(check_time.date()):
            return False
            
        # 检查时间段
        time_only = check_time.time()
        
        # 上午交易时间：9:30-11:30
        morning_start = datetime.strptime("09:30", "%H:%M").time()
        morning_end = datetime.strptime("11:30", "%H:%M").time()
        
        # 下午交易时间：13:00-15:00
        afternoon_start = datetime.strptime("13:00", "%H:%M").time()
        afternoon_end = datetime.strptime("15:00", "%H:%M").time()
        
        return (morning_start <= time_only <= morning_end) or \
               (afternoon_start <= time_only <= afternoon_end)


# 创建全局实例
trading_calendar = TradingCalendar()

# 便捷函数
def is_trading_day(check_date: Optional[date] = None) -> bool:
    """判断是否为交易日的便捷函数"""
    return trading_calendar.is_trading_day(check_date)

def get_last_trading_day(before_date: Optional[date] = None) -> date:
    """获取最后交易日的便捷函数"""
    return trading_calendar.get_last_trading_day(before_date)

def get_trading_days_between(start_date: date, end_date: date) -> List[date]:
    """获取交易日列表的便捷函数"""
    return trading_calendar.get_trading_days_between(start_date, end_date)

def is_market_open_time(check_time: Optional[datetime] = None) -> bool:
    """判断是否在交易时间的便捷函数"""
    return trading_calendar.is_market_open_time(check_time)
