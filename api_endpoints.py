# -*- coding: utf-8 -*-
"""
股票分析系统 API 端点实现
提供投资组合分析、个股分析、批量评分等API接口
"""

from flask import Blueprint, request, jsonify
import logging
import traceback
import time
from typing import List, Dict, Any

# 导入认证和限流模块
from auth_middleware import require_api_key, require_hmac_auth, api_access_logger
from rate_limiter import require_rate_limit
from api_response import APIResponse, ErrorCodes, validate_stock_code, normalize_stock_code, validate_request_data

# 导入分析模块
from stock_analyzer import StockAnalyzer
from risk_monitor import RiskMonitor
from fundamental_analyzer import FundamentalAnalyzer

# 导入HF Spaces优化
try:
    from hf_spaces_optimization import get_hf_timeout, is_hf_feature_enabled, get_hf_config
    HF_OPTIMIZATION_AVAILABLE = True
except ImportError:
    HF_OPTIMIZATION_AVAILABLE = False
    def get_hf_timeout(timeout_type): return 60
    def is_hf_feature_enabled(feature): return True
    def get_hf_config(key, default=None): return default

# 导入降级分析策略
try:
    from fallback_analysis_strategy import fallback_strategy
    FALLBACK_STRATEGY_AVAILABLE = True
except ImportError:
    FALLBACK_STRATEGY_AVAILABLE = False
    fallback_strategy = None

logger = logging.getLogger(__name__)

# 创建API蓝图
api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')


def api_error_handler(f):
    """API错误处理装饰器，确保所有错误都返回标准JSON格式"""
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API端点 {f.__name__} 出错: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")

            return APIResponse.error(
                code=ErrorCodes.INTERNAL_SERVER_ERROR,
                message='服务器内部错误',
                details={
                    'error_message': str(e),
                    'error_type': type(e).__name__,
                    'endpoint': f.__name__
                },
                status_code=500
            )
    decorated_function.__name__ = f.__name__
    return decorated_function

# 初始化分析器（这些应该从主应用中获取）
analyzer = None
risk_monitor = None
fundamental_analyzer = None

def init_analyzers(app_analyzer, app_risk_monitor, app_fundamental_analyzer):
    """初始化分析器实例"""
    global analyzer, risk_monitor, fundamental_analyzer
    analyzer = app_analyzer
    risk_monitor = app_risk_monitor
    fundamental_analyzer = app_fundamental_analyzer
    logger.info(f"分析器初始化完成: analyzer={analyzer is not None}, risk_monitor={risk_monitor is not None}, fundamental_analyzer={fundamental_analyzer is not None}")


@api_v1.route('/health', methods=['GET'])
def api_health():
    """API健康检查端点"""
    try:
        status = {
            'status': 'healthy',
            'version': '1.0.0',
            'analyzers': {
                'stock_analyzer': analyzer is not None,
                'risk_monitor': risk_monitor is not None,
                'fundamental_analyzer': fundamental_analyzer is not None
            },
            'features': {
                'hf_optimization': HF_OPTIMIZATION_AVAILABLE,
                'fallback_strategy': FALLBACK_STRATEGY_AVAILABLE
            },
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
        }

        # 如果分析器未初始化，状态为不健康
        if not all(status['analyzers'].values()):
            status['status'] = 'unhealthy'
            status['message'] = '部分分析器未初始化'

        return APIResponse.success(data=status)

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return APIResponse.error(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message='健康检查失败',
            details={'error': str(e)},
            status_code=500
        )


