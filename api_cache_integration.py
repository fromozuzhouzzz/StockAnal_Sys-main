# -*- coding: utf-8 -*-
"""
API缓存集成模块
确保API接口与现有MySQL缓存系统良好集成，优化数据获取性能
"""

import logging
import time
import hashlib
import json
from typing import Dict, Any, Optional, List
from functools import wraps
from flask import request, g

# 导入现有的缓存和数据库模块
try:
    from database import get_session, USE_DATABASE, StockData, AnalysisCache
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    USE_DATABASE = False

logger = logging.getLogger(__name__)


class APICacheManager:
    """API缓存管理器"""
    
    def __init__(self):
        self.cache_ttl = {
            'stock_analysis': 900,      # 个股分析：15分钟
            'portfolio_analysis': 300,  # 组合分析：5分钟
            'batch_score': 600,         # 批量评分：10分钟
            'market_data': 300,         # 市场数据：5分钟
            'fundamental_data': 86400,  # 基本面数据：1天
            'technical_indicators': 900 # 技术指标：15分钟
        }
    
    def generate_cache_key(self, cache_type: str, params: Dict) -> str:
        """生成缓存键"""
        # 创建参数的哈希值
        params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:16]
        
        # 添加用户等级信息（不同等级可能有不同的分析深度）
        user_tier = getattr(g, 'user_tier', 'free')
        
        return f"api_cache:{cache_type}:{user_tier}:{params_hash}"
    
    def get_cache(self, cache_key: str) -> Optional[Dict]:
        """从缓存获取数据"""
        if not DATABASE_AVAILABLE or not USE_DATABASE:
            return None
        
        try:
            session = get_session()
            cache_record = session.query(AnalysisCache).filter(
                AnalysisCache.cache_key == cache_key,
                AnalysisCache.expires_at > time.time()
            ).first()
            
            if cache_record:
                session.close()
                return {
                    'data': json.loads(cache_record.cache_data),
                    'created_at': cache_record.created_at,
                    'cache_hit': True
                }
            
            session.close()
            return None
            
        except Exception as e:
            logger.error(f"获取缓存数据出错: {e}")
            return None
    
    def set_cache(self, cache_key: str, data: Dict, ttl: int = None) -> bool:
        """设置缓存数据"""
        if not DATABASE_AVAILABLE or not USE_DATABASE:
            return False
        
        try:
            session = get_session()
            
            # 删除旧的缓存记录
            session.query(AnalysisCache).filter(
                AnalysisCache.cache_key == cache_key
            ).delete()
            
            # 创建新的缓存记录
            cache_record = AnalysisCache(
                cache_key=cache_key,
                cache_data=json.dumps(data, ensure_ascii=False),
                created_at=time.time(),
                expires_at=time.time() + (ttl or 900)
            )
            
            session.add(cache_record)
            session.commit()
            session.close()
            
            return True
            
        except Exception as e:
            logger.error(f"设置缓存数据出错: {e}")
            return False
    
    def invalidate_cache(self, pattern: str = None) -> int:
        """清除缓存"""
        if not DATABASE_AVAILABLE or not USE_DATABASE:
            return 0
        
        try:
            session = get_session()
            
            if pattern:
                # 清除匹配模式的缓存
                count = session.query(AnalysisCache).filter(
                    AnalysisCache.cache_key.like(f"%{pattern}%")
                ).delete(synchronize_session=False)
            else:
                # 清除过期缓存
                count = session.query(AnalysisCache).filter(
                    AnalysisCache.expires_at < time.time()
                ).delete(synchronize_session=False)
            
            session.commit()
            session.close()
            
            return count
            
        except Exception as e:
            logger.error(f"清除缓存出错: {e}")
            return 0


# 全局缓存管理器
api_cache_manager = APICacheManager()


