# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - 股票市场数据分析系统
修改：熊猫大侠
版本：v2.1.0
"""
# web_server.py

import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import csv
import io
from stock_analyzer import StockAnalyzer
from us_stock_service import USStockService
import threading
import logging
from logging.handlers import RotatingFileHandler
import traceback
import os
import json
from datetime import date, datetime, timedelta
from flask_cors import CORS
import time
from flask_caching import Cache
import threading
import sys
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv

# 条件导入数据库模块
try:
    from database import get_session, USE_DATABASE
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"数据库模块导入失败: {e}")
    DATABASE_AVAILABLE = False
    USE_DATABASE = False

    def get_session():
        """数据库不可用时的占位函数"""
        return None
from industry_analyzer import IndustryAnalyzer
from fundamental_analyzer import FundamentalAnalyzer
from capital_flow_analyzer import CapitalFlowAnalyzer
from scenario_predictor import ScenarioPredictor
from stock_qa import StockQA
from risk_monitor import RiskMonitor
from index_industry_analyzer import IndexIndustryAnalyzer
from news_fetcher import news_fetcher, start_news_scheduler
from data_service import DataService
from stock_precache_scheduler import precache_scheduler, init_precache_scheduler

# API功能导入
try:
    from api_integration import integrate_api_with_existing_app
    API_INTEGRATION_AVAILABLE = True
    print("API集成模块导入成功")
except ImportError as e:
    print(f"API集成模块导入失败: {e}")
    API_INTEGRATION_AVAILABLE = False

# 加载环境变量
load_dotenv()

# 检查是否需要初始化数据库
if DATABASE_AVAILABLE and USE_DATABASE:
    try:
        from database import init_db
        init_db()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        DATABASE_AVAILABLE = False
        USE_DATABASE = False

# 配置Swagger
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "股票智能分析系统 API文档"
    }
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 禁用模板缓存以确保修改立即生效
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

analyzer = StockAnalyzer()
us_stock_service = USStockService()

# 配置缓存
cache_config = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
}

# 如果配置了Redis，使用Redis作为缓存后端
if os.getenv('USE_REDIS_CACHE', 'False').lower() == 'true' and os.getenv('REDIS_URL'):
    cache_config = {
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': os.getenv('REDIS_URL'),
        'CACHE_DEFAULT_TIMEOUT': 300
    }

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# 确保全局变量在重新加载时不会丢失
if 'analyzer' not in globals():
    try:
        from stock_analyzer import StockAnalyzer

        analyzer = StockAnalyzer()
        print("成功初始化全局StockAnalyzer实例")
    except Exception as e:
        print(f"初始化StockAnalyzer时出错: {e}", file=sys.stderr)
        raise

# 初始化模块实例
fundamental_analyzer = FundamentalAnalyzer()
capital_flow_analyzer = CapitalFlowAnalyzer()
scenario_predictor = ScenarioPredictor(analyzer, os.getenv('OPENAI_API_KEY'), os.getenv('OPENAI_API_MODEL'))
stock_qa = StockQA(analyzer, os.getenv('OPENAI_API_KEY'), os.getenv('OPENAI_API_MODEL'))
risk_monitor = RiskMonitor(analyzer)
index_industry_analyzer = IndexIndustryAnalyzer(analyzer)
industry_analyzer = IndustryAnalyzer()
data_service = DataService()

start_news_scheduler()

# 线程本地存储
thread_local = threading.local()


def get_analyzer():
    """获取线程本地的分析器实例"""
    # 如果线程本地存储中没有分析器实例，创建一个新的
    if not hasattr(thread_local, 'analyzer'):
        thread_local.analyzer = StockAnalyzer()
    return thread_local.analyzer


# 配置日志
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('flask_app.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
app.logger.addHandler(handler)

# 旧的任务管理代码已移除，现在只使用统一任务管理器


# 统一任务管理系统 - 解决多套存储机制问题
class UnifiedTaskManager:
    """统一任务管理器 - 彻底解决任务存储不一致问题"""

    def __init__(self):
        self.tasks = {}  # 统一的任务存储
        self.lock = threading.RLock()  # 使用可重入锁，避免死锁
        self.protected_tasks = set()  # 受保护的任务ID集合

        # 任务状态常量
        self.PENDING = 'pending'
        self.RUNNING = 'running'
        self.COMPLETED = 'completed'
        self.FAILED = 'failed'
        self.CANCELLED = 'cancelled'

    def protect_task(self, task_id, duration_seconds=3600):
        """保护任务不被清理，默认保护1小时"""
        with self.lock:
            self.protected_tasks.add(task_id)
            app.logger.info(f"统一任务管理器: 任务 {task_id} 已加入保护列表")

            # 设置定时器自动移除保护
            def remove_protection():
                time.sleep(duration_seconds)
                with self.lock:
                    self.protected_tasks.discard(task_id)
                    app.logger.info(f"统一任务管理器: 任务 {task_id} 保护期结束")

            protection_thread = threading.Thread(target=remove_protection)
            protection_thread.daemon = True
            protection_thread.start()

    def is_task_protected(self, task_id):
        """检查任务是否受保护"""
        return task_id in self.protected_tasks

    def create_task(self, task_type, **params):
        """创建新任务 - 线程安全，增强调试"""
        import uuid
        task_id = str(uuid.uuid4())

        # 详细的任务创建日志
        app.logger.info(f"统一任务管理器: 开始创建任务，类型: {task_type}")
        app.logger.info(f"统一任务管理器: 生成任务ID: {task_id}")
        app.logger.info(f"统一任务管理器: 任务参数: {params}")

        with self.lock:
            # 检查任务ID是否已存在（理论上不应该发生）
            if task_id in self.tasks:
                app.logger.error(f"统一任务管理器: 严重错误！任务ID {task_id} 已存在！")
                # 重新生成ID
                task_id = str(uuid.uuid4())
                app.logger.info(f"统一任务管理器: 重新生成任务ID: {task_id}")

            task = {
                'id': task_id,
                'type': task_type,
                'status': self.PENDING,
                'progress': 0,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'progress_updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'params': params,
                'result': None,
                'error': None
            }

            # 添加任务类型特定的字段
            if task_type == 'market_scan':
                task.update({
                    'total': params.get('total', 0),
                    'processed': 0,
                    'found': 0,
                    'failed': 0,
                    'timeout': 0,
                    'estimated_remaining': 0
                })

            # 存储任务
            self.tasks[task_id] = task

            # 详细的存储验证日志
            app.logger.info(f"统一任务管理器: 任务 {task_id} 已存储到内存")
            app.logger.info(f"统一任务管理器: 任务创建后，当前任务数: {len(self.tasks)}")
            app.logger.info(f"统一任务管理器: 当前任务列表: {list(self.tasks.keys())}")

            # 立即验证任务是否正确存储
            verification_task = self.tasks.get(task_id)
            if verification_task:
                app.logger.info(f"统一任务管理器: 任务存储验证成功 - ID: {verification_task['id']}, 状态: {verification_task['status']}")
            else:
                app.logger.error(f"统一任务管理器: 严重错误！任务存储验证失败 - 任务 {task_id} 未找到！")

        return task_id, task

    def get_task(self, task_id):
        """获取任务 - 线程安全，增强调试"""
        app.logger.info(f"统一任务管理器: 开始查询任务 {task_id}")
        app.logger.info(f"统一任务管理器: 当前任务数量: {len(self.tasks)}")

        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                app.logger.info(f"统一任务管理器: 成功获取任务 {task_id}, 状态: {task['status']}, 类型: {task.get('type', '未知')}")
                app.logger.info(f"统一任务管理器: 任务详情 - 进度: {task.get('progress', 0)}%, 创建时间: {task.get('created_at', '未知')}")
                app.logger.info(f"统一任务管理器: 任务更新时间: {task.get('updated_at', '未知')}")

                # 检查任务是否是刚创建的
                try:
                    created_at = datetime.strptime(task['created_at'], '%Y-%m-%d %H:%M:%S')
                    age_seconds = (datetime.now() - created_at).total_seconds()
                    app.logger.info(f"统一任务管理器: 任务 {task_id} 创建于 {age_seconds:.1f} 秒前")
                except:
                    pass
            else:
                app.logger.error(f"统一任务管理器: 任务 {task_id} 不存在！")
                app.logger.error(f"统一任务管理器: 当前任务数: {len(self.tasks)}")
                app.logger.error(f"统一任务管理器: 当前任务列表: {list(self.tasks.keys())}")

                # 检查是否有相似的任务ID
                similar_ids = []
                for existing_id in self.tasks.keys():
                    if existing_id.startswith(task_id[:8]) or task_id.startswith(existing_id[:8]):
                        similar_ids.append(existing_id)
                        app.logger.warning(f"统一任务管理器: 发现相似任务ID: {existing_id}")

                if not similar_ids:
                    app.logger.error(f"统一任务管理器: 没有发现相似的任务ID")

            return task

    def update_task(self, task_id, status=None, progress=None, result=None, error=None, **kwargs):
        """更新任务状态 - 线程安全，增强调试"""
        app.logger.info(f"统一任务管理器: 开始更新任务 {task_id}")
        app.logger.info(f"统一任务管理器: 更新参数 - 状态: {status}, 进度: {progress}, 结果类型: {type(result).__name__ if result is not None else 'None'}")

        with self.lock:
            if task_id not in self.tasks:
                app.logger.error(f"统一任务管理器: 尝试更新不存在的任务 {task_id}")
                app.logger.error(f"统一任务管理器: 当前任务列表: {list(self.tasks.keys())}")
                return False

            task = self.tasks[task_id]
            old_status = task.get('status', '')
            old_progress = task.get('progress', 0)

            app.logger.info(f"统一任务管理器: 任务 {task_id} 当前状态: {old_status}, 当前进度: {old_progress}%")

            # 更新基本字段
            if status is not None:
                task['status'] = status
                app.logger.info(f"统一任务管理器: 任务 {task_id} 状态更新: {old_status} -> {status}")
            if progress is not None:
                task['progress'] = progress
                # 如果进度有变化，更新进度时间戳
                if progress != old_progress:
                    task['progress_updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    app.logger.info(f"统一任务管理器: 任务 {task_id} 进度更新: {old_progress}% -> {progress}%")
            if result is not None:
                task['result'] = result
                if isinstance(result, list):
                    app.logger.info(f"统一任务管理器: 任务 {task_id} 结果已保存，共 {len(result)} 个结果")
                else:
                    app.logger.info(f"统一任务管理器: 任务 {task_id} 结果已保存，类型: {type(result).__name__}")
            if error is not None:
                task['error'] = error
                app.logger.error(f"统一任务管理器: 任务 {task_id} 错误信息: {error}")

            # 更新其他字段
            for key, value in kwargs.items():
                task[key] = value
                app.logger.debug(f"统一任务管理器: 任务 {task_id} 更新字段 {key}: {value}")

            task['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 验证任务更新成功
            verification_task = self.tasks.get(task_id)
            if verification_task:
                app.logger.info(f"统一任务管理器: 任务 {task_id} 更新验证成功 - 最新状态: {verification_task['status']}, 最新进度: {verification_task.get('progress', 0)}%")
            else:
                app.logger.error(f"统一任务管理器: 严重错误！任务 {task_id} 更新后验证失败！")

            return True

    def cleanup_old_tasks(self):
        """清理旧任务 - 超保守策略，最大化任务保护"""
        with self.lock:
            now = datetime.now()
            to_delete = []

            app.logger.info(f"统一任务管理器: 开始清理检查，当前任务数: {len(self.tasks)}")

            for task_id, task in self.tasks.items():
                try:
                    created_at = datetime.strptime(task['created_at'], '%Y-%m-%d %H:%M:%S')
                    updated_at = datetime.strptime(task['updated_at'], '%Y-%m-%d %H:%M:%S')

                    # 计算任务创建时间和最后更新时间
                    creation_time_diff = (now - created_at).total_seconds()
                    update_time_diff = (now - updated_at).total_seconds()

                    should_delete = False

                    # 超强新任务保护机制：创建时间少于30分钟的任务绝对不会被清理
                    if creation_time_diff < 1800:  # 30分钟绝对保护期
                        app.logger.debug(f"统一任务管理器: 任务 {task_id} 创建时间少于30分钟，绝对保护不被清理")
                        continue

                    # 活跃任务保护：最近5分钟内有更新的任务不会被清理
                    if update_time_diff < 300:  # 5分钟活跃保护
                        app.logger.debug(f"统一任务管理器: 任务 {task_id} 最近5分钟内有更新，活跃保护不被清理")
                        continue

                    # 检查任务是否在保护列表中
                    if self.is_task_protected(task_id):
                        app.logger.info(f"统一任务管理器: 任务 {task_id} 在保护列表中，不被清理")
                        continue

                    if task['status'] in [self.COMPLETED, self.FAILED, self.CANCELLED]:
                        # 完成的任务，根据类型设置不同的保持时间
                        if task.get('type') == 'stock_analysis':
                            # 股票分析任务：保持2小时，确保前端有足够时间获取结果
                            should_delete = update_time_diff > 7200  # 2小时
                        elif task.get('type') == 'market_scan':
                            # 市场扫描任务：保持4小时，结果较复杂需要更长查看时间
                            should_delete = update_time_diff > 14400  # 4小时
                        else:
                            # 其他任务：保持1小时
                            should_delete = update_time_diff > 3600  # 1小时
                    elif task['status'] == self.RUNNING:
                        # 运行中的任务，极其保守的清理策略
                        if update_time_diff > 86400:  # 24小时
                            # 检查进度更新
                            progress_updated_at = datetime.strptime(
                                task.get('progress_updated_at', task['updated_at']),
                                '%Y-%m-%d %H:%M:%S'
                            )
                            progress_time_diff = (now - progress_updated_at).total_seconds()

                            # 只有在24小时内完全没有进度更新才清理
                            if progress_time_diff > 86400:  # 24小时内无进度更新
                                should_delete = True
                                app.logger.warning(f"统一任务管理器: 任务 {task_id} 运行超过24小时且24小时内无进度更新，判定为卡死")
                            else:
                                app.logger.info(f"统一任务管理器: 任务 {task_id} 虽然运行超过24小时，但最近有进度更新，继续保护")
                    elif task['status'] == self.PENDING:
                        # 等待中的任务，12小时后清理（大幅延长）
                        should_delete = update_time_diff > 43200  # 12小时

                    if should_delete:
                        # 最后一次确认：检查任务是否真的应该被删除
                        task_age_hours = creation_time_diff / 3600
                        update_age_hours = update_time_diff / 3600

                        # 额外保护：如果任务类型是stock_analysis且年龄小于2小时，不删除
                        if task.get('type') == 'stock_analysis' and task_age_hours < 2:
                            app.logger.warning(f"统一任务管理器: 任务 {task_id} 是股票分析任务且年龄小于2小时，额外保护不删除")
                            continue

                        to_delete.append(task_id)
                        app.logger.info(f"统一任务管理器: 准备清理任务 {task_id}，状态: {task['status']}, 类型: {task.get('type', '未知')}, 创建: {task_age_hours:.1f}小时前, 更新: {update_age_hours:.1f}小时前")

                except Exception as e:
                    app.logger.error(f"统一任务管理器: 清理任务 {task_id} 时出错: {str(e)}")

            # 删除旧任务
            if to_delete:
                app.logger.info(f"统一任务管理器: 准备删除 {len(to_delete)} 个任务")
                for task_id in to_delete:
                    del self.tasks[task_id]
                    app.logger.info(f"统一任务管理器: 已清理任务 {task_id}")
            else:
                app.logger.info(f"统一任务管理器: 没有需要清理的任务")

            return len(to_delete)

    def cleanup_completed_tasks(self):
        """清理所有已完成的任务 - 线程安全"""
        with self.lock:
            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                if task['status'] in [self.COMPLETED, self.FAILED, 'cancelled']:
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                del self.tasks[task_id]

            if tasks_to_remove:
                app.logger.info(f"统一任务管理器: 清理了 {len(tasks_to_remove)} 个已完成任务")

            return len(tasks_to_remove)

# 创建全局统一任务管理器
unified_task_manager = UnifiedTaskManager()

# 导入实时通信集成
try:
    from realtime_integration import init_realtime_communication
    REALTIME_AVAILABLE = True
except ImportError:
    REALTIME_AVAILABLE = False
    app.logger.warning("实时通信模块不可用，将使用传统轮询方式")

# 安全的兼容性接口 - 不直接暴露内部字典
class SafeTaskInterface:
    """安全的任务接口，防止直接操作内部字典"""

    def __init__(self, task_manager):
        self._task_manager = task_manager

    def __contains__(self, task_id):
        """检查任务是否存在"""
        return self._task_manager.get_task(task_id) is not None

    def __getitem__(self, task_id):
        """获取任务"""
        task = self._task_manager.get_task(task_id)
        if task is None:
            raise KeyError(f"任务 {task_id} 不存在")
        return task

    def __setitem__(self, task_id, task_data):
        """设置任务 - 不推荐直接使用，应该通过任务管理器方法"""
        app.logger.warning(f"直接设置任务 {task_id} - 建议使用任务管理器方法")
        # 这里可以添加逻辑来处理直接设置的情况
        pass

    def __delitem__(self, task_id):
        """删除任务 - 不推荐直接使用，应该通过任务管理器方法"""
        app.logger.warning(f"直接删除任务 {task_id} - 建议使用任务管理器方法")
        # 不执行实际删除，记录警告
        pass

    def items(self):
        """获取所有任务项"""
        with self._task_manager.lock:
            return list(self._task_manager.tasks.items())

    def keys(self):
        """获取所有任务ID"""
        with self._task_manager.lock:
            return list(self._task_manager.tasks.keys())

    def values(self):
        """获取所有任务"""
        with self._task_manager.lock:
            return list(self._task_manager.tasks.values())

# 创建安全的兼容性接口
scan_tasks = SafeTaskInterface(unified_task_manager)
task_lock = unified_task_manager.lock    # 锁可以安全共享

# 任务状态常量 - 兼容性
TASK_PENDING = unified_task_manager.PENDING
TASK_RUNNING = unified_task_manager.RUNNING
TASK_COMPLETED = unified_task_manager.COMPLETED
TASK_FAILED = unified_task_manager.FAILED

def generate_task_id():
    """生成唯一的任务ID"""
    import uuid
    return str(uuid.uuid4())


def start_market_scan_task_status(task_id, status, progress=None, result=None, error=None, **kwargs):
    """更新任务状态 - 使用统一任务管理器"""
    return unified_task_manager.update_task(
        task_id=task_id,
        status=status,
        progress=progress,
        result=result,
        error=error,
        **kwargs
    )


# 旧的个股分析任务管理代码已移除，现在使用统一任务管理器


# 定义自定义JSON编码器


# 在web_server.py中，更新convert_numpy_types函数以处理NaN值

# 将NumPy类型转换为Python原生类型的函数
def convert_numpy_types(obj):
    """递归地将字典和列表中的NumPy类型转换为Python原生类型"""
    try:
        import numpy as np
        import math

        if isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            # Handle NaN and Infinity specifically
            if np.isnan(obj):
                return None
            elif np.isinf(obj):
                return None if obj < 0 else 1e308  # Use a very large number for +Infinity
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        # Handle Python's own float NaN and Infinity
        elif isinstance(obj, float):
            if math.isnan(obj):
                return None
            elif math.isinf(obj):
                return None
            return obj
        # 添加对date和datetime类型的处理
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        else:
            return obj
    except ImportError:
        # 如果没有安装numpy，但需要处理date和datetime
        import math
        if isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        # Handle Python's own float NaN and Infinity
        elif isinstance(obj, float):
            if math.isnan(obj):
                return None
            elif math.isinf(obj):
                return None
            return obj
        return obj


# 同样更新 NumpyJSONEncoder 类
class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # For NumPy data types
        try:
            import numpy as np
            import math
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                # Handle NaN and Infinity specifically
                if np.isnan(obj):
                    return None
                elif np.isinf(obj):
                    return None
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.bool_):
                return bool(obj)
            # Handle Python's own float NaN and Infinity
            elif isinstance(obj, float):
                if math.isnan(obj):
                    return None
                elif math.isinf(obj):
                    return None
                return obj
        except ImportError:
            # Handle Python's own float NaN and Infinity if numpy is not available
            import math
            if isinstance(obj, float):
                if math.isnan(obj):
                    return None
                elif math.isinf(obj):
                    return None

        # 添加对date和datetime类型的处理
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()

        return super(NumpyJSONEncoder, self).default(obj)


# 使用我们的编码器的自定义 jsonify 函数
def custom_jsonify(data):
    return app.response_class(
        json.dumps(convert_numpy_types(data), cls=NumpyJSONEncoder),
        mimetype='application/json'
    )


# 保持API兼容的路由
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        stock_codes = data.get('stock_codes', [])
        market_type = data.get('market_type', 'A')

        if not stock_codes:
            return jsonify({'error': '请输入代码'}), 400

        app.logger.info(f"分析股票请求: {stock_codes}, 市场类型: {market_type}")

        # 设置最大处理时间，每只股票10秒
        max_time_per_stock = 10  # 秒
        max_total_time = max(30, min(60, len(stock_codes) * max_time_per_stock))  # 至少30秒，最多60秒

        start_time = time.time()
        results = []

        for stock_code in stock_codes:
            try:
                # 检查是否已超时
                if time.time() - start_time > max_total_time:
                    app.logger.warning(f"分析股票请求已超过{max_total_time}秒，提前返回已处理的{len(results)}只股票")
                    break

                # 使用线程本地缓存的分析器实例
                current_analyzer = get_analyzer()
                result = current_analyzer.quick_analyze_stock(stock_code.strip(), market_type)

                app.logger.info(
                    f"分析结果: 股票={stock_code}, 名称={result.get('stock_name', '未知')}, 行业={result.get('industry', '未知')}")
                results.append(result)
            except Exception as e:
                app.logger.error(f"分析股票 {stock_code} 时出错: {str(e)}")
                results.append({
                    'stock_code': stock_code,
                    'error': str(e),
                    'stock_name': '分析失败',
                    'industry': '未知'
                })

        return jsonify({'results': results})
    except Exception as e:
        app.logger.error(f"分析股票时出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/north_flow_history', methods=['POST'])
def api_north_flow_history():
    try:
        data = request.json
        stock_code = data.get('stock_code')
        days = data.get('days', 10)  # 默认为10天，对应前端的默认选项

        # 计算 end_date 为当前时间
        end_date = datetime.now().strftime('%Y%m%d')

        # 计算 start_date 为 end_date 减去指定的天数
        start_date = (datetime.now() - timedelta(days=int(days))).strftime('%Y%m%d')

        if not stock_code:
            return jsonify({'error': '请提供股票代码'}), 400

        # 调用北向资金历史数据方法
        from capital_flow_analyzer import CapitalFlowAnalyzer

        analyzer = CapitalFlowAnalyzer()
        result = analyzer.get_north_flow_history(stock_code, start_date, end_date)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"获取北向资金历史数据出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/search_us_stocks', methods=['GET'])
def search_us_stocks():
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'error': '请输入搜索关键词'}), 400

        results = us_stock_service.search_us_stocks(keyword)
        return jsonify({'results': results})

    except Exception as e:
        app.logger.error(f"搜索美股代码时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 新增可视化分析页面路由
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/stock_detail/<string:stock_code>')
def stock_detail(stock_code):
    market_type = request.args.get('market_type', 'A')
    return render_template('stock_detail.html', stock_code=stock_code, market_type=market_type)


@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')


@app.route('/market_scan')
def market_scan():
    return render_template('market_scan.html')


@app.route('/test_scan')
def test_scan():
    """测试扫描页面"""
    return send_from_directory('.', 'test_scan_simple.html')


# 基本面分析页面
@app.route('/fundamental')
def fundamental():
    return render_template('fundamental.html')


# 资金流向页面
@app.route('/capital_flow')
def capital_flow():
    return render_template('capital_flow.html')

# 修复验证页面
@app.route('/test_fix')
def test_fix():
    return render_template('test_fix.html')


# 情景预测页面
@app.route('/scenario_predict')
def scenario_predict():
    return render_template('scenario_predict.html')


# 风险监控页面
@app.route('/risk_monitor')
def risk_monitor_page():
    return render_template('risk_monitor.html')


# 智能问答页面
@app.route('/qa')
def qa_page():
    return render_template('qa.html')


# 行业分析页面
@app.route('/industry_analysis')
def industry_analysis():
    return render_template('industry_analysis.html')


def make_cache_key_with_stock():
    """创建包含股票代码的自定义缓存键"""
    path = request.path

    # 从请求体中获取股票代码
    stock_code = None
    if request.is_json:
        stock_code = request.json.get('stock_code')

    # 构建包含股票代码的键
    if stock_code:
        return f"{path}_{stock_code}"
    else:
        return path


@app.route('/api/start_stock_analysis', methods=['POST'])
def start_stock_analysis():
    """启动个股分析任务 - 使用统一任务管理器"""
    try:
        data = request.json
        stock_code = data.get('stock_code')
        market_type = data.get('market_type', 'A')

        if not stock_code:
            return jsonify({'error': '请输入股票代码'}), 400

        app.logger.info(f"准备分析股票: {stock_code}")

        # 使用统一任务管理器创建任务
        task_id, task = unified_task_manager.create_task(
            'stock_analysis',
            stock_code=stock_code,
            market_type=market_type
        )

        # 立即保护新创建的任务，防止被意外清理
        unified_task_manager.protect_task(task_id, duration_seconds=14400)  # 保护4小时，适应长时间分析任务

        # 启动后台线程执行分析
        def run_analysis():
            try:
                unified_task_manager.update_task(task_id, status=TASK_RUNNING, progress=10)

                # 执行分析
                result = analyzer.perform_enhanced_analysis(stock_code, market_type)

                # 更新任务状态为完成
                unified_task_manager.update_task(task_id, status=TASK_COMPLETED, progress=100, result=result)
                app.logger.info(f"分析任务 {task_id} 完成")

                # 延长已完成任务的保护时间，确保前端有足够时间获取结果
                unified_task_manager.protect_task(task_id, duration_seconds=7200)  # 额外保护2小时

            except Exception as e:
                app.logger.error(f"分析任务 {task_id} 失败: {str(e)}")
                app.logger.error(traceback.format_exc())
                unified_task_manager.update_task(task_id, status=TASK_FAILED, error=str(e))

        # 启动后台线程
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()

        # 返回任务ID和状态
        return jsonify({
            'task_id': task_id,
            'status': task['status'],
            'message': f'已启动分析任务: {stock_code}'
        })

    except Exception as e:
        app.logger.error(f"启动个股分析任务时出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis_status/<task_id>', methods=['GET'])
def get_analysis_status(task_id):
    """获取个股分析任务状态 - 使用统一任务管理器，增强日志追踪和错误处理"""
    # 记录状态查询请求
    app.logger.info(f"API请求: 查询分析任务状态 {task_id}")
    app.logger.info(f"当前统一任务管理器中的任务数: {len(unified_task_manager.tasks)}")

    try:
        task = unified_task_manager.get_task(task_id)

        if not task:
            app.logger.warning(f"API响应: 分析任务 {task_id} 不存在，返回404")
            app.logger.warning(f"当前任务列表: {list(unified_task_manager.tasks.keys())}")
            return jsonify({
                'error': '找不到指定的分析任务',
                'task_id': task_id,
                'available_tasks': len(unified_task_manager.tasks)
            }), 404

        # 记录成功获取任务状态
        app.logger.info(f"API响应: 成功获取分析任务 {task_id} 状态: {task['status']}, 进度: {task.get('progress', 0)}%")

        # 基本状态信息
        status = {
            'id': task['id'],
            'status': task['status'],
            'progress': task.get('progress', 0),
            'created_at': task['created_at'],
            'updated_at': task['updated_at'],
            'task_type': task.get('type', 'stock_analysis')
        }

    except Exception as e:
        app.logger.error(f"查询分析任务状态时出错: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'error': '查询任务状态时发生内部错误',
            'task_id': task_id
        }), 500

    # 如果任务完成，包含结果
    if task['status'] == TASK_COMPLETED and 'result' in task:
        status['result'] = task['result']
        app.logger.info(f"API响应: 分析任务 {task_id} 已完成，包含结果数据")

    # 如果任务失败，包含错误信息
    if task['status'] == TASK_FAILED and 'error' in task:
        status['error'] = task['error']
        app.logger.warning(f"API响应: 分析任务 {task_id} 失败，错误: {task['error']}")

    return custom_jsonify(status)


@app.route('/api/cancel_analysis/<task_id>', methods=['POST'])
def cancel_analysis(task_id):
    """取消个股分析任务 - 使用统一任务管理器"""
    task = unified_task_manager.get_task(task_id)

    if not task:
        return jsonify({'error': '找不到指定的分析任务'}), 404

    if task['status'] in [TASK_COMPLETED, TASK_FAILED]:
        return jsonify({'message': '任务已完成或失败，无法取消'})

    # 更新状态为取消
    unified_task_manager.update_task(task_id, status='cancelled', error='用户取消任务')
    app.logger.info(f"分析任务 {task_id} 已被用户取消")

    return jsonify({'message': '任务已取消'})


# 向后兼容的API已移除，请使用新的异步任务API


# 添加在web_server.py主代码中
@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    if request.path.startswith('/api/'):
        # 为API请求返回JSON格式的错误
        return jsonify({
            'error': '找不到请求的API端点',
            'path': request.path,
            'method': request.method
        }), 404
    # 为网页请求返回HTML错误页
    return render_template('error.html', error_code=404, message="找不到请求的页面"), 404


@app.errorhandler(500)
def server_error(error):
    """处理500错误"""
    app.logger.error(f"服务器错误: {str(error)}")
    if request.path.startswith('/api/'):
        # 为API请求返回JSON格式的错误
        return jsonify({
            'error': '服务器内部错误',
            'message': str(error)
        }), 500
    # 为网页请求返回HTML错误页
    return render_template('error.html', error_code=500, message="服务器内部错误"), 500


# Update the get_stock_data function in web_server.py to handle date formatting properly
@app.route('/api/stock_basic_info', methods=['GET'])
@cache.cached(timeout=1800, query_string=True)  # 缓存30分钟
def get_stock_basic_info():
    """获取股票基本信息API"""
    try:
        stock_code = request.args.get('stock_code')
        market_type = request.args.get('market_type', 'A')

        if not stock_code:
            return jsonify({'error': '请提供股票代码'}), 400

        app.logger.info(f"获取股票 {stock_code} 基本信息，市场类型: {market_type}")

        # 使用数据服务获取基本信息
        basic_info = data_service.get_stock_basic_info(stock_code, market_type)

        if basic_info:
            app.logger.info(f"成功获取股票基本信息: {basic_info.get('stock_name', '未知')}")
            return jsonify(basic_info)
        else:
            app.logger.warning(f"未找到股票 {stock_code} 的基本信息")
            return jsonify({'error': '未找到股票基本信息'}), 404

    except Exception as e:
        app.logger.error(f"获取股票基本信息时出错: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock_data', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_stock_data():
    try:
        stock_code = request.args.get('stock_code')
        market_type = request.args.get('market_type', 'A')
        period = request.args.get('period', '1y')  # 默认1年

        if not stock_code:
            return custom_jsonify({'error': '请提供股票代码'}), 400

        # 根据period计算start_date
        end_date = datetime.now().strftime('%Y%m%d')
        if period == '1m':
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        elif period == '3m':
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        elif period == '6m':
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
        elif period == '1y':
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        else:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        # 获取股票历史数据
        app.logger.info(
            f"获取股票 {stock_code} 的历史数据，市场: {market_type}, 起始日期: {start_date}, 结束日期: {end_date}")
        df = analyzer.get_stock_data(stock_code, market_type, start_date, end_date)

        # 计算技术指标
        app.logger.info(f"计算股票 {stock_code} 的技术指标")
        df = analyzer.calculate_indicators(df)

        # 检查数据是否为空
        if df.empty:
            app.logger.warning(f"股票 {stock_code} 的数据为空")
            return custom_jsonify({'error': '未找到股票数据'}), 404

        # 将DataFrame转为JSON格式
        app.logger.info(f"将数据转换为JSON格式，行数: {len(df)}")

        # 确保日期列是字符串格式 - 修复缓存问题
        if 'date' in df.columns:
            try:
                if pd.api.types.is_datetime64_any_dtype(df['date']):
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                else:
                    df = df.copy()
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            except Exception as e:
                app.logger.error(f"处理日期列时出错: {str(e)}")
                df['date'] = df['date'].astype(str)

        # 将NaN值替换为None
        df = df.replace({np.nan: None, np.inf: None, -np.inf: None})

        records = df.to_dict('records')

        app.logger.info(f"数据处理完成，返回 {len(records)} 条记录")
        return custom_jsonify({'data': records})
    except Exception as e:
        app.logger.error(f"获取股票数据时出错: {str(e)}")
        app.logger.error(traceback.format_exc())
        return custom_jsonify({'error': str(e)}), 500


# @app.route('/api/market_scan', methods=['POST'])
# def api_market_scan():
#     try:
#         data = request.json
#         stock_list = data.get('stock_list', [])
#         min_score = data.get('min_score', 60)
#         market_type = data.get('market_type', 'A')

#         if not stock_list:
#             return jsonify({'error': '请提供股票列表'}), 400

#         # 限制股票数量，避免过长处理时间
#         if len(stock_list) > 100:
#             app.logger.warning(f"股票列表过长 ({len(stock_list)}只)，截取前100只")
#             stock_list = stock_list[:100]

#         # 执行市场扫描
#         app.logger.info(f"开始扫描 {len(stock_list)} 只股票，最低分数: {min_score}")

#         # 使用线程池优化处理
#         results = []
#         max_workers = min(10, len(stock_list))  # 最多10个工作线程

#         # 设置较长的超时时间
#         timeout = 300  # 5分钟

#         def scan_thread():
#             try:
#                 return analyzer.scan_market(stock_list, min_score, market_type)
#             except Exception as e:
#                 app.logger.error(f"扫描线程出错: {str(e)}")
#                 return []

#         thread = threading.Thread(target=lambda: results.append(scan_thread()))
#         thread.start()
#         thread.join(timeout)

#         if thread.is_alive():
#             app.logger.error(f"市场扫描超时，已扫描 {len(stock_list)} 只股票超过 {timeout} 秒")
#             return custom_jsonify({'error': '扫描超时，请减少股票数量或稍后再试'}), 504

#         if not results or not results[0]:
#             app.logger.warning("扫描结果为空")
#             return custom_jsonify({'results': []})

#         scan_results = results[0]
#         app.logger.info(f"扫描完成，找到 {len(scan_results)} 只符合条件的股票")

#         # 使用自定义JSON格式处理NumPy数据类型
#         return custom_jsonify({'results': scan_results})
#     except Exception as e:
#         app.logger.error(f"执行市场扫描时出错: {traceback.format_exc()}")
#         return custom_jsonify({'error': str(e)}), 500

@app.route('/api/start_market_scan', methods=['POST'])
def start_market_scan():
    """启动市场扫描任务"""
    try:
        data = request.json
        stock_list = data.get('stock_list', [])
        min_score = data.get('min_score', 60)
        market_type = data.get('market_type', 'A')

        if not stock_list:
            return jsonify({'error': '请提供股票列表'}), 400

        # 限制股票数量，避免过长处理时间
        if len(stock_list) > 100:
            app.logger.warning(f"股票列表过长 ({len(stock_list)}只)，截取前100只")
            stock_list = stock_list[:100]

        # 使用统一任务管理器创建任务
        task_id, task = unified_task_manager.create_task(
            'market_scan',
            stock_list=stock_list,
            min_score=min_score,
            market_type=market_type,
            total=len(stock_list)
        )

        # 验证任务创建成功
        verification_task = unified_task_manager.get_task(task_id)
        if not verification_task:
            app.logger.error(f"任务创建失败！无法找到刚创建的任务 {task_id}")
            return jsonify({'error': '任务创建失败'}), 500
        else:
            app.logger.info(f"任务创建成功验证: {task_id}")

        # 记录任务创建的详细信息
        app.logger.info(f"任务创建详情: ID={task_id}, 类型=market_scan, 股票数={len(stock_list)}")
        app.logger.info(f"任务初始状态: {verification_task['status']}")

        # 立即更新任务状态为RUNNING，避免时序问题
        unified_task_manager.update_task(task_id, status=TASK_RUNNING, progress=0)
        app.logger.info(f"任务 {task_id} 状态已更新为RUNNING")

        # 启动后台线程执行扫描
        def run_scan():
            scan_start_time = time.time()
            failed_stocks = []
            timeout_stocks = []

            try:
                app.logger.info(f"开始扫描任务 {task_id}，共 {len(stock_list)} 只股票")

                # 执行分批处理
                results = []
                total = len(stock_list)
                batch_size = 5  # 减小批次大小，提高响应性
                processed_count = 0

                for i in range(0, total, batch_size):
                    # 检查任务是否被取消 - 使用统一任务管理器
                    current_task = unified_task_manager.get_task(task_id)
                    if not current_task or current_task['status'] != TASK_RUNNING:
                        app.logger.info(f"扫描任务 {task_id} 被取消")
                        return

                    batch = stock_list[i:i + batch_size]
                    batch_results = []
                    batch_start_time = time.time()

                    app.logger.info(f"处理批次 {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}，股票: {batch}")

                    for stock_code in batch:
                        stock_start_time = time.time()
                        try:
                            # 检查任务状态 - 使用统一任务管理器
                            current_task = unified_task_manager.get_task(task_id)
                            if not current_task or current_task['status'] != TASK_RUNNING:
                                app.logger.info(f"扫描任务 {task_id} 被取消")
                                return

                            # 使用较短的超时时间进行快速分析
                            report = analyzer.quick_analyze_stock(stock_code, market_type, timeout=15)
                            stock_time = time.time() - stock_start_time

                            if report['score'] >= min_score:
                                batch_results.append(report)
                                app.logger.info(f"股票 {stock_code} 符合条件，得分: {report['score']:.1f}，耗时: {stock_time:.2f}秒")
                            else:
                                app.logger.debug(f"股票 {stock_code} 不符合条件，得分: {report['score']:.1f}")

                        except Exception as e:
                            stock_time = time.time() - stock_start_time
                            error_msg = str(e)

                            if "超时" in error_msg or "timeout" in error_msg.lower():
                                timeout_stocks.append(stock_code)
                                app.logger.warning(f"股票 {stock_code} 分析超时: {stock_time:.2f}秒")
                            else:
                                failed_stocks.append(stock_code)
                                app.logger.error(f"分析股票 {stock_code} 时出错: {error_msg}")
                            continue

                        processed_count += 1

                    results.extend(batch_results)
                    batch_time = time.time() - batch_start_time

                    # 更新进度
                    progress = min(100, int((i + len(batch)) / total * 100))

                    # 计算预估剩余时间
                    elapsed_time = time.time() - scan_start_time
                    if processed_count > 0:
                        avg_time_per_stock = elapsed_time / processed_count
                        remaining_stocks = total - processed_count
                        estimated_remaining_time = avg_time_per_stock * remaining_stocks
                    else:
                        estimated_remaining_time = 0

                    # 更新任务状态，包含详细信息 - 使用统一任务管理器
                    unified_task_manager.update_task(
                        task_id,
                        status=TASK_RUNNING,
                        progress=progress,
                        processed=processed_count,
                        found=len(results),
                        failed=len(failed_stocks),
                        timeout=len(timeout_stocks),
                        estimated_remaining=int(estimated_remaining_time)
                    )

                    app.logger.info(f"批次完成，耗时: {batch_time:.2f}秒，当前找到 {len(results)} 只符合条件的股票")

                # 按得分排序
                results.sort(key=lambda x: x['score'], reverse=True)

                # 记录扫描统计信息
                total_time = time.time() - scan_start_time
                stats = {
                    'total_stocks': total,
                    'processed': processed_count,
                    'found': len(results),
                    'failed': len(failed_stocks),
                    'timeout': len(timeout_stocks),
                    'total_time': total_time,
                    'avg_time_per_stock': total_time / max(processed_count, 1)
                }

                # 更新任务状态为完成
                start_market_scan_task_status(task_id, TASK_COMPLETED, progress=100, result=results)

                app.logger.info(f"扫描任务 {task_id} 完成！统计信息: {stats}")
                if failed_stocks:
                    app.logger.warning(f"失败的股票: {failed_stocks}")
                if timeout_stocks:
                    app.logger.warning(f"超时的股票: {timeout_stocks}")

            except Exception as e:
                app.logger.error(f"扫描任务 {task_id} 失败: {str(e)}")
                app.logger.error(traceback.format_exc())
                start_market_scan_task_status(task_id, TASK_FAILED, error=str(e))

        # 启动后台线程
        thread = threading.Thread(target=run_scan)
        thread.daemon = True
        thread.start()

        # 获取更新后的任务状态
        updated_task = unified_task_manager.get_task(task_id)
        current_status = updated_task['status'] if updated_task else 'running'

        return jsonify({
            'task_id': task_id,
            'status': current_status,
            'message': f'已启动扫描任务，正在处理 {len(stock_list)} 只股票'
        })

    except Exception as e:
        app.logger.error(f"启动市场扫描任务时出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/scan_status/<task_id>', methods=['GET'])
def get_scan_status(task_id):
    """获取扫描任务状态 - 使用统一任务管理器"""
    # 增强调试日志
    app.logger.info(f"收到任务状态查询请求: {task_id}")
    app.logger.info(f"当前统一任务管理器中的任务数: {len(unified_task_manager.tasks)}")
    app.logger.info(f"当前任务ID列表: {list(unified_task_manager.tasks.keys())}")

    task = unified_task_manager.get_task(task_id)

    if not task:
        app.logger.error(f"任务 {task_id} 不存在！")
        app.logger.error(f"当前所有任务: {list(unified_task_manager.tasks.keys())}")
        return jsonify({'error': '找不到指定的扫描任务'}), 404

    # 详细的状态日志记录
    app.logger.info(f"成功查询任务 {task_id} 状态: {task['status']}, 进度: {task.get('progress', 0)}%")

    # 检查任务是否长时间无更新
    try:
        updated_at = datetime.strptime(task['updated_at'], '%Y-%m-%d %H:%M:%S')
        time_since_update = (datetime.now() - updated_at).total_seconds()
        if time_since_update > 300:  # 5分钟无更新
            app.logger.warning(f"任务 {task_id} 已 {time_since_update/60:.1f} 分钟无更新")
    except:
        pass

    # 基本状态信息
    status = {
        'id': task['id'],
        'status': task['status'],
        'progress': task.get('progress', 0),
        'total': task.get('total', 0),
        'processed': task.get('processed', 0),
        'found': task.get('found', 0),
        'failed': task.get('failed', 0),
        'timeout': task.get('timeout', 0),
        'estimated_remaining': task.get('estimated_remaining', 0),
        'created_at': task['created_at'],
        'updated_at': task['updated_at'],
        'progress_updated_at': task.get('progress_updated_at', task['updated_at'])
    }

    # 如果任务完成，包含结果
    if task['status'] == TASK_COMPLETED and 'result' in task:
        status['result'] = task['result']
        app.logger.info(f"任务 {task_id} 已完成，返回 {len(task['result'])} 个结果")

    # 如果任务失败，包含错误信息
    if task['status'] == TASK_FAILED and 'error' in task:
        status['error'] = task['error']
        app.logger.info(f"任务 {task_id} 失败: {task['error']}")

    return custom_jsonify(status)


@app.route('/api/cancel_scan/<task_id>', methods=['POST'])
def cancel_scan_task(task_id):
    """取消扫描任务 - 使用统一任务管理器"""
    try:
        task = unified_task_manager.get_task(task_id)
        if not task:
            return jsonify({'error': '找不到指定的扫描任务'}), 404

        # 只能取消正在运行或等待中的任务
        if task['status'] in [TASK_PENDING, TASK_RUNNING]:
            unified_task_manager.update_task(task_id, status='cancelled')
            app.logger.info(f"扫描任务 {task_id} 已被用户取消")
            return jsonify({'message': '任务已取消'})
        else:
            return jsonify({'error': f'任务状态为 {task["status"]}，无法取消'}), 400

    except Exception as e:
        app.logger.error(f"取消扫描任务时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/index_stocks', methods=['GET'])
def get_index_stocks():
    """获取指数成分股"""
    try:
        import akshare as ak
        index_code = request.args.get('index_code', '000300')  # 默认沪深300

        # 获取指数成分股
        app.logger.info(f"获取指数 {index_code} 成分股")
        if index_code == '000300':
            # 沪深300成分股
            stocks = ak.index_stock_cons_weight_csindex(symbol="000300")
        elif index_code == '000905':
            # 中证500成分股
            stocks = ak.index_stock_cons_weight_csindex(symbol="000905")
        elif index_code == '000852':
            # 中证1000成分股
            stocks = ak.index_stock_cons_weight_csindex(symbol="000852")
        elif index_code == '000001':
            # 上证指数
            stocks = ak.index_stock_cons_weight_csindex(symbol="000001")
        else:
            return jsonify({'error': '不支持的指数代码'}), 400

        # 提取股票代码列表
        stock_list = stocks['成分券代码'].tolist() if '成分券代码' in stocks.columns else []
        app.logger.info(f"找到 {len(stock_list)} 只成分股")

        return jsonify({'stock_list': stock_list})
    except Exception as e:
        app.logger.error(f"获取指数成分股时出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/industry_stocks', methods=['GET'])
def get_industry_stocks():
    """获取行业成分股"""
    try:
        import akshare as ak
        industry = request.args.get('industry', '')

        if not industry:
            return jsonify({'error': '请提供行业名称'}), 400

        # 获取行业成分股
        app.logger.info(f"获取 {industry} 行业成分股")
        stocks = ak.stock_board_industry_cons_em(symbol=industry)

        # 提取股票代码列表
        stock_list = stocks['代码'].tolist() if '代码' in stocks.columns else []
        app.logger.info(f"找到 {len(stock_list)} 只 {industry} 行业股票")

        return jsonify({'stock_list': stock_list})
    except Exception as e:
        app.logger.error(f"获取行业成分股时出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 使用统一任务管理器的清理函数
def clean_old_tasks():
    """清理旧的扫描任务 - 使用统一任务管理器"""
    return unified_task_manager.cleanup_old_tasks()


# 修改 run_task_cleaner 函数，降低清理频率并增加保护机制
def run_task_cleaner():
    """定期运行任务清理，并在每天 16:30 左右清理所有缓存"""
    while True:
        try:
            now = datetime.now()
            # 判断是否在收盘时间附近（16:25-16:35）
            is_market_close_time = (now.hour == 16 and 25 <= now.minute <= 35)

            # 只在特定时间进行清理，避免干扰正在运行的任务
            should_clean = False

            if is_market_close_time:
                # 收盘时间，进行全面清理
                should_clean = True
            elif now.hour in [2, 6, 10, 14, 18, 22]:  # 每4小时清理一次，避开交易时间
                should_clean = True

            if should_clean:
                cleaned = clean_old_tasks()

                # 如果是收盘时间，清理所有缓存
                if is_market_close_time:
                    # 清理分析器的数据缓存
                    analyzer.data_cache.clear()

                    # 清理 Flask 缓存
                    cache.clear()

                    # 清理统一任务管理器中的已完成任务
                    unified_task_manager.cleanup_completed_tasks()

                    app.logger.info("市场收盘时间检测到，已清理所有缓存数据")

                if cleaned > 0:
                    app.logger.info(f"清理了 {cleaned} 个旧的扫描任务")
            else:
                app.logger.debug("跳过任务清理，避免干扰正在运行的任务")

        except Exception as e:
            app.logger.error(f"任务清理出错: {str(e)}")

        # 每 2 小时检查一次，但只在特定时间点实际清理
        time.sleep(7200)


# 基本面分析路由
@app.route('/api/fundamental_analysis', methods=['POST'])
def api_fundamental_analysis():
    try:
        data = request.json
        stock_code = data.get('stock_code')

        if not stock_code:
            return jsonify({'error': '请提供股票代码'}), 400

        # 获取基本面分析结果
        result = fundamental_analyzer.calculate_fundamental_score(stock_code)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"基本面分析出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 资金流向分析路由
# Add to web_server.py

# 获取概念资金流向的API端点
@app.route('/api/concept_fund_flow', methods=['GET'])
def api_concept_fund_flow():
    try:
        period = request.args.get('period', '10日排行')  # Default to 10-day ranking

        # Get concept fund flow data
        result = capital_flow_analyzer.get_concept_fund_flow(period)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting concept fund flow: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 获取个股资金流向排名的API端点
@app.route('/api/individual_fund_flow_rank', methods=['GET'])
def api_individual_fund_flow_rank():
    try:
        period = request.args.get('period', '10日')  # Default to today

        # Get individual fund flow ranking data
        result = capital_flow_analyzer.get_individual_fund_flow_rank(period)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting individual fund flow ranking: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 获取个股资金流向的API端点
@app.route('/api/individual_fund_flow', methods=['GET'])
def api_individual_fund_flow():
    try:
        stock_code = request.args.get('stock_code')
        market_type = request.args.get('market_type', '')  # Auto-detect if not provided
        re_date = request.args.get('period-select')

        if not stock_code:
            return jsonify({'error': 'Stock code is required'}), 400

        # Get individual fund flow data
        result = capital_flow_analyzer.get_individual_fund_flow(stock_code, market_type, re_date)
        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting individual fund flow: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 获取板块内股票的API端点
@app.route('/api/sector_stocks', methods=['GET'])
def api_sector_stocks():
    try:
        sector = request.args.get('sector')

        if not sector:
            return jsonify({'error': 'Sector name is required'}), 400

        # Get sector stocks data
        result = capital_flow_analyzer.get_sector_stocks(sector)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"Error getting sector stocks: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# Update the existing capital flow API endpoint
@app.route('/api/capital_flow', methods=['POST'])
def api_capital_flow():
    try:
        data = request.json
        stock_code = data.get('stock_code')
        market_type = data.get('market_type', '')  # Auto-detect if not provided

        if not stock_code:
            return jsonify({'error': 'Stock code is required'}), 400

        # Calculate capital flow score
        result = capital_flow_analyzer.calculate_capital_flow_score(stock_code, market_type)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"Error calculating capital flow score: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 情景预测路由
@app.route('/api/scenario_predict', methods=['POST'])
def api_scenario_predict():
    try:
        data = request.json
        stock_code = data.get('stock_code')
        market_type = data.get('market_type', 'A')
        days = data.get('days', 60)

        if not stock_code:
            return jsonify({'error': '请提供股票代码'}), 400

        # 获取情景预测结果
        result = scenario_predictor.generate_scenarios(stock_code, market_type, days)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"情景预测出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 智能问答路由
@app.route('/api/qa', methods=['POST'])
def api_qa():
    try:
        data = request.json
        stock_code = data.get('stock_code')
        question = data.get('question')
        market_type = data.get('market_type', 'A')

        if not stock_code or not question:
            return jsonify({'error': '请提供股票代码和问题'}), 400

        # 获取智能问答结果
        result = stock_qa.answer_question(stock_code, question, market_type)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"智能问答出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 统一评分API端点
@app.route('/api/stock_score', methods=['POST'])
def api_stock_score():
    """统一的股票评分API，确保所有页面使用相同的评分算法"""
    try:
        data = request.json
        stock_code = data.get('stock_code')
        market_type = data.get('market_type', 'A')

        if not stock_code:
            return jsonify({'error': '请提供股票代码'}), 400

        app.logger.info(f"获取股票 {stock_code} 的统一评分，市场类型: {market_type}")

        # 使用线程本地缓存的分析器实例
        current_analyzer = get_analyzer()

        # 获取股票数据和计算指标
        df = current_analyzer.get_stock_data(stock_code, market_type)
        df = current_analyzer.calculate_indicators(df)

        # 计算评分（使用与投资组合页面相同的算法）
        score = current_analyzer.calculate_score(df, market_type)
        score_details = getattr(current_analyzer, 'score_details', {'total': score})

        # 获取最新数据用于显示
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # 获取基本信息
        try:
            stock_info = current_analyzer.get_stock_info(stock_code)
            stock_name = stock_info.get('股票名称', '未知')
            industry = stock_info.get('行业', '未知')
        except:
            stock_name = '未知'
            industry = '未知'

        # 构建返回数据
        result = {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'industry': industry,
            'score': score,
            'score_details': score_details,
            'price': float(latest['close']),
            'price_change': float((latest['close'] - prev['close']) / prev['close'] * 100),
            'recommendation': current_analyzer.get_recommendation(score),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        app.logger.info(f"股票 {stock_code} 评分计算完成: {score}")
        return custom_jsonify(result)

    except Exception as e:
        app.logger.error(f"获取股票评分出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 风险分析路由
@app.route('/api/risk_analysis', methods=['POST'])
def api_risk_analysis():
    try:
        data = request.json
        stock_code = data.get('stock_code')
        market_type = data.get('market_type', 'A')

        if not stock_code:
            return jsonify({'error': '请提供股票代码'}), 400

        # 获取风险分析结果
        result = risk_monitor.analyze_stock_risk(stock_code, market_type)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"风险分析出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 投资组合CSV批量导入路由
@app.route('/api/portfolio/import_csv', methods=['POST'])
def api_portfolio_import_csv():
    """处理CSV文件批量导入股票到投资组合"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({'error': '请选择CSV文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '请选择CSV文件'}), 400

        # 检查文件类型
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': '请上传CSV格式文件'}), 400

        # 读取CSV文件内容
        try:
            # 使用pandas读取CSV，更好地处理编码问题
            content = file.read()

            # 尝试不同的编码方式
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            df = None

            for encoding in encodings:
                try:
                    content_str = content.decode(encoding)
                    df = pd.read_csv(io.StringIO(content_str))
                    break
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue

            if df is None:
                return jsonify({'error': 'CSV文件编码不支持，请使用UTF-8或GBK编码'}), 400

        except Exception as e:
            return jsonify({'error': f'CSV文件读取失败: {str(e)}'}), 400

        # 检查是否有secID列
        if 'secID' not in df.columns:
            return jsonify({'error': 'CSV文件必须包含secID列'}), 400

        # 提取有效的股票代码
        stock_codes = df[df['secID'].notna() & (df['secID'] != '')]['secID'].tolist()

        if not stock_codes:
            return jsonify({'error': 'CSV文件中未找到有效的股票代码'}), 400

        # 转换股票代码格式
        converted_stocks = []
        failed_stocks = []

        for original_code in stock_codes:
            try:
                converted_code = convert_stock_code_for_portfolio(str(original_code).strip())
                if converted_code:
                    converted_stocks.append({
                        'original_code': original_code,
                        'converted_code': converted_code
                    })
                else:
                    failed_stocks.append({
                        'code': original_code,
                        'reason': '代码格式无法识别'
                    })
            except Exception as e:
                failed_stocks.append({
                    'code': original_code,
                    'reason': f'转换失败: {str(e)}'
                })

        return custom_jsonify({
            'success': True,
            'total_count': len(stock_codes),
            'converted_count': len(converted_stocks),
            'failed_count': len(failed_stocks),
            'converted_stocks': converted_stocks,
            'failed_stocks': failed_stocks
        })

    except Exception as e:
        app.logger.error(f"CSV批量导入出错: {traceback.format_exc()}")
        return jsonify({'error': f'处理失败: {str(e)}'}), 500


