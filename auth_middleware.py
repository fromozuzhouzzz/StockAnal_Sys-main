from functools import wraps
from flask import request, jsonify
import os
import time
import hashlib
import hmac


def get_api_key():
    return os.getenv('API_KEY', 'UZXJfw3YNX80DLfN')


def require_api_key(f):
    """需要API密钥验证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': '缺少API密钥'}), 401

        if api_key != get_api_key():
            return jsonify({'error': '无效的API密钥'}), 403

        return f(*args, **kwargs)
    return decorated_function


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


def require_hmac_auth(f):
    """需要HMAC认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_signature = request.headers.get('X-HMAC-Signature')
        if not request_signature:
            return jsonify({'error': '缺少HMAC签名'}), 401

        # 获取请求数据
        data = request.get_json(silent=True) or {}

        # 添加时间戳防止重放攻击
        timestamp = request.headers.get('X-Timestamp')
        if not timestamp:
            return jsonify({'error': '缺少时间戳'}), 401

        # 验证时间戳有效性（有效期5分钟）
        current_time = int(time.time())
        if abs(current_time - int(timestamp)) > 300:
            return jsonify({'error': '时间戳已过期'}), 401

        # 将时间戳加入验证数据
        verification_data = {**data, 'timestamp': timestamp}

        # 验证签名
        if not verify_hmac_signature(request_signature, verification_data):
            return jsonify({'error': '签名无效'}), 403
        return f(*args, **kwargs)
    return decorated_function