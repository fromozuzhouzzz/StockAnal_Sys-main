#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量数据更新器
专门用于投资组合的批量数据预加载和更新，优化CSV导出性能
"""

import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
from enum import Enum

from data_service import data_service
from stock_analyzer import StockAnalyzer
from smart_cache_manager import SmartCacheManager
from optimized_cache_strategy import optimized_cache
from intelligent_fallback_strategy import intelligent_fallback
from trading_calendar import trading_calendar, get_last_trading_day

logger = logging.getLogger(__name__)

class UpdateStatus(Enum):
    """更新状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StockUpdateResult:
    """单个股票更新结果"""
    stock_code: str
    status: UpdateStatus
    message: str
    duration: float
    data_updated: bool = False
    error: Optional[str] = None

@dataclass
class BatchUpdateProgress:
    """批量更新进度"""
    total_stocks: int
    completed_stocks: int
    failed_stocks: int
    skipped_stocks: int
    current_stock: Optional[str]
    start_time: datetime
    estimated_remaining: Optional[float]
    results: List[StockUpdateResult]

class BatchDataUpdater:
    """批量数据更新器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = StockAnalyzer()
        self.cache_manager = SmartCacheManager()
        
        # 更新会话管理
        self.active_sessions: Dict[str, BatchUpdateProgress] = {}
        self.session_lock = threading.Lock()
        
        # 性能配置
        self.max_workers = 3  # 限制并发数，避免API限流
        self.update_timeout = 30  # 单个股票更新超时时间（秒）
        self.batch_size = 5  # 批处理大小
        
        # 智能更新策略
        self.force_update_threshold = timedelta(hours=4)  # 强制更新阈值
        self.skip_update_threshold = timedelta(minutes=30)  # 跳过更新阈值
    
    def start_batch_update(self, stock_codes: List[str], session_id: str,
                          force_update: bool = False) -> str:
        """
        启动批量数据更新

        Args:
            stock_codes: 股票代码列表
            session_id: 会话ID
            force_update: 是否强制更新

        Returns:
            str: 会话ID
        """
        try:
            # 验证输入
            if not stock_codes:
                raise ValueError("股票代码列表不能为空")

            # 去重并验证股票代码
            valid_codes = self._validate_stock_codes(stock_codes)
            if not valid_codes:
                raise ValueError("没有有效的股票代码")

            # 优化：预先检查缓存新鲜度，减少不必要的更新
            if not force_update:
                cache_freshness = optimized_cache.check_cache_freshness(valid_codes)
                # 过滤出真正需要更新的股票
                codes_to_update = [code for code, needs_update in cache_freshness.items() if needs_update]
                self.logger.info(f"缓存检查完成：{len(valid_codes)} 只股票中，{len(codes_to_update)} 只需要更新")
            else:
                codes_to_update = valid_codes

            # 创建更新进度对象
            progress = BatchUpdateProgress(
                total_stocks=len(codes_to_update),
                completed_stocks=0,
                failed_stocks=0,
                skipped_stocks=len(valid_codes) - len(codes_to_update),  # 预先跳过的数量
                current_stock=None,
                start_time=datetime.now(),
                estimated_remaining=None,
                results=[]
            )

            # 添加跳过的股票结果
            if not force_update:
                skipped_codes = set(valid_codes) - set(codes_to_update)
                for code in skipped_codes:
                    progress.results.append(StockUpdateResult(
                        stock_code=code,
                        status=UpdateStatus.SKIPPED,
                        message="缓存数据较新，跳过更新",
                        duration=0
                    ))

            # 注册会话
            with self.session_lock:
                self.active_sessions[session_id] = progress

            # 启动异步更新任务
            threading.Thread(
                target=self._execute_batch_update,
                args=(codes_to_update, session_id, force_update),
                daemon=True
            ).start()

            self.logger.info(f"启动批量数据更新会话 {session_id}，共 {len(codes_to_update)} 只股票需要更新")
            return session_id

        except Exception as e:
            self.logger.error(f"启动批量更新失败: {e}")
            raise
    
    def get_update_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取更新进度
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 进度信息
        """
        with self.session_lock:
            progress = self.active_sessions.get(session_id)
            
        if not progress:
            return None
        
        # 计算进度百分比
        progress_percent = (progress.completed_stocks + progress.failed_stocks + progress.skipped_stocks) / progress.total_stocks * 100
        
        # 估算剩余时间
        elapsed_time = (datetime.now() - progress.start_time).total_seconds()
        if progress.completed_stocks > 0:
            avg_time_per_stock = elapsed_time / (progress.completed_stocks + progress.failed_stocks + progress.skipped_stocks)
            remaining_stocks = progress.total_stocks - progress.completed_stocks - progress.failed_stocks - progress.skipped_stocks
            estimated_remaining = avg_time_per_stock * remaining_stocks
        else:
            estimated_remaining = None
        
        return {
            'session_id': session_id,
            'status': 'running' if progress.current_stock else 'completed',
            'progress': {
                'total': progress.total_stocks,
                'completed': progress.completed_stocks,
                'failed': progress.failed_stocks,
                'skipped': progress.skipped_stocks,
                'percent': round(progress_percent, 1)
            },
            'current_stock': progress.current_stock,
            'timing': {
                'start_time': progress.start_time.isoformat(),
                'elapsed_seconds': round(elapsed_time, 1),
                'estimated_remaining_seconds': round(estimated_remaining, 1) if estimated_remaining else None
            },
            'results': [
                {
                    'stock_code': result.stock_code,
                    'status': result.status.value,
                    'message': result.message,
                    'duration': round(result.duration, 2),
                    'data_updated': result.data_updated,
                    'error': result.error
                }
                for result in progress.results[-10:]  # 只返回最近10个结果
            ]
        }
    
    def _validate_stock_codes(self, stock_codes: List[str]) -> List[str]:
        """验证并标准化股票代码"""
        valid_codes = []
        for code in stock_codes:
            if isinstance(code, str) and len(code.strip()) > 0:
                # 标准化股票代码格式
                normalized_code = code.strip().upper()
                if '.' not in normalized_code:
                    # 自动添加市场后缀
                    if normalized_code.startswith('6'):
                        normalized_code += '.SH'
                    elif normalized_code.startswith(('0', '3')):
                        normalized_code += '.SZ'
                
                if normalized_code not in valid_codes:
                    valid_codes.append(normalized_code)
        
        return valid_codes
    
    def _execute_batch_update(self, stock_codes: List[str], session_id: str, force_update: bool):
        """执行批量更新（在后台线程中运行）"""
        try:
            with self.session_lock:
                progress = self.active_sessions[session_id]
            
            # 使用线程池进行并发更新
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 分批处理，避免过多并发
                for i in range(0, len(stock_codes), self.batch_size):
                    batch = stock_codes[i:i + self.batch_size]
                    
                    # 提交批次任务
                    future_to_stock = {
                        executor.submit(self._update_single_stock, code, force_update): code
                        for code in batch
                    }
                    
                    # 处理完成的任务
                    for future in as_completed(future_to_stock, timeout=self.update_timeout * len(batch)):
                        stock_code = future_to_stock[future]
                        
                        # 更新当前处理的股票
                        with self.session_lock:
                            progress.current_stock = stock_code
                        
                        try:
                            result = future.result()
                            
                            # 更新统计
                            with self.session_lock:
                                progress.results.append(result)
                                if result.status == UpdateStatus.COMPLETED:
                                    progress.completed_stocks += 1
                                elif result.status == UpdateStatus.FAILED:
                                    progress.failed_stocks += 1
                                elif result.status == UpdateStatus.SKIPPED:
                                    progress.skipped_stocks += 1
                            
                            self.logger.info(f"股票 {stock_code} 更新完成: {result.status.value} - {result.message}")
                            
                        except Exception as e:
                            # 处理单个股票更新异常
                            error_result = StockUpdateResult(
                                stock_code=stock_code,
                                status=UpdateStatus.FAILED,
                                message=f"更新异常: {str(e)}",
                                duration=0,
                                error=str(e)
                            )
                            
                            with self.session_lock:
                                progress.results.append(error_result)
                                progress.failed_stocks += 1
                            
                            self.logger.error(f"股票 {stock_code} 更新异常: {e}")
            
            # 更新完成
            with self.session_lock:
                progress.current_stock = None
            
            self.logger.info(f"批量更新会话 {session_id} 完成: 成功 {progress.completed_stocks}, 失败 {progress.failed_stocks}, 跳过 {progress.skipped_stocks}")
            
        except Exception as e:
            self.logger.error(f"批量更新执行失败: {e}")
            with self.session_lock:
                if session_id in self.active_sessions:
                    self.active_sessions[session_id].current_stock = None
    
    def _update_single_stock(self, stock_code: str, force_update: bool) -> StockUpdateResult:
        """
        更新单个股票数据
        
        Args:
            stock_code: 股票代码
            force_update: 是否强制更新
            
        Returns:
            StockUpdateResult: 更新结果
        """
        start_time = time.time()
        
        try:
            # 检查是否需要更新
            if not force_update and not self._should_update_stock(stock_code):
                return StockUpdateResult(
                    stock_code=stock_code,
                    status=UpdateStatus.SKIPPED,
                    message="数据较新，跳过更新",
                    duration=time.time() - start_time
                )
            
            # 执行数据更新
            success = self._perform_stock_update(stock_code)
            
            if success:
                return StockUpdateResult(
                    stock_code=stock_code,
                    status=UpdateStatus.COMPLETED,
                    message="数据更新成功",
                    duration=time.time() - start_time,
                    data_updated=True
                )
            else:
                return StockUpdateResult(
                    stock_code=stock_code,
                    status=UpdateStatus.FAILED,
                    message="数据更新失败",
                    duration=time.time() - start_time,
                    error="API调用失败或数据无效"
                )
                
        except Exception as e:
            return StockUpdateResult(
                stock_code=stock_code,
                status=UpdateStatus.FAILED,
                message=f"更新异常: {str(e)}",
                duration=time.time() - start_time,
                error=str(e)
            )
    
    def _should_update_stock(self, stock_code: str) -> bool:
        """判断是否需要更新股票数据"""
        try:
            # 检查缓存数据的新鲜度
            last_update = self.cache_manager.get_last_update_time(stock_code)
            
            if last_update:
                time_since_update = datetime.now() - last_update
                
                # 如果数据很新（30分钟内），跳过更新
                if time_since_update < self.skip_update_threshold:
                    return False
                
                # 如果数据较旧（4小时以上），强制更新
                if time_since_update > self.force_update_threshold:
                    return True
            
            # 检查是否在交易时间
            if not trading_calendar.is_market_open_time():
                # 非交易时间，检查是否有当日数据
                if self.cache_manager.has_today_data(stock_code):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"判断更新需求失败 {stock_code}: {e}")
            return True  # 出错时默认需要更新
    
    def _perform_stock_update(self, stock_code: str) -> bool:
        """执行股票数据更新，使用智能降级策略"""
        try:
            # 使用智能降级策略获取数据
            stock_data, data_source = intelligent_fallback.get_stock_data_with_fallback(stock_code)

            if stock_data:
                self.logger.info(f"股票 {stock_code} 数据更新成功，数据源: {data_source.value}")

                # 如果是API数据，尝试预计算评分
                if data_source.value in ['api_fresh', 'cache_fresh']:
                    try:
                        # 获取历史价格数据用于评分计算
                        end_date = datetime.now().strftime('%Y%m%d')
                        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                        price_data = data_service.get_stock_price_history(stock_code, start_date, end_date)

                        if price_data is not None and len(price_data) > 0:
                            score_result = self.analyzer.calculate_score(price_data)
                            # 缓存评分结果
                            self.cache_manager.cache_score_result(stock_code, score_result)
                            self.logger.debug(f"股票 {stock_code} 评分计算完成")
                    except Exception as score_error:
                        self.logger.warning(f"股票 {stock_code} 评分计算失败: {score_error}")
                        # 评分失败不影响数据更新成功

                return True
            else:
                self.logger.warning(f"股票 {stock_code} 数据获取失败")
                return False

        except Exception as e:
            self.logger.error(f"执行股票 {stock_code} 数据更新失败: {e}")
            return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """清理旧的更新会话"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with self.session_lock:
            old_sessions = [
                session_id for session_id, progress in self.active_sessions.items()
                if progress.start_time < cutoff_time and progress.current_stock is None
            ]
            
            for session_id in old_sessions:
                del self.active_sessions[session_id]
        
        if old_sessions:
            self.logger.info(f"清理了 {len(old_sessions)} 个旧的更新会话")

# 全局实例
batch_updater = BatchDataUpdater()
