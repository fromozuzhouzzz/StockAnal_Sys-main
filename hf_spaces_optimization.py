# -*- coding: utf-8 -*-
"""
Hugging Face Spaces 平台优化配置
针对HF Spaces的资源限制和环境特点进行优化
"""

import os
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HFSpacesOptimizer:
    """Hugging Face Spaces 优化器"""
    
    def __init__(self):
        self.is_hf_spaces = self._detect_hf_spaces()
        self.optimization_config = self._get_optimization_config()
        
    def _detect_hf_spaces(self) -> bool:
        """检测是否运行在Hugging Face Spaces环境"""
        # HF Spaces 特有的环境变量
        hf_indicators = [
            'SPACE_ID',
            'SPACE_AUTHOR_NAME', 
            'SPACE_REPO_NAME',
            'GRADIO_SERVER_NAME'
        ]
        
        for indicator in hf_indicators:
            if os.getenv(indicator):
                logger.info(f"检测到Hugging Face Spaces环境: {indicator}={os.getenv(indicator)}")
                return True
        
        # 检查域名
        if 'hf.space' in os.getenv('GRADIO_SERVER_NAME', ''):
            logger.info("通过域名检测到Hugging Face Spaces环境")
            return True
            
        return False
    
    def _get_optimization_config(self) -> Dict[str, Any]:
        """获取优化配置"""
        if self.is_hf_spaces:
            return {
                # 超时配置 - 延长超时时间以适应复杂分析
                'api_timeout': 180,  # API请求超时（秒）- 延长到3分钟
                'analysis_timeout': 180,  # 分析超时（秒）- 延长到3分钟
                'data_fetch_timeout': 60,  # 数据获取超时（秒）- 延长到1分钟
                
                # 资源限制 - 优化并发和批处理
                'max_concurrent_requests': 4,  # 最大并发请求数 - 增加并发
                'max_stocks_per_batch': 20,  # 批量分析最大股票数 - 增加批次大小
                'memory_limit_mb': 1024,  # 内存限制（MB）- 增加内存限制
                
                # 缓存配置 - 优化缓存策略
                'cache_size': 5000,  # 缓存大小 - 增加缓存容量
                'cache_ttl': 3600,  # 缓存TTL（秒）- 延长缓存时间
                
                # 重试配置
                'max_retries': 2,  # 最大重试次数
                'retry_delay': 1,  # 重试延迟（秒）
                
                # 数据源配置
                'enable_fallback': True,  # 启用降级策略
                'prefer_cached_data': True,  # 优先使用缓存数据
                
                # 功能开关
                'enable_ai_analysis': False,  # 关闭AI分析以节省资源
                'enable_complex_indicators': False,  # 关闭复杂指标计算
                'enable_detailed_logging': False,  # 关闭详细日志
            }
        else:
            # 本地或其他环境的默认配置
            return {
                'api_timeout': 60,
                'analysis_timeout': 120,
                'data_fetch_timeout': 30,
                'max_concurrent_requests': 10,
                'max_stocks_per_batch': 50,
                'memory_limit_mb': 2048,
                'cache_size': 5000,
                'cache_ttl': 900,
                'max_retries': 3,
                'retry_delay': 2,
                'enable_fallback': True,
                'prefer_cached_data': False,
                'enable_ai_analysis': True,
                'enable_complex_indicators': True,
                'enable_detailed_logging': True,
            }
    
    def apply_optimizations(self):
        """应用优化配置"""
        if not self.is_hf_spaces:
            logger.info("非HF Spaces环境，跳过优化")
            return
            
        logger.info("应用Hugging Face Spaces优化配置")
        
        # 设置环境变量
        for key, value in self.optimization_config.items():
            env_key = f"HF_OPT_{key.upper()}"
            os.environ[env_key] = str(value)
            
        # 应用特定优化
        self._optimize_logging()
        self._optimize_memory()
        self._optimize_timeouts()
        
        logger.info("Hugging Face Spaces优化配置已应用")
    
    def _optimize_logging(self):
        """优化日志配置"""
        if self.optimization_config.get('enable_detailed_logging', False):
            return
            
        # 减少日志级别以节省资源
        logging.getLogger('akshare').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        
        logger.info("已优化日志配置")
    
    def _optimize_memory(self):
        """优化内存使用"""
        import gc
        
        # 强制垃圾回收
        gc.collect()
        
        # 设置内存限制相关的环境变量
        memory_limit = self.optimization_config.get('memory_limit_mb', 512)
        os.environ['MEMORY_LIMIT_MB'] = str(memory_limit)
        
        logger.info(f"已设置内存限制: {memory_limit}MB")
    
    def _optimize_timeouts(self):
        """优化超时配置"""
        timeouts = {
            'API_TIMEOUT': self.optimization_config.get('api_timeout', 30),
            'ANALYSIS_TIMEOUT': self.optimization_config.get('analysis_timeout', 45),
            'DATA_FETCH_TIMEOUT': self.optimization_config.get('data_fetch_timeout', 20),
        }
        
        for key, value in timeouts.items():
            os.environ[key] = str(value)
            
        logger.info(f"已设置超时配置: {timeouts}")
    
    def get_config(self, key: str, default=None):
        """获取配置值"""
        return self.optimization_config.get(key, default)
    
    def is_feature_enabled(self, feature: str) -> bool:
        """检查功能是否启用"""
        return self.optimization_config.get(f'enable_{feature}', True)
    
    def get_timeout(self, timeout_type: str) -> int:
        """获取超时配置"""
        timeout_map = {
            'api': 'api_timeout',
            'analysis': 'analysis_timeout', 
            'data_fetch': 'data_fetch_timeout'
        }
        
        config_key = timeout_map.get(timeout_type, 'api_timeout')
        return self.optimization_config.get(config_key, 30)
    
    def should_use_fallback(self) -> bool:
        """是否应该使用降级策略"""
        return self.optimization_config.get('enable_fallback', True)
    
    def get_cache_config(self) -> Dict[str, int]:
        """获取缓存配置"""
        return {
            'size': self.optimization_config.get('cache_size', 1000),
            'ttl': self.optimization_config.get('cache_ttl', 1800)
        }
    
    def get_retry_config(self) -> Dict[str, int]:
        """获取重试配置"""
        return {
            'max_retries': self.optimization_config.get('max_retries', 2),
            'delay': self.optimization_config.get('retry_delay', 1)
        }

# 全局优化器实例
hf_optimizer = HFSpacesOptimizer()

def init_hf_spaces_optimization():
    """初始化HF Spaces优化"""
    hf_optimizer.apply_optimizations()
    return hf_optimizer

def get_hf_config(key: str, default=None):
    """获取HF优化配置"""
    return hf_optimizer.get_config(key, default)

def is_hf_feature_enabled(feature: str) -> bool:
    """检查HF环境下功能是否启用"""
    return hf_optimizer.is_feature_enabled(feature)

def get_hf_timeout(timeout_type: str) -> int:
    """获取HF环境下的超时配置"""
    return hf_optimizer.get_timeout(timeout_type)

# 使用示例
if __name__ == "__main__":
    optimizer = init_hf_spaces_optimization()
    print(f"运行环境: {'Hugging Face Spaces' if optimizer.is_hf_spaces else '其他环境'}")
    print(f"优化配置: {optimizer.optimization_config}")