@api_v1.route('/status', methods=['GET'])
def api_status():
    """API详细状态端点"""
    try:
        # 基本状态信息
        status_info = {
            'api_version': '1.0.0',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'uptime': time.time() - start_time if 'start_time' in globals() else 0
        }

        # 分析器状态
        analyzer_status = {
            'stock_analyzer': {
                'initialized': analyzer is not None,
                'type': type(analyzer).__name__ if analyzer else None
            },
            'risk_monitor': {
                'initialized': risk_monitor is not None,
                'type': type(risk_monitor).__name__ if risk_monitor else None
            },
            'fundamental_analyzer': {
                'initialized': fundamental_analyzer is not None,
                'type': type(fundamental_analyzer).__name__ if fundamental_analyzer else None
            }
        }

        # 功能状态
        feature_status = {
            'hf_optimization': {
                'available': HF_OPTIMIZATION_AVAILABLE,
                'enabled': HF_OPTIMIZATION_AVAILABLE and get_hf_config('enable_optimization', True)
            },
            'fallback_strategy': {
                'available': FALLBACK_STRATEGY_AVAILABLE,
                'current_level': fallback_strategy.get_strategy_status() if FALLBACK_STRATEGY_AVAILABLE else None
            }
        }

        # 环境信息
        import os
        environment_info = {
            'is_hf_spaces': any(os.getenv(var) for var in ['SPACE_ID', 'GRADIO_SERVER_NAME']),
            'python_version': os.sys.version.split()[0],
            'environment_vars': {
                'USE_DATABASE': os.getenv('USE_DATABASE'),
                'USE_REDIS_CACHE': os.getenv('USE_REDIS_CACHE'),
                'SPACE_ID': os.getenv('SPACE_ID')
            }
        }

        return APIResponse.success(data={
            'status': status_info,
            'analyzers': analyzer_status,
            'features': feature_status,
            'environment': environment_info
        })

    except Exception as e:
        logger.error(f"状态检查失败: {e}")
        return APIResponse.error(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message='状态检查失败',
            details={'error': str(e)},
            status_code=500
        )


@api_v1.route('/portfolio/analyze', methods=['POST'])
@api_access_logger
@require_rate_limit('/api/v1/portfolio/analyze')
@require_api_key('portfolio_analysis')
def analyze_portfolio():
    """
    投资组合分析API
    
    请求格式:
    {
        "stocks": [
            {
                "stock_code": "000001.SZ",
                "weight": 0.3,
                "market_type": "A"
            }
        ],
        "analysis_params": {
            "risk_preference": "moderate",
            "time_horizon": "medium"
        }
    }
    """
    try:
        # 验证请求数据
        data = request.get_json()
        validation_error = validate_request_data(data, ['stocks'])
        if validation_error:
            return APIResponse.error(
                code=ErrorCodes.INVALID_REQUEST_FORMAT,
                message='请求参数验证失败',
                details=validation_error,
                status_code=400
            )
        
        stocks = data.get('stocks', [])
        analysis_params = data.get('analysis_params', {})
        
        # 验证股票列表
        if not stocks or len(stocks) == 0:
            return APIResponse.error(
                code=ErrorCodes.MISSING_REQUIRED_FIELD,
                message='股票列表不能为空',
                status_code=400
            )
        
        if len(stocks) > 50:  # 限制组合大小
            return APIResponse.error(
                code=ErrorCodes.PORTFOLIO_TOO_LARGE,
                message='投资组合股票数量不能超过50只',
                details={'max_stocks': 50, 'provided': len(stocks)},
                status_code=400
            )
        
        # 验证和标准化股票代码
        invalid_codes = []
        normalized_stocks = []
        total_weight = 0
        
        for stock in stocks:
            stock_code = stock.get('stock_code')
            weight = stock.get('weight', 1.0)
            market_type = stock.get('market_type', 'A')
            
            if not stock_code:
                return APIResponse.error(
                    code=ErrorCodes.MISSING_REQUIRED_FIELD,
                    message='股票代码不能为空',
                    status_code=400
                )
            
            if not validate_stock_code(stock_code):
                invalid_codes.append(stock_code)
                continue
            
            normalized_code = normalize_stock_code(stock_code)
            normalized_stocks.append({
                'stock_code': normalized_code,
                'weight': float(weight),
                'market_type': market_type
            })
            total_weight += float(weight)
        
        if invalid_codes:
            return APIResponse.error(
                code=ErrorCodes.INVALID_STOCK_CODE,
                message='包含无效的股票代码',
                details={'invalid_codes': invalid_codes},
                status_code=400
            )
        
        # 权重标准化
        if total_weight > 0:
            for stock in normalized_stocks:
                stock['weight'] = stock['weight'] / total_weight
        
        # 执行投资组合分析
        start_time = time.time()
        
        # 分析每只股票
        individual_results = []
        portfolio_score = 0
        
        for stock in normalized_stocks:
            try:
                # 获取股票分析结果
                stock_result = analyzer.quick_analyze_stock(
                    stock['stock_code'], 
                    stock['market_type']
                )
                
                # 计算加权贡献
                weighted_score = stock_result['score'] * stock['weight']
                portfolio_score += weighted_score
                
                individual_results.append({
                    'stock_code': stock['stock_code'],
                    'stock_name': stock_result.get('stock_name', '未知'),
                    'score': stock_result['score'],
                    'weight': stock['weight'],
                    'contribution': weighted_score,
                    'risk_level': stock_result.get('risk_level', '中等'),
                    'recommendation': stock_result.get('recommendation', '持有')
                })
                
            except Exception as e:
                logger.error(f"分析股票 {stock['stock_code']} 时出错: {str(e)}")
                individual_results.append({
                    'stock_code': stock['stock_code'],
                    'error': f'分析失败: {str(e)}',
                    'weight': stock['weight'],
                    'contribution': 0
                })
        
        # 执行组合风险分析
        try:
            risk_analysis = risk_monitor.analyze_portfolio_risk(normalized_stocks)
        except Exception as e:
            logger.error(f"组合风险分析出错: {str(e)}")
            risk_analysis = {
                'error': f'风险分析失败: {str(e)}',
                'portfolio_risk_score': 50  # 默认中等风险
            }
        
        # 生成投资建议
        recommendations = generate_portfolio_recommendations(
            portfolio_score, risk_analysis, analysis_params
        )
        
        # 构建响应数据
        processing_time = int((time.time() - start_time) * 1000)
        
        response_data = {
            'portfolio_score': round(portfolio_score, 2),
            'risk_level': get_risk_level(risk_analysis.get('portfolio_risk_score', 50)),
            'risk_analysis': {
                'volatility_risk': risk_analysis.get('volatility_risk', {}),
                'concentration_risk': calculate_concentration_risk(normalized_stocks),
                'correlation_risk': risk_analysis.get('correlation_risk', {}),
                'overall_risk_score': risk_analysis.get('portfolio_risk_score', 50)
            },
            'recommendations': recommendations,
            'individual_stocks': individual_results,
            'portfolio_stats': {
                'total_stocks': len(normalized_stocks),
                'successful_analysis': len([r for r in individual_results if 'error' not in r]),
                'failed_analysis': len([r for r in individual_results if 'error' in r])
            }
        }
        
        meta = {
            'analysis_time': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'processing_time_ms': processing_time,
            'cache_hit': False,  # 组合分析通常不缓存
            'analysis_params': analysis_params
        }
        
        return APIResponse.success(data=response_data, meta=meta)
        
    except Exception as e:
        logger.error(f"投资组合分析API出错: {traceback.format_exc()}")
        return APIResponse.error(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message='投资组合分析失败',
            details={'error_message': str(e)},
            status_code=500
        )