def api_cache(cache_type: str, ttl: int = None, key_params: List[str] = None):
    """API缓存装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 生成缓存键
            if key_params:
                # 使用指定的参数生成缓存键
                cache_params = {}
                request_data = request.get_json() or {}
                for param in key_params:
                    if param in request_data:
                        cache_params[param] = request_data[param]
            else:
                # 使用所有请求参数
                cache_params = request.get_json() or {}
            
            cache_key = api_cache_manager.generate_cache_key(cache_type, cache_params)
            
            # 尝试从缓存获取数据
            cached_result = api_cache_manager.get_cache(cache_key)
            if cached_result:
                logger.info(f"API缓存命中: {cache_key}")
                return cached_result['data']
            
            # 执行原函数
            start_time = time.time()
            result = f(*args, **kwargs)
            processing_time = time.time() - start_time
            
            # 将结果存入缓存
            cache_ttl = ttl or api_cache_manager.cache_ttl.get(cache_type, 900)
            
            # 只缓存成功的结果
            if hasattr(result, 'status_code') and result.status_code == 200:
                try:
                    result_data = result.get_json()
                    if result_data.get('success'):
                        # 添加缓存元数据
                        if 'meta' not in result_data:
                            result_data['meta'] = {}
                        result_data['meta']['cache_hit'] = False
                        result_data['meta']['processing_time_ms'] = int(processing_time * 1000)
                        
                        api_cache_manager.set_cache(cache_key, result_data, cache_ttl)
                        logger.info(f"API结果已缓存: {cache_key}, TTL: {cache_ttl}秒")
                except Exception as e:
                    logger.error(f"缓存API结果出错: {e}")
            
            return result
        
        return decorated_function
    return decorator


def smart_cache_invalidation(stock_codes: List[str] = None, cache_types: List[str] = None):
    """智能缓存失效"""
    try:
        if stock_codes:
            # 清除特定股票相关的缓存
            for stock_code in stock_codes:
                pattern = f"stock_code:{stock_code}"
                count = api_cache_manager.invalidate_cache(pattern)
                logger.info(f"清除股票 {stock_code} 相关缓存: {count} 条")
        
        if cache_types:
            # 清除特定类型的缓存
            for cache_type in cache_types:
                pattern = f"api_cache:{cache_type}"
                count = api_cache_manager.invalidate_cache(pattern)
                logger.info(f"清除 {cache_type} 类型缓存: {count} 条")
        
        # 清除过期缓存
        expired_count = api_cache_manager.invalidate_cache()
        if expired_count > 0:
            logger.info(f"清除过期缓存: {expired_count} 条")
            
    except Exception as e:
        logger.error(f"智能缓存失效出错: {e}")


def get_cache_statistics() -> Dict:
    """获取缓存统计信息"""
    if not DATABASE_AVAILABLE or not USE_DATABASE:
        return {'error': '数据库不可用'}
    
    try:
        session = get_session()
        
        # 总缓存数量
        total_count = session.query(AnalysisCache).count()
        
        # 有效缓存数量
        valid_count = session.query(AnalysisCache).filter(
            AnalysisCache.expires_at > time.time()
        ).count()
        
        # 过期缓存数量
        expired_count = total_count - valid_count
        
        # 按类型统计
        type_stats = {}
        cache_records = session.query(AnalysisCache).all()
        
        for record in cache_records:
            cache_type = record.cache_key.split(':')[1] if ':' in record.cache_key else 'unknown'
            if cache_type not in type_stats:
                type_stats[cache_type] = {'total': 0, 'valid': 0, 'expired': 0}
            
            type_stats[cache_type]['total'] += 1
            if record.expires_at > time.time():
                type_stats[cache_type]['valid'] += 1
            else:
                type_stats[cache_type]['expired'] += 1
        
        session.close()
        
        return {
            'total_count': total_count,
            'valid_count': valid_count,
            'expired_count': expired_count,
            'hit_rate': 0.0,  # 需要额外统计
            'type_statistics': type_stats
        }
        
    except Exception as e:
        logger.error(f"获取缓存统计出错: {e}")
        return {'error': str(e)}


def preload_cache_for_popular_stocks():
    """为热门股票预加载缓存"""
    popular_stocks = [
        '000001.SZ', '000002.SZ', '600000.SH', '600036.SH', '000858.SZ',
        '600519.SH', '000725.SZ', '002415.SZ', '600276.SH', '000568.SZ'
    ]
    
    logger.info("开始为热门股票预加载缓存")
    
    try:
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        for stock_code in popular_stocks:
            try:
                # 预加载个股分析数据
                result = analyzer.quick_analyze_stock(stock_code, 'A')
                
                # 生成缓存键并存储
                cache_params = {'stock_code': stock_code, 'market_type': 'A'}
                cache_key = api_cache_manager.generate_cache_key('stock_analysis', cache_params)
                
                api_cache_manager.set_cache(cache_key, {
                    'success': True,
                    'data': result,
                    'meta': {'preloaded': True}
                }, 1800)  # 30分钟TTL
                
                logger.info(f"预加载股票 {stock_code} 缓存完成")
                
            except Exception as e:
                logger.error(f"预加载股票 {stock_code} 缓存失败: {e}")
        
        logger.info("热门股票缓存预加载完成")
        
    except Exception as e:
        logger.error(f"预加载缓存出错: {e}")


def schedule_cache_cleanup():
    """定期清理缓存"""
    import threading
    import time
    
    def cleanup_worker():
        while True:
            try:
                # 每小时清理一次过期缓存
                expired_count = api_cache_manager.invalidate_cache()
                if expired_count > 0:
                    logger.info(f"定期清理过期缓存: {expired_count} 条")
                
                time.sleep(3600)  # 1小时
                
            except Exception as e:
                logger.error(f"定期缓存清理出错: {e}")
                time.sleep(300)  # 出错时等待5分钟
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("缓存清理调度器已启动")


# 启动缓存清理调度器
if DATABASE_AVAILABLE and USE_DATABASE:
    schedule_cache_cleanup()