def convert_stock_code_for_portfolio(code):
    """
    转换股票代码格式，参考robust_batch_analyzer.py的逻辑
    输入: 603316.XSHG, 601218.XSHG 等格式
    输出: 603316, 601218 等简化格式（适合投资组合页面）
    """
    try:
        code = str(code).strip().upper()

        # 如果已经是简单格式（6位数字），直接返回
        if code.isdigit() and len(code) == 6:
            return code

        # 处理带交易所后缀的格式
        if '.' in code:
            stock_part = code.split('.')[0]
            if stock_part.isdigit() and len(stock_part) == 6:
                return stock_part

        # 处理其他可能的格式
        # 提取6位数字
        import re
        match = re.search(r'\d{6}', code)
        if match:
            return match.group()

        return None

    except Exception as e:
        app.logger.error(f"股票代码转换失败 {code}: {e}")
        return None


# 投资组合风险分析路由
@app.route('/api/portfolio_risk', methods=['POST'])
def api_portfolio_risk():
    try:
        data = request.json
        portfolio = data.get('portfolio', [])

        if not portfolio:
            return jsonify({'error': '请提供投资组合'}), 400

        # 获取投资组合风险分析结果
        result = risk_monitor.analyze_portfolio_risk(portfolio)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"投资组合风险分析出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 指数分析路由
