#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合CSV导出功能修复测试脚本
测试403 Forbidden错误的修复效果
"""

import requests
import json
import time
from datetime import datetime

# 测试配置
HF_SPACES_URL = "https://fromozu-stock-analysis.hf.space"
LOCAL_URL = "http://localhost:8888"
API_KEY = "UZXJfw3YNX80DLfN"

# 测试数据
test_portfolio = {
    "stocks": [
        {
            "stock_code": "000001.SZ",
            "weight": 30,
            "market_type": "A"
        },
        {
            "stock_code": "000002.SZ", 
            "weight": 25,
            "market_type": "A"
        },
        {
            "stock_code": "600000.SH",
            "weight": 45,
            "market_type": "A"
        }
    ],
    "portfolio_name": "测试投资组合",
    "export_format": "csv"
}

def test_export_api(base_url, endpoint, headers=None, description=""):
    """测试导出API"""
    url = f"{base_url}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            url,
            json=test_portfolio,
            headers=headers or {},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 成功！")
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
                print(f"文件名: {filename}")
            print(f"内容长度: {len(response.content)} 字节")
            
            # 保存文件用于验证
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            local_filename = f"test_export_{timestamp}.csv"
            with open(local_filename, 'wb') as f:
                f.write(response.content)
            print(f"已保存到: {local_filename}")
            
        else:
            print("❌ 失败！")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data}")
            except:
                print(f"响应内容: {response.text[:500]}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {str(e)}")
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")

def main():
    """主测试函数"""
    print("🚀 开始测试投资组合CSV导出功能修复效果")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试场景1: HF Spaces - 带API密钥的主导出API
    test_export_api(
        HF_SPACES_URL,
        "/api/v1/portfolio/export",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        description="HF Spaces - 主导出API（带API密钥）"
    )
    
    # 测试场景2: HF Spaces - 不带API密钥的主导出API
    test_export_api(
        HF_SPACES_URL,
        "/api/v1/portfolio/export",
        headers={
            "Content-Type": "application/json"
        },
        description="HF Spaces - 主导出API（不带API密钥）"
    )
    
    # 测试场景3: HF Spaces - 简化导出API
    test_export_api(
        HF_SPACES_URL,
        "/api/portfolio/export-simple",
        headers={
            "Content-Type": "application/json"
        },
        description="HF Spaces - 简化导出API（备用方案）"
    )
    
    # 测试场景4: 本地服务器（如果可用）
    try:
        response = requests.get(f"{LOCAL_URL}/", timeout=5)
        if response.status_code == 200:
            print(f"\n🔍 检测到本地服务器运行中，进行本地测试...")
            
            test_export_api(
                LOCAL_URL,
                "/api/v1/portfolio/export",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY
                },
                description="本地服务器 - 主导出API"
            )
    except:
        print(f"\n⚠️  本地服务器未运行，跳过本地测试")
    
    print(f"\n{'='*60}")
    print("🎯 测试总结:")
    print("1. 如果HF Spaces主API返回200，说明API密钥修复成功")
    print("2. 如果主API仍然403，但简化API返回200，说明备用方案有效")
    print("3. 如果都失败，需要进一步调试")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
