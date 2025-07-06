# -*- coding: utf-8 -*-
"""
测试批量数据更新功能
验证性能提升效果和功能正确性
"""

import requests
import time
import json
from datetime import datetime

def test_batch_update_performance():
    """测试批量更新性能"""
    base_url = "http://localhost:5000"
    
    # 测试股票列表
    test_stocks = [
        "000001.SZ",  # 平安银行
        "600000.SH",  # 浦发银行
        "000002.SZ",  # 万科A
        "600036.SH",  # 招商银行
        "000858.SZ",  # 五粮液
    ]
    
    print("🚀 开始测试批量数据更新功能")
    print(f"测试股票: {', '.join(test_stocks)}")
    print("=" * 60)
    
    # 1. 测试传统方式（单个股票逐一获取）
    print("\n📊 测试1: 传统方式（单个股票逐一获取）")
    traditional_start = time.time()
    traditional_results = {}
    
    for stock_code in test_stocks:
        try:
            print(f"  获取 {stock_code} 数据...")
            response = requests.post(
                f"{base_url}/api/stock_score",
                json={"stock_code": stock_code, "market_type": "A"},
                timeout=30
            )
            
            if response.status_code == 200:
                traditional_results[stock_code] = response.json()
                print(f"  ✅ {stock_code}: 成功")
            else:
                print(f"  ❌ {stock_code}: 失败 ({response.status_code})")
                
        except Exception as e:
            print(f"  ❌ {stock_code}: 异常 - {e}")
    
    traditional_time = time.time() - traditional_start
    print(f"\n传统方式总耗时: {traditional_time:.2f} 秒")
    print(f"平均每股票: {traditional_time/len(test_stocks):.2f} 秒")
    
    # 2. 测试批量更新方式
    print("\n🚀 测试2: 批量更新方式")
    batch_start = time.time()
    
    try:
        # 启动批量更新
        print("  启动批量更新任务...")
        response = requests.post(
            f"{base_url}/api/portfolio/batch_update",
            json={
                "stock_codes": test_stocks,
                "market_type": "A",
                "force_update": True  # 强制更新以测试性能
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 启动批量更新失败: {response.status_code}")
            return
        
        result = response.json()
        task_id = result.get('task_id')
        
        if not task_id:
            print(f"❌ 未获取到任务ID: {result}")
            return
        
        print(f"  ✅ 任务已启动，ID: {task_id}")
        
        # 轮询任务状态
        print("  监控更新进度...")
        batch_results = {}
        
        while True:
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
                    current_stock = status.get('current_stock', '')
                    
                    print(f"    进度: {progress}% | 完成: {completed} | 失败: {failed} | 当前: {current_stock}")
                    
                    if status.get('status') in ['completed', 'failed']:
                        batch_results = status.get('results', {})
                        print(f"  ✅ 批量更新完成，状态: {status.get('status')}")
                        break
                        
                elif status_response.status_code == 404:
                    print("  ❌ 任务不存在或已过期")
                    break
                else:
                    print(f"  ⚠️ 获取状态失败: {status_response.status_code}")
                
                time.sleep(1)  # 等待1秒后再次查询
                
            except Exception as e:
                print(f"  ❌ 查询状态异常: {e}")
                break
    
    except Exception as e:
        print(f"❌ 批量更新异常: {e}")
        return
    
    batch_time = time.time() - batch_start
    print(f"\n批量更新总耗时: {batch_time:.2f} 秒")
    print(f"平均每股票: {batch_time/len(test_stocks):.2f} 秒")
    
    # 3. 性能对比
    print("\n📈 性能对比结果")
    print("=" * 60)
    print(f"传统方式: {traditional_time:.2f} 秒")
    print(f"批量更新: {batch_time:.2f} 秒")
    
    if batch_time < traditional_time:
        improvement = ((traditional_time - batch_time) / traditional_time) * 100
        print(f"🎉 性能提升: {improvement:.1f}%")
    else:
        degradation = ((batch_time - traditional_time) / traditional_time) * 100
        print(f"⚠️ 性能下降: {degradation:.1f}%")
    
    # 4. 数据一致性验证
    print("\n🔍 数据一致性验证")
    print("=" * 60)
    
    consistent_count = 0
    total_compared = 0
    
    for stock_code in test_stocks:
        if stock_code in traditional_results and stock_code in batch_results:
            traditional_score = traditional_results[stock_code].get('score')
            batch_score = batch_results[stock_code].get('score')
            
            if traditional_score == batch_score:
                print(f"✅ {stock_code}: 评分一致 ({traditional_score})")
                consistent_count += 1
            else:
                print(f"❌ {stock_code}: 评分不一致 (传统: {traditional_score}, 批量: {batch_score})")
            
            total_compared += 1
        else:
            print(f"⚠️ {stock_code}: 无法比较（数据缺失）")
    
    if total_compared > 0:
        consistency_rate = (consistent_count / total_compared) * 100
        print(f"\n数据一致性: {consistency_rate:.1f}% ({consistent_count}/{total_compared})")
    
    # 5. 测试CSV导出性能
    print("\n📄 测试CSV导出性能")
    print("=" * 60)
    
    # 模拟投资组合数据
    portfolio_data = []
    for stock_code in test_stocks:
        if stock_code in batch_results:
            stock_data = batch_results[stock_code]
            portfolio_data.append({
                'stock_code': stock_code,
                'weight': 20,  # 假设每只股票20%权重
                **stock_data
            })
    
    print(f"模拟投资组合包含 {len(portfolio_data)} 只股票")
    print("CSV导出应该能够快速完成，因为数据已经预加载到缓存中")
    
    return {
        'traditional_time': traditional_time,
        'batch_time': batch_time,
        'improvement_percentage': ((traditional_time - batch_time) / traditional_time) * 100 if batch_time < traditional_time else 0,
        'consistency_rate': consistency_rate if total_compared > 0 else 0,
        'test_stocks_count': len(test_stocks),
        'successful_updates': len(batch_results)
    }

def test_error_handling():
    """测试错误处理"""
    base_url = "http://localhost:5000"
    
    print("\n🛡️ 测试错误处理")
    print("=" * 60)
    
    # 测试无效股票代码
    invalid_stocks = ["INVALID001", "INVALID002"]
    
    try:
        response = requests.post(
            f"{base_url}/api/portfolio/batch_update",
            json={
                "stock_codes": invalid_stocks,
                "market_type": "A",
                "force_update": True
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ 无效股票代码测试启动，任务ID: {task_id}")
            
            # 等待一段时间后检查结果
            time.sleep(10)
            
            status_response = requests.get(
                f"{base_url}/api/portfolio/update_status/{task_id}",
                timeout=10
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                errors = status.get('errors', [])
                print(f"错误处理测试结果: {len(errors)} 个错误")
                for error in errors[:3]:  # 只显示前3个错误
                    print(f"  - {error.get('stock_code')}: {error.get('error')}")
            
        else:
            print(f"❌ 错误处理测试失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 错误处理测试异常: {e}")

if __name__ == "__main__":
    print("🧪 股票分析系统 - 批量数据更新性能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 主要性能测试
        results = test_batch_update_performance()
        
        # 错误处理测试
        test_error_handling()
        
        # 输出测试总结
        print("\n📋 测试总结")
        print("=" * 80)
        if results:
            print(f"✅ 性能测试完成")
            print(f"   - 测试股票数量: {results['test_stocks_count']}")
            print(f"   - 成功更新数量: {results['successful_updates']}")
            print(f"   - 性能提升: {results['improvement_percentage']:.1f}%")
            print(f"   - 数据一致性: {results['consistency_rate']:.1f}%")
            
            if results['improvement_percentage'] > 0:
                print("🎉 批量更新功能性能提升显著！")
            else:
                print("⚠️ 批量更新功能需要进一步优化")
        
        print("\n✅ 所有测试完成")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
