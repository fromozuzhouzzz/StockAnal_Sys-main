from functools import wraps
from flask import request, jsonify, g
import os
import time
import hashlib
import hmac
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class APIKeyManager:
    """API密钥管理器"""

    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.revoked_keys = set()

    def _load_api_keys(self) -> Dict:
        """从环境变量或配置文件加载API密钥"""
        # 默认API密钥配置
        default_keys = {
            'UZXJfw3YNX80DLfN': {
                'tier': 'free',
                'permissions': ['stock_analysis', 'portfolio_analysis'],
                'created_at': '2025-01-01T00:00:00Z',
                'expires_at': None,
                'active': True
            }
        }

        # 尝试从环境变量加载
        api_keys_json = os.getenv('API_KEYS_CONFIG')
        if api_keys_json:
            try:
                return json.loads(api_keys_json)
            except json.JSONDecodeError:
                logger.warning("API_KEYS_CONFIG格式错误，使用默认配置")

        return default_keys

    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """验证API密钥"""
        if not api_key or api_key in self.revoked_keys:
            return None

        key_info = self.api_keys.get(api_key)
        if not key_info:
            return None

        # 检查是否激活
        if not key_info.get('active', True):
            return None

        # 检查是否过期
        expires_at = key_info.get('expires_at')
        if expires_at:
            try:
                expire_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.now() > expire_time:
                    return None
            except ValueError:
                logger.warning(f"API密钥 {api_key} 的过期时间格式错误")

        return key_info

    def get_user_tier(self, api_key: str) -> str:
        """获取用户等级"""
        key_info = self.validate_api_key(api_key)
        return key_info.get('tier', 'free') if key_info else 'free'

    def check_permission(self, api_key: str, permission: str) -> bool:
        """检查权限"""
        key_info = self.validate_api_key(api_key)
        if not key_info:
            return False

        permissions = key_info.get('permissions', [])
        return permission in permissions or 'all' in permissions

    def revoke_api_key(self, api_key: str):
        """撤销API密钥"""
        self.revoked_keys.add(api_key)
        logger.info(f"API密钥已撤销: {api_key[:8]}...")

    def generate_api_key(self, tier: str = 'free', permissions: List[str] = None) -> str:
        """生成新的API密钥"""
        api_key = f"{tier}_{uuid.uuid4().hex}"

        self.api_keys[api_key] = {
            'tier': tier,
            'permissions': permissions or ['stock_analysis'],
            'created_at': datetime.now().isoformat() + 'Z',
            'expires_at': None,
            'active': True
        }

        return api_key


# 全局API密钥管理器
api_key_manager = APIKeyManager()


def get_api_key():
    """获取默认API密钥（向后兼容）"""
    return os.getenv('API_KEY', 'UZXJfw3YNX80DLfN')


