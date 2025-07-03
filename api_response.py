# -*- coding: utf-8 -*-
"""
API响应格式标准化模块
提供统一的API响应格式，包括成功响应、错误响应、分页等
"""

from flask import jsonify, request
from datetime import datetime
import uuid
import time
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class APIResponse:
    """API响应格式标准化类"""
    
    @staticmethod
    def success(data: Any = None, message: str = None, meta: Dict = None, status_code: int = 200):
        """成功响应格式"""
        response_data = {
            'success': True,
            'data': data,
            'meta': {
                'timestamp': datetime.now().isoformat() + 'Z',
                'request_id': str(uuid.uuid4()),
                'processing_time_ms': getattr(request, '_start_time', None) and 
                                    int((time.time() - request._start_time) * 1000) or None,
                **(meta or {})
            }
        }
        
        if message:
            response_data['message'] = message
            
        response = jsonify(response_data)
        response.status_code = status_code
        return response
    
    @staticmethod
    def error(code: str, message: str, details: Any = None, status_code: int = 400):
        """错误响应格式"""
        response_data = {
            'success': False,
            'error': {
                'code': code,
                'message': message,
                'details': details
            },
            'meta': {
                'timestamp': datetime.now().isoformat() + 'Z',
                'request_id': str(uuid.uuid4()),
                'endpoint': request.endpoint,
                'method': request.method
            }
        }
        
        response = jsonify(response_data)
        response.status_code = status_code
        return response
    
    @staticmethod
    def paginated(data: List, page: int, per_page: int, total: int, meta: Dict = None):
        """分页响应格式"""
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination_meta = {
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_page': page + 1 if has_next else None,
                'prev_page': page - 1 if has_prev else None
            },
            'timestamp': datetime.now().isoformat() + 'Z',
            'request_id': str(uuid.uuid4()),
            **(meta or {})
        }
        
        return APIResponse.success(data=data, meta=pagination_meta)
    
    @staticmethod
    def task_created(task_id: str, task_type: str, estimated_time: int = None):
        """任务创建响应格式"""
        data = {
            'task_id': task_id,
            'task_type': task_type,
            'status': 'pending',
            'created_at': datetime.now().isoformat() + 'Z',
            'estimated_completion_time': estimated_time
        }
        
        meta = {
            'status_endpoint': f'/api/v1/tasks/{task_id}',
            'result_endpoint': f'/api/v1/tasks/{task_id}/result'
        }
        
        return APIResponse.success(data=data, meta=meta, status_code=201)
    
    @staticmethod
    def task_status(task_id: str, status: str, progress: int = None, 
                   estimated_remaining: int = None, result: Any = None):
        """任务状态响应格式"""
        data = {
            'task_id': task_id,
            'status': status,
            'progress': progress,
            'estimated_remaining_seconds': estimated_remaining,
            'updated_at': datetime.now().isoformat() + 'Z'
        }
        
        if result is not None:
            data['result'] = result
            
        return APIResponse.success(data=data)


class ErrorCodes:
    """标准错误代码定义"""
    
    # 认证相关错误
    MISSING_API_KEY = 'MISSING_API_KEY'
    INVALID_API_KEY = 'INVALID_API_KEY'
    EXPIRED_API_KEY = 'EXPIRED_API_KEY'
    INSUFFICIENT_PERMISSIONS = 'INSUFFICIENT_PERMISSIONS'
    RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED'
    
    # 请求相关错误
    INVALID_REQUEST_FORMAT = 'INVALID_REQUEST_FORMAT'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    INVALID_PARAMETER_VALUE = 'INVALID_PARAMETER_VALUE'
    INVALID_STOCK_CODE = 'INVALID_STOCK_CODE'
    
    # 业务逻辑错误
    STOCK_NOT_FOUND = 'STOCK_NOT_FOUND'
    ANALYSIS_FAILED = 'ANALYSIS_FAILED'
    INSUFFICIENT_DATA = 'INSUFFICIENT_DATA'
    PORTFOLIO_TOO_LARGE = 'PORTFOLIO_TOO_LARGE'
    
    # 系统错误
    INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR'
    SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE'
    TIMEOUT_ERROR = 'TIMEOUT_ERROR'
    DATABASE_ERROR = 'DATABASE_ERROR'
    
    # 任务相关错误
    TASK_NOT_FOUND = 'TASK_NOT_FOUND'
    TASK_FAILED = 'TASK_FAILED'
    TASK_TIMEOUT = 'TASK_TIMEOUT'


