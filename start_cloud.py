#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云部署启动脚本
适用于 Railway, Render, Fly.io 等云平台
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def setup_environment():
    """设置云部署环境"""
    # 确保必要的目录存在
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # 设置默认环境变量
    if not os.getenv('PORT'):
        os.environ['PORT'] = '8888'
    
    if not os.getenv('PYTHONUNBUFFERED'):
        os.environ['PYTHONUNBUFFERED'] = '1'
    
    # 检查必需的环境变量
    required_vars = ['OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"错误：缺少必需的环境变量: {', '.join(missing_vars)}")
        print("请在部署平台设置这些环境变量")
        sys.exit(1)
    
    print("环境检查完成 ✓")

def check_dependencies():
    """检查依赖包"""
    try:
        import flask
        import pandas
        import numpy
        import akshare
        print("依赖包检查完成 ✓")
    except ImportError as e:
        print(f"错误：缺少依赖包 {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)

def main():
    """主函数"""
    print("🚀 启动股票分析系统...")
    
    # 环境设置
    setup_environment()
    
    # 依赖检查
    check_dependencies()
    
    # 启动应用
    try:
        from web_server import app
        port = int(os.getenv('PORT', 8888))
        
        print(f"✅ 系统启动成功，端口: {port}")
        print(f"🌐 访问地址: http://localhost:{port}")
        
        # 在云环境中使用 gunicorn，本地开发使用 Flask 开发服务器
        if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER') or os.getenv('FLY_APP_NAME'):
            # 云环境，使用 gunicorn
            import subprocess
            cmd = [
                'gunicorn',
                '--bind', f'0.0.0.0:{port}',
                '--workers', '2',
                '--timeout', '300',
                '--max-requests', '1000',
                '--max-requests-jitter', '100',
                'web_server:app'
            ]
            subprocess.run(cmd)
        else:
            # 本地开发环境
            app.run(host='0.0.0.0', port=port, debug=False)
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
