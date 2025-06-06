#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Flask测试服务器
"""

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/risk_monitor')
def risk_monitor():
    return render_template('risk_monitor.html')

if __name__ == '__main__':
    print("✅ 简单测试服务器启动成功")
    print("🌐 访问地址: http://localhost:8888")
    app.run(host='0.0.0.0', port=8888, debug=True)