def handle_validation_error(error_details: Dict):
    """处理参数验证错误"""
    return APIResponse.error(
        code=ErrorCodes.INVALID_REQUEST_FORMAT,
        message='请求参数验证失败',
        details=error_details,
        status_code=400
    )


def handle_stock_code_error(invalid_codes: List[str]):
    """处理股票代码错误"""
    return APIResponse.error(
        code=ErrorCodes.INVALID_STOCK_CODE,
        message='无效的股票代码',
        details={
            'invalid_codes': invalid_codes,
            'supported_formats': ['000001.SZ', '600000.SH', '300001.SZ']
        },
        status_code=400
    )


def handle_analysis_error(stock_code: str, error_message: str):
    """处理分析错误"""
    return APIResponse.error(
        code=ErrorCodes.ANALYSIS_FAILED,
        message=f'股票 {stock_code} 分析失败',
        details={'error_message': error_message},
        status_code=500
    )


def handle_rate_limit_error(limit: int, reset_time: int):
    """处理限流错误"""
    return APIResponse.error(
        code=ErrorCodes.RATE_LIMIT_EXCEEDED,
        message='请求频率超过限制',
        details={
            'limit': limit,
            'reset_time': reset_time,
            'retry_after': reset_time - int(time.time())
        },
        status_code=429
    )


def handle_task_not_found_error(task_id: str):
    """处理任务不存在错误"""
    return APIResponse.error(
        code=ErrorCodes.TASK_NOT_FOUND,
        message='任务不存在',
        details={'task_id': task_id},
        status_code=404
    )


def handle_internal_error(error_message: str = None):
    """处理内部服务器错误"""
    return APIResponse.error(
        code=ErrorCodes.INTERNAL_SERVER_ERROR,
        message='内部服务器错误',
        details={'error_message': error_message} if error_message else None,
        status_code=500
    )


class ResponseHeaders:
    """响应头管理"""
    
    @staticmethod
    def add_cors_headers(response):
        """添加CORS头"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key, X-HMAC-Signature, X-Timestamp'
        return response
    
    @staticmethod
    def add_cache_headers(response, max_age: int = 300):
        """添加缓存头"""
        response.headers['Cache-Control'] = f'public, max-age={max_age}'
        response.headers['ETag'] = str(hash(response.get_data()))
        return response
    
    @staticmethod
    def add_rate_limit_headers(response, limit: int, remaining: int, reset_time: int):
        """添加限流头"""
        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Reset'] = str(reset_time)
        return response


def validate_stock_code(stock_code: str) -> bool:
    """验证股票代码格式"""
    if not stock_code or not isinstance(stock_code, str):
        return False
    
    # A股代码格式验证
    import re
    patterns = [
        r'^\d{6}\.(SZ|SH)$',  # 标准格式：000001.SZ
        r'^\d{6}$'            # 简化格式：000001
    ]
    
    return any(re.match(pattern, stock_code.upper()) for pattern in patterns)


def normalize_stock_code(stock_code: str) -> str:
    """标准化股票代码格式"""
    if not stock_code:
        return stock_code
    
    stock_code = stock_code.upper().strip()
    
    # 如果只有6位数字，自动添加后缀
    if stock_code.isdigit() and len(stock_code) == 6:
        # 根据代码范围判断市场
        code_num = int(stock_code)
        if code_num >= 600000:
            return f"{stock_code}.SH"
        else:
            return f"{stock_code}.SZ"
    
    return stock_code


def validate_request_data(data: Dict, required_fields: List[str]) -> Optional[Dict]:
    """验证请求数据"""
    if not data:
        return {'message': '请求体不能为空'}
    
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        return {
            'message': '缺少必需字段',
            'missing_fields': missing_fields
        }
    
    return None


def timing_middleware(f):
    """请求计时中间件"""
    def decorated_function(*args, **kwargs):
        request._start_time = time.time()
        return f(*args, **kwargs)
    return decorated_function
