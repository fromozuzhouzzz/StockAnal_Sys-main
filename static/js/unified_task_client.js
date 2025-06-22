/**
 * 统一任务状态客户端管理器
 * 自动选择最佳通信方式：WebSocket > SSE > 智能轮询
 */

class UnifiedTaskClient {
    constructor() {
        this.communicationMethod = null; // 'websocket', 'sse', 'polling'
        this.taskCallbacks = new Map(); // task_id -> callback function
        this.subscribedTasks = new Set();
        this.fallbackAttempts = 0;
        this.maxFallbackAttempts = 3;
        
        this.init();
    }
    
    async init() {
        console.log('初始化统一任务状态客户端...');
        
        // 尝试按优先级初始化通信方式
        const methods = [
            { name: 'websocket', check: () => this.tryWebSocket() },
            { name: 'sse', check: () => this.trySSE() },
            { name: 'polling', check: () => this.tryPolling() }
        ];
        
        for (const method of methods) {
            try {
                const success = await method.check();
                if (success) {
                    this.communicationMethod = method.name;
                    console.log(`✓ 使用通信方式: ${method.name.toUpperCase()}`);
                    break;
                }
            } catch (error) {
                console.warn(`✗ ${method.name.toUpperCase()} 初始化失败:`, error);
            }
        }
        
        if (!this.communicationMethod) {
            console.error('所有通信方式初始化失败');
            return false;
        }
        
        // 设置全局事件监听
        this.setupGlobalEventHandlers();
        return true;
    }
    
    async tryWebSocket() {
        return new Promise((resolve) => {
            if (!window.wsTaskClient) {
                resolve(false);
                return;
            }
            
            // 检查WebSocket是否可用
            if (window.wsTaskClient.isConnected()) {
                resolve(true);
            } else {
                // 等待连接建立
                const timeout = setTimeout(() => {
                    resolve(false);
                }, 5000); // 5秒超时
                
                const checkConnection = () => {
                    if (window.wsTaskClient.isConnected()) {
                        clearTimeout(timeout);
                        resolve(true);
                    } else {
                        setTimeout(checkConnection, 100);
                    }
                };
                
                checkConnection();
            }
        });
    }
    
    async trySSE() {
        return new Promise((resolve) => {
            if (!window.EventSource || !window.sseTaskClient) {
                resolve(false);
                return;
            }
            
            // SSE通常立即可用
            resolve(true);
        });
    }
    
    async tryPolling() {
        // 轮询总是可用的
        return Promise.resolve(true);
    }
    
    subscribeTask(taskId, callback = null) {
        console.log(`订阅任务状态: ${taskId} (使用 ${this.communicationMethod})`);
        
        // 保存回调函数
        if (callback) {
            this.taskCallbacks.set(taskId, callback);
        }
        
        this.subscribedTasks.add(taskId);
        
        // 根据通信方式调用相应的订阅方法
        switch (this.communicationMethod) {
            case 'websocket':
                return this.subscribeWebSocket(taskId, callback);
                
            case 'sse':
                return this.subscribeSSE(taskId, callback);
                
            case 'polling':
                return this.subscribePolling(taskId, callback);
                
            default:
                console.error('未知的通信方式:', this.communicationMethod);
                return false;
        }
    }
    
    subscribeWebSocket(taskId, callback) {
        if (!window.wsTaskClient) {
            return this.fallbackToNextMethod(taskId, callback);
        }
        
        const success = window.wsTaskClient.subscribeTask(taskId, (data) => {
            this.handleTaskUpdate(taskId, data, callback);
        });
        
        if (!success) {
            return this.fallbackToNextMethod(taskId, callback);
        }
        
        return true;
    }
    
    subscribeSSE(taskId, callback) {
        if (!window.sseTaskClient) {
            return this.fallbackToNextMethod(taskId, callback);
        }
        
        const success = window.sseTaskClient.subscribeTask(taskId, (data) => {
            this.handleTaskUpdate(taskId, data, callback);
        });
        
        if (!success) {
            return this.fallbackToNextMethod(taskId, callback);
        }
        
        return true;
    }
    
    subscribePolling(taskId, callback) {
        if (!window.smartPolling) {
            console.error('智能轮询管理器不可用');
            return false;
        }
        
        const statusUrl = `/api/analysis_status/${taskId}`;
        
        window.smartPolling.startPolling(taskId, statusUrl, (data) => {
            this.handleTaskUpdate(taskId, data, callback);
        }, {
            // 针对已知问题优化的轮询配置
            initialInterval: 5000,      // 5秒初始间隔
            maxInterval: 30000,         // 30秒最大间隔
            maxRetries: 15,             // 增加重试次数
            completedTaskKeepTime: 120000, // 完成后保持2分钟
            adaptiveThreshold: 3        // 3次无变化后调整间隔
        });
        
        return true;
    }
    