def generate_portfolio_recommendations(portfolio_score: float, risk_analysis: Dict, params: Dict) -> List[str]:
    """生成投资组合建议"""
    recommendations = []
    
    # 基于评分的建议
    if portfolio_score >= 80:
        recommendations.append("投资组合整体表现优秀，建议继续持有")
    elif portfolio_score >= 60:
        recommendations.append("投资组合表现良好，可适当调整优化")
    else:
        recommendations.append("投资组合表现较弱，建议重新配置")
    
    # 基于风险的建议
    risk_score = risk_analysis.get('portfolio_risk_score', 50)
    if risk_score > 70:
        recommendations.append("组合风险较高，建议适当分散投资")
    elif risk_score < 30:
        recommendations.append("组合风险较低，可考虑适当增加收益性资产")
    
    # 基于用户偏好的建议
    risk_preference = params.get('risk_preference', 'moderate')
    if risk_preference == 'conservative' and risk_score > 50:
        recommendations.append("根据您的保守风险偏好，建议降低组合风险")
    elif risk_preference == 'aggressive' and risk_score < 50:
        recommendations.append("根据您的激进风险偏好，可考虑增加高收益资产")
    
    return recommendations


def calculate_concentration_risk(stocks: List[Dict]) -> Dict:
    """计算集中度风险"""
    if not stocks:
        return {'score': 0, 'level': '低'}
    
    # 计算权重分布
    weights = [stock['weight'] for stock in stocks]
    max_weight = max(weights)
    
    # 计算赫芬达尔指数
    hhi = sum(w * w for w in weights)
    
    # 风险评分 (0-100)
    concentration_score = min(100, hhi * 100 + max_weight * 50)
    
    if concentration_score > 70:
        level = '高'
    elif concentration_score > 40:
        level = '中'
    else:
        level = '低'
    
    return {
        'score': round(concentration_score, 2),
        'level': level,
        'max_weight': round(max_weight, 3),
        'hhi': round(hhi, 3),
        'diversification': len(stocks)
    }


