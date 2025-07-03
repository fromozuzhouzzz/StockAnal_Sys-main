# -*- coding: utf-8 -*-
"""
API限流器 - 防止API滥用，支持多种限流策略
"""

import time
import threading
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify, g
import hashlib
import os
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """API限流器 - 支持滑动窗口和令牌桶算法"""
    
    def __init__(self):
        self.requests = defaultdict(deque)  # 存储请求时间戳
        self.tokens = defaultdict(dict)     # 令牌桶存储
        self.lock = threading.RLock()
        
        # 默认限流配置
        self.default_limits = {
            'free': {'requests': 100, 'window': 3600},      # 免费用户: 100次/小时
            'paid': {'requests': 1000, 'window': 3600},     # 付费用户: 1000次/小时  
            'enterprise': {'requests': 10000, 'window': 3600}, # 企业用户: 10000次/小时
            'ip': {'requests': 200, 'window': 3600}         # IP限制: 200次/小时
        }
        
        # 端点特定限流配置
        self.endpoint_limits = {
            '/api/v1/stock/analyze': {'requests': 50, 'window': 3600},
            '/api/v1/portfolio/analyze': {'requests': 20, 'window': 3600},
            '/api/v1/stocks/batch-score': {'requests': 10, 'window': 3600}
        }
    
    def get_user_tier(self, api_key):
        """根据API密钥获取用户等级"""
        # 这里可以从数据库或配置文件中获取用户等级
        # 暂时使用简单的映射
        tier_mapping = {
            'enterprise_': 'enterprise',
            'paid_': 'paid',
            'free_': 'free'
        }
        
        for prefix, tier in tier_mapping.items():
            if api_key.startswith(prefix):
                return tier
        
        return 'free'  # 默认为免费用户
    
    def get_client_id(self):
        """获取客户端标识符"""
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"api_key:{api_key}"
        else:
            # 使用IP地址作为标识符
            return f"ip:{request.remote_addr}"
    
    def sliding_window_check(self, client_id, limit_config):
        """滑动窗口限流检查"""
        current_time = time.time()
        window_start = current_time - limit_config['window']
        
        with self.lock:
            # 清理过期的请求记录
            while (self.requests[client_id] and 
                   self.requests[client_id][0] < window_start):
                self.requests[client_id].popleft()
            
            # 检查是否超过限制
            if len(self.requests[client_id]) >= limit_config['requests']:
                return False, len(self.requests[client_id])
            
            # 记录当前请求
            self.requests[client_id].append(current_time)
            return True, len(self.requests[client_id])
    
    def token_bucket_check(self, client_id, limit_config):
        """令牌桶限流检查"""
        current_time = time.time()
        bucket_key = f"{client_id}:bucket"
        
        with self.lock:
            if bucket_key not in self.tokens:
                # 初始化令牌桶
                self.tokens[bucket_key] = {
                    'tokens': limit_config['requests'],
                    'last_refill': current_time,
                    'capacity': limit_config['requests'],
                    'refill_rate': limit_config['requests'] / limit_config['window']
                }
            
            bucket = self.tokens[bucket_key]
            
            # 计算需要添加的令牌数
            time_passed = current_time - bucket['last_refill']
            tokens_to_add = time_passed * bucket['refill_rate']
            
            # 更新令牌数量
            bucket['tokens'] = min(bucket['capacity'], 
                                 bucket['tokens'] + tokens_to_add)
            bucket['last_refill'] = current_time
            
            # 检查是否有足够的令牌
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                return True, bucket['tokens']
            else:
                return False, bucket['tokens']
    
    def check_rate_limit(self, endpoint=None):
        """检查是否超过限流"""
        client_id = self.get_client_id()
        api_key = request.headers.get('X-API-Key')
        
        # 确定限流配置
        if api_key:
            user_tier = self.get_user_tier(api_key)
            limit_config = self.default_limits[user_tier].copy()
        else:
            limit_config = self.default_limits['ip'].copy()
        
        # 检查端点特定限制
        if endpoint and endpoint in self.endpoint_limits:
            endpoint_config = self.endpoint_limits[endpoint]
            # 使用更严格的限制
            if endpoint_config['requests'] < limit_config['requests']:
                limit_config = endpoint_config
        
        # 执行限流检查（使用滑动窗口算法）
        allowed, current_count = self.sliding_window_check(client_id, limit_config)
        
        # 计算重置时间
        reset_time = int(time.time()) + limit_config['window']
        remaining = max(0, limit_config['requests'] - current_count)
        
        return {
            'allowed': allowed,
            'limit': limit_config['requests'],
            'remaining': remaining,
            'reset_time': reset_time,
            'current_count': current_count
        }
    
    def cleanup_expired_records(self):
        """清理过期的限流记录"""
        current_time = time.time()
        
        with self.lock:
            # 清理请求记录
            for client_id in list(self.requests.keys()):
                while (self.requests[client_id] and 
                       self.requests[client_id][0] < current_time - 3600):
                    self.requests[client_id].popleft()
                
                # 删除空的记录
                if not self.requests[client_id]:
                    del self.requests[client_id]
            
            # 清理令牌桶记录
            for bucket_key in list(self.tokens.keys()):
                if self.tokens[bucket_key]['last_refill'] < current_time - 7200:
                    del self.tokens[bucket_key]


