# -*- coding: utf-8 -*-
"""
测试批量数据更新功能修复效果
验证数据类型错误修复和降级策略
"""

import requests
import time
import json
from datetime import datetime

def test_single_stock_analysis():
    """测试单只股票分析是否修复数据类型错误"""
    print("🔧 测试单只股票分析修复效果")
    print("=" * 50)
    
    test_stocks = ["000001.SZ", "600000.SH", "000002.SZ"]
    
    for stock_code in test_stocks:
        try:
            print(f"\n测试股票: {stock_code}")
            
            # 直接测试StockAnalyzer
            from stock_analyzer import StockAnalyzer
            analyzer = StockAnalyzer()
            
            # 测试quick_analyze_stock方法
            result = analyzer.quick_analyze_stock(stock_code, 'A')
            
            if isinstance(result, dict):
                print(f"✅ 成功: 股票名称={result.get('stock_name', '未知')}, 评分={result.get('score', 0)}")
                if 'error' in result:
                    print(f"⚠️ 有错误但已降级: {result['error']}")
                if 'fallback' in result:
                    print(f"📦 使用降级数据: {result.get('data_source', '未知')}")
            else:
                print(f"❌ 返回数据类型错误: {type(result)}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")

def test_batch_update_api():
    """测试批量更新API修复效果"""
    print("\n🚀 测试批量更新API修复效果")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    test_stocks = ["000001.SZ", "600000.SH", "000002.SZ"]
    
    try:
        # 启动批量更新
        print("启动批量更新...")
        response = requests.post(
            f"{base_url}/api/portfolio/batch_update",
            json={
                "stock_codes": test_stocks,
                "market_type": "A",
                "force_update": False
            },
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                print(f"✅ 任务启动成功，ID: {task_id}")
                
                # 监控进度
                success_count = 0
                error_count = 0
                fallback_count = 0
                
                for i in range(60):  # 最多等待60秒
                    time.sleep(1)
                    
                    try:
                        status_response = requests.get(
                            f"{base_url}/api/portfolio/update_status/{task_id}",
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            progress = status.get('progress_percentage', 0)
                            completed = status.get('completed_stocks', 0)
                            failed = status.get('failed_stocks', 0)
                            
                            print(f"进度: {progress}% | 完成: {completed} | 失败: {failed}")
                            
                            if status.get('status') in ['completed', 'failed']:
                                print(f"任务完成，状态: {status.get('status')}")
                                
                                # 分析结果
                                results = status.get('results', {})
                                errors = status.get('errors', [])
                                
                                print(f"\n📊 结果分析:")
                                print(f"成功更新: {len(results)} 只股票")
                                print(f"失败数量: {len(errors)} 只股票")
                                
                                # 检查降级数据使用情况
                                for stock_code, data in results.items():
                                    if isinstance(data, dict):
                                        if data.get('fallback'):
                                            fallback_count += 1
                                            print(f"📦 {stock_code}: 使用降级数据 ({data.get('data_source', '未知')})")
                                        else:
                                            success_count += 1
                                            print(f"✅ {stock_code}: 正常获取数据")
                                    else:
                                        error_count += 1
                                        print(f"❌ {stock_code}: 数据类型错误")
                                
                                # 显示错误详情
                                if errors:
                                    print(f"\n❌ 错误详情:")
                                    for error in errors[:5]:  # 只显示前5个错误
                                        print(f"  - {error.get('stock_code')}: {error.get('error')}")
                                
                                break
                        else:
                            print(f"获取状态失败: {status_response.status_code}")
                            
                    except Exception as e:
                        print(f"查询状态异常: {e}")
                        break
                
                # 计算修复效果
                total_processed = success_count + error_count + fallback_count
                if total_processed > 0:
                    success_rate = (success_count + fallback_count) / total_processed * 100
                    print(f"\n📈 修复效果:")
                    print(f"总处理数量: {total_processed}")
                    print(f"成功率: {success_rate:.1f}% (包含降级数据)")
                    print(f"正常数据: {success_count}")
                    print(f"降级数据: {fallback_count}")
                    print(f"失败数量: {error_count}")
                    
                    if success_rate >= 80:
                        print("🎉 修复效果良好！")
                    elif success_rate >= 50:
                        print("⚠️ 修复效果一般，需要进一步优化")
                    else:
                        print("❌ 修复效果不佳，需要重新检查")
                
            else:
                print("❌ 未获取到任务ID")
        else:
            print(f"❌ 启动批量更新失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def test_database_connection():
    """测试数据库连接修复效果"""
    print("\n🗄️ 测试数据库连接修复效果")
    print("=" * 50)
    
    try:
        from database import test_connection, get_session
        
        # 测试连接
        if test_connection():
            print("✅ 数据库连接测试成功")
            
            # 测试会话获取（带重试机制）
            session = get_session()
            if session:
                print("✅ 数据库会话获取成功（带重试机制）")
                session.close()
            else:
                print("❌ 数据库会话获取失败")
        else:
            print("❌ 数据库连接测试失败")
            
    except Exception as e:
        print(f"❌ 数据库测试异常: {e}")

def test_server_status():
    """测试服务器状态"""
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"服务器状态: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"服务器连接失败: {e}")
        return False

if __name__ == "__main__":
    print("🛠️ 股票分析系统 - 批量数据更新功能修复测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 1. 测试单只股票分析修复
        test_single_stock_analysis()
        
        # 2. 测试数据库连接修复
        test_database_connection()
        
        # 3. 测试批量更新API修复（需要服务器运行）
        if test_server_status():
            print("✅ 服务器连接正常")
            test_batch_update_api()
        else:
            print("⚠️ 服务器未运行，跳过API测试")
        
        print("\n✅ 所有修复测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
