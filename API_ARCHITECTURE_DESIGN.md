# 股票分析系统 API 接口架构设计

## 概述

本文档定义了股票分析系统的RESTful API接口架构，提供外部系统调用股票分析功能的标准化接口。

## API版本控制

- **当前版本**: v1
- **基础URL**: `/api/v1`
- **版本控制方式**: URL路径版本控制

## 认证机制

### 1. API密钥认证
```http
X-API-Key: your_api_key_here
```

### 2. HMAC签名认证（高安全级别）
```http
X-API-Key: your_api_key_here
X-HMAC-Signature: hmac_signature
X-Timestamp: unix_timestamp
```

## 核心API端点

### 1. 投资组合分析API

**端点**: `POST /api/v1/portfolio/analyze`

**请求格式**:
```json
{
  "stocks": [
    {
      "stock_code": "000001.SZ",
      "weight": 0.3,
      "market_type": "A"
    },
    {
      "stock_code": "600000.SH", 
      "weight": 0.7,
      "market_type": "A"
    }
  ],
  "analysis_params": {
    "risk_preference": "moderate",
    "time_horizon": "medium"
  }
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "portfolio_score": 75.5,
    "risk_level": "medium",
    "risk_analysis": {
      "volatility_risk": 65.2,
      "concentration_risk": 45.8,
      "correlation_risk": 55.3
    },
    "recommendations": [
      "建议适当分散投资",
      "关注市场波动风险"
    ],
    "individual_stocks": [
      {
        "stock_code": "000001.SZ",
        "score": 78.2,
        "weight": 0.3,
        "contribution": 23.46
      }
    ]
  },
  "meta": {
    "analysis_time": "2025-01-03T10:30:00Z",
    "cache_hit": true,
    "processing_time_ms": 1250
  }
}
```

### 2. 个股分析API

**端点**: `POST /api/v1/stock/analyze`

**请求格式**:
```json
{
  "stock_code": "000001.SZ",
  "market_type": "A",
  "analysis_depth": "full",
  "include_ai_analysis": true,
  "time_range": 60
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "stock_info": {
      "stock_code": "000001.SZ",
      "stock_name": "平安银行",
      "industry": "银行",
      "market_type": "A"
    },
    "analysis_result": {
      "overall_score": 78.5,
      "technical_score": 75.2,
      "fundamental_score": 82.1,
      "capital_flow_score": 77.8
    },
    "technical_analysis": {
      "trend": "上升",
      "support_levels": [12.50, 12.20],
      "resistance_levels": [13.80, 14.20],
      "indicators": {
        "rsi": 65.2,
        "macd_signal": "买入",
        "ma_trend": "多头排列"
      }
    },
    "fundamental_analysis": {
      "pe_ratio": 5.8,
      "pb_ratio": 0.65,
      "roe": 12.5,
      "debt_ratio": 45.2
    },
    "risk_assessment": {
      "risk_level": "中等",
      "volatility": 25.3,
      "beta": 1.15
    },
    "ai_analysis": {
      "summary": "该股票基本面良好...",
      "recommendation": "建议持有",
      "confidence": 0.85
    }
  },
  "meta": {
    "analysis_time": "2025-01-03T10:30:00Z",
    "data_freshness": "实时",
    "processing_time_ms": 2150
  }
}
```

### 3. 批量股票评分API

**端点**: `POST /api/v1/stocks/batch-score`

**请求格式**:
```json
{
  "stock_codes": ["000001.SZ", "600000.SH", "000002.SZ"],
  "market_type": "A",
  "min_score": 60,
  "sort_by": "score",
  "sort_order": "desc"
}
```

**响应格式**:
```json
{
  "success": true,
  "data": {
    "total_analyzed": 3,
    "qualified_count": 2,
    "results": [
      {
        "stock_code": "000001.SZ",
        "stock_name": "平安银行",
        "score": 78.5,
        "risk_level": "中等",
        "recommendation": "买入"
      },
      {
        "stock_code": "600000.SH", 
        "stock_name": "浦发银行",
        "score": 72.3,
        "risk_level": "中等",
        "recommendation": "持有"
      }
    ]
  },
  "meta": {
    "analysis_time": "2025-01-03T10:30:00Z",
    "processing_time_ms": 5250,
    "cache_hit_rate": 0.67
  }
}
```

### 4. 异步任务API

**创建任务**: `POST /api/v1/tasks`
```json
{
  "task_type": "portfolio_analysis",
  "params": {
    "stocks": [...],
    "analysis_depth": "full"
  }
}
```

**查询任务状态**: `GET /api/v1/tasks/{task_id}`
```json
{
  "success": true,
  "data": {
    "task_id": "uuid-string",
    "status": "running",
    "progress": 65,
    "estimated_completion": "2025-01-03T10:35:00Z",
    "created_at": "2025-01-03T10:30:00Z"
  }
}
```

**获取任务结果**: `GET /api/v1/tasks/{task_id}/result`

## 错误处理

### 标准错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "INVALID_STOCK_CODE",
    "message": "提供的股票代码无效",
    "details": {
      "invalid_codes": ["INVALID001"],
      "suggestion": "请检查股票代码格式"
    }
  },
  "meta": {
    "request_id": "req_123456789",
    "timestamp": "2025-01-03T10:30:00Z"
  }
}
```

### HTTP状态码规范
- `200 OK`: 请求成功
- `201 Created`: 任务创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 认证失败
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `429 Too Many Requests`: 请求频率超限
- `500 Internal Server Error`: 服务器内部错误

## 限流策略

### 基础限流
- **免费用户**: 100次/小时
- **付费用户**: 1000次/小时
- **企业用户**: 10000次/小时

### 端点特定限流
- 个股分析: 50次/小时
- 投资组合分析: 20次/小时
- 批量评分: 10次/小时

## 缓存策略

### 数据缓存TTL
- **实时数据**: 5分钟
- **技术指标**: 15分钟
- **基本面数据**: 1天
- **历史数据**: 7天

### 缓存键策略
- 个股分析: `stock_analysis:{stock_code}:{market_type}:{date}`
- 组合分析: `portfolio_analysis:{hash(stocks)}:{params_hash}`

## 集成现有系统

### 1. 任务管理器集成
- 复用 `unified_task_manager`
- 支持异步任务处理
- 任务状态实时更新

### 2. 分析引擎集成
- `StockAnalyzer`: 核心分析功能
- `RiskMonitor`: 风险评估
- `FundamentalAnalyzer`: 基本面分析

### 3. 缓存系统集成
- MySQL缓存: 长期数据存储
- Redis缓存: 实时数据缓存
- 智能缓存策略

## 安全考虑

### 1. 输入验证
- 股票代码格式验证
- 参数范围检查
- SQL注入防护

### 2. 输出过滤
- 敏感信息过滤
- 数据脱敏处理

### 3. 访问控制
- API密钥管理
- 用户权限分级
- IP白名单支持

## 监控和日志

### 1. 性能监控
- 响应时间监控
- 错误率统计
- 缓存命中率

### 2. 业务监控
- API调用统计
- 用户行为分析
- 系统负载监控

### 3. 日志记录
- 请求日志
- 错误日志
- 性能日志