    fallbackToNextMethod(taskId, callback) {
        this.fallbackAttempts++;
        
        if (this.fallbackAttempts >= this.maxFallbackAttempts) {
            console.error('所有通信方式都失败，无法订阅任务:', taskId);
            return false;
        }
        
        console.warn(`通信方式 ${this.communicationMethod} 失败，尝试降级...`);
        
        // 降级到下一个方法
        const methods = ['websocket', 'sse', 'polling'];
        const currentIndex = methods.indexOf(this.communicationMethod);
        
        if (currentIndex < methods.length - 1) {
            this.communicationMethod = methods[currentIndex + 1];
            console.log(`降级到: ${this.communicationMethod}`);
            return this.subscribeTask(taskId, callback);
        }
        
        return false;
    }
    
    handleTaskUpdate(taskId, data, callback) {
        console.log(`任务 ${taskId} 状态更新:`, data);
        
        // 调用任务特定的回调
        if (callback) {
            try {
                callback(data);
            } catch (error) {
                console.error('任务回调执行错误:', error);
            }
        }
        
        // 调用全局回调
        if (this.taskCallbacks.has(taskId)) {
            const globalCallback = this.taskCallbacks.get(taskId);
            try {
                globalCallback(data);
            } catch (error) {
                console.error('全局任务回调执行错误:', error);
            }
        }
        
        // 如果任务完成，自动取消订阅
        if (['completed', 'failed', 'cancelled'].includes(data.status)) {
            setTimeout(() => {
                this.unsubscribeTask(taskId);
            }, 2000);
        }
    }
    
    unsubscribeTask(taskId) {
        console.log(`取消订阅任务: ${taskId}`);
        
        this.subscribedTasks.delete(taskId);
        this.taskCallbacks.delete(taskId);
        
        // 根据通信方式调用相应的取消订阅方法
        switch (this.communicationMethod) {
            case 'websocket':
                if (window.wsTaskClient) {
                    window.wsTaskClient.unsubscribeTask(taskId);
                }
                break;
                
            case 'sse':
                if (window.sseTaskClient) {
                    window.sseTaskClient.unsubscribeTask(taskId);
                }
                break;
                
            case 'polling':
                if (window.smartPolling) {
                    window.smartPolling.stopPolling(taskId);
                }
                break;
        }
    }
    
    setupGlobalEventHandlers() {
        // 监听连接失败事件，自动降级
        window.addEventListener('sseReconnectFailed', (event) => {
            const taskId = event.detail.task_id;
            console.warn(`SSE连接失败，任务 ${taskId} 降级到轮询`);
            
            if (this.subscribedTasks.has(taskId)) {
                const callback = this.taskCallbacks.get(taskId);
                this.communicationMethod = 'polling';
                this.subscribePolling(taskId, callback);
            }
        });
        
        // 监听WebSocket断开事件
        window.addEventListener('wsDisconnected', () => {
            console.warn('WebSocket断开，降级到SSE');
            this.communicationMethod = 'sse';
            
            // 重新订阅所有任务
            const tasks = Array.from(this.subscribedTasks);
            tasks.forEach(taskId => {
                const callback = this.taskCallbacks.get(taskId);
                this.subscribeSSE(taskId, callback);
            });
        });
    }
    
    getCommunicationMethod() {
        return this.communicationMethod;
    }
    
    getSubscribedTasks() {
        return Array.from(this.subscribedTasks);
    }
    
    getStats() {
        const baseStats = {
            communicationMethod: this.communicationMethod,
            subscribedTasks: this.subscribedTasks.size,
            fallbackAttempts: this.fallbackAttempts
        };
        
        // 添加具体通信方式的统计
        switch (this.communicationMethod) {
            case 'websocket':
                if (window.wsTaskClient) {
                    baseStats.websocket = {
                        connected: window.wsTaskClient.isConnected(),
                        subscribedTasks: window.wsTaskClient.getSubscribedTasks()
                    };
                }
                break;
                
            case 'sse':
                if (window.sseTaskClient) {
                    baseStats.sse = window.sseTaskClient.getStats();
                }
                break;
                
            case 'polling':
                if (window.smartPolling) {
                    baseStats.polling = window.smartPolling.getStats();
                }
                break;
        }
        
        return baseStats;
    }
    
    disconnect() {
        console.log('断开统一任务客户端连接');
        
        // 取消所有订阅
        const tasks = Array.from(this.subscribedTasks);
        tasks.forEach(taskId => this.unsubscribeTask(taskId));
        
        // 断开具体的连接
        if (window.wsTaskClient) {
            window.wsTaskClient.disconnect();
        }
        if (window.sseTaskClient) {
            window.sseTaskClient.disconnect();
        }
        if (window.smartPolling) {
            window.smartPolling.stopAllPolling();
        }
    }
}

// 创建全局统一任务客户端实例
window.unifiedTaskClient = new UnifiedTaskClient();

// 提供便捷的全局函数
window.subscribeTaskStatus = function(taskId, callback) {
    return window.unifiedTaskClient.subscribeTask(taskId, callback);
};

window.unsubscribeTaskStatus = function(taskId) {
    window.unifiedTaskClient.unsubscribeTask(taskId);
};

// 页面卸载时清理连接
window.addEventListener('beforeunload', function() {
    if (window.unifiedTaskClient) {
        window.unifiedTaskClient.disconnect();
    }
});

console.log('统一任务状态客户端已初始化');
