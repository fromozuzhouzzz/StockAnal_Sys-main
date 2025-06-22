# -*- coding: utf-8 -*-
"""
WebSocket任务状态实时推送管理器
解决前端轮询效率低下和404错误问题
"""

import json
import logging
import threading
import time
from datetime import datetime
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room

class WebSocketTaskManager:
    """WebSocket任务状态管理器"""
    
    def __init__(self, app=None, task_manager=None):
        self.app = app
        self.task_manager = task_manager
        self.socketio = None
        self.client_rooms = {}  # 客户端房间映射 {client_id: [task_ids]}
        self.task_subscribers = {}  # 任务订阅者映射 {task_id: [client_ids]}
        self.lock = threading.Lock()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        self.app = app
        self.socketio = SocketIO(
            app, 
            cors_allowed_origins="*",
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )
        self._register_handlers()
        
    def _register_handlers(self):
        """注册WebSocket事件处理器"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """客户端连接"""
            client_id = request.sid
            with self.lock:
                self.client_rooms[client_id] = []
            
            self.app.logger.info(f"WebSocket客户端连接: {client_id}")
            emit('connected', {'status': 'success', 'client_id': client_id})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """客户端断开连接"""
            client_id = request.sid
            self._cleanup_client(client_id)
            self.app.logger.info(f"WebSocket客户端断开: {client_id}")
        
        @self.socketio.on('subscribe_task')
        def handle_subscribe_task(data):
            """订阅任务状态更新"""
            client_id = request.sid
            task_id = data.get('task_id')
            
            if not task_id:
                emit('error', {'message': '缺少任务ID'})
                return
            
            # 加入任务房间
            join_room(f"task_{task_id}")
            
            with self.lock:
                # 更新客户端房间映射
                if client_id not in self.client_rooms:
                    self.client_rooms[client_id] = []
                if task_id not in self.client_rooms[client_id]:
                    self.client_rooms[client_id].append(task_id)
                
                # 更新任务订阅者映射
                if task_id not in self.task_subscribers:
                    self.task_subscribers[task_id] = []
                if client_id not in self.task_subscribers[task_id]:
                    self.task_subscribers[task_id].append(client_id)
            
            # 立即发送当前任务状态
            current_status = self._get_task_status(task_id)
            if current_status:
                emit('task_status_update', current_status)
                self.app.logger.info(f"客户端 {client_id} 订阅任务 {task_id}，当前状态: {current_status.get('status')}")
            else:
                emit('task_not_found', {'task_id': task_id})
        
        @self.socketio.on('unsubscribe_task')
        def handle_unsubscribe_task(data):
            """取消订阅任务状态"""
            client_id = request.sid
            task_id = data.get('task_id')
            
            if task_id:
                leave_room(f"task_{task_id}")
                self._remove_task_subscription(client_id, task_id)
                self.app.logger.info(f"客户端 {client_id} 取消订阅任务 {task_id}")
    
    def _cleanup_client(self, client_id):
        """清理客户端相关数据"""
        with self.lock:
            # 清理客户端房间映射
            if client_id in self.client_rooms:
                task_ids = self.client_rooms[client_id]
                for task_id in task_ids:
                    self._remove_task_subscription(client_id, task_id)
                del self.client_rooms[client_id]
    
    def _remove_task_subscription(self, client_id, task_id):
        """移除任务订阅"""
        with self.lock:
            # 从任务订阅者中移除客户端
            if task_id in self.task_subscribers:
                if client_id in self.task_subscribers[task_id]:
                    self.task_subscribers[task_id].remove(client_id)
                
                # 如果没有订阅者了，清理任务订阅
                if not self.task_subscribers[task_id]:
                    del self.task_subscribers[task_id]
            
            # 从客户端房间中移除任务
            if client_id in self.client_rooms:
                if task_id in self.client_rooms[client_id]:
                    self.client_rooms[client_id].remove(task_id)
    
    def _get_task_status(self, task_id):
        """获取任务状态"""
        if not self.task_manager:
            return None
        
        task = self.task_manager.get_task(task_id)
        if not task:
            return None
        
        return {
            'task_id': task_id,
            'status': task['status'],
            'progress': task.get('progress', 0),
            'result': task.get('result'),
            'error': task.get('error'),
            'updated_at': task['updated_at'],
            'task_type': task.get('type', 'unknown')
        }
    
    def broadcast_task_update(self, task_id, status_data=None):
        """广播任务状态更新"""
        if not self.socketio:
            return
        
        # 获取最新任务状态
        if not status_data:
            status_data = self._get_task_status(task_id)
        
        if not status_data:
            # 任务不存在，通知订阅者
            self.socketio.emit(
                'task_not_found', 
                {'task_id': task_id}, 
                room=f"task_{task_id}"
            )
            return
        
        # 广播状态更新
        self.socketio.emit(
            'task_status_update', 
            status_data, 
            room=f"task_{task_id}"
        )
        
        self.app.logger.info(f"广播任务 {task_id} 状态更新: {status_data['status']}")
        
        # 如果任务完成，延迟清理订阅
        if status_data['status'] in ['completed', 'failed', 'cancelled']:
            threading.Timer(300, self._cleanup_completed_task, args=[task_id]).start()  # 5分钟后清理
    
    def _cleanup_completed_task(self, task_id):
        """清理已完成任务的订阅"""
        with self.lock:
            if task_id in self.task_subscribers:
                self.app.logger.info(f"清理已完成任务 {task_id} 的WebSocket订阅")
                del self.task_subscribers[task_id]
    
    def get_stats(self):
        """获取WebSocket统计信息"""
        with self.lock:
            return {
                'connected_clients': len(self.client_rooms),
                'active_subscriptions': len(self.task_subscribers),
                'total_task_subscribers': sum(len(subscribers) for subscribers in self.task_subscribers.values())
            }

# 全局WebSocket管理器实例
websocket_task_manager = None

def init_websocket_manager(app, task_manager):
    """初始化WebSocket管理器"""
    global websocket_task_manager
    websocket_task_manager = WebSocketTaskManager(app, task_manager)
    return websocket_task_manager

def get_websocket_manager():
    """获取WebSocket管理器实例"""
    return websocket_task_manager
