#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析系统投资组合CSV导出功能综合测试
测试403 Forbidden错误的修复效果和多层级降级机制
"""

import requests
import json
import time
from datetime import datetime

# 测试配置
HF_SPACES_URL = "https://fromozu-stock-analysis.hf.space"
API_KEY = "UZXJfw3YNX80DLfN"

# 测试数据
test_portfolio = {
    "stocks": [
        {"stock_code": "000001.SZ", "weight": 30, "market_type": "A"},
        {"stock_code": "000002.SZ", "weight": 25, "market_type": "A"},
        {"stock_code": "600000.SH", "weight": 45, "market_type": "A"}
    ],
    "portfolio_name": "测试投资组合",
    "export_format": "csv"
}

def test_api_endpoint(url, headers=None, description="", expected_status=200):
    """测试API端点"""
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"期望状态码: {expected_status}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        response = requests.post(
            url,
            json=test_portfolio,
            headers=headers or {},
            timeout=30
        )
        end_time = time.time()
        
        print(f"状态码: {response.status_code}")
        print(f"响应时间: {end_time - start_time:.2f}秒")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == expected_status:
            print("✅ 状态码符合预期")
            
            if response.status_code == 200:
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                    print(f"文件名: {filename}")
                print(f"内容长度: {len(response.content)} 字节")
                
                # 验证CSV内容
                if response.content:
                    content_preview = response.content[:200].decode('utf-8-sig', errors='ignore')
                    print(f"内容预览: {content_preview}")
                    
                    # 保存测试文件
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    test_filename = f"test_export_{description.replace(' ', '_')}_{timestamp}.csv"
                    with open(test_filename, 'wb') as f:
                        f.write(response.content)
                    print(f"已保存到: {test_filename}")
                
                return True
            else:
                return True
        else:
            print("❌ 状态码不符合预期")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容: {response.text[:500]}")
            return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

def test_frontend_functionality():
    """测试前端功能可用性"""
    print(f"\n{'='*60}")
    print("测试: 前端页面可访问性")
    print(f"{'='*60}")
    
    try:
        response = requests.get(f"{HF_SPACES_URL}/portfolio", timeout=10)
        print(f"投资组合页面状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 检查页面是否包含导出按钮
            if 'export-portfolio-btn' in response.text:
                print("✅ 导出按钮存在")
            else:
                print("❌ 导出按钮不存在")
            
            # 检查是否包含新的导出函数
            if 'exportPortfolioEnhanced' in response.text:
                print("✅ 增强导出函数存在")
            else:
                print("❌ 增强导出函数不存在")
            
            if 'exportPortfolioClientSide' in response.text:
                print("✅ 前端直接导出函数存在")
            else:
                print("❌ 前端直接导出函数不存在")
            
            return True
        else:
            print("❌ 页面访问失败")
            return False
            
    except Exception as e:
        print(f"❌ 页面测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始综合测试投资组合CSV导出功能修复效果")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 测试1: 主导出API（带正确API密钥）
    results['main_api_correct_key'] = test_api_endpoint(
        f"{HF_SPACES_URL}/api/v1/portfolio/export",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        description="主导出API（正确API密钥）",
        expected_status=200
    )
    
    # 测试2: 主导出API（错误API密钥）
    results['main_api_wrong_key'] = test_api_endpoint(
        f"{HF_SPACES_URL}/api/v1/portfolio/export",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "wrong_key"
        },
        description="主导出API（错误API密钥）",
        expected_status=403
    )
    
    # 测试3: 主导出API（无API密钥）
    results['main_api_no_key'] = test_api_endpoint(
        f"{HF_SPACES_URL}/api/v1/portfolio/export",
        headers={
            "Content-Type": "application/json"
        },
        description="主导出API（无API密钥）",
        expected_status=401
    )
    
    # 测试4: 简化导出API
    results['simple_api'] = test_api_endpoint(
        f"{HF_SPACES_URL}/api/portfolio/export-simple",
        headers={
            "Content-Type": "application/json"
        },
        description="简化导出API",
        expected_status=200
    )
    
    # 测试5: 前端页面功能
    results['frontend'] = test_frontend_functionality()
    
    # 测试总结
    print(f"\n{'='*60}")
    print("🎯 测试总结:")
    print(f"{'='*60}")
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总体结果: {success_count}/{total_count} 测试通过")
    
    # 修复效果评估
    print(f"\n📊 修复效果评估:")
    if results.get('main_api_correct_key'):
        print("🎉 主要问题已解决！403错误已修复，API密钥认证正常工作")
    elif results.get('simple_api'):
        print("🔧 备用方案可用，简化导出API工作正常")
    elif results.get('frontend'):
        print("💡 前端功能可用，用户可以使用前端直接导出")
    else:
        print("⚠️  需要进一步调试，所有导出方案都有问题")
    
    # 降级机制测试
    print(f"\n🔄 降级机制测试:")
    if not results.get('main_api_correct_key') and results.get('simple_api'):
        print("✅ 第一级降级（主API→简化API）可用")
    if not results.get('simple_api') and results.get('frontend'):
        print("✅ 第二级降级（简化API→前端导出）可用")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    main()