def get_risk_level(risk_score: float) -> str:
    """根据风险评分获取风险等级"""
    if risk_score >= 70:
        return '高风险'
    elif risk_score >= 40:
        return '中等风险'
    else:
        return '低风险'


@api_v1.route('/stock/analyze', methods=['POST'])
@api_error_handler
@api_access_logger
@require_rate_limit('/api/v1/stock/analyze')
@require_api_key('stock_analysis')
def analyze_stock():
    """
    个股分析API

    请求格式:
    {
        "stock_code": "000001.SZ",
        "market_type": "A",
        "analysis_depth": "full",
        "include_ai_analysis": true,
        "time_range": 60
    }
    """
    try:
        # 声明全局变量
        global analyzer, risk_monitor, fundamental_analyzer

        # 检查分析器是否已初始化
        if analyzer is None or risk_monitor is None or fundamental_analyzer is None:
            logger.error("分析器未初始化")
            logger.error(f"analyzer: {analyzer}, risk_monitor: {risk_monitor}, fundamental_analyzer: {fundamental_analyzer}")

            # 尝试重新初始化分析器
            try:
                from stock_analyzer import StockAnalyzer
                from risk_monitor import RiskMonitor as RiskMonitorClass
                from fundamental_analyzer import FundamentalAnalyzer as FundamentalAnalyzerClass

                if analyzer is None:
                    analyzer = StockAnalyzer()
                    logger.info("重新初始化 StockAnalyzer")
                if risk_monitor is None:
                    risk_monitor = RiskMonitorClass(analyzer)
                    logger.info("重新初始化 RiskMonitor")
                if fundamental_analyzer is None:
                    fundamental_analyzer = FundamentalAnalyzerClass()
                    logger.info("重新初始化 FundamentalAnalyzer")

            except Exception as init_error:
                logger.error(f"重新初始化分析器失败: {init_error}")
                return APIResponse.error(
                    code=ErrorCodes.INTERNAL_SERVER_ERROR,
                    message='分析器初始化失败',
                    details={
                        'error_message': str(init_error),
                        'error_type': type(init_error).__name__
                    },
                    status_code=500
                )

        # 验证请求数据
        data = request.get_json()
        validation_error = validate_request_data(data, ['stock_code'])
        if validation_error:
            return APIResponse.error(
                code=ErrorCodes.INVALID_REQUEST_FORMAT,
                message='请求参数验证失败',
                details=validation_error,
                status_code=400
            )

        stock_code = data.get('stock_code')
        market_type = data.get('market_type', 'A')
        analysis_depth = data.get('analysis_depth', 'full')
        include_ai_analysis = data.get('include_ai_analysis', True)
        time_range = data.get('time_range', 60)

        # 验证股票代码
        if not validate_stock_code(stock_code):
            return APIResponse.error(
                code=ErrorCodes.INVALID_STOCK_CODE,
                message='无效的股票代码',
                details={'stock_code': stock_code},
                status_code=400
            )

        # 标准化股票代码
        normalized_code = normalize_stock_code(stock_code)
        logger.info(f"开始分析股票: {normalized_code}, 分析深度: {analysis_depth}")

        # 应用HF Spaces优化
        if HF_OPTIMIZATION_AVAILABLE:
            # 在HF环境下强制使用快速分析
            if not is_hf_feature_enabled('complex_indicators'):
                analysis_depth = 'quick'
                logger.info("HF Spaces环境：使用快速分析模式")

            # 禁用AI分析以节省资源
            if not is_hf_feature_enabled('ai_analysis'):
                include_ai_analysis = False
                logger.info("HF Spaces环境：禁用AI分析")

        # 执行股票分析 - 使用降级策略
        start_time = time.time()
        analysis_timeout = get_hf_timeout('analysis')

        # 初始化变量以避免UnboundLocalError
        analysis_result = None
        risk_assessment = None
        fundamental_result = None
        response_data = None

        try:
            # 使用降级分析策略
            if FALLBACK_STRATEGY_AVAILABLE:
                logger.info(f"使用降级分析策略分析股票: {normalized_code}")
                analysis_data = fallback_strategy.analyze_stock_with_fallback(
                    normalized_code, market_type, analyzer, risk_monitor, fundamental_analyzer
                )

                # 检查是否是错误响应
                if analysis_data.get('error'):
                    return APIResponse.error(
                        code=ErrorCodes.ANALYSIS_FAILED,
                        message='个股分析失败',
                        details={
                            'error_message': analysis_data.get('message', '降级策略失败'),
                            'fallback_info': analysis_data.get('fallback_info', {}),
                            'stock_code': normalized_code
                        },
                        status_code=500
                    )

                # 使用降级策略的结果
                response_data = analysis_data

            else:
                # 传统分析方式（备用）
                logger.warning("降级策略不可用，使用传统分析方式")

                if analysis_depth == 'full':
                    analysis_result = analyzer.perform_enhanced_analysis(normalized_code, market_type)
                else:
                    analysis_result = analyzer.quick_analyze_stock(normalized_code, market_type)

                risk_assessment = risk_monitor.analyze_stock_risk(normalized_code, market_type)

                if HF_OPTIMIZATION_AVAILABLE and not is_hf_feature_enabled('complex_indicators'):
                    fundamental_result = {'total_score': 50, 'details': '简化分析'}
                else:
                    fundamental_result = fundamental_analyzer.calculate_fundamental_score(normalized_code)

                # 格式化传统分析结果
                response_data = _format_traditional_result(
                    normalized_code, analysis_result, risk_assessment, fundamental_result, market_type
                )

        except Exception as e:
            logger.error(f"分析股票 {normalized_code} 时出错: {str(e)}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")

            # 如果有降级策略，尝试使用基础响应
            if FALLBACK_STRATEGY_AVAILABLE:
                logger.info("尝试使用降级策略的基础响应")
                try:
                    response_data = fallback_strategy._basic_response(normalized_code, market_type)
                except Exception as fallback_error:
                    logger.error(f"降级策略基础响应也失败: {fallback_error}")
                    # 如果连基础响应都失败，返回错误
                    return APIResponse.error(
                        code=ErrorCodes.ANALYSIS_FAILED,
                        message='个股分析失败',
                        details={
                            'error_message': str(e),
                            'error_type': type(e).__name__,
                            'stock_code': normalized_code,
                            'fallback_failed': True,
                            'fallback_error': str(fallback_error)
                        },
                        status_code=500
                    )
            else:
                return APIResponse.error(
                    code=ErrorCodes.ANALYSIS_FAILED,
                    message='个股分析失败',
                    details={
                        'error_message': str(e),
                        'error_type': type(e).__name__,
                        'stock_code': normalized_code
                    },
                    status_code=500
                )

        # 确保response_data存在
        if response_data is None:
            return APIResponse.error(
                code=ErrorCodes.ANALYSIS_FAILED,
                message='个股分析失败',
                details={
                    'error_message': '分析过程中未生成有效数据',
                    'stock_code': normalized_code
                },
                status_code=500
            )

        # 计算处理时间
        processing_time = int((time.time() - start_time) * 1000)

        # 添加处理时间到响应数据
        if 'fallback_info' not in response_data:
            response_data['fallback_info'] = {}
        response_data['fallback_info']['processing_time_ms'] = processing_time

        # 添加AI分析（如果请求且analysis_result存在）
        if include_ai_analysis and analysis_result and analysis_result.get('ai_analysis'):
            response_data['ai_analysis'] = {
                'summary': analysis_result['ai_analysis'].get('summary', ''),
                'recommendation': analysis_result['ai_analysis'].get('recommendation', ''),
                'confidence': analysis_result['ai_analysis'].get('confidence', 0.5)
            }

        meta = {
            'analysis_time': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'data_freshness': '实时',
            'processing_time_ms': processing_time,
            'analysis_depth': analysis_depth,
            'cache_hit': getattr(analysis_result, 'cache_hit', False) if analysis_result else False
        }

        return APIResponse.success(data=response_data, meta=meta)

    except Exception as e:
        logger.error(f"个股分析API出错: {traceback.format_exc()}")
        return APIResponse.error(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message='个股分析失败',
            details={'error_message': str(e)},
            status_code=500
        )