@app.route('/api/index_analysis', methods=['GET'])
def api_index_analysis():
    try:
        index_code = request.args.get('index_code')
        limit = int(request.args.get('limit', 30))

        if not index_code:
            return jsonify({'error': '请提供指数代码'}), 400

        # 获取指数分析结果
        result = index_industry_analyzer.analyze_index(index_code, limit)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"指数分析出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 行业分析路由
@app.route('/api/industry_analysis', methods=['GET'])
def api_industry_analysis():
    try:
        industry = request.args.get('industry')
        limit = int(request.args.get('limit', 30))

        if not industry:
            return jsonify({'error': '请提供行业名称'}), 400

        # 获取行业分析结果
        result = index_industry_analyzer.analyze_industry(industry, limit)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"行业分析出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/industry_fund_flow', methods=['GET'])
def api_industry_fund_flow():
    """获取行业资金流向数据"""
    try:
        symbol = request.args.get('symbol', '即时')

        result = industry_analyzer.get_industry_fund_flow(symbol)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"获取行业资金流向数据出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/industry_detail', methods=['GET'])
def api_industry_detail():
    """获取行业详细信息"""
    try:
        industry = request.args.get('industry')

        if not industry:
            return jsonify({'error': '请提供行业名称'}), 400

        result = industry_analyzer.get_industry_detail(industry)

        app.logger.info(f"返回前 (result)：{result}")
        if not result:
            return jsonify({'error': f'未找到行业 {industry} 的详细信息'}), 404

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"获取行业详细信息出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 行业比较路由
@app.route('/api/industry_compare', methods=['GET'])
def api_industry_compare():
    try:
        limit = int(request.args.get('limit', 10))

        # 获取行业比较结果
        result = index_industry_analyzer.compare_industries(limit)

        return custom_jsonify(result)
    except Exception as e:
        app.logger.error(f"行业比较出错: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# 保存股票分析结果到数据库
def save_analysis_result(stock_code, market_type, result):
    """保存分析结果到数据库"""
    if not (DATABASE_AVAILABLE and USE_DATABASE):
        return

    try:
        session = get_session()

        # 创建新的分析结果记录
        from database import AnalysisResult
        analysis = AnalysisResult(
            stock_code=stock_code,
            market_type=market_type,
            score=result.get('scores', {}).get('total', 0),
            recommendation=result.get('recommendation', {}).get('action', ''),
            technical_data=result.get('technical_analysis', {}),
            fundamental_data=result.get('fundamental_data', {}),
            capital_flow_data=result.get('capital_flow_data', {}),
            ai_analysis=result.get('ai_analysis', '')
        )

        session.add(analysis)
        session.commit()

    except Exception as e:
        app.logger.error(f"保存分析结果到数据库时出错: {str(e)}")
        if session:
            session.rollback()
    finally:
        if session:
            session.close()


# 从数据库获取历史分析结果
@app.route('/api/history_analysis', methods=['GET'])
def get_history_analysis():
    """获取股票的历史分析结果"""
    if not (DATABASE_AVAILABLE and USE_DATABASE):
        return jsonify({'error': '数据库功能未启用'}), 400

    stock_code = request.args.get('stock_code')
    limit = int(request.args.get('limit', 10))

    if not stock_code:
        return jsonify({'error': '请提供股票代码'}), 400

    try:
        session = get_session()

        # 查询历史分析结果
        from database import AnalysisResult
        results = session.query(AnalysisResult) \
            .filter(AnalysisResult.stock_code == stock_code) \
            .order_by(AnalysisResult.analysis_date.desc()) \
            .limit(limit) \
            .all()

        # 转换为字典列表
        history = [result.to_dict() for result in results]

        return jsonify({'history': history})

    except Exception as e:
        app.logger.error(f"获取历史分析结果时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

# 添加新闻API端点
# 添加到web_server.py文件中
@app.route('/api/latest_news', methods=['GET'])
def get_latest_news():
    try:
        days = int(request.args.get('days', 1))  # 默认获取1天的新闻
        limit = int(request.args.get('limit', 1000))  # 默认最多获取1000条
        only_important = request.args.get('important', '0') == '1'  # 是否只看重要新闻
        news_type = request.args.get('type', 'all')  # 新闻类型，可选值: all, hotspot

        # 从news_fetcher模块获取新闻数据
        news_data = news_fetcher.get_latest_news(days=days, limit=limit)

        # 过滤新闻
        if only_important:
            # 根据关键词过滤重要新闻
            important_keywords = ['重要', '利好', '重磅', '突发', '关注']
            news_data = [news for news in news_data if
                         any(keyword in (news.get('content', '') or '') for keyword in important_keywords)]

        if news_type == 'hotspot':
            # 过滤舆情热点相关新闻
            hotspot_keywords = [
                # 舆情直接相关词
                '舆情', '舆论', '热点', '热议', '热搜', '话题',

                # 关注度相关词
                '关注度', '高度关注', '引发关注', '市场关注', '持续关注', '重点关注',
                '密切关注', '广泛关注', '集中关注', '投资者关注',

                # 传播相关词
                '爆文', '刷屏', '刷爆', '冲上热搜', '纷纷转发', '广泛传播',
                '热传', '病毒式传播', '迅速扩散', '高度转发',

                # 社交媒体相关词
                '微博热搜', '微博话题', '知乎热议', '抖音热门', '今日头条', '朋友圈热议',
                '微信热文', '社交媒体热议', 'APP热榜',

                # 情绪相关词
                '情绪高涨', '市场情绪', '投资情绪', '恐慌情绪', '亢奋情绪',
                '乐观情绪', '悲观情绪', '投资者情绪', '公众情绪',

                # 突发事件相关
                '突发', '紧急', '爆发', '突现', '紧急事态', '快讯', '突发事件',
                '重大事件', '意外事件', '突发新闻',

                # 行业动态相关
                '行业动向', '市场动向', '板块轮动', '资金流向', '产业趋势',
                '政策导向', '监管动态', '风口', '市场风向',

                # 舆情分析相关
                '舆情分析', '舆情监测', '舆情报告', '舆情数据', '舆情研判',
                '舆情趋势', '舆情预警', '舆情通报', '舆情简报',

                # 市场焦点相关
                '市场焦点', '焦点话题', '焦点股', '焦点事件', '投资焦点',
                '关键词', '今日看点', '重点关切', '核心议题',

                # 传统媒体相关
                '头版头条', '财经头条', '要闻', '重磅新闻', '独家报道',
                '深度报道', '特别关注', '重点报道', '专题报道',

                # 特殊提示词
                '投资舆情', '今日舆情', '今日热点', '投资热点', '市场热点',
                '每日热点', '关注要点', '交易热点', '今日重点',

                # AI基础技术
                '人工智能', 'AI', '机器学习', '深度学习', '神经网络', '大模型',
                'LLM', '大语言模型', '生成式AI', '生成式人工智能', '算法',

                # AI细分技术
                '自然语言处理', 'NLP', '计算机视觉', 'CV', '语音识别',
                '图像生成', '多模态', '强化学习', '联邦学习', '知识图谱',
                '边缘计算', '量子计算', '类脑计算', '神经形态计算',

                # 热门AI模型/产品
                'GPT', 'GPT-4', 'GPT-5', 'GPT-4o', 'ChatGPT', 'Claude',
                'Gemini', 'Llama', 'Llama3', 'Stable Diffusion', 'DALL-E',
                'Midjourney', 'Sora', 'Anthropic', 'Runway', 'Copilot',
                'Bard', 'GLM', 'Ernie', '文心一言', '通义千问', '讯飞星火','DeepSeek',

                # AI应用领域
                'AIGC', '智能驾驶', '自动驾驶', '智能助手', '智能医疗',
                '智能制造', '智能客服', '智能金融', '智能教育',
                '智能家居', '机器人', 'RPA', '数字人', '虚拟人',
                '智能安防', '计算机辅助',

                # AI硬件
                'AI芯片', 'GPU', 'TPU', 'NPU', 'FPGA', '算力', '推理芯片',
                '训练芯片', 'NVIDIA', '英伟达', 'AMD', '高性能计算',

                # AI企业
                'OpenAI', '微软AI', '谷歌AI', 'Google DeepMind', 'Meta AI',
                '百度智能云', '阿里云AI', '腾讯AI', '华为AI', '商汤科技',
                '旷视科技', '智源人工智能', '云从科技', '科大讯飞',

                # AI监管/伦理
                'AI监管', 'AI伦理', 'AI安全', 'AI风险', 'AI治理',
                'AI对齐', 'AI偏见', 'AI隐私', 'AGI', '通用人工智能',
                '超级智能', 'AI法规', 'AI责任', 'AI透明度',

                # AI市场趋势
                'AI创业', 'AI投资', 'AI融资', 'AI估值', 'AI泡沫',
                'AI风口', 'AI赛道', 'AI产业链', 'AI应用落地', 'AI转型',
                'AI红利', 'AI市值', 'AI概念股',

                # 新兴AI概念
                'AI Agent', 'AI智能体', '多智能体', '自主AI',
                'AI搜索引擎', 'RAG', '检索增强生成', '思维链', 'CoT',
                '大模型微调', '提示工程', 'Prompt Engineering',
                '基础模型', 'Foundation Model', '小模型', '专用模型',

                # 人工智能舆情专用
                'AI热点', 'AI风潮', 'AI革命', 'AI热议', 'AI突破',
                'AI进展', 'AI挑战', 'AI竞赛', 'AI战略', 'AI政策',
                'AI风险', 'AI恐慌', 'AI威胁', 'AI机遇'
            ]

            # 在API处理中使用
            if news_type == 'hotspot':
                # 过滤舆情热点相关新闻
                def has_keyword(item):
                    title = item.get('title', '')
                    content = item.get('content', '')
                    return any(keyword in title for keyword in hotspot_keywords) or \
                        any(keyword in content for keyword in hotspot_keywords)

                news_data = [news for news in news_data if has_keyword(news)]

        return jsonify({'success': True, 'news': news_data})
    except Exception as e:
        app.logger.error(f"获取最新新闻数据时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ======================== 预缓存管理API ========================

@app.route('/api/precache/status', methods=['GET'])
def get_precache_status():
    """获取预缓存状态"""
    try:
        stats = precache_scheduler.get_stats()
        return jsonify({
            'success': True,
            'stats': stats,
            'is_running': precache_scheduler.is_running
        })
    except Exception as e:
        app.logger.error(f"获取预缓存状态失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/precache/manual', methods=['POST'])
def manual_precache():
    """手动执行预缓存任务"""
    try:
        data = request.json or {}
        index_code = data.get('index_code', '000300')
        max_stocks = data.get('max_stocks', 50)

        # 在后台线程中执行预缓存
        def run_precache():
            precache_scheduler.manual_precache(index_code, max_stocks)

        thread = threading.Thread(target=run_precache)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': f'预缓存任务已启动，将处理 {max_stocks} 只股票'
        })

    except Exception as e:
        app.logger.error(f"手动预缓存失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 在应用启动时启动清理线程（保持原有代码不变）
cleaner_thread = threading.Thread(target=run_task_cleaner)
cleaner_thread.daemon = True
cleaner_thread.start()

# 初始化预缓存调度器
try:
    if init_precache_scheduler():
        app.logger.info("✓ 股票数据预缓存调度器初始化成功")
    else:
        app.logger.warning("✗ 股票数据预缓存调度器初始化失败")
except Exception as e:
    app.logger.error(f"✗ 预缓存调度器初始化异常: {str(e)}")

# 初始化实时通信功能
if REALTIME_AVAILABLE:
    try:
        realtime_integration = init_realtime_communication(app, unified_task_manager)
        app.logger.info("✓ 实时通信功能初始化成功")

        # 获取SocketIO实例用于运行
        socketio = realtime_integration.get_socketio()

    except Exception as e:
        app.logger.error(f"✗ 实时通信功能初始化失败: {str(e)}")
        socketio = None
else:
    socketio = None

# 集成API功能
if API_INTEGRATION_AVAILABLE:
    try:
        if integrate_api_with_existing_app(app):
            app.logger.info("✅ API功能集成成功")
            print("✅ API功能集成成功")
        else:
            app.logger.error("❌ API功能集成失败")
            print("❌ API功能集成失败")
    except Exception as e:
        app.logger.error(f"API功能集成出错: {e}")
        print(f"❌ API功能集成出错: {e}")
else:
    print("⚠️  API集成模块不可用，跳过API功能集成")

if __name__ == '__main__':
    # 将 host 设置为 '0.0.0.0' 使其支持所有网络接口访问
    if socketio:
        # 使用SocketIO运行应用（支持WebSocket）
        app.logger.info("使用SocketIO运行应用（支持WebSocket和SSE）")
        socketio.run(app, host='0.0.0.0', port=8888, debug=False)
    else:
        # 使用标准Flask运行应用（仅支持轮询）
        app.logger.info("使用标准Flask运行应用（仅支持轮询）")
        app.run(host='0.0.0.0', port=8888, debug=False)