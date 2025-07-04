# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - Hugging Face Spaces 部署版本
修改：熊猫大侠
版本：v2.1.0 - HF Spaces Edition
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 应用HF Spaces性能优化配置
try:
    from hf_spaces_performance_config import init_hf_spaces_performance
    performance_config = init_hf_spaces_performance()
    if performance_config:
        logger.info("✅ HF Spaces性能优化配置已应用")
    else:
        logger.warning("⚠️ HF Spaces性能优化配置应用失败")
except Exception as e:
    logger.error(f"❌ 性能优化配置导入失败: {e}")

# 设置环境变量，适配 Hugging Face Spaces 环境
os.environ.setdefault('USE_DATABASE', 'False')
os.environ.setdefault('USE_REDIS_CACHE', 'False')
os.environ.setdefault('FLASK_ENV', 'production')

# 创建必要的目录
os.makedirs('data', exist_ok=True)
os.makedirs('data/news', exist_ok=True)
os.makedirs('logs', exist_ok=True)

try:
    # 导入主应用
    from web_server import app
    logger.info("成功导入 web_server 应用")
except Exception as e:
    logger.error(f"导入 web_server 失败: {e}")
    sys.exit(1)

if __name__ == "__main__":
    # 获取端口号，Hugging Face Spaces 会自动设置 PORT 环境变量
    port = int(os.environ.get("PORT", 7860))

    logger.info(f"启动应用，端口: {port}")
    logger.info(f"数据库状态: {os.environ.get('USE_DATABASE', 'False')}")
    logger.info(f"Redis缓存状态: {os.environ.get('USE_REDIS_CACHE', 'False')}")

    # 启动应用
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,  # 生产环境关闭调试模式
        threaded=True
    )
