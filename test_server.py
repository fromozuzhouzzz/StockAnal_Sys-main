#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务器启动脚本
"""

import os
import sys

# 设置环境变量
os.environ['OPENAI_API_KEY'] = 'dummy'
os.environ['OPENAI_API_MODEL'] = 'gpt-3.5-turbo'

try:
    from web_server import app
    print("✅ 服务器启动成功")
    print("🌐 访问地址: http://localhost:8888")
    app.run(host='0.0.0.0', port=8888, debug=False)
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
