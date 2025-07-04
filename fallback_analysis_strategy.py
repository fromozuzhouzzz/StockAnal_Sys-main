# -*- coding: utf-8 -*-
"""
降级分析策略
实现多层次的股票分析降级机制，确保在任何情况下都能提供有意义的结果
"""

import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

class FallbackAnalysisStrategy:
    """降级分析策略"""
    
    def __init__(self):
        self.fallback_levels = [
            'full_analysis',      # 完整分析
            'simplified_analysis', # 简化分析
            'cached_analysis',    # 缓存分析
            'mock_analysis',      # 模拟分析
            'basic_response'      # 基础响应
        ]
        self.current_level = 0
        self.failure_count = 0
        self.last_success_time = time.time()
        
    def analyze_stock_with_fallback(self, stock_code: str, market_type: str = 'A', 
                                  analyzer=None, risk_monitor=None, fundamental_analyzer=None) -> Dict[str, Any]:
        """使用降级策略分析股票"""
        
        for level_index, level in enumerate(self.fallback_levels):
            try:
                logger.info(f"尝试 {level} 分析股票 {stock_code}")
                
                if level == 'full_analysis':
                    result = self._full_analysis(stock_code, market_type, analyzer, risk_monitor, fundamental_analyzer)
                elif level == 'simplified_analysis':
                    result = self._simplified_analysis(stock_code, market_type, analyzer)
                elif level == 'cached_analysis':
                    result = self._cached_analysis(stock_code, market_type)
                elif level == 'mock_analysis':
                    result = self._mock_analysis(stock_code, market_type)
                else:  # basic_response
                    result = self._basic_response(stock_code, market_type)
                
                # 如果成功，重置失败计数
                self.failure_count = 0
                self.last_success_time = time.time()
                self.current_level = level_index
                
                # 添加降级信息
                result['fallback_info'] = {
                    'level_used': level,
                    'level_index': level_index,
                    'is_fallback': level_index > 0,
                    'analysis_time': datetime.now().isoformat()
                }
                
                logger.info(f"股票 {stock_code} 使用 {level} 分析成功")
                return result
                
            except Exception as e:
                logger.warning(f"{level} 分析失败: {e}")
                self.failure_count += 1
                continue
        
        # 如果所有级别都失败，返回错误响应
        logger.error(f"所有降级策略都失败，股票: {stock_code}")
        return self._error_response(stock_code, market_type)
    
    def _full_analysis(self, stock_code: str, market_type: str, analyzer, risk_monitor, fundamental_analyzer) -> Dict[str, Any]:
        """完整分析"""
        if not analyzer:
            raise Exception("分析器未初始化")
        
        # 执行完整分析
        analysis_result = analyzer.perform_enhanced_analysis(stock_code, market_type)
        risk_assessment = risk_monitor.analyze_stock_risk(stock_code, market_type) if risk_monitor else {}
        fundamental_result = fundamental_analyzer.calculate_fundamental_score(stock_code) if fundamental_analyzer else {}
        
        return self._format_analysis_result(stock_code, analysis_result, risk_assessment, fundamental_result, 'full')
    
    def _simplified_analysis(self, stock_code: str, market_type: str, analyzer) -> Dict[str, Any]:
        """简化分析"""
        if not analyzer:
            raise Exception("分析器未初始化")
        
        # 使用快速分析
        analysis_result = analyzer.quick_analyze_stock(stock_code, market_type)
        
        # 简化的风险和基本面分析
        risk_assessment = {'total_risk_score': 50, 'risk_level': '中等'}
        fundamental_result = {'total_score': 50, 'details': '简化分析'}
        
        return self._format_analysis_result(stock_code, analysis_result, risk_assessment, fundamental_result, 'simplified')
    
    def _cached_analysis(self, stock_code: str, market_type: str) -> Dict[str, Any]:
        """缓存分析 - 使用历史数据或预设数据"""
        logger.info(f"使用缓存数据分析 {stock_code}")
        
        # 尝试从缓存获取数据
        cached_data = self._get_cached_data(stock_code)
        if cached_data:
            return cached_data
        
        # 如果没有缓存，生成基于股票代码的确定性数据
        return self._generate_deterministic_analysis(stock_code, market_type)
    
    def _mock_analysis(self, stock_code: str, market_type: str) -> Dict[str, Any]:
        """模拟分析 - 生成合理的模拟数据"""
        logger.info(f"使用模拟数据分析 {stock_code}")
        
        # 基于股票代码生成确定性的模拟数据
        seed = hash(stock_code) % 1000
        random.seed(seed)
        
        # 生成模拟价格数据
        base_price = 10 + (seed % 100)
        price_change = random.uniform(-5, 5)
        
        # 生成模拟评分
        technical_score = 40 + random.randint(0, 40)
        fundamental_score = 40 + random.randint(0, 40)
        overall_score = (technical_score + fundamental_score) / 2
        
        analysis_result = {
            'stock_code': stock_code,
            'stock_name': f'模拟股票{stock_code[-4:]}',
            'industry': '模拟行业',
            'score': overall_score,
            'price': base_price,
            'price_change': price_change,
            'ma_trend': 'UP' if price_change > 0 else 'DOWN',
            'rsi': 30 + random.randint(0, 40),
            'macd_signal': 'BUY' if overall_score > 60 else 'SELL',
            'volume_status': 'NORMAL',
            'recommendation': self._get_recommendation(overall_score)
        }
        
        risk_assessment = {
            'total_risk_score': 30 + random.randint(0, 40),
            'volatility_risk': {'score': 30 + random.randint(0, 40)},
            'trend_risk': {'score': 30 + random.randint(0, 40)},
            'volume_risk': {'score': 30 + random.randint(0, 40)}
        }
        
        fundamental_result = {
            'total_score': fundamental_score,
            'pe_ttm': 10 + random.randint(0, 30),
            'pb': 1 + random.random() * 3,
            'roe': 5 + random.randint(0, 20),
            'debt_ratio': 20 + random.randint(0, 40)
        }
        
        return self._format_analysis_result(stock_code, analysis_result, risk_assessment, fundamental_result, 'mock')
    
    def _basic_response(self, stock_code: str, market_type: str) -> Dict[str, Any]:
        """基础响应 - 最简单的响应"""
        logger.info(f"返回基础响应 {stock_code}")
        
        return {
            'stock_info': {
                'stock_code': stock_code,
                'stock_name': f'股票{stock_code[-4:]}',
                'industry': '未知',
                'market_type': market_type
            },
            'analysis_result': {
                'overall_score': 50,
                'technical_score': 50,
                'fundamental_score': 50,
                'capital_flow_score': 50
            },
            'technical_analysis': {
                'trend': '未知',
                'support_levels': [],
                'resistance_levels': [],
                'indicators': {
                    'rsi': 50,
                    'macd_signal': '持有',
                    'ma_trend': '未知',
                    'volume_status': '正常'
                }
            },
            'fundamental_analysis': {
                'pe_ratio': 0,
                'pb_ratio': 0,
                'roe': 0,
                'debt_ratio': 0,
                'growth_score': 50,
                'profitability_score': 50
            },
            'risk_assessment': {
                'risk_level': '中等',
                'volatility': 50,
                'trend_risk': 50,
                'volume_risk': 50,
                'total_risk_score': 50
            },
            'recommendation': '持有',
            'fallback_info': {
                'level_used': 'basic_response',
                'level_index': 4,
                'is_fallback': True,
                'analysis_time': datetime.now().isoformat(),
                'message': '由于数据获取问题，返回基础响应'
            }
        }
    
    def _error_response(self, stock_code: str, market_type: str) -> Dict[str, Any]:
        """错误响应"""
        return {
            'error': True,
            'message': '所有分析策略都失败',
            'stock_code': stock_code,
            'market_type': market_type,
            'timestamp': datetime.now().isoformat(),
            'fallback_info': {
                'all_levels_failed': True,
                'failure_count': self.failure_count
            }
        }
    
    def _format_analysis_result(self, stock_code: str, analysis_result: Dict, 
                              risk_assessment: Dict, fundamental_result: Dict, level: str) -> Dict[str, Any]:
        """格式化分析结果"""
        return {
            'stock_info': {
                'stock_code': stock_code,
                'stock_name': analysis_result.get('stock_name', '未知'),
                'industry': analysis_result.get('industry', '未知'),
                'market_type': 'A'
            },
            'analysis_result': {
                'overall_score': analysis_result.get('score', 50),
                'technical_score': analysis_result.get('technical_score', 50),
                'fundamental_score': fundamental_result.get('total_score', 50),
                'capital_flow_score': analysis_result.get('capital_flow_score', 50)
            },
            'technical_analysis': {
                'trend': analysis_result.get('ma_trend', '未知'),
                'support_levels': analysis_result.get('support_levels', []),
                'resistance_levels': analysis_result.get('resistance_levels', []),
                'indicators': {
                    'rsi': analysis_result.get('rsi', 50),
                    'macd_signal': analysis_result.get('macd_signal', '持有'),
                    'ma_trend': analysis_result.get('ma_trend', '未知'),
                    'volume_status': analysis_result.get('volume_status', '正常')
                }
            },
            'fundamental_analysis': {
                'pe_ratio': fundamental_result.get('pe_ttm', 0),
                'pb_ratio': fundamental_result.get('pb', 0),
                'roe': fundamental_result.get('roe', 0),
                'debt_ratio': fundamental_result.get('debt_ratio', 0),
                'growth_score': fundamental_result.get('growth_score', 50),
                'profitability_score': fundamental_result.get('profitability_score', 50)
            },
            'risk_assessment': {
                'risk_level': self._get_risk_level(risk_assessment.get('total_risk_score', 50)),
                'volatility': risk_assessment.get('volatility_risk', {}).get('score', 50),
                'trend_risk': risk_assessment.get('trend_risk', {}).get('score', 50),
                'volume_risk': risk_assessment.get('volume_risk', {}).get('score', 50),
                'total_risk_score': risk_assessment.get('total_risk_score', 50)
            },
            'recommendation': analysis_result.get('recommendation', '持有')
        }
    
    def _get_cached_data(self, stock_code: str) -> Optional[Dict]:
        """获取缓存数据"""
        # 这里可以实现真正的缓存逻辑
        # 目前返回None，表示没有缓存
        return None
    
    def _generate_deterministic_analysis(self, stock_code: str, market_type: str) -> Dict[str, Any]:
        """生成基于股票代码的确定性分析"""
        # 基于股票代码生成确定性数据
        code_hash = hash(stock_code)
        
        analysis_result = {
            'stock_code': stock_code,
            'stock_name': f'缓存股票{stock_code[-4:]}',
            'industry': '缓存行业',
            'score': 40 + (abs(code_hash) % 40),
            'price': 10 + (abs(code_hash) % 100),
            'price_change': -5 + (abs(code_hash) % 10),
            'ma_trend': 'UP' if code_hash % 2 == 0 else 'DOWN',
            'rsi': 30 + (abs(code_hash) % 40),
            'macd_signal': 'BUY' if code_hash % 3 == 0 else 'SELL',
            'volume_status': 'NORMAL',
            'recommendation': '持有'
        }
        
        risk_assessment = {'total_risk_score': 30 + (abs(code_hash) % 40)}
        fundamental_result = {'total_score': 40 + (abs(code_hash) % 40)}
        
        return self._format_analysis_result(stock_code, analysis_result, risk_assessment, fundamental_result, 'cached')
    
    def _get_recommendation(self, score: float) -> str:
        """根据评分获取推荐"""
        if score >= 80:
            return '强烈买入'
        elif score >= 70:
            return '买入'
        elif score >= 60:
            return '持有'
        elif score >= 50:
            return '观望'
        else:
            return '卖出'
    
    def _get_risk_level(self, risk_score: float) -> str:
        """根据风险评分获取风险等级"""
        if risk_score >= 80:
            return '高风险'
        elif risk_score >= 60:
            return '中高风险'
        elif risk_score >= 40:
            return '中等风险'
        elif risk_score >= 20:
            return '中低风险'
        else:
            return '低风险'
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """获取策略状态"""
        return {
            'current_level': self.fallback_levels[self.current_level],
            'current_level_index': self.current_level,
            'failure_count': self.failure_count,
            'last_success_time': self.last_success_time,
            'time_since_last_success': time.time() - self.last_success_time,
            'available_levels': self.fallback_levels
        }

# 全局实例
fallback_strategy = FallbackAnalysisStrategy()
