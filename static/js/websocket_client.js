/**
 * WebSocket客户端管理器
 * 提供实时任务状态更新，替代传统轮询机制
 */

class WebSocketTaskClient {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 1秒
        this.subscribedTasks = new Set();
        this.taskCallbacks = new Map(); // task_id -> callback function
        
        this.init();
    }
    
    init() {
        // 检查是否支持WebSocket
        if (!window.io) {
            console.warn('Socket.IO未加载，回退到轮询模式');
            return false;
        }
        
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true
            });
            
            this.setupEventHandlers();
            return true;
        } catch (error) {
            console.error('WebSocket初始化失败:', error);
            return false;
        }
    }
    
    setupEventHandlers() {
        // 连接成功
        this.socket.on('connect', () => {
            console.log('WebSocket连接成功');
            this.connected = true;
            this.reconnectAttempts = 0;
            
            // 重新订阅之前的任务
            this.subscribedTasks.forEach(taskId => {
                this.subscribeTask(taskId);
            });
        });
        
        // 连接断开
        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket连接断开:', reason);
            this.connected = false;
            
            // 自动重连
            if (reason === 'io server disconnect') {
                // 服务器主动断开，不重连
                console.log('服务器主动断开连接');
            } else {
                // 网络问题，尝试重连
                this.attemptReconnect();
            }
        });
        
        // 任务状态更新
        this.socket.on('task_status_update', (data) => {
            console.log('收到任务状态更新:', data);
            this.handleTaskStatusUpdate(data);
        });
        
        // 任务不存在
        this.socket.on('task_not_found', (data) => {
            console.warn('任务不存在:', data.task_id);
            this.handleTaskNotFound(data.task_id);
        });
        
        // 连接确认
        this.socket.on('connected', (data) => {
            console.log('WebSocket连接确认:', data);
        });
        
        // 错误处理
        this.socket.on('error', (error) => {
            console.error('WebSocket错误:', error);
        });
        
        // 连接错误
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket连接错误:', error);
            this.attemptReconnect();
        });
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('WebSocket重连次数超限，回退到轮询模式');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // 指数退避
        
        console.log(`WebSocket重连尝试 ${this.reconnectAttempts}/${this.maxReconnectAttempts}，${delay}ms后重试`);
        
        setTimeout(() => {
            if (!this.connected) {
                this.socket.connect();
            }
        }, delay);
    }
    
    subscribeTask(taskId, callback = null) {
        if (!this.socket || !this.connected) {
            console.warn('WebSocket未连接，无法订阅任务:', taskId);
            return false;
        }
        
        console.log('订阅任务状态:', taskId);
        this.subscribedTasks.add(taskId);
        
        if (callback) {
            this.taskCallbacks.set(taskId, callback);
        }
        
        this.socket.emit('subscribe_task', { task_id: taskId });
        return true;
    }
    
    unsubscribeTask(taskId) {
        if (!this.socket) {
            return;
        }
        
        console.log('取消订阅任务:', taskId);
        this.subscribedTasks.delete(taskId);
        this.taskCallbacks.delete(taskId);
        
        if (this.connected) {
            this.socket.emit('unsubscribe_task', { task_id: taskId });
        }
    }
    
    handleTaskStatusUpdate(data) {
        const taskId = data.task_id;
        const status = data.status;
        
        // 调用任务特定的回调函数
        if (this.taskCallbacks.has(taskId)) {
            const callback = this.taskCallbacks.get(taskId);
            try {
                callback(data);
            } catch (error) {
                console.error('任务回调函数执行错误:', error);
            }
        }
        
        // 如果任务完成，自动取消订阅
        if (['completed', 'failed', 'cancelled'].includes(status)) {
            console.log(`任务 ${taskId} 已完成，状态: ${status}`);
            setTimeout(() => {
                this.unsubscribeTask(taskId);
            }, 1000); // 1秒后取消订阅
        }
        
        // 触发全局事件
        window.dispatchEvent(new CustomEvent('taskStatusUpdate', {
            detail: data
        }));
    }
    
    handleTaskNotFound(taskId) {
        console.warn(`任务 ${taskId} 不存在，可能已被清理`);
        
        // 触发任务不存在事件
        window.dispatchEvent(new CustomEvent('taskNotFound', {
            detail: { task_id: taskId }
        }));
        
        // 自动取消订阅
        this.unsubscribeTask(taskId);
    }
    
    isConnected() {
        return this.connected;
    }
    
    getSubscribedTasks() {
        return Array.from(this.subscribedTasks);
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// 创建全局WebSocket客户端实例
window.wsTaskClient = new WebSocketTaskClient();

// 提供便捷的全局函数
window.subscribeTaskStatus = function(taskId, callback) {
    if (window.wsTaskClient && window.wsTaskClient.isConnected()) {
        return window.wsTaskClient.subscribeTask(taskId, callback);
    }
    return false;
};

window.unsubscribeTaskStatus = function(taskId) {
    if (window.wsTaskClient) {
        window.wsTaskClient.unsubscribeTask(taskId);
    }
};

// 页面卸载时清理连接
window.addEventListener('beforeunload', function() {
    if (window.wsTaskClient) {
        window.wsTaskClient.disconnect();
    }
});

console.log('WebSocket任务客户端已初始化');
