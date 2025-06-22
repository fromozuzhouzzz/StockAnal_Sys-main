# -*- coding: utf-8 -*-
"""
Server-Sent Events (SSE) 任务状态推送管理器
作为WebSocket的备选方案，适用于不支持WebSocket的环境
"""

import json
import threading
import time
import queue
from datetime import datetime
from flask import Response, request, stream_template

class SSETaskManager:
    """SSE任务状态管理器"""
    
    def __init__(self, app=None, task_manager=None):
        self.app = app
        self.task_manager = task_manager
        self.clients = {}  # {client_id: {'queue': queue, 'tasks': set(), 'last_ping': time}}
        self.task_subscribers = {}  # {task_id: set(client_ids)}
        self.lock = threading.Lock()
        self.cleanup_thread = None
        self.running = True
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        self.app = app
        self._register_routes()
        self._start_cleanup_thread()
    
    def _register_routes(self):
        """注册SSE路由"""
        
        @self.app.route('/api/sse/task_status/<task_id>')
        def sse_task_status(task_id):
            """SSE任务状态流"""
            client_id = request.args.get('client_id', f"client_{int(time.time() * 1000)}")
            
            def event_stream():
                # 注册客户端
                client_queue = self._register_client(client_id, task_id)
                
                try:
                    # 发送初始连接确认
                    yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id, 'task_id': task_id})}\n\n"
                    
                    # 立即发送当前任务状态
                    current_status = self._get_task_status(task_id)
                    if current_status:
                        yield f"data: {json.dumps({'type': 'task_status', 'data': current_status})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'task_not_found', 'task_id': task_id})}\n\n"
                        return
                    
                    # 持续发送更新
                    while True:
                        try:
                            # 等待消息，超时后发送心跳
                            message = client_queue.get(timeout=30)
                            
                            if message is None:  # 停止信号
                                break
                            
                            yield f"data: {json.dumps(message)}\n\n"
                            
                            # 如果任务完成，发送完成消息后结束流
                            if (message.get('type') == 'task_status' and 
                                message.get('data', {}).get('status') in ['completed', 'failed', 'cancelled']):
                                # 延迟5秒后结束连接，确保客户端收到最终状态
                                time.sleep(5)
                                break
                                
                        except queue.Empty:
                            # 发送心跳保持连接
                            yield f"data: {json.dumps({'type': 'ping', 'timestamp': time.time()})}\n\n"
                            self._update_client_ping(client_id)
                            
                except GeneratorExit:
                    # 客户端断开连接
                    pass
                finally:
                    # 清理客户端
                    self._unregister_client(client_id)
            
            return Response(
                event_stream(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Cache-Control'
                }
            )
    
    def _register_client(self, client_id, task_id):
        """注册SSE客户端"""
        with self.lock:
            # 创建客户端队列
            client_queue = queue.Queue(maxsize=100)
            
            self.clients[client_id] = {
                'queue': client_queue,
                'tasks': {task_id},
                'last_ping': time.time()
            }
            
            # 添加任务订阅
            if task_id not in self.task_subscribers:
                self.task_subscribers[task_id] = set()
            self.task_subscribers[task_id].add(client_id)
            
            self.app.logger.info(f"SSE客户端 {client_id} 订阅任务 {task_id}")
            return client_queue
    
    def _unregister_client(self, client_id):
        """注销SSE客户端"""
        with self.lock:
            if client_id in self.clients:
                # 清理任务订阅
                tasks = self.clients[client_id]['tasks']
                for task_id in tasks:
                    if task_id in self.task_subscribers:
                        self.task_subscribers[task_id].discard(client_id)
                        if not self.task_subscribers[task_id]:
                            del self.task_subscribers[task_id]
                
                # 发送停止信号
                try:
                    self.clients[client_id]['queue'].put(None, block=False)
                except queue.Full:
                    pass
                
                del self.clients[client_id]
                self.app.logger.info(f"SSE客户端 {client_id} 已断开")
    
    def _update_client_ping(self, client_id):
        """更新客户端心跳时间"""
        with self.lock:
            if client_id in self.clients:
                self.clients[client_id]['last_ping'] = time.time()
    
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
        """广播任务状态更新到SSE客户端"""
        # 获取最新任务状态
        if not status_data:
            status_data = self._get_task_status(task_id)
        
        if not status_data:
            # 任务不存在，通知订阅者
            message = {'type': 'task_not_found', 'task_id': task_id}
        else:
            message = {'type': 'task_status', 'data': status_data}
        
        with self.lock:
            if task_id in self.task_subscribers:
                subscribers = list(self.task_subscribers[task_id])
                
                for client_id in subscribers:
                    if client_id in self.clients:
                        try:
                            self.clients[client_id]['queue'].put(message, block=False)
                        except queue.Full:
                            # 队列满了，移除客户端
                            self.app.logger.warning(f"SSE客户端 {client_id} 队列满，移除客户端")
                            self._unregister_client(client_id)
        
        self.app.logger.info(f"SSE广播任务 {task_id} 状态更新: {status_data.get('status') if status_data else 'not_found'}")
    
    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup_worker():
            while self.running:
                try:
                    current_time = time.time()
                    with self.lock:
                        # 清理超时的客户端（5分钟无心跳）
                        timeout_clients = []
                        for client_id, client_info in self.clients.items():
                            if current_time - client_info['last_ping'] > 300:  # 5分钟
                                timeout_clients.append(client_id)
                        
                        for client_id in timeout_clients:
                            self.app.logger.info(f"清理超时SSE客户端: {client_id}")
                            self._unregister_client(client_id)
                    
                    time.sleep(60)  # 每分钟检查一次
                    
                except Exception as e:
                    self.app.logger.error(f"SSE清理线程错误: {str(e)}")
                    time.sleep(60)
        
        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def get_stats(self):
        """获取SSE统计信息"""
        with self.lock:
            return {
                'connected_clients': len(self.clients),
                'active_subscriptions': len(self.task_subscribers),
                'total_task_subscribers': sum(len(subscribers) for subscribers in self.task_subscribers.values())
            }
    
    def shutdown(self):
        """关闭SSE管理器"""
        self.running = False
        with self.lock:
            # 通知所有客户端断开
            for client_id in list(self.clients.keys()):
                self._unregister_client(client_id)

# 全局SSE管理器实例
sse_task_manager = None

def init_sse_manager(app, task_manager):
    """初始化SSE管理器"""
    global sse_task_manager
    sse_task_manager = SSETaskManager(app, task_manager)
    return sse_task_manager

def get_sse_manager():
    """获取SSE管理器实例"""
    return sse_task_manager