@api_v1.route('/stocks/batch-score', methods=['POST'])
@api_access_logger
@require_rate_limit('/api/v1/stocks/batch-score')
@require_api_key('batch_analysis')
def batch_score_stocks():
    """
    批量股票评分API

    请求格式:
    {
        "stock_codes": ["000001.SZ", "600000.SH", "000002.SZ"],
        "market_type": "A",
        "min_score": 60,
        "sort_by": "score",
        "sort_order": "desc"
    }
    """
    try:
        # 验证请求数据
        data = request.get_json()
        validation_error = validate_request_data(data, ['stock_codes'])
        if validation_error:
            return APIResponse.error(
                code=ErrorCodes.INVALID_REQUEST_FORMAT,
                message='请求参数验证失败',
                details=validation_error,
                status_code=400
            )

        stock_codes = data.get('stock_codes', [])
        market_type = data.get('market_type', 'A')
        min_score = data.get('min_score', 0)
        sort_by = data.get('sort_by', 'score')
        sort_order = data.get('sort_order', 'desc')

        # 验证股票代码列表
        if not stock_codes or len(stock_codes) == 0:
            return APIResponse.error(
                code=ErrorCodes.MISSING_REQUIRED_FIELD,
                message='股票代码列表不能为空',
                status_code=400
            )

        if len(stock_codes) > 100:  # 限制批量大小
            return APIResponse.error(
                code=ErrorCodes.PORTFOLIO_TOO_LARGE,
                message='批量分析股票数量不能超过100只',
                details={'max_stocks': 100, 'provided': len(stock_codes)},
                status_code=400
            )

        # 验证和标准化股票代码
        invalid_codes = []
        valid_codes = []

        for code in stock_codes:
            if not validate_stock_code(code):
                invalid_codes.append(code)
            else:
                valid_codes.append(normalize_stock_code(code))

        if invalid_codes:
            return APIResponse.error(
                code=ErrorCodes.INVALID_STOCK_CODE,
                message='包含无效的股票代码',
                details={'invalid_codes': invalid_codes},
                status_code=400
            )

        # 执行批量分析
        start_time = time.time()
        results = []
        successful_count = 0
        failed_count = 0

        for stock_code in valid_codes:
            try:
                # 快速分析获取评分
                analysis_result = analyzer.quick_analyze_stock(stock_code, market_type)

                score = analysis_result.get('score', 0)

                # 应用最低评分过滤
                if score >= min_score:
                    results.append({
                        'stock_code': stock_code,
                        'stock_name': analysis_result.get('stock_name', '未知'),
                        'score': round(score, 2),
                        'risk_level': get_risk_level(analysis_result.get('risk_score', 50)),
                        'recommendation': analysis_result.get('recommendation', '持有'),
                        'price': analysis_result.get('price', 0),
                        'price_change': analysis_result.get('price_change', 0),
                        'volume_status': analysis_result.get('volume_status', '未知'),
                        'ma_trend': analysis_result.get('ma_trend', '未知')
                    })

                successful_count += 1

            except Exception as e:
                logger.error(f"分析股票 {stock_code} 时出错: {str(e)}")
                failed_count += 1

                # 可选：包含失败的股票信息
                results.append({
                    'stock_code': stock_code,
                    'error': f'分析失败: {str(e)}',
                    'score': 0
                })

        # 排序结果
        if results and sort_by in ['score', 'price_change']:
            reverse = (sort_order.lower() == 'desc')
            results.sort(
                key=lambda x: x.get(sort_by, 0) if 'error' not in x else -999,
                reverse=reverse
            )

        # 过滤掉失败的结果（如果不需要显示）
        qualified_results = [r for r in results if 'error' not in r]

        processing_time = int((time.time() - start_time) * 1000)

        response_data = {
            'total_analyzed': len(valid_codes),
            'successful_count': successful_count,
            'failed_count': failed_count,
            'qualified_count': len(qualified_results),
            'results': qualified_results
        }

        meta = {
            'analysis_time': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'processing_time_ms': processing_time,
            'filter_criteria': {
                'min_score': min_score,
                'sort_by': sort_by,
                'sort_order': sort_order
            },
            'cache_hit_rate': 0.0  # 批量分析通常缓存命中率较低
        }

        return APIResponse.success(data=response_data, meta=meta)

    except Exception as e:
        logger.error(f"批量股票评分API出错: {traceback.format_exc()}")
        return APIResponse.error(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message='批量股票评分失败',
            details={'error_message': str(e)},
            status_code=500
        )


