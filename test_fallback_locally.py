#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地测试降级策略
验证降级分析策略是否正常工作
"""

def test_fallback_strategy():
    """测试降级策略"""
    print("=== 测试降级分析策略 ===")
    
    try:
        from fallback_analysis_strategy import fallback_strategy
        
        # 测试不同的股票代码
        test_stocks = ['603316.SH', '601218.SH', '000001.SZ']
        
        for stock_code in test_stocks:
            print(f"\n测试股票: {stock_code}")
            
            # 使用降级策略分析（传入None作为分析器，强制使用降级）
            result = fallback_strategy.analyze_stock_with_fallback(
                stock_code, 'A', None, None, None
            )
            
            if result and not result.get('error'):
                fallback_info = result.get('fallback_info', {})
                print(f"✅ 降级分析成功")
                print(f"   使用级别: {fallback_info.get('level_used', 'unknown')}")
                print(f"   是否降级: {fallback_info.get('is_fallback', False)}")
                print(f"   股票名称: {result.get('stock_info', {}).get('stock_name', 'unknown')}")
                print(f"   综合评分: {result.get('analysis_result', {}).get('overall_score', 0)}")
            else:
                print(f"❌ 降级分析失败: {result.get('message', 'Unknown error')}")
        
        # 测试策略状态
        status = fallback_strategy.get_strategy_status()
        print(f"\n策略状态: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_source_fallback():
    """测试数据源降级"""
    print("\n=== 测试数据源降级 ===")
    
    try:
        from data_source_fallback import data_source_fallback
        
        # 测试获取股票数据
        stock_code = '603316.SH'
        print(f"测试获取股票数据: {stock_code}")
        
        data = data_source_fallback.get_stock_data(stock_code, 'basic')
        
        if data:
            data_source = data.get('data_source', {})
            print(f"✅ 数据获取成功")
            print(f"   数据源: {data_source.get('source', 'unknown')}")
            print(f"   是否降级: {data_source.get('is_fallback', False)}")
            print(f"   股票名称: {data.get('stock_name', 'unknown')}")
            print(f"   股票价格: {data.get('price', 0)}")
        else:
            print(f"❌ 数据获取失败")
        
        # 测试数据源状态
        status = data_source_fallback.get_source_status()
        print(f"\n数据源状态: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints_import():
    """测试API端点导入"""
    print("\n=== 测试API端点导入 ===")
    
    try:
        from api_endpoints import FALLBACK_STRATEGY_AVAILABLE, fallback_strategy
        
        print(f"降级策略可用: {FALLBACK_STRATEGY_AVAILABLE}")
        print(f"降级策略实例: {fallback_strategy}")
        
        if FALLBACK_STRATEGY_AVAILABLE and fallback_strategy:
            # 测试基础响应
            result = fallback_strategy._basic_response('603316.SH', 'A')
            print(f"✅ 基础响应测试成功")
            print(f"   股票代码: {result.get('stock_info', {}).get('stock_code', 'unknown')}")
            print(f"   综合评分: {result.get('analysis_result', {}).get('overall_score', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hf_optimization():
    """测试HF优化"""
    print("\n=== 测试HF优化 ===")
    
    try:
        from hf_spaces_optimization import init_hf_spaces_optimization, get_hf_timeout
        
        optimizer = init_hf_spaces_optimization()
        print(f"HF优化器初始化: {optimizer}")
        print(f"是否HF环境: {optimizer.is_hf_spaces}")
        print(f"API超时: {get_hf_timeout('api')}")
        print(f"分析超时: {get_hf_timeout('analysis')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔍 本地降级策略测试")
    print("="*50)
    
    tests = [
        ("降级分析策略", test_fallback_strategy),
        ("数据源降级", test_data_source_fallback),
        ("API端点导入", test_api_endpoints_import),
        ("HF优化", test_hf_optimization)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 总结
    print(f"\n{'='*50}")
    print("🎯 测试总结")
    print("="*50)
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    print(f"\n成功率: {success_rate:.1f}% ({success_count}/{total_count})")
    
    if success_rate == 100:
        print("🎉 所有本地测试通过！降级策略工作正常")
    elif success_rate >= 75:
        print("✅ 大部分测试通过，降级策略基本可用")
    else:
        print("⚠️ 多个测试失败，需要检查降级策略实现")

if __name__ == "__main__":
    main()
