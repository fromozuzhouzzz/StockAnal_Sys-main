/**
 * 智能轮询策略管理器
 * 提供自适应轮询间隔和智能错误处理，作为WebSocket/SSE的兼容性方案
 */

class SmartPollingManager {
    constructor() {
        this.activeTasks = new Map(); // task_id -> polling config
        this.defaultConfig = {
            initialInterval: 2000,      // 初始轮询间隔：2秒
            maxInterval: 30000,         // 最大轮询间隔：30秒
            backoffMultiplier: 1.5,     // 退避倍数
            maxRetries: 10,             // 最大重试次数
            retryResetTime: 300000,     // 重试计数重置时间：5分钟
            completedTaskKeepTime: 60000, // 已完成任务保持时间：1分钟
            adaptiveThreshold: 5        // 自适应阈值：连续5次无变化后增加间隔
        };
    }
    
    startPolling(taskId, statusUrl, callback, config = {}) {
        // 合并配置
        const pollingConfig = { ...this.defaultConfig, ...config };
        
        // 如果任务已在轮询，先停止
        if (this.activeTasks.has(taskId)) {
            this.stopPolling(taskId);
        }
        
        const taskState = {
            taskId: taskId,
            statusUrl: statusUrl,
            callback: callback,
            config: pollingConfig,
            
            // 轮询状态
            currentInterval: pollingConfig.initialInterval,
            retryCount: 0,
            consecutiveNoChange: 0,
            lastStatus: null,
            lastProgress: -1,
            startTime: Date.now(),
            lastSuccessTime: Date.now(),
            
            // 定时器
            timeoutId: null,
            
            // 统计信息
            totalRequests: 0,
            successRequests: 0,
            errorRequests: 0
        };
        
        this.activeTasks.set(taskId, taskState);
        
        console.log(`开始智能轮询任务: ${taskId}，初始间隔: ${pollingConfig.initialInterval}ms`);
        
        // 立即执行第一次轮询
        this._pollTask(taskState);
        
        return taskState;
    }
    
    stopPolling(taskId) {
        if (!this.activeTasks.has(taskId)) {
            return false;
        }
        
        const taskState = this.activeTasks.get(taskId);
        
        // 清理定时器
        if (taskState.timeoutId) {
            clearTimeout(taskState.timeoutId);
            taskState.timeoutId = null;
        }
        
        // 记录统计信息
        const duration = Date.now() - taskState.startTime;
        console.log(`停止轮询任务: ${taskId}，运行时间: ${duration}ms，总请求: ${taskState.totalRequests}，成功: ${taskState.successRequests}，失败: ${taskState.errorRequests}`);
        
        this.activeTasks.delete(taskId);
        return true;
    }
    
    _pollTask(taskState) {
        const { taskId, statusUrl, callback, config } = taskState;
        
        taskState.totalRequests++;
        
        // 发起AJAX请求
        $.ajax({
            url: statusUrl,
            method: 'GET',
            timeout: 10000, // 10秒超时
            success: (response) => {
                this._handleSuccess(taskState, response);
            },
            error: (xhr, status, error) => {
                this._handleError(taskState, xhr, status, error);
            }
        });
    }
    
    _handleSuccess(taskState, response) {
        const { taskId, callback, config } = taskState;
        
        taskState.successRequests++;
        taskState.retryCount = 0; // 重置重试计数
        taskState.lastSuccessTime = Date.now();
        
        // 检查任务状态变化
        const currentStatus = response.status;
        const currentProgress = response.progress || 0;
        
        const statusChanged = taskState.lastStatus !== currentStatus;
        const progressChanged = taskState.lastProgress !== currentProgress;
        
        if (statusChanged || progressChanged) {
            taskState.consecutiveNoChange = 0;
            console.log(`任务 ${taskId} 状态更新: ${currentStatus} (${currentProgress}%)`);
        } else {
            taskState.consecutiveNoChange++;
        }
        
        taskState.lastStatus = currentStatus;
        taskState.lastProgress = currentProgress;
        
        // 调用回调函数
        try {
            callback(response);
        } catch (error) {
            console.error(`任务 ${taskId} 回调函数执行错误:`, error);
        }
        
        // 检查任务是否完成
        if (['completed', 'failed', 'cancelled'].includes(currentStatus)) {
            console.log(`任务 ${taskId} 已完成，状态: ${currentStatus}`);
            
            // 延迟停止轮询，给用户时间查看结果
            setTimeout(() => {
                this.stopPolling(taskId);
            }, config.completedTaskKeepTime);
            
            return;
        }
        
        // 计算下次轮询间隔
        const nextInterval = this._calculateNextInterval(taskState);
        
        // 安排下次轮询
        taskState.timeoutId = setTimeout(() => {
            if (this.activeTasks.has(taskId)) {
                this._pollTask(taskState);
            }
        }, nextInterval);
    }
    
