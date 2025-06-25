#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析系统性能监控器
开发者：熊猫大侠
版本：v1.0.0
功能：实时监控系统性能，包括缓存命中率、API调用时间、数据库查询效率等
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import json
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.lock = threading.Lock()
        
        # 性能指标
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'db_queries': 0,
            'errors': 0,
            'total_requests': 0
        }
        
        # 时间序列数据
        self.time_series = {
            'api_call_times': deque(maxlen=max_history_size),
            'db_query_times': deque(maxlen=max_history_size),
            'cache_query_times': deque(maxlen=max_history_size),
            'error_times': deque(maxlen=max_history_size)
        }
        
        # 错误统计
        self.error_stats = defaultdict(int)
        
        # 性能阈值
        self.thresholds = {
            'api_call_time': 5.0,      # API调用时间阈值（秒）
            'db_query_time': 1.0,      # 数据库查询时间阈值（秒）
            'cache_hit_rate': 0.8,     # 缓存命中率阈值
            'error_rate': 0.05         # 错误率阈值
        }
        
        # 启动监控线程
        self._start_monitoring()
    
    def _start_monitoring(self):
        """启动监控线程"""
        def monitor_task():
            while True:
                try:
                    time.sleep(60)  # 每分钟检查一次
                    self._check_performance_alerts()
                except Exception as e:
                    logger.error(f"性能监控任务失败: {e}")
        
        monitor_thread = threading.Thread(target=monitor_task, daemon=True)
        monitor_thread.start()
    
    def record_cache_hit(self, query_time: float = 0.0):
        """记录缓存命中"""
        with self.lock:
            self.metrics['cache_hits'] += 1
            self.metrics['total_requests'] += 1
            if query_time > 0:
                self.time_series['cache_query_times'].append({
                    'time': time.time(),
                    'duration': query_time
                })
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        with self.lock:
            self.metrics['cache_misses'] += 1
            self.metrics['total_requests'] += 1
    
    def record_api_call(self, duration: float, success: bool = True, error: str = None):
        """记录API调用"""
        with self.lock:
            self.metrics['api_calls'] += 1
            self.time_series['api_call_times'].append({
                'time': time.time(),
                'duration': duration,
                'success': success
            })
            
            if not success:
                self.metrics['errors'] += 1
                self.time_series['error_times'].append({
                    'time': time.time(),
                    'type': 'api_call',
                    'error': error
                })
                if error:
                    self.error_stats[error] += 1
    
    def record_db_query(self, duration: float, success: bool = True, error: str = None):
        """记录数据库查询"""
        with self.lock:
            self.metrics['db_queries'] += 1
            self.time_series['db_query_times'].append({
                'time': time.time(),
                'duration': duration,
                'success': success
            })
            
            if not success:
                self.metrics['errors'] += 1
                self.time_series['error_times'].append({
                    'time': time.time(),
                    'type': 'db_query',
                    'error': error
                })
                if error:
                    self.error_stats[error] += 1
    
    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        total_cache_requests = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total_cache_requests == 0:
            return 0.0
        return self.metrics['cache_hits'] / total_cache_requests
    
    def get_error_rate(self) -> float:
        """获取错误率"""
        if self.metrics['total_requests'] == 0:
            return 0.0
        return self.metrics['errors'] / self.metrics['total_requests']
    
    def get_avg_api_call_time(self, last_n: int = 100) -> float:
        """获取平均API调用时间"""
        recent_calls = list(self.time_series['api_call_times'])[-last_n:]
        if not recent_calls:
            return 0.0
        return sum(call['duration'] for call in recent_calls) / len(recent_calls)
    
    def get_avg_db_query_time(self, last_n: int = 100) -> float:
        """获取平均数据库查询时间"""
        recent_queries = list(self.time_series['db_query_times'])[-last_n:]
        if not recent_queries:
            return 0.0
        return sum(query['duration'] for query in recent_queries) / len(recent_queries)
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': self.metrics.copy(),
            'rates': {
                'cache_hit_rate': self.get_cache_hit_rate(),
                'error_rate': self.get_error_rate()
            },
            'avg_times': {
                'api_call_time': self.get_avg_api_call_time(),
                'db_query_time': self.get_avg_db_query_time()
            },
            'top_errors': dict(sorted(self.error_stats.items(), 
                                    key=lambda x: x[1], reverse=True)[:5])
        }
    
    def _check_performance_alerts(self):
        """检查性能告警"""
        alerts = []
        
        # 检查缓存命中率
        cache_hit_rate = self.get_cache_hit_rate()
        if cache_hit_rate < self.thresholds['cache_hit_rate']:
            alerts.append(f"缓存命中率过低: {cache_hit_rate:.2%} < {self.thresholds['cache_hit_rate']:.2%}")
        
        # 检查错误率
        error_rate = self.get_error_rate()
        if error_rate > self.thresholds['error_rate']:
            alerts.append(f"错误率过高: {error_rate:.2%} > {self.thresholds['error_rate']:.2%}")
        
        # 检查API调用时间
        avg_api_time = self.get_avg_api_call_time()
        if avg_api_time > self.thresholds['api_call_time']:
            alerts.append(f"API调用时间过长: {avg_api_time:.2f}秒 > {self.thresholds['api_call_time']}秒")
        
        # 检查数据库查询时间
        avg_db_time = self.get_avg_db_query_time()
        if avg_db_time > self.thresholds['db_query_time']:
            alerts.append(f"数据库查询时间过长: {avg_db_time:.2f}秒 > {self.thresholds['db_query_time']}秒")
        
        # 记录告警
        if alerts:
            logger.warning("性能告警:")
            for alert in alerts:
                logger.warning(f"  - {alert}")
    
    def export_metrics(self, filename: str = None) -> str:
        """导出性能指标"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_metrics_{timestamp}.json"
        
        data = {
            'export_time': datetime.now().isoformat(),
            'summary': self.get_performance_summary(),
            'time_series': {
                'api_call_times': list(self.time_series['api_call_times']),
                'db_query_times': list(self.time_series['db_query_times']),
                'cache_query_times': list(self.time_series['cache_query_times']),
                'error_times': list(self.time_series['error_times'])
            },
            'error_stats': dict(self.error_stats)
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"性能指标已导出到: {filename}")
            return filename
        except Exception as e:
            logger.error(f"导出性能指标失败: {e}")
            return None
    
    def reset_metrics(self):
        """重置性能指标"""
        with self.lock:
            self.metrics = {
                'cache_hits': 0,
                'cache_misses': 0,
                'api_calls': 0,
                'db_queries': 0,
                'errors': 0,
                'total_requests': 0
            }
            
            for key in self.time_series:
                self.time_series[key].clear()
            
            self.error_stats.clear()
        
        logger.info("性能指标已重置")
    
    def get_recent_errors(self, last_minutes: int = 60) -> List[Dict]:
        """获取最近的错误"""
        cutoff_time = time.time() - (last_minutes * 60)
        recent_errors = [
            error for error in self.time_series['error_times']
            if error['time'] > cutoff_time
        ]
        return recent_errors
    
    def get_performance_trend(self, metric: str, last_minutes: int = 60) -> List[Dict]:
        """获取性能趋势"""
        cutoff_time = time.time() - (last_minutes * 60)
        
        if metric == 'api_call_time':
            data = self.time_series['api_call_times']
        elif metric == 'db_query_time':
            data = self.time_series['db_query_times']
        elif metric == 'cache_query_time':
            data = self.time_series['cache_query_times']
        else:
            return []
        
        return [item for item in data if item['time'] > cutoff_time]


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def monitor_api_call(func):
    """API调用监控装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            performance_monitor.record_api_call(duration, success=True)
            return result
        except Exception as e:
            duration = time.time() - start_time
            performance_monitor.record_api_call(duration, success=False, error=str(e))
            raise
    return wrapper


def monitor_db_query(func):
    """数据库查询监控装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            performance_monitor.record_db_query(duration, success=True)
            return result
        except Exception as e:
            duration = time.time() - start_time
            performance_monitor.record_db_query(duration, success=False, error=str(e))
            raise
    return wrapper


if __name__ == "__main__":
    # 测试性能监控器
    monitor = PerformanceMonitor()
    
    # 模拟一些性能数据
    import random
    
    for i in range(100):
        # 模拟缓存命中/未命中
        if random.random() < 0.8:
            monitor.record_cache_hit(random.uniform(0.001, 0.01))
        else:
            monitor.record_cache_miss()
        
        # 模拟API调用
        monitor.record_api_call(
            random.uniform(0.5, 3.0),
            success=random.random() < 0.95,
            error="网络超时" if random.random() < 0.05 else None
        )
        
        # 模拟数据库查询
        monitor.record_db_query(
            random.uniform(0.01, 0.5),
            success=random.random() < 0.98
        )
    
    # 打印性能摘要
    summary = monitor.get_performance_summary()
    print("性能摘要:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    # 导出指标
    filename = monitor.export_metrics()
    print(f"性能指标已导出到: {filename}")
