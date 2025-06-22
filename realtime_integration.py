# -*- coding: utf-8 -*-
"""
实时通信集成配置
将WebSocket、SSE和智能轮询集成到现有的Flask应用中
"""

from flask import Flask
from flask_socketio import SocketIO
import logging

# 导入实时通信管理器
from websocket_task_manager import init_websocket_manager, get_websocket_manager
from sse_task_manager import init_sse_manager, get_sse_manager

class RealtimeIntegration:
    """实时通信集成管理器"""
    
    def __init__(self):
        self.websocket_manager = None
        self.sse_manager = None
        self.task_manager = None
        self.app = None
        self.socketio = None
        
    def init_app(self, app, task_manager):
        """初始化实时通信功能"""
        self.app = app
        self.task_manager = task_manager
        
        app.logger.info("初始化实时通信功能...")
        
        try:
            # 1. 初始化WebSocket管理器
            self.websocket_manager = init_websocket_manager(app, task_manager)
            self.socketio = self.websocket_manager.socketio
            app.logger.info("✓ WebSocket管理器初始化成功")
            
        except Exception as e:
            app.logger.error(f"✗ WebSocket管理器初始化失败: {str(e)}")
            self.websocket_manager = None
        
        try:
            # 2. 初始化SSE管理器
            self.sse_manager = init_sse_manager(app, task_manager)
            app.logger.info("✓ SSE管理器初始化成功")
            
        except Exception as e:
            app.logger.error(f"✗ SSE管理器初始化失败: {str(e)}")
            self.sse_manager = None
        
        # 3. 集成任务状态广播
        self._integrate_task_broadcasting()
        
        # 4. 添加调试路由
        self._add_debug_routes()
        
        app.logger.info("实时通信功能初始化完成")
        
    def _integrate_task_broadcasting(self):
        """集成任务状态广播到现有的任务管理器"""
        if not self.task_manager:
            return
        
        # 保存原始的update_task方法
        original_update_task = self.task_manager.update_task
        
        def enhanced_update_task(task_id, **kwargs):
            """增强的任务更新方法，包含实时广播"""
            # 调用原始更新方法
            result = original_update_task(task_id, **kwargs)
            
            # 获取更新后的任务状态
            task = self.task_manager.get_task(task_id)
            if task:
                status_data = {
                    'task_id': task_id,
                    'status': task['status'],
                    'progress': task.get('progress', 0),
                    'result': task.get('result'),
                    'error': task.get('error'),
                    'updated_at': task['updated_at'],
                    'task_type': task.get('type', 'unknown')
                }
                
                # 广播到WebSocket客户端
                if self.websocket_manager:
                    try:
                        self.websocket_manager.broadcast_task_update(task_id, status_data)
                    except Exception as e:
                        self.app.logger.error(f"WebSocket广播失败: {str(e)}")
                
                # 广播到SSE客户端
                if self.sse_manager:
                    try:
                        self.sse_manager.broadcast_task_update(task_id, status_data)
                    except Exception as e:
                        self.app.logger.error(f"SSE广播失败: {str(e)}")
            
            return result
        
        # 替换任务管理器的update_task方法
        self.task_manager.update_task = enhanced_update_task
        self.app.logger.info("任务状态广播集成完成")
    
    def _add_debug_routes(self):
        """添加调试和监控路由"""
        
        @self.app.route('/api/realtime/stats')
        def realtime_stats():
            """获取实时通信统计信息"""
            stats = {
                'websocket': None,
                'sse': None,
                'task_manager': None
            }
            
            if self.websocket_manager:
                try:
                    stats['websocket'] = self.websocket_manager.get_stats()
                except Exception as e:
                    stats['websocket'] = {'error': str(e)}
            
            if self.sse_manager:
                try:
                    stats['sse'] = self.sse_manager.get_stats()
                except Exception as e:
                    stats['sse'] = {'error': str(e)}
            
            if self.task_manager:
                try:
                    stats['task_manager'] = {
                        'total_tasks': len(self.task_manager.tasks),
                        'protected_tasks': len(self.task_manager.protected_tasks)
                    }
                except Exception as e:
                    stats['task_manager'] = {'error': str(e)}
            
            return stats
        
        @self.app.route('/api/realtime/test/<task_id>')
        def test_realtime_broadcast(task_id):
            """测试实时广播功能"""
            test_data = {
                'task_id': task_id,
                'status': 'running',
                'progress': 50,
                'result': None,
                'error': None,
                'updated_at': '2025-06-22 12:00:00',
                'task_type': 'test'
            }
            
            results = {}
            
            # 测试WebSocket广播
            if self.websocket_manager:
                try:
                    self.websocket_manager.broadcast_task_update(task_id, test_data)
                    results['websocket'] = 'success'
                except Exception as e:
                    results['websocket'] = f'error: {str(e)}'
            else:
                results['websocket'] = 'not_available'
            
            # 测试SSE广播
            if self.sse_manager:
                try:
                    self.sse_manager.broadcast_task_update(task_id, test_data)
                    results['sse'] = 'success'
                except Exception as e:
                    results['sse'] = f'error: {str(e)}'
            else:
                results['sse'] = 'not_available'
            
            return {
                'test_task_id': task_id,
                'test_data': test_data,
                'broadcast_results': results
            }
    
    def get_socketio(self):
        """获取SocketIO实例"""
        return self.socketio
    
    def shutdown(self):
        """关闭实时通信功能"""
        if self.sse_manager:
            self.sse_manager.shutdown()
        
        if self.websocket_manager and self.socketio:
            # SocketIO会在Flask应用关闭时自动清理
            pass

# 全局实时通信集成实例
realtime_integration = RealtimeIntegration()

def init_realtime_communication(app, task_manager):
    """初始化实时通信功能的便捷函数"""
    global realtime_integration
    realtime_integration.init_app(app, task_manager)
    return realtime_integration

def get_realtime_integration():
    """获取实时通信集成实例"""
    return realtime_integration