# 异步任务处理API
@api_v1.route('/tasks', methods=['POST'])
@api_access_logger
@require_rate_limit('/api/v1/tasks')
@require_api_key('task_management')
def create_task():
    """
    创建异步任务API

    请求格式:
    {
        "task_type": "portfolio_analysis",
        "params": {
            "stocks": [...],
            "analysis_depth": "full"
        }
    }
    """
    try:
        # 验证请求数据
        data = request.get_json()
        validation_error = validate_request_data(data, ['task_type', 'params'])
        if validation_error:
            return APIResponse.error(
                code=ErrorCodes.INVALID_REQUEST_FORMAT,
                message='请求参数验证失败',
                details=validation_error,
                status_code=400
            )

        task_type = data.get('task_type')
        params = data.get('params', {})

        # 验证任务类型
        valid_task_types = ['portfolio_analysis', 'stock_analysis', 'batch_score', 'market_scan']
        if task_type not in valid_task_types:
            return APIResponse.error(
                code=ErrorCodes.INVALID_PARAMETER_VALUE,
                message='无效的任务类型',
                details={'valid_types': valid_task_types},
                status_code=400
            )

        # 导入任务管理器
        from 任务存储不一致问题完整解决方案 import unified_task_manager

        # 创建任务
        task_id, task = unified_task_manager.create_task(task_type, **params)

        # 估算完成时间
        estimated_time = estimate_task_completion_time(task_type, params)

        return APIResponse.task_created(
            task_id=task_id,
            task_type=task_type,
            estimated_time=estimated_time
        )

    except Exception as e:
        logger.error(f"创建任务API出错: {traceback.format_exc()}")
        return APIResponse.error(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message='创建任务失败',
            details={'error_message': str(e)},
            status_code=500
        )