    _handleError(taskState, xhr, status, error) {
        const { taskId, config } = taskState;
        
        taskState.errorRequests++;
        taskState.retryCount++;
        
        console.warn(`任务 ${taskId} 轮询错误 (${taskState.retryCount}/${config.maxRetries}):`, {
            status: xhr.status,
            statusText: xhr.statusText,
            error: error
        });
        
        // 特殊处理404错误
        if (xhr.status === 404) {
            console.warn(`任务 ${taskId} 不存在 (404)，可能已被清理`);
            
            // 如果是新任务（运行时间少于1分钟），继续重试
            const runningTime = Date.now() - taskState.startTime;
            if (runningTime < 60000) {
                console.log(`任务 ${taskId} 运行时间较短 (${runningTime}ms)，继续重试`);
            } else {
                // 运行时间较长，可能真的被清理了
                console.log(`任务 ${taskId} 运行时间较长且出现404，可能已被清理`);
            }
        }
        
        // 检查是否超过最大重试次数
        if (taskState.retryCount >= config.maxRetries) {
            // 重试次数用尽，重置计数并继续（但增加间隔）
            console.warn(`任务 ${taskId} 重试次数用尽，重置计数并继续轮询`);
            taskState.retryCount = 0;
            taskState.currentInterval = Math.min(taskState.currentInterval * 2, config.maxInterval);
        }
        
        // 计算重试间隔（错误时使用指数退避）
        const retryInterval = Math.min(
            taskState.currentInterval * Math.pow(config.backoffMultiplier, taskState.retryCount),
            config.maxInterval
        );
        
        console.log(`任务 ${taskId} 将在 ${retryInterval}ms 后重试`);
        
        // 安排重试
        taskState.timeoutId = setTimeout(() => {
            if (this.activeTasks.has(taskId)) {
                this._pollTask(taskState);
            }
        }, retryInterval);
    }
    
    _calculateNextInterval(taskState) {
        const { config } = taskState;
        let nextInterval = taskState.currentInterval;
        
        // 自适应间隔调整
        if (taskState.consecutiveNoChange >= config.adaptiveThreshold) {
            // 连续无变化，增加轮询间隔
            nextInterval = Math.min(nextInterval * config.backoffMultiplier, config.maxInterval);
            taskState.currentInterval = nextInterval;
            console.log(`任务 ${taskState.taskId} 连续无变化，调整间隔为: ${nextInterval}ms`);
        } else if (taskState.consecutiveNoChange === 0) {
            // 有变化，重置为较短间隔
            nextInterval = Math.max(config.initialInterval, taskState.currentInterval / config.backoffMultiplier);
            taskState.currentInterval = nextInterval;
        }
        
        return nextInterval;
    }
    
    getTaskState(taskId) {
        return this.activeTasks.get(taskId);
    }
    
    getAllTasks() {
        return Array.from(this.activeTasks.keys());
    }
    
    getStats() {
        const stats = {
            activeTasks: this.activeTasks.size,
            tasks: []
        };
        
        this.activeTasks.forEach((taskState, taskId) => {
            const duration = Date.now() - taskState.startTime;
            stats.tasks.push({
                taskId: taskId,
                status: taskState.lastStatus,
                progress: taskState.lastProgress,
                currentInterval: taskState.currentInterval,
                retryCount: taskState.retryCount,
                duration: duration,
                totalRequests: taskState.totalRequests,
                successRate: taskState.totalRequests > 0 ? (taskState.successRequests / taskState.totalRequests * 100).toFixed(1) + '%' : '0%'
            });
        });
        
        return stats;
    }
    
    stopAllPolling() {
        console.log('停止所有轮询任务');
        const taskIds = Array.from(this.activeTasks.keys());
        taskIds.forEach(taskId => this.stopPolling(taskId));
    }
}

// 创建全局智能轮询管理器实例
window.smartPolling = new SmartPollingManager();

// 提供便捷的全局函数
window.startSmartPolling = function(taskId, statusUrl, callback, config) {
    return window.smartPolling.startPolling(taskId, statusUrl, callback, config);
};

window.stopSmartPolling = function(taskId) {
    return window.smartPolling.stopPolling(taskId);
};

// 页面卸载时清理所有轮询
window.addEventListener('beforeunload', function() {
    if (window.smartPolling) {
        window.smartPolling.stopAllPolling();
    }
});

console.log('智能轮询管理器已初始化');
