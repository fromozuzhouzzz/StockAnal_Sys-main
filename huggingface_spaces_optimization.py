#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Spaces平台优化配置
针对HF Spaces平台的特殊环境进行系统优化
"""

import os
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HuggingFaceSpacesOptimizer:
    """Hugging Face Spaces平台优化器"""
    
    def __init__(self):
        self.platform_name = "Hugging Face Spaces"
        self.optimizations_applied = []
        
    def detect_platform(self) -> bool:
        """检测是否运行在Hugging Face Spaces上"""
        # HF Spaces特有的环境变量
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
        
        return False
    
    def optimize_for_hf_spaces(self) -> Dict[str, Any]:
        """针对HF Spaces进行优化配置"""
        optimizations = {
            'platform_detected': self.detect_platform(),
            'applied_optimizations': [],
            'warnings': [],
            'recommendations': []
        }
        
        if not optimizations['platform_detected']:
            optimizations['warnings'].append("未检测到Hugging Face Spaces环境")
            return optimizations
        
        # 1. 数据库配置优化
        db_config = self._optimize_database_config()
        optimizations['database'] = db_config
        optimizations['applied_optimizations'].extend(db_config.get('optimizations', []))
        
        # 2. 缓存配置优化
        cache_config = self._optimize_cache_config()
        optimizations['cache'] = cache_config
        optimizations['applied_optimizations'].extend(cache_config.get('optimizations', []))
        
        # 3. 实时通信配置优化
        realtime_config = self._optimize_realtime_config()
        optimizations['realtime'] = realtime_config
        optimizations['applied_optimizations'].extend(realtime_config.get('optimizations', []))
        
        # 4. 性能配置优化
        performance_config = self._optimize_performance_config()
        optimizations['performance'] = performance_config
        optimizations['applied_optimizations'].extend(performance_config.get('optimizations', []))
        
        return optimizations
    
    def _optimize_database_config(self) -> Dict[str, Any]:
        """优化数据库配置"""
        config = {
            'optimizations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # 检查数据库URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            config['warnings'].append("DATABASE_URL未设置，将使用内存缓存")
            config['recommendations'].append("建议配置外部数据库（如Aiven MySQL）以获得更好的性能")
            
            # 设置内存数据库作为降级方案
            os.environ['USE_DATABASE'] = 'False'
            config['optimizations'].append("已禁用数据库，使用内存缓存")
        else:
            # 优化数据库连接池配置（适合HF Spaces的资源限制）
            os.environ['DATABASE_POOL_SIZE'] = '3'  # 减少连接池大小
            os.environ['DATABASE_POOL_TIMEOUT'] = '10'  # 减少超时时间
            os.environ['DATABASE_POOL_RECYCLE'] = '1800'  # 30分钟回收连接
            config['optimizations'].append("已优化数据库连接池配置")
        
        return config
    
    def _optimize_cache_config(self) -> Dict[str, Any]:
        """优化缓存配置"""
        config = {
            'optimizations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Redis在HF Spaces上不可用，禁用L2缓存
        config['warnings'].append("Redis不可用，已禁用L2缓存")
        config['optimizations'].append("使用内存+数据库两级缓存策略")
        
        # 优化内存缓存大小（适合HF Spaces的内存限制）
        os.environ['CACHE_L1_SIZE'] = '5000'  # 减少L1缓存大小
        config['optimizations'].append("已优化内存缓存大小")
        
        return config
    
    def _optimize_realtime_config(self) -> Dict[str, Any]:
        """优化实时通信配置"""
        config = {
            'optimizations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # HF Spaces可能不支持WebSocket，使用轮询降级
        config['warnings'].append("WebSocket可能不可用，将使用轮询方式")
        config['optimizations'].append("已配置轮询降级策略")
        
        # 优化轮询间隔（减少服务器负载）
        os.environ['POLLING_INTERVAL'] = '60'  # 增加轮询间隔到60秒
        config['optimizations'].append("已优化轮询间隔")
        
        return config
    
    def _optimize_performance_config(self) -> Dict[str, Any]:
        """优化性能配置"""
        config = {
            'optimizations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # 优化并发配置（适合HF Spaces的CPU限制）
        os.environ['MAX_WORKERS'] = '2'  # 减少工作线程数
        os.environ['BATCH_SIZE'] = '20'  # 减少批处理大小
        config['optimizations'].append("已优化并发和批处理配置")
        
        # 启用数据压缩
        os.environ['ENABLE_COMPRESSION'] = 'True'
        config['optimizations'].append("已启用数据压缩")
        
        # 优化缓存TTL（减少API调用）
        os.environ['REALTIME_DATA_TTL'] = '900'  # 15分钟
        os.environ['BASIC_INFO_TTL'] = '86400'   # 24小时
        config['optimizations'].append("已优化缓存过期时间")
        
        return config
    
    def apply_optimizations(self) -> bool:
        """应用所有优化配置"""
        try:
            logger.info(f"开始为{self.platform_name}应用优化配置...")
            
            optimizations = self.optimize_for_hf_spaces()
            
            if optimizations['platform_detected']:
                logger.info("✅ 平台检测成功")
                
                for opt in optimizations['applied_optimizations']:
                    logger.info(f"✅ {opt}")
                
                for warning in optimizations.get('warnings', []):
                    logger.warning(f"⚠️ {warning}")
                
                for rec in optimizations.get('recommendations', []):
                    logger.info(f"💡 {rec}")
                
                logger.info(f"✅ {self.platform_name}优化配置应用完成")
                return True
            else:
                logger.info("ℹ️ 未检测到Hugging Face Spaces环境，跳过优化")
                return False
                
        except Exception as e:
            logger.error(f"❌ 优化配置应用失败: {e}")
            return False

# 全局优化器实例
hf_optimizer = HuggingFaceSpacesOptimizer()

def init_hf_spaces_optimization():
    """初始化Hugging Face Spaces优化"""
    return hf_optimizer.apply_optimizations()

if __name__ == "__main__":
    # 直接运行时应用优化
    init_hf_spaces_optimization()
