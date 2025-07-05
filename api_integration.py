# -*- coding: utf-8 -*-
"""
API集成模块
将新的API功能集成到现有的Flask应用中
"""

import logging
import time
from typing import Dict, Any
from flask import Flask

# 导入API模块
from api_endpoints import api_v1, init_analyzers
from rate_limiter import start_cleanup_scheduler
from api_cache_integration import preload_cache_for_popular_stocks
from auth_middleware import api_key_manager

logger = logging.getLogger(__name__)


def register_api_endpoints(app: Flask):
    """注册API端点到Flask应用"""
    try:
        # 注册API蓝图
        app.register_blueprint(api_v1)
        logger.info("API v1端点已注册")

        # 初始化分析器 - 尝试从多个来源获取分析器实例
        from stock_analyzer import StockAnalyzer
        from risk_monitor import RiskMonitor
        from fundamental_analyzer import FundamentalAnalyzer

        # 尝试从app对象获取分析器实例
        analyzer = getattr(app, 'analyzer', None)
        risk_monitor_instance = getattr(app, 'risk_monitor', None)
        fundamental_analyzer_instance = getattr(app, 'fundamental_analyzer', None)

        # 如果app对象中没有，尝试从全局变量获取
        if analyzer is None:
            try:
                import web_server
                analyzer = getattr(web_server, 'analyzer', None)
                risk_monitor_instance = getattr(web_server, 'risk_monitor', None)
                fundamental_analyzer_instance = getattr(web_server, 'fundamental_analyzer', None)
                logger.info("从web_server模块获取分析器实例")
            except Exception as e:
                logger.warning(f"无法从web_server模块获取分析器: {e}")

        # 如果仍然没有，创建新的实例
        if analyzer is None:
            analyzer = StockAnalyzer()
            logger.info("创建新的StockAnalyzer实例")
        if risk_monitor_instance is None:
            risk_monitor_instance = RiskMonitor(analyzer)
            logger.info("创建新的RiskMonitor实例")
        if fundamental_analyzer_instance is None:
            fundamental_analyzer_instance = FundamentalAnalyzer()
            logger.info("创建新的FundamentalAnalyzer实例")

        # 初始化API端点的分析器
        init_analyzers(analyzer, risk_monitor_instance, fundamental_analyzer_instance)
        logger.info("API分析器已初始化")

        return True

    except Exception as e:
        logger.error(f"注册API端点失败: {e}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False


def setup_api_middleware(app: Flask):
    """设置API中间件"""
    try:
        # 启动限流器清理调度器
        start_cleanup_scheduler()
        logger.info("限流器清理调度器已启动")
        
        # 移除自动预加载热门股票缓存，避免系统启动时的API调用
        # 如需预加载，可通过API手动触发：POST /api/v1/cache/preload
        # import threading
        # def preload_cache():
        #     try:
        #         preload_cache_for_popular_stocks()
        #     except Exception as e:
        #         logger.error(f"预加载缓存失败: {e}")
        #
        # cache_thread = threading.Thread(target=preload_cache, daemon=True)
        # cache_thread.start()
        logger.info("缓存预加载已禁用，系统启动更快")
        
        return True
        
    except Exception as e:
        logger.error(f"设置API中间件失败: {e}")
        return False


def add_api_routes_to_existing_app(app: Flask):
    """将API路由添加到现有应用"""
    
    # 添加API状态检查端点
    @app.route('/api/v1/health', methods=['GET'])
    def api_health_check():
        """API健康检查"""
        from api_response import APIResponse
        from api_cache_integration import get_cache_statistics
        
        try:
            # 检查各个组件状态
            status = {
                'api_version': '1.0.0',
                'status': 'healthy',
                'components': {
                    'database': check_database_status(),
                    'cache': check_cache_status(),
                    'analyzers': check_analyzers_status()
                },
                'cache_statistics': get_cache_statistics()
            }
            
            return APIResponse.success(data=status)
            
        except Exception as e:
            logger.error(f"API健康检查失败: {e}")
            from api_response import ErrorCodes
            return APIResponse.error(
                code=ErrorCodes.INTERNAL_SERVER_ERROR,
                message='健康检查失败',
                details={'error': str(e)},
                status_code=500
            )
    
    # 添加API密钥管理端点（仅限管理员）
    @app.route('/api/v1/admin/api-keys', methods=['POST'])
    def generate_api_key():
        """生成新的API密钥（管理员功能）"""
        from flask import request
        from api_response import APIResponse, ErrorCodes
        from auth_middleware import require_api_key
        
        # 这里应该添加管理员权限检查
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != app.config.get('ADMIN_KEY'):
            return APIResponse.error(
                code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
                message='需要管理员权限',
                status_code=403
            )
        
        try:
            data = request.get_json() or {}
            tier = data.get('tier', 'free')
            permissions = data.get('permissions', ['stock_analysis'])
            
            new_api_key = api_key_manager.generate_api_key(tier, permissions)
            
            return APIResponse.success(data={
                'api_key': new_api_key,
                'tier': tier,
                'permissions': permissions,
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            })
            
        except Exception as e:
            logger.error(f"生成API密钥失败: {e}")
            return APIResponse.error(
                code=ErrorCodes.INTERNAL_SERVER_ERROR,
                message='生成API密钥失败',
                details={'error': str(e)},
                status_code=500
            )
    
    # 添加缓存管理端点
    @app.route('/api/v1/admin/cache/clear', methods=['POST'])
    def clear_api_cache():
        """清除API缓存（管理员功能）"""
        from flask import request
        from api_response import APIResponse, ErrorCodes
        from api_cache_integration import smart_cache_invalidation
        
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != app.config.get('ADMIN_KEY'):
            return APIResponse.error(
                code=ErrorCodes.INSUFFICIENT_PERMISSIONS,
                message='需要管理员权限',
                status_code=403
            )
        
        try:
            data = request.get_json() or {}
            stock_codes = data.get('stock_codes')
            cache_types = data.get('cache_types')
            
            smart_cache_invalidation(stock_codes, cache_types)
            
            return APIResponse.success(data={
                'message': '缓存清除完成',
                'cleared_stock_codes': stock_codes,
                'cleared_cache_types': cache_types
            })
            
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return APIResponse.error(
                code=ErrorCodes.INTERNAL_SERVER_ERROR,
                message='清除缓存失败',
                details={'error': str(e)},
                status_code=500
            )
    
    logger.info("API管理端点已添加")


def check_database_status() -> Dict:
    """检查数据库状态"""
    try:
        from database import test_connection, USE_DATABASE
        if USE_DATABASE:
            connected = test_connection()
            return {'status': 'connected' if connected else 'disconnected', 'enabled': True}
        else:
            return {'status': 'disabled', 'enabled': False}
    except Exception as e:
        return {'status': 'error', 'error': str(e), 'enabled': False}


def check_cache_status() -> Dict:
    """检查缓存状态"""
    try:
        from api_cache_integration import get_cache_statistics
        stats = get_cache_statistics()
        return {'status': 'active', 'statistics': stats}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def check_analyzers_status() -> Dict:
    """检查分析器状态"""
    try:
        # 简单测试分析器是否可用
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # 尝试获取一个简单的股票信息
        test_result = analyzer.get_stock_info('000001.SZ')
        
        return {
            'status': 'active',
            'test_result': bool(test_result)
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def integrate_api_with_existing_app(app: Flask) -> bool:
    """将API功能集成到现有应用"""
    try:
        logger.info("开始集成API功能到现有应用")
        
        # 1. 注册API端点
        if not register_api_endpoints(app):
            logger.error("注册API端点失败")
            return False
        
        # 2. 设置中间件
        if not setup_api_middleware(app):
            logger.error("设置API中间件失败")
            return False
        
        # 3. 添加管理端点
        add_api_routes_to_existing_app(app)
        
        # 4. 更新应用配置
        app.config.setdefault('API_ENABLED', True)
        app.config.setdefault('API_VERSION', '1.0.0')
        
        logger.info("API功能集成完成")
        return True
        
    except Exception as e:
        logger.error(f"API功能集成失败: {e}")
        return False


# 使用示例
def example_usage():
    """使用示例"""
    print("""
    # 在现有的web_server.py中添加以下代码来集成API功能：
    
    from api_integration import integrate_api_with_existing_app
    
    # 在创建Flask应用后
    app = Flask(__name__)
    
    # 集成API功能
    if integrate_api_with_existing_app(app):
        print("API功能集成成功")
    else:
        print("API功能集成失败")
    
    # API端点将在以下路径可用：
    # POST /api/v1/portfolio/analyze - 投资组合分析
    # POST /api/v1/stock/analyze - 个股分析  
    # POST /api/v1/stocks/batch-score - 批量股票评分
    # POST /api/v1/tasks - 创建异步任务
    # GET /api/v1/tasks/{task_id} - 查询任务状态
    # GET /api/v1/tasks/{task_id}/result - 获取任务结果
    # GET /api/v1/health - API健康检查
    """)