@api_v1.route('/tasks/<task_id>', methods=['GET'])
@api_access_logger
@require_rate_limit('/api/v1/tasks')
@require_api_key('task_management')
def get_task_status(task_id):
    """
    查询任务状态API
    """
    try:
        # 导入任务管理器
        from 任务存储不一致问题完整解决方案 import unified_task_manager

        # 获取任务信息
        task = unified_task_manager.get_task(task_id)

        if not task:
            return APIResponse.error(
                code=ErrorCodes.TASK_NOT_FOUND,
                message='任务不存在',
                details={'task_id': task_id},
                status_code=404
            )

        # 计算预估剩余时间
        estimated_remaining = None
        if task['status'] == 'running' and task.get('progress', 0) > 0:
            progress = task['progress']
            if progress > 0 and progress < 100:
                # 基于当前进度估算剩余时间
                estimated_remaining = int((100 - progress) * 2)  # 简单估算

        return APIResponse.task_status(
            task_id=task_id,
            status=task['status'],
            progress=task.get('progress'),
            estimated_remaining=estimated_remaining,
            result=task.get('result') if task['status'] == 'completed' else None
        )

    except Exception as e:
        logger.error(f"查询任务状态API出错: {traceback.format_exc()}")
        return APIResponse.error(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message='查询任务状态失败',
            details={'error_message': str(e)},
            status_code=500
        )


@api_v1.route('/tasks/<task_id>/result', methods=['GET'])
@api_access_logger
@require_rate_limit('/api/v1/tasks')
@require_api_key('task_management')
def get_task_result(task_id):
    """
    获取任务结果API
    """
    try:
        # 导入任务管理器
        from 任务存储不一致问题完整解决方案 import unified_task_manager

        # 获取任务信息
        task = unified_task_manager.get_task(task_id)

        if not task:
            return APIResponse.error(
                code=ErrorCodes.TASK_NOT_FOUND,
                message='任务不存在',
                details={'task_id': task_id},
                status_code=404
            )

        if task['status'] != 'completed':
            return APIResponse.error(
                code=ErrorCodes.TASK_NOT_FOUND,
                message='任务尚未完成',
                details={
                    'task_id': task_id,
                    'current_status': task['status'],
                    'progress': task.get('progress', 0)
                },
                status_code=202  # Accepted but not ready
            )

        result = task.get('result')
        if not result:
            return APIResponse.error(
                code=ErrorCodes.TASK_FAILED,
                message='任务完成但无结果数据',
                details={'task_id': task_id},
                status_code=500
            )

        meta = {
            'task_id': task_id,
            'task_type': task.get('type'),
            'completed_at': task.get('updated_at'),
            'processing_time': task.get('processing_time')
        }

        return APIResponse.success(data=result, meta=meta)

    except Exception as e:
        logger.error(f"获取任务结果API出错: {traceback.format_exc()}")
        return APIResponse.error(
            code=ErrorCodes.INTERNAL_SERVER_ERROR,
            message='获取任务结果失败',
            details={'error_message': str(e)},
            status_code=500
        )