# 全局限流器实例
rate_limiter = RateLimiter()


def require_rate_limit(endpoint=None):
    """限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查限流
            result = rate_limiter.check_rate_limit(endpoint or request.endpoint)
            
            if not result['allowed']:
                response = jsonify({
                    'success': False,
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': '请求频率超过限制',
                        'details': {
                            'limit': result['limit'],
                            'reset_time': result['reset_time']
                        }
                    }
                })
                response.status_code = 429
                
                # 添加限流相关的响应头
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                response.headers['X-RateLimit-Reset'] = str(result['reset_time'])
                
                return response
            
            # 在响应中添加限流信息
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(result['limit'])
                response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                response.headers['X-RateLimit-Reset'] = str(result['reset_time'])
            
            return response
        
        return decorated_function
    return decorator


def adaptive_rate_limit(base_limit=None):
    """自适应限流装饰器 - 根据系统负载动态调整"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取系统负载信息
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory_percent = psutil.virtual_memory().percent
                
                # 根据系统负载调整限流
                load_factor = 1.0
                if cpu_percent > 80 or memory_percent > 80:
                    load_factor = 0.5  # 高负载时减少50%的请求
                elif cpu_percent > 60 or memory_percent > 60:
                    load_factor = 0.7  # 中等负载时减少30%的请求
                
                # 临时调整限流配置
                original_limits = rate_limiter.default_limits.copy()
                for tier in rate_limiter.default_limits:
                    rate_limiter.default_limits[tier]['requests'] = int(
                        original_limits[tier]['requests'] * load_factor
                    )
                
                try:
                    return require_rate_limit()(f)(*args, **kwargs)
                finally:
                    # 恢复原始限流配置
                    rate_limiter.default_limits = original_limits
                    
            except ImportError:
                # 如果psutil不可用，使用普通限流
                return require_rate_limit()(f)(*args, **kwargs)
        
        return decorated_function
    return decorator


def get_rate_limit_status():
    """获取当前限流状态"""
    client_id = rate_limiter.get_client_id()
    api_key = request.headers.get('X-API-Key')
    
    if api_key:
        user_tier = rate_limiter.get_user_tier(api_key)
        limit_config = rate_limiter.default_limits[user_tier]
    else:
        limit_config = rate_limiter.default_limits['ip']
    
    current_time = time.time()
    window_start = current_time - limit_config['window']
    
    with rate_limiter.lock:
        # 清理过期记录
        while (rate_limiter.requests[client_id] and 
               rate_limiter.requests[client_id][0] < window_start):
            rate_limiter.requests[client_id].popleft()
        
        current_count = len(rate_limiter.requests[client_id])
        remaining = max(0, limit_config['requests'] - current_count)
        reset_time = int(current_time) + limit_config['window']
        
        return {
            'limit': limit_config['requests'],
            'remaining': remaining,
            'reset_time': reset_time,
            'current_count': current_count,
            'window_seconds': limit_config['window']
        }


# 定期清理过期记录的后台任务
def start_cleanup_scheduler():
    """启动清理调度器"""
    def cleanup_worker():
        while True:
            try:
                rate_limiter.cleanup_expired_records()
                time.sleep(300)  # 每5分钟清理一次
            except Exception as e:
                logger.error(f"限流记录清理出错: {e}")
                time.sleep(60)  # 出错时等待1分钟再重试
    
    import threading
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("限流记录清理调度器已启动")


# 启动清理调度器
if __name__ != '__main__':
    start_cleanup_scheduler()
