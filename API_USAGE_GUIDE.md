# 股票分析系统 API 使用指南

## 概述

本指南详细介绍如何使用股票分析系统的RESTful API接口，包括认证、请求格式、响应处理和错误处理等。

## 快速开始

### 1. 获取API密钥

联系系统管理员获取API密钥，或使用默认测试密钥：
```
X-API-Key: UZXJfw3YNX80DLfN
```

### 2. 基础请求格式

所有API请求都需要包含以下头部：
```http
Content-Type: application/json
X-API-Key: your_api_key_here
```

### 3. 基础URL

```
http://your-domain.com/api/v1
```

## 核心API端点

### 1. 投资组合分析

**端点**: `POST /api/v1/portfolio/analyze`

**功能**: 分析投资组合的整体表现和风险

**请求示例**:
```bash
curl -X POST "http://localhost:8888/api/v1/portfolio/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: UZXJfw3YNX80DLfN" \
  -d '{
    "stocks": [
      {
        "stock_code": "000001.SZ",
        "weight": 0.4,
        "market_type": "A"
      },
      {
        "stock_code": "600000.SH",
        "weight": 0.6,
        "market_type": "A"
      }
    ],
    "analysis_params": {
      "risk_preference": "moderate",
      "time_horizon": "medium"
    }
  }'
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "portfolio_score": 75.5,
    "risk_level": "中等风险",
    "risk_analysis": {
      "volatility_risk": 65.2,
      "concentration_risk": 45.8,
      "correlation_risk": 55.3,
      "overall_risk_score": 55.4
    },
    "recommendations": [
      "投资组合表现良好，可适当调整优化",
      "根据您的保守风险偏好，建议降低组合风险"
    ],
    "individual_stocks": [
      {
        "stock_code": "000001.SZ",
        "stock_name": "平安银行",
        "score": 78.2,
        "weight": 0.4,
        "contribution": 31.28,
        "risk_level": "中等",
        "recommendation": "买入"
      }
    ]
  },
  "meta": {
    "analysis_time": "2025-01-03T10:30:00Z",
    "processing_time_ms": 1250,
    "cache_hit": false
  }
}
```

### 2. 个股分析

**端点**: `POST /api/v1/stock/analyze`

**功能**: 分析单只股票的详细信息

**请求示例**:
```bash
curl -X POST "http://localhost:8888/api/v1/stock/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: UZXJfw3YNX80DLfN" \
  -d '{
    "stock_code": "000001.SZ",
    "market_type": "A",
    "analysis_depth": "full",
    "include_ai_analysis": true
  }'
```

**响应示例**:
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
      "total_risk_score": 45.2
    },
    "ai_analysis": {
      "summary": "该股票基本面良好，技术面呈现上升趋势...",
      "recommendation": "建议买入",
      "confidence": 0.85
    }
  }
}
```

### 3. 批量股票评分

**端点**: `POST /api/v1/stocks/batch-score`

**功能**: 批量分析多只股票的评分

**请求示例**:
```bash
curl -X POST "http://localhost:8888/api/v1/stocks/batch-score" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: UZXJfw3YNX80DLfN" \
  -d '{
    "stock_codes": ["000001.SZ", "600000.SH", "000002.SZ"],
    "market_type": "A",
    "min_score": 60,
    "sort_by": "score",
    "sort_order": "desc"
  }'
```

### 4. 异步任务管理

**创建任务**: `POST /api/v1/tasks`
```bash
curl -X POST "http://localhost:8888/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: UZXJfw3YNX80DLfN" \
  -d '{
    "task_type": "portfolio_analysis",
    "params": {
      "stocks": [{"stock_code": "000001.SZ", "weight": 1.0}]
    }
  }'
```

**查询任务状态**: `GET /api/v1/tasks/{task_id}`
```bash
curl -X GET "http://localhost:8888/api/v1/tasks/your-task-id" \
  -H "X-API-Key: UZXJfw3YNX80DLfN"
```

**获取任务结果**: `GET /api/v1/tasks/{task_id}/result`
```bash
curl -X GET "http://localhost:8888/api/v1/tasks/your-task-id/result" \
  -H "X-API-Key: UZXJfw3YNX80DLfN"
```

## 认证机制

### 1. API密钥认证（基础）

在请求头中包含API密钥：
```http
X-API-Key: your_api_key_here
```

### 2. HMAC签名认证（高安全级别）

对于敏感操作，使用HMAC签名：
```http
X-API-Key: your_api_key_here
X-HMAC-Signature: hmac_sha256_signature
X-Timestamp: unix_timestamp
```

**HMAC签名生成示例（Python）**:
```python
import hmac
import hashlib
import time
import json

def generate_hmac_signature(data, api_key, secret_key):
    timestamp = str(int(time.time()))
    
    # 构建签名数据
    sign_data = {**data, 'timestamp': timestamp, 'api_key': api_key}
    sign_string = '&'.join(f"{k}={v}" for k, v in sorted(sign_data.items()))
    
    # 生成HMAC签名
    signature = hmac.new(
        secret_key.encode(),
        sign_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature, timestamp
```

## 错误处理

### 标准错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {
      "additional_info": "详细信息"
    }
  },
  "meta": {
    "timestamp": "2025-01-03T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| `MISSING_API_KEY` | 401 | 缺少API密钥 |
| `INVALID_API_KEY` | 403 | 无效的API密钥 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `INVALID_STOCK_CODE` | 400 | 无效的股票代码 |
| `PORTFOLIO_TOO_LARGE` | 400 | 投资组合过大 |
| `ANALYSIS_FAILED` | 500 | 分析失败 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |

## 限流策略

### 基础限流

- **免费用户**: 100次/小时
- **付费用户**: 1000次/小时  
- **企业用户**: 10000次/小时

### 端点特定限流

- **个股分析**: 50次/小时
- **投资组合分析**: 20次/小时
- **批量评分**: 10次/小时

### 限流响应头

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1641024000
```

## 最佳实践

### 1. 错误重试

```python
import time
import requests

def api_request_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 429:  # 限流
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
                continue
            
            return response
            
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 指数退避
```

### 2. 批量处理

```python
def batch_analyze_stocks(stock_codes, batch_size=10):
    results = []
    
    for i in range(0, len(stock_codes), batch_size):
        batch = stock_codes[i:i + batch_size]
        
        response = requests.post(
            f"{base_url}/api/v1/stocks/batch-score",
            json={"stock_codes": batch},
            headers=headers
        )
        
        if response.status_code == 200:
            batch_results = response.json()['data']['results']
            results.extend(batch_results)
        
        time.sleep(1)  # 避免触发限流
    
    return results
```

### 3. 缓存利用

```python
import hashlib
import json

def get_cache_key(request_data):
    data_str = json.dumps(request_data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

def cached_api_request(url, data, cache_ttl=300):
    cache_key = get_cache_key(data)
    
    # 检查缓存
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # 发送请求
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    # 存储到缓存
    if response.status_code == 200:
        cache.set(cache_key, result, ttl=cache_ttl)
    
    return result
```

## 健康检查

**端点**: `GET /api/v1/health`

检查API服务状态：
```bash
curl -X GET "http://localhost:8888/api/v1/health" \
  -H "X-API-Key: UZXJfw3YNX80DLfN"
```

## 支持与反馈

如有问题或建议，请联系：
- 邮箱: support@example.com
- 文档: `/api/docs` (Swagger UI)
- 健康检查: `/api/v1/health`