def estimate_task_completion_time(task_type: str, params: Dict) -> int:
    """估算任务完成时间（秒）"""
    base_times = {
        'stock_analysis': 30,      # 个股分析：30秒
        'portfolio_analysis': 60,  # 组合分析：60秒
        'batch_score': 120,        # 批量评分：120秒
        'market_scan': 300         # 市场扫描：300秒
    }

    base_time = base_times.get(task_type, 60)

    # 根据参数调整时间
    if task_type == 'portfolio_analysis':
        stocks_count = len(params.get('stocks', []))
        base_time += stocks_count * 5  # 每只股票增加5秒
    elif task_type == 'batch_score':
        codes_count = len(params.get('stock_codes', []))
        base_time += codes_count * 2   # 每只股票增加2秒
    elif task_type == 'market_scan':
        stocks_count = len(params.get('stock_list', []))
        base_time += stocks_count * 1  # 每只股票增加1秒

    return min(base_time, 1800)  # 最大30分钟


def get_risk_level(risk_score):
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


def _format_traditional_result(stock_code: str, analysis_result: Dict,
                             risk_assessment: Dict, fundamental_result: Dict, market_type: str) -> Dict:
    """格式化传统分析结果"""
    try:
        # 安全获取数据，提供默认值
        stock_name = analysis_result.get('stock_name', '未知') if analysis_result else '未知'
        overall_score = analysis_result.get('score', 0) if analysis_result else 0
        technical_score = analysis_result.get('technical_score', 0) if analysis_result else 0
        fundamental_score = fundamental_result.get('total_score', 0) if fundamental_result else 0
        risk_score = risk_assessment.get('total_risk_score', 50) if risk_assessment else 50

        # 构建响应数据
        response_data = {
            'stock_info': {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'industry': analysis_result.get('industry', '未知') if analysis_result else '未知',
                'market_type': market_type
            },
            'analysis_result': {
                'overall_score': overall_score,
                'technical_score': technical_score,
                'fundamental_score': fundamental_score,
                'risk_score': risk_score
            },
            'scores': {
                'overall_score': overall_score,
                'technical_score': technical_score,
                'fundamental_score': fundamental_score,
                'risk_score': risk_score
            },
            'risk_assessment': {
                'total_risk_score': risk_score,
                'risk_level': get_risk_level(risk_score)
            },
            'recommendation': analysis_result.get('recommendation', '持有') if analysis_result else '持有',
            'fallback_info': {
                'analysis_type': 'traditional',
                'data_source': 'direct_api'
            }
        }

        # 添加基本信息（如果存在）
        if analysis_result:
            basic_info = {
                'name': stock_name,
                'current_price': analysis_result.get('price', 0),
                'change_percent': analysis_result.get('price_change', 0),
                'volume': analysis_result.get('volume', 0)
            }
            response_data['basic_info'] = basic_info

        return response_data

    except Exception as e:
        logger.error(f"格式化传统分析结果失败: {e}")
        # 返回基础结构
        return {
            'stock_info': {
                'stock_code': stock_code,
                'stock_name': '未知',
                'industry': '未知',
                'market_type': market_type
            },
            'analysis_result': {
                'overall_score': 0,
                'technical_score': 0,
                'fundamental_score': 0,
                'risk_score': 50
            },
            'scores': {
                'overall_score': 0,
                'technical_score': 0,
                'fundamental_score': 0,
                'risk_score': 50
            },
            'risk_assessment': {
                'total_risk_score': 50,
                'risk_level': '中等风险'
            },
            'recommendation': '持有',
            'fallback_info': {
                'analysis_type': 'error_fallback',
                'error_message': str(e)
            }
        }