def require_api_key(permission: str = None):
    """需要API密钥验证的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_API_KEY',
                        'message': '缺少API密钥',
                        'details': '请在请求头中提供X-API-Key'
                    }
                }), 401

            # 验证API密钥
            key_info = api_key_manager.validate_api_key(api_key)
            if not key_info:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_API_KEY',
                        'message': '无效的API密钥',
                        'details': 'API密钥不存在、已过期或已被撤销'
                    }
                }), 403

            # 检查权限
            if permission and not api_key_manager.check_permission(api_key, permission):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'message': '权限不足',
                        'details': f'需要权限: {permission}'
                    }
                }), 403

            # 将用户信息存储到请求上下文
            g.api_key = api_key
            g.user_tier = key_info['tier']
            g.user_permissions = key_info['permissions']

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_tier(min_tier: str):
    """需要特定用户等级的装饰器"""
    tier_levels = {'free': 0, 'paid': 1, 'enterprise': 2}

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_API_KEY',
                        'message': '缺少API密钥'
                    }
                }), 401

            user_tier = api_key_manager.get_user_tier(api_key)
            user_level = tier_levels.get(user_tier, 0)
            required_level = tier_levels.get(min_tier, 0)

            if user_level < required_level:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'TIER_INSUFFICIENT',
                        'message': f'需要{min_tier}等级或更高',
                        'details': f'当前等级: {user_tier}'
                    }
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_hmac_signature(data, secret_key=None):
    if secret_key is None:
        secret_key = os.getenv('HMAC_SECRET', 'default_hmac_secret_for_development')

    if isinstance(data, dict):
        # 对字典进行排序，确保相同的数据产生相同的签名
        data = '&'.join(f"{k}={v}" for k, v in sorted(data.items()))

    # 使用HMAC-SHA256生成签名
    signature = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

    return signature


def verify_hmac_signature(request_signature, data, secret_key=None):
    expected_signature = generate_hmac_signature(data, secret_key)
    return hmac.compare_digest(request_signature, expected_signature)


def require_hmac_auth(permission: str = None):
    """需要HMAC认证的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 首先验证API密钥
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_API_KEY',
                        'message': '缺少API密钥'
                    }
                }), 401

            key_info = api_key_manager.validate_api_key(api_key)
            if not key_info:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_API_KEY',
                        'message': '无效的API密钥'
                    }
                }), 403

            # 验证HMAC签名
            request_signature = request.headers.get('X-HMAC-Signature')
            if not request_signature:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_HMAC_SIGNATURE',
                        'message': '缺少HMAC签名'
                    }
                }), 401

            # 获取请求数据
            data = request.get_json(silent=True) or {}

            # 添加时间戳防止重放攻击
            timestamp = request.headers.get('X-Timestamp')
            if not timestamp:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_TIMESTAMP',
                        'message': '缺少时间戳'
                    }
                }), 401

            # 验证时间戳有效性（有效期5分钟）
            try:
                current_time = int(time.time())
                request_time = int(timestamp)
                if abs(current_time - request_time) > 300:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'TIMESTAMP_EXPIRED',
                            'message': '时间戳已过期',
                            'details': '请求时间戳与服务器时间差超过5分钟'
                        }
                    }), 401
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_TIMESTAMP',
                        'message': '时间戳格式无效'
                    }
                }), 400

            # 将时间戳和API密钥加入验证数据
            verification_data = {**data, 'timestamp': timestamp, 'api_key': api_key}

            # 验证签名
            if not verify_hmac_signature(request_signature, verification_data):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_SIGNATURE',
                        'message': 'HMAC签名无效'
                    }
                }), 403

            # 检查权限
            if permission and not api_key_manager.check_permission(api_key, permission):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'message': '权限不足',
                        'details': f'需要权限: {permission}'
                    }
                }), 403

            # 将用户信息存储到请求上下文
            g.api_key = api_key
            g.user_tier = key_info['tier']
            g.user_permissions = key_info['permissions']
            g.authenticated_via = 'hmac'

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user_info():
    """获取当前用户信息"""
    return {
        'api_key': getattr(g, 'api_key', None),
        'tier': getattr(g, 'user_tier', 'anonymous'),
        'permissions': getattr(g, 'user_permissions', []),
        'auth_method': getattr(g, 'authenticated_via', 'none')
    }


def log_api_access(endpoint: str, success: bool = True, error_code: str = None):
    """记录API访问日志"""
    user_info = get_current_user_info()

    log_data = {
        'timestamp': datetime.now().isoformat(),
        'endpoint': endpoint,
        'method': request.method,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'api_key': user_info['api_key'][:8] + '...' if user_info['api_key'] else None,
        'user_tier': user_info['tier'],
        'success': success,
        'error_code': error_code
    }

    if success:
        logger.info(f"API访问成功: {json.dumps(log_data, ensure_ascii=False)}")
    else:
        logger.warning(f"API访问失败: {json.dumps(log_data, ensure_ascii=False)}")


def api_access_logger(f):
    """API访问日志装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            log_api_access(request.endpoint, success=True)
            return result
        except Exception as e:
            log_api_access(request.endpoint, success=False, error_code=str(e))
            raise
    return decorated_function