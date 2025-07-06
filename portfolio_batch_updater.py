# -*- coding: utf-8 -*-
"""
投资组合批量数据更新器
提供高效的批量股票数据更新功能，优化CSV导出性能
"""

import logging
import time
import uuid
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# 导入数据服务和缓存管理器
try:
    from data_service import DataService
except ImportError:
    DataService = None

try:
    from database_optimizer import DatabaseOptimizer
except ImportError:
    DatabaseOptimizer = None

# 导入股票分析器
try:
    from stock_analyzer import StockAnalyzer
except ImportError:
    StockAnalyzer = None

logger = logging.getLogger(__name__)


class PortfolioBatchUpdater:
    """投资组合批量数据更新器"""
    
    def __init__(self):
        # 初始化服务组件（处理可能的导入失败）
        self.data_service = DataService() if DataService else None
        self.db_optimizer = DatabaseOptimizer() if DatabaseOptimizer else None
        self.analyzer = StockAnalyzer() if StockAnalyzer else None

        # 检查必要组件
        if not self.analyzer:
            raise ImportError("StockAnalyzer 导入失败，批量更新功能不可用")

        # 任务状态管理
        self.active_tasks = {}
        self.task_lock = threading.Lock()

        # 并发控制
        self.max_concurrent_requests = 5
        self.request_delay = 0.2  # 请求间隔200ms

        # 缓存检查配置
        self.cache_check_threshold = 300  # 5分钟内的缓存认为是新鲜的
        
    def batch_update_stocks(self, stock_codes: List[str], market_type: str = 'A', 
                           force_update: bool = False) -> Dict[str, Any]:
        """
        批量更新股票数据
        
        Args:
            stock_codes: 股票代码列表
            market_type: 市场类型
            force_update: 是否强制更新（忽略缓存）
            
        Returns:
            包含任务ID和初始状态的字典
        """
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 初始化任务状态
            task_status = {
                'task_id': task_id,
                'status': 'running',
                'total_stocks': len(stock_codes),
                'completed_stocks': 0,
                'failed_stocks': 0,
                'skipped_stocks': 0,
                'start_time': datetime.now().isoformat(),
                'progress_percentage': 0,
                'current_stock': None,
                'results': {},
                'errors': [],
                'cache_hits': 0,
                'api_calls': 0
            }
            
            # 保存任务状态
            with self.task_lock:
                self.active_tasks[task_id] = task_status
            
            # 启动后台更新任务
            thread = threading.Thread(
                target=self._execute_batch_update,
                args=(task_id, stock_codes, market_type, force_update)
            )
            thread.daemon = True
            thread.start()
            
            return {
                'task_id': task_id,
                'status': 'started',
                'total_stocks': len(stock_codes),
                'message': f'开始批量更新 {len(stock_codes)} 只股票的数据'
            }
            
        except Exception as e:
            logger.error(f"启动批量更新任务失败: {e}")
            return {
                'error': f'启动批量更新失败: {str(e)}',
                'status': 'failed'
            }
    
    def _execute_batch_update(self, task_id: str, stock_codes: List[str], 
                             market_type: str, force_update: bool):
        """执行批量更新任务"""
        try:
            # 获取任务状态
            task_status = self.active_tasks[task_id]
            
            # 第一步：批量检查缓存状态
            logger.info(f"任务 {task_id}: 开始批量缓存检查")
            cache_status = self._batch_check_cache_status(stock_codes, market_type, force_update)
            
            # 更新统计信息
            task_status['cache_hits'] = len(cache_status['fresh_stocks'])
            task_status['skipped_stocks'] = len(cache_status['fresh_stocks'])
            
            # 需要更新的股票
            stocks_to_update = cache_status['stale_stocks']
            
            if not stocks_to_update:
                # 所有股票都有新鲜缓存
                task_status['status'] = 'completed'
                task_status['progress_percentage'] = 100
                task_status['end_time'] = datetime.now().isoformat()
                task_status['message'] = '所有股票数据都是最新的，无需更新'
                logger.info(f"任务 {task_id}: 所有股票缓存都是新鲜的")
                return
            
            logger.info(f"任务 {task_id}: 需要更新 {len(stocks_to_update)} 只股票")
            
            # 第二步：并发更新需要更新的股票
            self._concurrent_update_stocks(task_id, stocks_to_update, market_type)
            
            # 任务完成
            task_status['status'] = 'completed'
            task_status['progress_percentage'] = 100
            task_status['end_time'] = datetime.now().isoformat()
            
            # 计算总耗时
            start_time = datetime.fromisoformat(task_status['start_time'])
            end_time = datetime.fromisoformat(task_status['end_time'])
            duration = (end_time - start_time).total_seconds()
            
            task_status['duration_seconds'] = duration
            task_status['message'] = f'批量更新完成，耗时 {duration:.1f} 秒'
            
            logger.info(f"任务 {task_id}: 批量更新完成，成功 {task_status['completed_stocks']} 只，"
                       f"失败 {task_status['failed_stocks']} 只，跳过 {task_status['skipped_stocks']} 只")
            
        except Exception as e:
            logger.error(f"执行批量更新任务 {task_id} 失败: {e}")
            task_status = self.active_tasks.get(task_id, {})
            task_status['status'] = 'failed'
            task_status['error'] = str(e)
            task_status['end_time'] = datetime.now().isoformat()
    
    def _batch_check_cache_status(self, stock_codes: List[str], market_type: str,
                                 force_update: bool) -> Dict[str, List[str]]:
        """批量检查股票缓存状态"""
        fresh_stocks = []
        stale_stocks = []

        if force_update:
            # 强制更新，所有股票都需要更新
            stale_stocks = stock_codes.copy()
            logger.info(f"强制更新模式，将更新所有 {len(stock_codes)} 只股票")
        else:
            # 智能缓存检查：同时检查多个缓存层
            try:
                if self.db_optimizer:
                    # 1. 批量检查基本信息缓存
                    basic_info_cache = self.db_optimizer.batch_get_stock_basic_info(stock_codes, market_type)

                    # 2. 批量检查实时数据缓存
                    realtime_cache = self.db_optimizer.batch_get_stock_realtime_data(stock_codes, market_type)

                    # 3. 智能分析每只股票的缓存状态
                    for stock_code in stock_codes:
                        cache_status = self._analyze_stock_cache_status(
                            stock_code, basic_info_cache, realtime_cache
                        )

                        if cache_status['is_fresh']:
                            fresh_stocks.append(stock_code)
                            logger.debug(f"股票 {stock_code} 缓存新鲜，跳过更新")
                        else:
                            stale_stocks.append(stock_code)
                            logger.debug(f"股票 {stock_code} 需要更新: {cache_status['reason']}")

                    logger.info(f"缓存检查完成：{len(fresh_stocks)} 只新鲜，{len(stale_stocks)} 只需更新")
                else:
                    # 没有数据库优化器，所有股票都需要更新
                    logger.warning("数据库优化器不可用，将更新所有股票")
                    stale_stocks = stock_codes.copy()

            except Exception as e:
                logger.warning(f"批量缓存检查失败，将更新所有股票: {e}")
                stale_stocks = stock_codes.copy()

        return {
            'fresh_stocks': fresh_stocks,
            'stale_stocks': stale_stocks
        }

    def _analyze_stock_cache_status(self, stock_code: str, basic_info_cache: Dict,
                                   realtime_cache: Dict) -> Dict[str, Any]:
        """分析单只股票的缓存状态"""
        try:
            # 检查基本信息缓存
            basic_info = basic_info_cache.get(stock_code)
            realtime_data = realtime_cache.get(stock_code)

            # 如果没有基本信息缓存，肯定需要更新
            if not basic_info:
                return {
                    'is_fresh': False,
                    'reason': '缺少基本信息缓存'
                }

            # 检查基本信息是否新鲜
            if not self._is_cache_fresh(basic_info):
                return {
                    'is_fresh': False,
                    'reason': '基本信息缓存过期'
                }

            # 检查实时数据缓存
            if not realtime_data:
                return {
                    'is_fresh': False,
                    'reason': '缺少实时数据缓存'
                }

            # 检查实时数据是否新鲜（更严格的时间要求）
            if not self._is_realtime_cache_fresh(realtime_data):
                return {
                    'is_fresh': False,
                    'reason': '实时数据缓存过期'
                }

            # 检查数据完整性
            required_fields = ['stock_name', 'current_price', 'change_pct']
            missing_fields = [field for field in required_fields
                            if not realtime_data.get(field)]

            if missing_fields:
                return {
                    'is_fresh': False,
                    'reason': f'缺少必要字段: {", ".join(missing_fields)}'
                }

            # 所有检查都通过
            return {
                'is_fresh': True,
                'reason': '缓存数据完整且新鲜'
            }

        except Exception as e:
            logger.warning(f"分析股票 {stock_code} 缓存状态失败: {e}")
            return {
                'is_fresh': False,
                'reason': f'缓存状态分析失败: {str(e)}'
            }
    
    def _is_cache_fresh(self, cache_data: Dict) -> bool:
        """检查缓存数据是否新鲜"""
        try:
            updated_at = cache_data.get('updated_at')
            if not updated_at:
                return False

            # 解析更新时间
            if isinstance(updated_at, str):
                update_time = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
            else:
                update_time = updated_at

            # 检查是否在阈值时间内
            time_diff = (datetime.now() - update_time).total_seconds()
            return time_diff < self.cache_check_threshold

        except Exception as e:
            logger.warning(f"检查缓存新鲜度失败: {e}")
            return False

    def _is_realtime_cache_fresh(self, cache_data: Dict) -> bool:
        """检查实时数据缓存是否新鲜（更严格的时间要求）"""
        try:
            updated_at = cache_data.get('updated_at')
            if not updated_at:
                return False

            # 解析更新时间
            if isinstance(updated_at, str):
                update_time = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
            else:
                update_time = updated_at

            # 实时数据要求更严格：5分钟内的数据才算新鲜
            realtime_threshold = 300  # 5分钟
            time_diff = (datetime.now() - update_time).total_seconds()

            # 如果是交易时间，要求更严格
            if self._is_trading_time():
                realtime_threshold = 180  # 交易时间内3分钟

            return time_diff < realtime_threshold

        except Exception as e:
            logger.warning(f"检查实时缓存新鲜度失败: {e}")
            return False

    def _is_trading_time(self) -> bool:
        """检查当前是否为交易时间"""
        try:
            now = datetime.now()
            weekday = now.weekday()

            # 周末不是交易时间
            if weekday >= 5:  # 5=周六, 6=周日
                return False

            # 检查是否在交易时间段内
            current_time = now.time()

            # A股交易时间：9:30-11:30, 13:00-15:00
            morning_start = datetime.strptime('09:30', '%H:%M').time()
            morning_end = datetime.strptime('11:30', '%H:%M').time()
            afternoon_start = datetime.strptime('13:00', '%H:%M').time()
            afternoon_end = datetime.strptime('15:00', '%H:%M').time()

            return ((morning_start <= current_time <= morning_end) or
                   (afternoon_start <= current_time <= afternoon_end))

        except Exception as e:
            logger.warning(f"检查交易时间失败: {e}")
            return False
    
    def _concurrent_update_stocks(self, task_id: str, stock_codes: List[str], market_type: str):
        """并发更新股票数据"""
        task_status = self.active_tasks[task_id]
        total_stocks = len(stock_codes)

        # 初始化详细统计
        task_status['detailed_stats'] = {
            'api_errors': 0,
            'timeout_errors': 0,
            'connection_errors': 0,
            'database_errors': 0,
            'unknown_errors': 0,
            'total_elapsed_time': 0,
            'average_time_per_stock': 0
        }

        logger.info(f"任务 {task_id}: 开始并发更新 {total_stocks} 只股票，最大并发数: {self.max_concurrent_requests}")

        with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
            # 提交所有更新任务
            future_to_stock = {
                executor.submit(self._update_single_stock, stock_code, market_type): stock_code
                for stock_code in stock_codes
            }

            # 处理完成的任务
            completed_count = 0
            for future in as_completed(future_to_stock):
                stock_code = future_to_stock[future]
                task_status['current_stock'] = stock_code
                completed_count += 1

                try:
                    result = future.result(timeout=30)  # 30秒超时

                    # 更新统计信息
                    if 'elapsed_time' in result:
                        task_status['detailed_stats']['total_elapsed_time'] += result['elapsed_time']

                    if result['success']:
                        task_status['completed_stocks'] += 1
                        task_status['api_calls'] += 1
                        task_status['results'][stock_code] = result['data']
                        logger.info(f"任务 {task_id}: 成功更新股票 {stock_code} ({completed_count}/{total_stocks})")
                    else:
                        task_status['failed_stocks'] += 1

                        # 分类错误统计
                        error_type = result.get('error_type', 'UNKNOWN_ERROR')
                        if error_type == 'API_ERROR':
                            task_status['detailed_stats']['api_errors'] += 1
                        elif error_type == 'TIMEOUT_ERROR':
                            task_status['detailed_stats']['timeout_errors'] += 1
                        elif error_type == 'CONNECTION_ERROR':
                            task_status['detailed_stats']['connection_errors'] += 1
                        elif error_type == 'DATABASE_ERROR':
                            task_status['detailed_stats']['database_errors'] += 1
                        else:
                            task_status['detailed_stats']['unknown_errors'] += 1

                        # 记录错误详情
                        error_info = {
                            'stock_code': stock_code,
                            'error': result['error'],
                            'error_type': error_type,
                            'error_detail': result.get('error_detail', '')
                        }
                        task_status['errors'].append(error_info)

                        logger.warning(f"任务 {task_id}: 更新股票 {stock_code} 失败 ({error_type}): {result['error']}")

                except Exception as e:
                    task_status['failed_stocks'] += 1
                    task_status['detailed_stats']['unknown_errors'] += 1

                    error_info = {
                        'stock_code': stock_code,
                        'error': f'处理异常: {str(e)}',
                        'error_type': 'PROCESSING_ERROR',
                        'error_detail': str(e)
                    }
                    task_status['errors'].append(error_info)

                    logger.error(f"任务 {task_id}: 处理股票 {stock_code} 时异常: {e}")

                # 更新进度
                total_processed = task_status['completed_stocks'] + task_status['failed_stocks']
                task_status['progress_percentage'] = int((total_processed / total_stocks) * 100)

                # 计算平均处理时间
                if task_status['detailed_stats']['total_elapsed_time'] > 0:
                    task_status['detailed_stats']['average_time_per_stock'] = (
                        task_status['detailed_stats']['total_elapsed_time'] / total_processed
                    )

                # 动态调整请求间隔
                if task_status['detailed_stats']['api_errors'] > total_processed * 0.3:
                    # 如果API错误率超过30%，增加延迟
                    dynamic_delay = self.request_delay * 2
                    logger.warning(f"API错误率过高，增加请求延迟到 {dynamic_delay} 秒")
                else:
                    dynamic_delay = self.request_delay

                # 添加请求间隔，避免API限流
                if completed_count < total_stocks:  # 最后一个请求不需要延迟
                    time.sleep(dynamic_delay)

        # 清除当前处理股票状态
        task_status['current_stock'] = None

        # 记录最终统计
        stats = task_status['detailed_stats']
        logger.info(f"任务 {task_id}: 并发更新完成 - 成功: {task_status['completed_stocks']}, "
                   f"失败: {task_status['failed_stocks']}, "
                   f"平均耗时: {stats['average_time_per_stock']:.2f}秒/股票")
    
    def _update_single_stock(self, stock_code: str, market_type: str) -> Dict[str, Any]:
        """更新单只股票数据"""
        start_time = time.time()

        try:
            logger.info(f"开始更新股票 {stock_code}")

            # 调用股票分析器获取完整数据
            result = self.analyzer.calculate_score(stock_code, market_type)

            if result:
                # 验证返回数据的完整性
                required_fields = ['stock_code', 'stock_name', 'score']
                missing_fields = [field for field in required_fields if not result.get(field)]

                if missing_fields:
                    error_msg = f"返回数据缺少必要字段: {', '.join(missing_fields)}"
                    logger.warning(f"股票 {stock_code} 数据不完整: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'partial_data': result
                    }

                # 记录成功更新
                elapsed_time = time.time() - start_time
                logger.info(f"成功更新股票 {stock_code}，耗时 {elapsed_time:.2f} 秒")

                return {
                    'success': True,
                    'data': result,
                    'elapsed_time': elapsed_time
                }
            else:
                error_msg = '股票分析器返回空结果'
                logger.warning(f"股票 {stock_code} 更新失败: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = str(e)

            # 分类错误类型
            if 'AKShare' in error_msg:
                error_type = 'API_ERROR'
                user_friendly_msg = 'AKShare数据接口异常'
            elif 'timeout' in error_msg.lower():
                error_type = 'TIMEOUT_ERROR'
                user_friendly_msg = '请求超时'
            elif 'connection' in error_msg.lower():
                error_type = 'CONNECTION_ERROR'
                user_friendly_msg = '网络连接异常'
            elif 'database' in error_msg.lower() or 'mysql' in error_msg.lower():
                error_type = 'DATABASE_ERROR'
                user_friendly_msg = '数据库操作异常'
            else:
                error_type = 'UNKNOWN_ERROR'
                user_friendly_msg = '未知错误'

            logger.error(f"股票 {stock_code} 更新失败 ({error_type}): {error_msg}")

            return {
                'success': False,
                'error': user_friendly_msg,
                'error_type': error_type,
                'error_detail': error_msg,
                'elapsed_time': elapsed_time
            }
    
    def get_update_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取更新任务状态"""
        with self.task_lock:
            return self.active_tasks.get(task_id)
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的任务（超过指定小时数）"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with self.task_lock:
            tasks_to_remove = []
            
            for task_id, task_status in self.active_tasks.items():
                if task_status.get('status') in ['completed', 'failed']:
                    end_time_str = task_status.get('end_time')
                    if end_time_str:
                        try:
                            end_time = datetime.fromisoformat(end_time_str)
                            if end_time < cutoff_time:
                                tasks_to_remove.append(task_id)
                        except Exception:
                            # 如果解析时间失败，也删除这个任务
                            tasks_to_remove.append(task_id)
            
            # 删除过期任务
            for task_id in tasks_to_remove:
                del self.active_tasks[task_id]
            
            if tasks_to_remove:
                logger.info(f"清理了 {len(tasks_to_remove)} 个过期任务")
