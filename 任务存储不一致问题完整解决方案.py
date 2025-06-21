#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务存储不一致问题完整解决方案

这个脚本提供了一个统一的任务管理系统，
彻底解决多套存储机制导致的不一致问题。
"""

import threading
import uuid
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedTaskManager:
    """统一任务管理器 - 解决多套存储系统的问题"""
    
    def __init__(self):
        self.tasks = {}  # 统一的任务存储
        self.lock = threading.RLock()  # 使用可重入锁
        
        # 任务状态常量
        self.PENDING = 'pending'
        self.RUNNING = 'running'
        self.COMPLETED = 'completed'
        self.FAILED = 'failed'
        self.CANCELLED = 'cancelled'
        
    def create_task(self, task_type, **params):
        """创建新任务"""
        task_id = str(uuid.uuid4())
        
        with self.lock:
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
            
            self.tasks[task_id] = task
            logger.info(f"创建任务: {task_id}, 类型: {task_type}")
            
        return task_id, task
    
    def get_task(self, task_id):
        """获取任务"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                logger.debug(f"获取任务: {task_id}, 状态: {task['status']}")
            else:
                logger.warning(f"任务不存在: {task_id}, 当前任务数: {len(self.tasks)}")
            return task
    
    def update_task(self, task_id, status=None, progress=None, result=None, error=None, **kwargs):
        """更新任务状态"""
        with self.lock:
            if task_id not in self.tasks:
                logger.error(f"尝试更新不存在的任务: {task_id}")
                return False
            
            task = self.tasks[task_id]
            old_status = task.get('status', '')
            old_progress = task.get('progress', 0)
            
            # 更新基本字段
            if status is not None:
                task['status'] = status
            if progress is not None:
                task['progress'] = progress
                # 如果进度有变化，更新进度时间戳
                if progress != old_progress:
                    task['progress_updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if result is not None:
                task['result'] = result
            if error is not None:
                task['error'] = error
            
            # 更新其他字段
            for key, value in kwargs.items():
                task[key] = value
            
            task['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 详细日志记录
            if status != old_status or progress != old_progress:
                logger.info(f"任务 {task_id} 状态更新: {old_status} -> {status}, 进度: {old_progress}% -> {progress}%")
            
            return True
    
    def delete_task(self, task_id):
        """删除任务"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.info(f"删除任务: {task_id}")
                return True
            return False
    
    def list_tasks(self, task_type=None, status=None):
        """列出任务"""
        with self.lock:
            tasks = []
            for task_id, task in self.tasks.items():
                if task_type and task.get('type') != task_type:
                    continue
                if status and task.get('status') != status:
                    continue
                tasks.append((task_id, task))
            return tasks
    
    def cleanup_old_tasks(self):
        """清理旧任务 - 保守策略"""
        with self.lock:
            now = datetime.now()
            to_delete = []
            
            for task_id, task in self.tasks.items():
                try:
                    updated_at = datetime.strptime(task['updated_at'], '%Y-%m-%d %H:%M:%S')
                    time_diff = (now - updated_at).total_seconds()
                    
                    should_delete = False
                    
                    if task['status'] in [self.COMPLETED, self.FAILED, self.CANCELLED]:
                        # 完成的任务，6小时后清理
                        should_delete = time_diff > 21600
                    elif task['status'] == self.RUNNING:
                        # 运行中的任务，只有在超过12小时且无进度更新时才清理
                        if time_diff > 43200:  # 12小时
                            progress_updated_at = datetime.strptime(
                                task.get('progress_updated_at', task['updated_at']), 
                                '%Y-%m-%d %H:%M:%S'
                            )
                            progress_time_diff = (now - progress_updated_at).total_seconds()
                            if progress_time_diff > 7200:  # 2小时内无进度更新
                                should_delete = True
                                logger.warning(f"任务 {task_id} 运行超过12小时且2小时内无进度更新，判定为卡死")
                    elif task['status'] == self.PENDING:
                        # 等待中的任务，4小时后清理
                        should_delete = time_diff > 14400
                    
                    if should_delete:
                        to_delete.append(task_id)
                        logger.info(f"准备清理任务 {task_id}，状态: {task['status']}, 已存在: {time_diff/60:.1f}分钟")
                        
                except Exception as e:
                    logger.error(f"清理任务 {task_id} 时出错: {str(e)}")
            
            # 删除旧任务
            for task_id in to_delete:
                del self.tasks[task_id]
            
            return len(to_delete)


# 创建全局任务管理器实例
task_manager = UnifiedTaskManager()


def apply_unified_task_management_fix():
    """应用统一任务管理修复"""
    
    fix_code = '''
# 统一任务管理系统修复代码
# 将此代码添加到 web_server.py 的开头

import threading
import uuid
from datetime import datetime

class UnifiedTaskManager:
    """统一任务管理器"""
    
    def __init__(self):
        self.tasks = {}
        self.lock = threading.RLock()
        
        # 任务状态常量
        self.PENDING = 'pending'
        self.RUNNING = 'running'
        self.COMPLETED = 'completed'
        self.FAILED = 'failed'
        self.CANCELLED = 'cancelled'
    
    def create_task(self, task_type, **params):
        """创建新任务"""
        task_id = str(uuid.uuid4())
        
        with self.lock:
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
            
            if task_type == 'market_scan':
                task.update({
                    'total': params.get('total', 0),
                    'processed': 0,
                    'found': 0,
                    'failed': 0,
                    'timeout': 0,
                    'estimated_remaining': 0
                })
            
            self.tasks[task_id] = task
            app.logger.info(f"统一任务管理器: 创建任务 {task_id}")
            
        return task_id, task
    
    def get_task(self, task_id):
        """获取任务"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                app.logger.warning(f"统一任务管理器: 任务 {task_id} 不存在，当前任务数: {len(self.tasks)}")
            return task
    
    def update_task(self, task_id, status=None, progress=None, result=None, error=None, **kwargs):
        """更新任务状态"""
        with self.lock:
            if task_id not in self.tasks:
                app.logger.error(f"统一任务管理器: 尝试更新不存在的任务 {task_id}")
                return False
            
            task = self.tasks[task_id]
            old_progress = task.get('progress', 0)
            
            if status is not None:
                task['status'] = status
            if progress is not None:
                task['progress'] = progress
                if progress != old_progress:
                    task['progress_updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if result is not None:
                task['result'] = result
            if error is not None:
                task['error'] = error
            
            for key, value in kwargs.items():
                task[key] = value
            
            task['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return True

# 创建全局任务管理器
unified_task_manager = UnifiedTaskManager()

# 替换原有的任务管理函数
def create_market_scan_task(**params):
    """创建市场扫描任务"""
    return unified_task_manager.create_task('market_scan', **params)

def get_market_scan_task(task_id):
    """获取市场扫描任务"""
    return unified_task_manager.get_task(task_id)

def update_market_scan_task(task_id, **kwargs):
    """更新市场扫描任务"""
    return unified_task_manager.update_task(task_id, **kwargs)
'''
    
    return fix_code


if __name__ == "__main__":
    # 测试统一任务管理器
    print("测试统一任务管理器...")
    
    # 创建任务
    task_id, task = task_manager.create_task('market_scan', stock_list=['000001'], total=1)
    print(f"创建任务: {task_id}")
    
    # 获取任务
    retrieved_task = task_manager.get_task(task_id)
    print(f"获取任务: {retrieved_task['id'] if retrieved_task else 'None'}")
    
    # 更新任务
    success = task_manager.update_task(task_id, status='running', progress=50)
    print(f"更新任务: {'成功' if success else '失败'}")
    
    # 再次获取任务
    updated_task = task_manager.get_task(task_id)
    print(f"更新后状态: {updated_task['status'] if updated_task else 'None'}")
    
    print("统一任务管理器测试完成！")
