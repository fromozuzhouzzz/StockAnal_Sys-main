#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金流向页面测试服务器
"""

from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('capital_flow.html')

@app.route('/capital_flow')
def capital_flow():
    return render_template('capital_flow.html')

# 模拟API数据
@app.route('/api/concept_fund_flow')
def concept_fund_flow():
    # 模拟概念资金流向数据
    mock_data = [
        {
            "rank": 1,
            "sector": "人工智能",
            "sector_index": 1234.56,
            "change_percent": 2.34,
            "inflow": 12.45,
            "outflow": 8.76,
            "net_flow": 3.69,
            "company_count": 45
        },
        {
            "rank": 2,
            "sector": "新能源汽车",
            "sector_index": 987.65,
            "change_percent": -1.23,
            "inflow": 8.90,
            "outflow": 11.23,
            "net_flow": -2.33,
            "company_count": 32
        },
        {
            "rank": 3,
            "sector": "半导体",
            "sector_index": 2345.67,
            "change_percent": 3.45,
            "inflow": 15.67,
            "outflow": 9.87,
            "net_flow": 5.80,
            "company_count": 28
        }
    ]
    return jsonify(mock_data)

@app.route('/api/sector_stocks')
def sector_stocks():
    # 模拟概念成分股数据
    mock_data = [
        {
            "code": "000001",
            "name": "平安银行",
            "price": 12.34,
            "change_percent": 1.23,
            "main_net_inflow": 1234567890,
            "main_net_inflow_percent": 2.34
        },
        {
            "code": "000002",
            "name": "万科A",
            "price": 23.45,
            "change_percent": -0.87,
            "main_net_inflow": -987654321,
            "main_net_inflow_percent": -1.56
        },
        {
            "code": "000858",
            "name": "五粮液",
            "price": 156.78,
            "change_percent": 2.45,
            "main_net_inflow": 2345678901,
            "main_net_inflow_percent": 3.21
        }
    ]
    return jsonify(mock_data)

@app.route('/api/individual_fund_flow_rank')
def individual_fund_flow_rank():
    # 模拟个股资金流向排名数据
    mock_data = [
        {
            "rank": 1,
            "code": "000001",
            "name": "平安银行",
            "price": 12.34,
            "change_percent": 1.23,
            "main_net_inflow": 1234567890,
            "main_net_inflow_percent": 2.34,
            "super_large_net_inflow": 567890123,
            "large_net_inflow": 345678901,
            "medium_net_inflow": 123456789,
            "small_net_inflow": 98765432
        },
        {
            "rank": 2,
            "code": "000002",
            "name": "万科A",
            "price": 23.45,
            "change_percent": -0.87,
            "main_net_inflow": -987654321,
            "main_net_inflow_percent": -1.56,
            "super_large_net_inflow": -456789012,
            "large_net_inflow": -234567890,
            "medium_net_inflow": -123456789,
            "small_net_inflow": -87654321
        }
    ]
    return jsonify(mock_data)

if __name__ == '__main__':
    print("✅ 资金流向测试服务器启动成功")
    print("🌐 访问地址: http://localhost:8888")
    print("📊 资金流向页面: http://localhost:8888/capital_flow")
    app.run(host='0.0.0.0', port=8888, debug=True)
