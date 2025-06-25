#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析系统批量处理优化器
开发者：熊猫大侠
版本：v1.0.0
功能：优化批量股票数据处理性能，实现并发处理和智能缓存
"""

import asyncio
import aiohttp
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Any
import threading
from dataclasses import dataclass
from datetime import datetime

from data_service import DataService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BatchResult:
    """批量处理结果"""
    stock_code: str
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    processing_time: float = 0.0

class BatchOptimizer:
    """批量处理优化器"""
    
    def __init__(self, data_service: DataService = None):
        self.data_service = data_service or DataService()
        self.max_workers = 20  # 最大并发数
        self.batch_size = 50   # 批次大小
        self.timeout = 60      # 批量处理超时时间
        
        # 性能统计
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_time': 0.0,
            'avg_time_per_stock': 0.0
        }
    
    def process_stock_batch(self, stock_codes: List[str], 
                           operation: str = 'basic_info',
                           max_workers: int = None) -> List[BatchResult]:
        """
        批量处理股票数据
        
        Args:
            stock_codes: 股票代码列表
            operation: 操作类型 ('basic_info', 'realtime_data', 'price_history')
            max_workers: 最大并发数
        
        Returns:
            批量处理结果列表
        """
        if max_workers is None:
            max_workers = min(self.max_workers, len(stock_codes))
        
        logger.info(f"开始批量处理 {len(stock_codes)} 只股票，操作类型: {operation}")
        start_time = time.time()
        
        results = []
        
        # 分批处理
        for i in range(0, len(stock_codes), self.batch_size):
            batch = stock_codes[i:i + self.batch_size]
            logger.info(f"处理批次 {i//self.batch_size + 1}，股票数量: {len(batch)}")
            
            batch_results = self._process_batch_concurrent(batch, operation, max_workers)
            results.extend(batch_results)
        
        # 更新统计信息
        total_time = time.time() - start_time
        self._update_stats(results, total_time)
        
        logger.info(f"批量处理完成，总耗时: {total_time:.2f}秒")
        self._log_stats()
        
        return results
    
    def _process_batch_concurrent(self, stock_codes: List[str], 
                                 operation: str, 
                                 max_workers: int) -> List[BatchResult]:
        """并发处理单个批次"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_stock = {
                executor.submit(self._process_single_stock, stock_code, operation): stock_code
                for stock_code in stock_codes
            }
            
            # 收集结果
            for future in as_completed(future_to_stock, timeout=self.timeout):
                stock_code = future_to_stock[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"处理股票 {stock_code} 时发生异常: {e}")
                    results.append(BatchResult(
                        stock_code=stock_code,
                        success=False,
                        error=str(e)
                    ))
        
        return results
    
    def _process_single_stock(self, stock_code: str, operation: str) -> BatchResult:
        """处理单只股票"""
        start_time = time.time()
        
        try:
            if operation == 'basic_info':
                data = self.data_service.get_stock_basic_info(stock_code)
            elif operation == 'realtime_data':
                data = self.data_service.get_stock_realtime_data(stock_code)
            elif operation == 'price_history':
                data = self.data_service.get_stock_price_history(stock_code)
            else:
                raise ValueError(f"不支持的操作类型: {operation}")
            
            processing_time = time.time() - start_time
            
            if data is not None:
                return BatchResult(
                    stock_code=stock_code,
                    success=True,
                    data=data,
                    processing_time=processing_time
                )
            else:
                return BatchResult(
                    stock_code=stock_code,
                    success=False,
                    error="获取数据为空",
                    processing_time=processing_time
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return BatchResult(
                stock_code=stock_code,
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def _update_stats(self, results: List[BatchResult], total_time: float):
        """更新统计信息"""
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        self.stats['total_processed'] += len(results)
        self.stats['successful'] += successful
        self.stats['failed'] += failed
        self.stats['total_time'] += total_time
        
        if self.stats['total_processed'] > 0:
            self.stats['avg_time_per_stock'] = self.stats['total_time'] / self.stats['total_processed']
    
    def _log_stats(self):
        """记录统计信息"""
        logger.info("批量处理统计:")
        logger.info(f"  总处理数量: {self.stats['total_processed']}")
        logger.info(f"  成功数量: {self.stats['successful']}")
        logger.info(f"  失败数量: {self.stats['failed']}")
        logger.info(f"  成功率: {self.stats['successful']/self.stats['total_processed']*100:.1f}%")
        logger.info(f"  平均每股处理时间: {self.stats['avg_time_per_stock']:.3f}秒")
        logger.info(f"  吞吐量: {1/self.stats['avg_time_per_stock']:.2f}股/秒")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_time': 0.0,
            'avg_time_per_stock': 0.0
        }
    
    def optimize_market_scan(self, stock_codes: List[str]) -> Dict:
        """
        优化市场扫描功能
        
        Args:
            stock_codes: 股票代码列表
            
        Returns:
            扫描结果字典
        """
        logger.info(f"开始优化市场扫描，股票数量: {len(stock_codes)}")
        
        # 并发获取基本信息
        basic_info_results = self.process_stock_batch(stock_codes, 'basic_info')
        
        # 并发获取实时数据
        realtime_results = self.process_stock_batch(stock_codes, 'realtime_data')
        
        # 合并结果
        scan_results = {}
        for basic_result, realtime_result in zip(basic_info_results, realtime_results):
            stock_code = basic_result.stock_code
            
            if basic_result.success and realtime_result.success:
                scan_results[stock_code] = {
                    'basic_info': basic_result.data,
                    'realtime_data': realtime_result.data,
                    'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                # 记录失败原因
                errors = []
                if not basic_result.success:
                    errors.append(f"基本信息: {basic_result.error}")
                if not realtime_result.success:
                    errors.append(f"实时数据: {realtime_result.error}")
                
                scan_results[stock_code] = {
                    'error': '; '.join(errors),
                    'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        logger.info(f"市场扫描完成，成功: {len([r for r in scan_results.values() if 'error' not in r])}")
        return scan_results
    
    def preload_cache(self, stock_codes: List[str], operations: List[str] = None):
        """
        预加载缓存
        
        Args:
            stock_codes: 股票代码列表
            operations: 操作类型列表，默认为 ['basic_info', 'realtime_data']
        """
        if operations is None:
            operations = ['basic_info', 'realtime_data']
        
        logger.info(f"开始预加载缓存，股票数量: {len(stock_codes)}, 操作类型: {operations}")
        
        for operation in operations:
            logger.info(f"预加载 {operation} 数据...")
            results = self.process_stock_batch(stock_codes, operation)
            successful = sum(1 for r in results if r.success)
            logger.info(f"{operation} 预加载完成，成功率: {successful/len(results)*100:.1f}%")


# 全局批量优化器实例
batch_optimizer = BatchOptimizer()


def optimize_batch_processing(stock_codes: List[str], operation: str = 'basic_info') -> List[BatchResult]:
    """
    便捷函数：优化批量处理
    
    Args:
        stock_codes: 股票代码列表
        operation: 操作类型
        
    Returns:
        批量处理结果
    """
    return batch_optimizer.process_stock_batch(stock_codes, operation)


def optimize_market_scan(stock_codes: List[str]) -> Dict:
    """
    便捷函数：优化市场扫描
    
    Args:
        stock_codes: 股票代码列表
        
    Returns:
        扫描结果
    """
    return batch_optimizer.optimize_market_scan(stock_codes)


if __name__ == "__main__":
    # 测试批量优化器
    test_stocks = ['000001', '000002', '600000', '600036', '000858']
    
    optimizer = BatchOptimizer()
    
    # 测试批量处理
    results = optimizer.process_stock_batch(test_stocks, 'basic_info')
    
    # 打印结果
    for result in results:
        if result.success:
            print(f"✓ {result.stock_code}: 成功 ({result.processing_time:.3f}秒)")
        else:
            print(f"✗ {result.stock_code}: 失败 - {result.error}")
    
    # 打印统计信息
    optimizer._log_stats()
