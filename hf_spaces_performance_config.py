# -*- coding: utf-8 -*-
"""
HF Spaces 性能优化配置
针对Hugging Face Spaces环境的专门性能优化配置
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HFSpacesPerformanceConfig:
    """HF Spaces性能优化配置类"""
    
    def __init__(self):
        self.is_hf_spaces = self._detect_hf_spaces()
        self.config = self._load_config()
        
    def _detect_hf_spaces(self) -> bool:
        """检测是否在HF Spaces环境中运行"""
        hf_indicators = [
            'SPACE_ID',
            'SPACE_AUTHOR_NAME', 
            'SPACE_REPO_NAME',
            'HF_HOME'
        ]
        return any(os.getenv(indicator) for indicator in hf_indicators)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载性能优化配置"""
        if self.is_hf_spaces:
            return {
                # 超时配置 - 延长到180秒
                'API_TIMEOUT': 180,
                'ANALYSIS_TIMEOUT': 180,
                'DATA_FETCH_TIMEOUT': 60,
                'REQUEST_TIMEOUT': 180,
                'GUNICORN_TIMEOUT': 300,
                
                # 数据库配置优化
                'DATABASE_POOL_SIZE': 15,
                'DATABASE_POOL_TIMEOUT': 60,
                'DATABASE_POOL_RECYCLE': 1800,
                'DATABASE_POOL_MAX_OVERFLOW': 20,
                
                # 缓存配置优化
                'CACHE_SIZE': 5000,
                'CACHE_TTL': 3600,
                'MEMORY_CACHE_SIZE': 5000,
                'REALTIME_DATA_TTL': 900,
                'BASIC_INFO_TTL': 86400,
                
                # 并发配置优化
                'MAX_WORKERS': 4,
                'MAX_CONCURRENT_REQUESTS': 4,
                'BATCH_SIZE': 20,
                'THREAD_POOL_SIZE': 4,
                
                # AKShare API配置优化
                'AKSHARE_TIMEOUT': 60,
                'AKSHARE_MAX_RETRIES': 5,
                'AKSHARE_RETRY_DELAY': 2,
                
                # 内存优化
                'MEMORY_LIMIT_MB': 1024,
                'ENABLE_COMPRESSION': True,
                'GC_THRESHOLD': 1000,
                
                # 功能开关
                'ENABLE_AI_ANALYSIS': False,
                'ENABLE_COMPLEX_INDICATORS': True,
                'ENABLE_DETAILED_LOGGING': False,
                'ENABLE_FALLBACK': True,
                'PREFER_CACHED_DATA': True,
            }
        else:
            # 本地环境配置
            return {
                'API_TIMEOUT': 30,
                'ANALYSIS_TIMEOUT': 45,
                'DATA_FETCH_TIMEOUT': 20,
                'REQUEST_TIMEOUT': 60,
                'DATABASE_POOL_SIZE': 10,
                'CACHE_SIZE': 1000,
                'MAX_WORKERS': 2,
                'AKSHARE_TIMEOUT': 30,
                'ENABLE_AI_ANALYSIS': True,
                'ENABLE_COMPLEX_INDICATORS': True,
            }
    
    def apply_config(self):
        """应用性能优化配置到环境变量"""
        logger.info(f"应用HF Spaces性能优化配置 (HF环境: {self.is_hf_spaces})")
        
        for key, value in self.config.items():
            os.environ[key] = str(value)
            
        logger.info(f"已设置 {len(self.config)} 个性能优化参数")
        
        # 记录关键配置
        key_configs = [
            'API_TIMEOUT', 'ANALYSIS_TIMEOUT', 'DATABASE_POOL_SIZE', 
            'CACHE_SIZE', 'MAX_WORKERS', 'BATCH_SIZE'
        ]
        
        for key in key_configs:
            if key in self.config:
                logger.info(f"  {key}: {self.config[key]}")
    
    def get_config(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def is_feature_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        feature_key = f"ENABLE_{feature.upper()}"
        return self.config.get(feature_key, True)


def init_hf_spaces_performance():
    """初始化HF Spaces性能优化"""
    try:
        config = HFSpacesPerformanceConfig()
        config.apply_config()
        
        logger.info("✅ HF Spaces性能优化配置初始化成功")
        return config
        
    except Exception as e:
        logger.error(f"❌ HF Spaces性能优化配置初始化失败: {e}")
        return None


def get_hf_timeout(timeout_type: str) -> int:
    """获取HF环境的超时配置"""
    timeout_map = {
        'api': int(os.getenv('API_TIMEOUT', '180')),
        'analysis': int(os.getenv('ANALYSIS_TIMEOUT', '180')),
        'data_fetch': int(os.getenv('DATA_FETCH_TIMEOUT', '60')),
        'request': int(os.getenv('REQUEST_TIMEOUT', '180')),
    }
    return timeout_map.get(timeout_type, 60)


def is_hf_feature_enabled(feature: str) -> bool:
    """检查HF环境中的功能是否启用"""
    feature_key = f"ENABLE_{feature.upper()}"
    return os.getenv(feature_key, 'True').lower() == 'true'


# 自动初始化（如果在HF Spaces环境中）
if __name__ != "__main__":
    # 检测是否在HF Spaces环境中
    hf_indicators = ['SPACE_ID', 'SPACE_AUTHOR_NAME', 'SPACE_REPO_NAME', 'HF_HOME']
    if any(os.getenv(indicator) for indicator in hf_indicators):
        init_hf_spaces_performance()
