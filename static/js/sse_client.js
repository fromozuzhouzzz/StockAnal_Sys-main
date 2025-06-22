/**
 * Server-Sent Events (SSE) 客户端管理器
 * 作为WebSocket的备选方案，提供实时任务状态更新
 */

class SSETaskClient {
    constructor() {
        this.eventSources = new Map(); // task_id -> EventSource
        this.taskCallbacks = new Map(); // task_id -> callback function
        this.clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        this.reconnectAttempts = new Map(); // task_id -> attempt count
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 1秒
    }
    
    subscribeTask(taskId, callback = null) {
        // 检查是否已经订阅
        if (this.eventSources.has(taskId)) {
            console.log(`任务 ${taskId} 已经订阅`);
            return true;
        }
        
        // 检查浏览器是否支持SSE
        if (!window.EventSource) {
            console.warn('浏览器不支持Server-Sent Events，回退到轮询模式');
            return false;
        }
        
        console.log(`SSE订阅任务状态: ${taskId}`);
        
        // 保存回调函数
        if (callback) {
            this.taskCallbacks.set(taskId, callback);
        }
        
        // 创建EventSource连接
        const url = `/api/sse/task_status/${taskId}?client_id=${this.clientId}`;
        const eventSource = new EventSource(url);
        
        // 设置事件处理器
        eventSource.onopen = (event) => {
            console.log(`SSE连接已建立: ${taskId}`);
            this.reconnectAttempts.set(taskId, 0);
        };
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(taskId, data);
            } catch (error) {
                console.error('SSE消息解析错误:', error, event.data);
            }
        };
        
        eventSource.onerror = (event) => {
            console.error(`SSE连接错误: ${taskId}`, event);
            
            // 检查连接状态
            if (eventSource.readyState === EventSource.CLOSED) {
                console.log(`SSE连接已关闭: ${taskId}`);
                this.eventSources.delete(taskId);
                
                // 尝试重连
                this.attemptReconnect(taskId, callback);
            } else if (eventSource.readyState === EventSource.CONNECTING) {
                console.log(`SSE正在重连: ${taskId}`);
            }
        };
        
        this.eventSources.set(taskId, eventSource);
        return true;
    }
    
    unsubscribeTask(taskId) {
        console.log(`SSE取消订阅任务: ${taskId}`);
        
        // 关闭EventSource连接
        if (this.eventSources.has(taskId)) {
            const eventSource = this.eventSources.get(taskId);
            eventSource.close();
            this.eventSources.delete(taskId);
        }
        
        // 清理回调和重连计数
        this.taskCallbacks.delete(taskId);
        this.reconnectAttempts.delete(taskId);
    }
    
    attemptReconnect(taskId, callback) {
        const attempts = this.reconnectAttempts.get(taskId) || 0;
        
        if (attempts >= this.maxReconnectAttempts) {
            console.error(`SSE任务 ${taskId} 重连次数超限，停止重连`);
            this.taskCallbacks.delete(taskId);
            this.reconnectAttempts.delete(taskId);
            
            // 触发重连失败事件
            window.dispatchEvent(new CustomEvent('sseReconnectFailed', {
                detail: { task_id: taskId }
            }));
            return;
        }
        
        this.reconnectAttempts.set(taskId, attempts + 1);
        const delay = this.reconnectDelay * Math.pow(2, attempts); // 指数退避
        
        console.log(`SSE任务 ${taskId} 重连尝试 ${attempts + 1}/${this.maxReconnectAttempts}，${delay}ms后重试`);
        
        setTimeout(() => {
            this.subscribeTask(taskId, callback);
        }, delay);
    }
    
    handleMessage(taskId, message) {
        const messageType = message.type;
        
        switch (messageType) {
            case 'connected':
                console.log(`SSE连接确认: ${taskId}`, message);
                break;
                
            case 'task_status':
                const statusData = message.data;
                console.log(`SSE任务状态更新: ${taskId}`, statusData);
                
                // 调用任务特定的回调函数
                if (this.taskCallbacks.has(taskId)) {
                    const callback = this.taskCallbacks.get(taskId);
                    try {
                        callback(statusData);
                    } catch (error) {
                        console.error('SSE任务回调函数执行错误:', error);
                    }
                }
                
                // 触发全局事件
                window.dispatchEvent(new CustomEvent('taskStatusUpdate', {
                    detail: statusData
                }));
                
                // 如果任务完成，自动取消订阅
                if (['completed', 'failed', 'cancelled'].includes(statusData.status)) {
                    console.log(`SSE任务 ${taskId} 已完成，状态: ${statusData.status}`);
                    setTimeout(() => {
                        this.unsubscribeTask(taskId);
                    }, 2000); // 2秒后取消订阅
                }
                break;
                
            case 'task_not_found':
                console.warn(`SSE任务不存在: ${taskId}`);
                
                // 触发任务不存在事件
                window.dispatchEvent(new CustomEvent('taskNotFound', {
                    detail: { task_id: taskId }
                }));
                
                // 自动取消订阅
                this.unsubscribeTask(taskId);
                break;
                
            case 'ping':
                // 心跳消息，保持连接活跃
                console.debug(`SSE心跳: ${taskId}`);
                break;
                
            default:
                console.log(`SSE未知消息类型: ${messageType}`, message);
        }
    }
    
    getSubscribedTasks() {
        return Array.from(this.eventSources.keys());
    }
    
    isSubscribed(taskId) {
        return this.eventSources.has(taskId);
    }
    
    getConnectionState(taskId) {
        if (!this.eventSources.has(taskId)) {
            return 'not_connected';
        }
        
        const eventSource = this.eventSources.get(taskId);
        switch (eventSource.readyState) {
            case EventSource.CONNECTING:
                return 'connecting';
            case EventSource.OPEN:
                return 'open';
            case EventSource.CLOSED:
                return 'closed';
            default:
                return 'unknown';
        }
    }
    
    disconnect() {
        console.log('SSE断开所有连接');
        
        // 关闭所有EventSource连接
        this.eventSources.forEach((eventSource, taskId) => {
            eventSource.close();
        });
        
        // 清理所有数据
        this.eventSources.clear();
        this.taskCallbacks.clear();
        this.reconnectAttempts.clear();
    }
    
    getStats() {
        return {
            subscribedTasks: this.eventSources.size,
            clientId: this.clientId,
            connections: Array.from(this.eventSources.keys()).map(taskId => ({
                taskId: taskId,
                state: this.getConnectionState(taskId)
            }))
        };
    }
}

// 创建全局SSE客户端实例
window.sseTaskClient = new SSETaskClient();

// 提供便捷的全局函数
window.subscribeTaskStatusSSE = function(taskId, callback) {
    return window.sseTaskClient.subscribeTask(taskId, callback);
};

window.unsubscribeTaskStatusSSE = function(taskId) {
    window.sseTaskClient.unsubscribeTask(taskId);
};

// 页面卸载时清理连接
window.addEventListener('beforeunload', function() {
    if (window.sseTaskClient) {
        window.sseTaskClient.disconnect();
    }
});

console.log('SSE任务客户端已初始化');
