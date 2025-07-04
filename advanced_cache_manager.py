#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级缓存管理器
开发者：熊猫大侠
版本：v2.0.0
功能：智能缓存管理、预热、一致性保证、多级缓存策略
"""

import time
import threading
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pickle
import zlib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "L1_MEMORY"      # L1: 内存缓存（最快）
    L2_REDIS = "L2_REDIS"        # L2: Redis缓存（中等速度）
    L3_DATABASE = "L3_DATABASE"  # L3: 数据库缓存（较慢）
    L4_API = "L4_API"           # L4: API调用（最慢）

class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "LRU"                 # 最近最少使用
    LFU = "LFU"                 # 最少使用频率
    TTL = "TTL"                 # 基于时间过期
    ADAPTIVE = "ADAPTIVE"       # 自适应策略

@dataclass
class CacheItem:
    """缓存项"""
    key: str
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_access: float = 0
    size: int = 0
    level: CacheLevel = CacheLevel.L1_MEMORY
    compressed: bool = False

@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    avg_access_time: float = 0.0
    hit_rate: float = 0.0
    memory_usage: int = 0
    
    def update_hit_rate(self):
        """更新命中率"""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests

class AdvancedCacheManager:
    """高级缓存管理器"""
    
    def __init__(self, 
                 l1_size: int = 10000,
                 l2_enabled: bool = False,
                 l3_enabled: bool = True,
                 strategy: CacheStrategy = CacheStrategy.ADAPTIVE,
                 compression_threshold: int = 1024):
        
        self.l1_size = l1_size
        self.l2_enabled = l2_enabled
        self.l3_enabled = l3_enabled
        self.strategy = strategy
        self.compression_threshold = compression_threshold
        
        # L1缓存：内存缓存
        self.l1_cache: OrderedDict[str, CacheItem] = OrderedDict()
        self.l1_stats = CacheStats()
        
        # L2缓存：Redis缓存（如果启用）
        self.redis_client = None
        self.l2_stats = CacheStats()
        
        # L3缓存：数据库缓存
        self.l3_stats = CacheStats()
        
        # 缓存访问统计
        self.access_patterns = defaultdict(list)
        self.hot_keys = set()
        
        # 线程锁
        self.lock = threading.RLock()
        
        # 预热任务
        self.preload_tasks = []
        self.preload_executor = ThreadPoolExecutor(max_workers=5)
        
        # 初始化Redis连接（如果启用）
        if self.l2_enabled:
            self._init_redis()
        
        # 启动后台任务
        self._start_background_tasks()
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            import redis
            import os
            
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
                # 测试连接
                self.redis_client.ping()
                logger.info("Redis缓存已启用")
            else:
                logger.warning("Redis URL未配置，禁用L2缓存")
                self.l2_enabled = False
        except ImportError:
            logger.warning("Redis库未安装，禁用L2缓存")
            self.l2_enabled = False
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.l2_enabled = False
    
    def _start_background_tasks(self):
        """启动后台任务"""
        def background_worker():
            while True:
                try:
                    time.sleep(60)  # 每分钟执行一次
                    self._cleanup_expired()
                    self._analyze_access_patterns()
                    self._optimize_cache_distribution()
                except Exception as e:
                    logger.error(f"后台任务执行失败: {e}")
        
        worker_thread = threading.Thread(target=background_worker, daemon=True)
        worker_thread.start()
    
    def _generate_key(self, data_type: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [data_type]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        key_str = "|".join(key_parts)
        
        # 对长键进行哈希
        if len(key_str) > 200:
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            return f"{data_type}|hash:{key_hash}"
        
        return key_str
    
    def _compress_data(self, data: Any) -> Tuple[bytes, bool]:
        """压缩数据"""
        try:
            serialized = pickle.dumps(data)
            if len(serialized) > self.compression_threshold:
                compressed = zlib.compress(serialized)
                if len(compressed) < len(serialized) * 0.8:  # 压缩率超过20%才使用
                    return compressed, True
            return serialized, False
        except Exception as e:
            logger.warning(f"数据压缩失败: {e}")
            return pickle.dumps(data), False
    
    def _decompress_data(self, data: bytes, compressed: bool) -> Any:
        """解压数据"""
        try:
            if compressed:
                decompressed = zlib.decompress(data)
                return pickle.loads(decompressed)
            else:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"数据解压失败: {e}")
            return None
    
    def _calculate_size(self, data: Any) -> int:
        """计算数据大小"""
        try:
            return len(pickle.dumps(data))
        except:
            return 0
    
    def get(self, data_type: str, ttl: int = 900, **kwargs) -> Optional[Any]:
        """获取缓存数据"""
        key = self._generate_key(data_type, **kwargs)
        start_time = time.time()
        
        try:
            # L1缓存查询
            result = self._get_from_l1(key, ttl)
            if result is not None:
                self._record_access(key, CacheLevel.L1_MEMORY, time.time() - start_time)
                return result
            
            # L2缓存查询（Redis）
            if self.l2_enabled:
                result = self._get_from_l2(key, ttl)
                if result is not None:
                    # 回写到L1缓存
                    self._set_to_l1(key, result, ttl)
                    self._record_access(key, CacheLevel.L2_REDIS, time.time() - start_time)
                    return result
            
            # L3缓存查询（数据库）
            if self.l3_enabled:
                result = self._get_from_l3(key, ttl, data_type, **kwargs)
                if result is not None:
                    # 回写到上级缓存
                    self._set_to_l1(key, result, ttl)
                    if self.l2_enabled:
                        self._set_to_l2(key, result, ttl)
                    self._record_access(key, CacheLevel.L3_DATABASE, time.time() - start_time)
                    return result
            
            # 缓存未命中
            self._record_miss(key, time.time() - start_time)
            return None
            
        except Exception as e:
            logger.error(f"缓存获取失败: {e}")
            return None
    
    def set(self, data_type: str, data: Any, ttl: int = 900, **kwargs) -> bool:
        """设置缓存数据"""
        key = self._generate_key(data_type, **kwargs)
        
        try:
            # 写入所有级别的缓存
            success = True
            
            # L1缓存
            success &= self._set_to_l1(key, data, ttl)
            
            # L2缓存（Redis）
            if self.l2_enabled:
                success &= self._set_to_l2(key, data, ttl)
            
            # L3缓存（数据库）
            if self.l3_enabled:
                success &= self._set_to_l3(key, data, ttl, data_type, **kwargs)
            
            return success
            
        except Exception as e:
            logger.error(f"缓存设置失败: {e}")
            return False
    
    def _get_from_l1(self, key: str, ttl: int) -> Optional[Any]:
        """从L1缓存获取数据"""
        with self.lock:
            if key in self.l1_cache:
                item = self.l1_cache[key]
                
                # 检查是否过期
                if time.time() - item.timestamp < ttl:
                    # 更新访问信息
                    item.access_count += 1
                    item.last_access = time.time()
                    
                    # 移动到末尾（LRU策略）
                    self.l1_cache.move_to_end(key)
                    
                    self.l1_stats.hits += 1
                    return item.data
                else:
                    # 过期删除
                    del self.l1_cache[key]
            
            self.l1_stats.misses += 1
            return None
    
    def _set_to_l1(self, key: str, data: Any, ttl: int) -> bool:
        """设置L1缓存"""
        with self.lock:
            try:
                # 检查是否需要清理空间
                if len(self.l1_cache) >= self.l1_size:
                    self._evict_l1_items()
                
                # 创建缓存项
                item = CacheItem(
                    key=key,
                    data=data,
                    timestamp=time.time(),
                    ttl=ttl,
                    access_count=1,
                    last_access=time.time(),
                    size=self._calculate_size(data),
                    level=CacheLevel.L1_MEMORY
                )
                
                self.l1_cache[key] = item
                return True
                
            except Exception as e:
                logger.error(f"L1缓存设置失败: {e}")
                return False
    
    def _evict_l1_items(self):
        """清理L1缓存项"""
        if self.strategy == CacheStrategy.LRU:
            # 删除最近最少使用的项
            items_to_remove = len(self.l1_cache) - self.l1_size + 1000
            for _ in range(min(items_to_remove, len(self.l1_cache))):
                self.l1_cache.popitem(last=False)
                self.l1_stats.evictions += 1
        
        elif self.strategy == CacheStrategy.LFU:
            # 删除使用频率最低的项
            sorted_items = sorted(self.l1_cache.items(), 
                                key=lambda x: x[1].access_count)
            items_to_remove = len(self.l1_cache) - self.l1_size + 1000
            
            for i in range(min(items_to_remove, len(sorted_items))):
                key = sorted_items[i][0]
                if key in self.l1_cache:
                    del self.l1_cache[key]
                    self.l1_stats.evictions += 1
        
        elif self.strategy == CacheStrategy.ADAPTIVE:
            # 自适应策略：结合访问频率和时间
            current_time = time.time()
            scored_items = []
            
            for key, item in self.l1_cache.items():
                # 计算综合分数（访问频率 + 时间衰减）
                time_factor = 1.0 / (current_time - item.last_access + 1)
                freq_factor = item.access_count
                score = time_factor * freq_factor
                scored_items.append((key, score))
            
            # 删除分数最低的项
            scored_items.sort(key=lambda x: x[1])
            items_to_remove = len(self.l1_cache) - self.l1_size + 1000
            
            for i in range(min(items_to_remove, len(scored_items))):
                key = scored_items[i][0]
                if key in self.l1_cache:
                    del self.l1_cache[key]
                    self.l1_stats.evictions += 1
    
    def _get_from_l2(self, key: str, ttl: int) -> Optional[Any]:
        """从L2缓存（Redis）获取数据"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                # 解压数据
                cache_item = pickle.loads(data)
                if time.time() - cache_item['timestamp'] < ttl:
                    self.l2_stats.hits += 1
                    return self._decompress_data(cache_item['data'], cache_item['compressed'])
                else:
                    # 过期删除
                    self.redis_client.delete(key)
            
            self.l2_stats.misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Redis获取失败: {e}")
            self.l2_stats.misses += 1
            return None
    
    def _set_to_l2(self, key: str, data: Any, ttl: int) -> bool:
        """设置L2缓存（Redis）"""
        if not self.redis_client:
            return False
        
        try:
            # 压缩数据
            compressed_data, is_compressed = self._compress_data(data)
            
            cache_item = {
                'data': compressed_data,
                'timestamp': time.time(),
                'compressed': is_compressed
            }
            
            serialized = pickle.dumps(cache_item)
            self.redis_client.setex(key, ttl, serialized)
            return True
            
        except Exception as e:
            logger.error(f"Redis设置失败: {e}")
            return False
    
    def _get_from_l3(self, key: str, ttl: int, data_type: str, **kwargs) -> Optional[Any]:
        """从L3缓存（数据库）获取数据"""
        try:
            # 确保在Flask应用上下文中执行
            try:
                from flask import has_app_context
                if not has_app_context():
                    # 如果没有应用上下文，尝试创建一个
                    try:
                        from web_server import app
                        with app.app_context():
                            return self._get_from_l3_internal(key, ttl, data_type, **kwargs)
                    except Exception as e:
                        logger.warning(f"无法创建应用上下文，跳过L3缓存: {e}")
                        self.l3_stats.misses += 1
                        return None
                else:
                    return self._get_from_l3_internal(key, ttl, data_type, **kwargs)
            except ImportError:
                # Flask不可用，直接调用内部方法
                return self._get_from_l3_internal(key, ttl, data_type, **kwargs)

        except Exception as e:
            logger.error(f"L3缓存获取失败: {e}")
            self.l3_stats.misses += 1
            return None

    def _get_from_l3_internal(self, key: str, ttl: int, data_type: str, **kwargs) -> Optional[Any]:
        """L3缓存内部获取逻辑"""
        try:
            from database import get_session, StockBasicInfo, StockRealtimeData, FinancialData, CapitalFlowData
            from datetime import datetime

            session = get_session()
            result = None

            # 根据数据类型查询相应的表
            if data_type == 'basic_info':
                stock_code = kwargs.get('stock_code')
                if stock_code:
                    record = session.query(StockBasicInfo).filter_by(
                        stock_code=stock_code
                    ).filter(
                        StockBasicInfo.expires_at > datetime.now()
                    ).first()
                    if record:
                        result = record.to_dict()
                        self.l3_stats.hits += 1
                    else:
                        self.l3_stats.misses += 1

            elif data_type == 'realtime':
                stock_code = kwargs.get('stock_code')
                if stock_code:
                    record = session.query(StockRealtimeData).filter_by(
                        stock_code=stock_code
                    ).filter(
                        StockRealtimeData.expires_at > datetime.now()
                    ).first()
                    if record:
                        result = record.to_dict()
                        self.l3_stats.hits += 1
                    else:
                        self.l3_stats.misses += 1

            session.close()
            return result

        except Exception as e:
            logger.error(f"L3缓存内部获取失败: {e}")
            if 'session' in locals():
                session.close()
            self.l3_stats.misses += 1
            return None
    
    def _set_to_l3(self, key: str, data: Any, ttl: int, data_type: str, **kwargs) -> bool:
        """设置L3缓存（数据库）"""
        # 这里需要根据具体的数据类型调用相应的数据库保存
        # 暂时返回True，由具体实现类重写
        return True
    
    def _record_access(self, key: str, level: CacheLevel, access_time: float):
        """记录访问信息"""
        # 更新统计
        if level == CacheLevel.L1_MEMORY:
            self.l1_stats.total_requests += 1
            self.l1_stats.avg_access_time = (
                (self.l1_stats.avg_access_time * (self.l1_stats.total_requests - 1) + access_time) 
                / self.l1_stats.total_requests
            )
            self.l1_stats.update_hit_rate()
        elif level == CacheLevel.L2_REDIS:
            self.l2_stats.total_requests += 1
            self.l2_stats.update_hit_rate()
        elif level == CacheLevel.L3_DATABASE:
            self.l3_stats.total_requests += 1
            self.l3_stats.update_hit_rate()
        
        # 记录访问模式
        self.access_patterns[key].append({
            'timestamp': time.time(),
            'level': level.value,
            'access_time': access_time
        })
        
        # 保持访问历史在合理范围内
        if len(self.access_patterns[key]) > 100:
            self.access_patterns[key] = self.access_patterns[key][-50:]
    
    def _record_miss(self, key: str, access_time: float):
        """记录缓存未命中"""
        self.l1_stats.total_requests += 1
        self.l1_stats.update_hit_rate()
        
        if self.l2_enabled:
            self.l2_stats.total_requests += 1
            self.l2_stats.update_hit_rate()
        
        if self.l3_enabled:
            self.l3_stats.total_requests += 1
            self.l3_stats.update_hit_rate()
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        with self.lock:
            for key, item in self.l1_cache.items():
                if current_time - item.timestamp > item.ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.l1_cache[key]
        
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def _analyze_access_patterns(self):
        """分析访问模式"""
        current_time = time.time()
        hot_threshold = 10  # 热点数据阈值
        
        # 分析热点数据
        hot_keys = set()
        for key, accesses in self.access_patterns.items():
            # 统计最近1小时的访问次数
            recent_accesses = [
                a for a in accesses 
                if current_time - a['timestamp'] < 3600
            ]
            
            if len(recent_accesses) >= hot_threshold:
                hot_keys.add(key)
        
        self.hot_keys = hot_keys
        
        if hot_keys:
            logger.info(f"检测到 {len(hot_keys)} 个热点缓存键")
    
    def _optimize_cache_distribution(self):
        """优化缓存分布"""
        # 将热点数据优先保留在L1缓存
        with self.lock:
            for key in self.hot_keys:
                if key in self.l1_cache:
                    # 移动到末尾，降低被清理的概率
                    self.l1_cache.move_to_end(key)
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            'l1_cache': asdict(self.l1_stats),
            'l2_cache': asdict(self.l2_stats) if self.l2_enabled else None,
            'l3_cache': asdict(self.l3_stats) if self.l3_enabled else None,
            'cache_sizes': {
                'l1_items': len(self.l1_cache),
                'l1_max_size': self.l1_size,
                'hot_keys': len(self.hot_keys)
            },
            'strategy': self.strategy.value,
            'levels_enabled': {
                'l1': True,
                'l2': self.l2_enabled,
                'l3': self.l3_enabled
            }
        }
    
    def preload_data(self, data_loader: Callable, keys: List[str], ttl: int = 900):
        """预加载数据"""
        def preload_task():
            for key in keys:
                try:
                    data = data_loader(key)
                    if data is not None:
                        # 解析键获取参数
                        parts = key.split('|')
                        data_type = parts[0]
                        kwargs = {}
                        for part in parts[1:]:
                            if '=' in part:
                                k, v = part.split('=', 1)
                                kwargs[k] = v
                        
                        self.set(data_type, data, ttl, **kwargs)
                        logger.debug(f"预加载缓存: {key}")
                except Exception as e:
                    logger.error(f"预加载失败 {key}: {e}")
        
        future = self.preload_executor.submit(preload_task)
        self.preload_tasks.append(future)
        return future
    
    def invalidate(self, pattern: str = None, data_type: str = None):
        """失效缓存"""
        keys_to_remove = []
        
        with self.lock:
            for key in self.l1_cache.keys():
                if pattern and pattern in key:
                    keys_to_remove.append(key)
                elif data_type and key.startswith(data_type):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.l1_cache[key]
        
        # 同时清理Redis缓存
        if self.l2_enabled and self.redis_client:
            try:
                if pattern:
                    keys = self.redis_client.keys(f"*{pattern}*")
                elif data_type:
                    keys = self.redis_client.keys(f"{data_type}*")
                else:
                    keys = []
                
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis缓存失效失败: {e}")
        
        logger.info(f"失效了 {len(keys_to_remove)} 个缓存项")


# 全局高级缓存管理器实例
advanced_cache_manager = AdvancedCacheManager()


if __name__ == "__main__":
    # 测试高级缓存管理器
    cache = AdvancedCacheManager(l1_size=1000, strategy=CacheStrategy.ADAPTIVE)
    
    # 测试数据
    test_data = {"stock_code": "000001", "price": 10.5, "volume": 1000000}
    
    # 设置缓存
    cache.set("test_stock", test_data, ttl=300, stock_code="000001")
    
    # 获取缓存
    result = cache.get("test_stock", ttl=300, stock_code="000001")
    print(f"缓存结果: {result}")
    
    # 获取统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {json.dumps(stats, indent=2)}")
    
    print("高级缓存管理器测试完成！")
