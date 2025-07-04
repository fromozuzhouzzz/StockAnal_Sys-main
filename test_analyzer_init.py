#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分析器初始化
验证分析器是否正确初始化和工作
"""

def test_local_analyzer():
    """测试本地分析器"""
    print("=== 测试本地分析器初始化 ===")
    
    try:
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer()
        print("✅ StockAnalyzer 初始化成功")
        
        # 测试基本功能
        stock_info = analyzer.get_stock_info('603316.SH')
        print(f"股票信息获取: {stock_info is not None}")
        
        # 测试快速分析
        result = analyzer.quick_analyze_stock('603316.SH', 'A')
        print(f"快速分析: {result is not None}")
        print(f"分析结果: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ StockAnalyzer 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_analyzer_init():
    """测试API分析器初始化"""
    print("\n=== 测试API分析器初始化 ===")
    
    try:
        from api_endpoints import analyzer, risk_monitor, fundamental_analyzer
        
        print(f"analyzer: {analyzer}")
        print(f"risk_monitor: {risk_monitor}")
        print(f"fundamental_analyzer: {fundamental_analyzer}")
        
        if analyzer is None:
            print("❌ analyzer 未初始化")
            
            # 尝试手动初始化
            from api_endpoints import init_analyzers
            from stock_analyzer import StockAnalyzer
            from risk_monitor import RiskMonitor
            from fundamental_analyzer import FundamentalAnalyzer
            
            test_analyzer = StockAnalyzer()
            test_risk_monitor = RiskMonitor(test_analyzer)
            test_fundamental_analyzer = FundamentalAnalyzer()
            
            init_analyzers(test_analyzer, test_risk_monitor, test_fundamental_analyzer)
            
            print("✅ 手动初始化完成")
            
            # 重新检查
            from api_endpoints import analyzer as new_analyzer
            print(f"重新检查 analyzer: {new_analyzer}")
            
        else:
            print("✅ analyzer 已初始化")
            
        return True
        
    except Exception as e:
        print(f"❌ API分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_integration():
    """测试API集成"""
    print("\n=== 测试API集成 ===")
    
    try:
        from api_integration import register_api_endpoints
        from flask import Flask
        
        # 创建测试应用
        app = Flask(__name__)
        
        # 模拟web_server中的分析器
        from stock_analyzer import StockAnalyzer
        from risk_monitor import RiskMonitor
        from fundamental_analyzer import FundamentalAnalyzer
        
        app.analyzer = StockAnalyzer()
        app.risk_monitor = RiskMonitor(app.analyzer)
        app.fundamental_analyzer = FundamentalAnalyzer()
        
        # 注册API端点
        success = register_api_endpoints(app)
        print(f"API端点注册: {'✅ 成功' if success else '❌ 失败'}")
        
        return success
        
    except Exception as e:
        print(f"❌ API集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🔍 开始分析器初始化测试")
    
    # 测试本地分析器
    local_ok = test_local_analyzer()
    
    # 测试API分析器初始化
    api_ok = test_api_analyzer_init()
    
    # 测试API集成
    integration_ok = test_api_integration()
    
    print(f"\n🎯 测试总结")
    print(f"本地分析器: {'✅ 正常' if local_ok else '❌ 异常'}")
    print(f"API分析器: {'✅ 正常' if api_ok else '❌ 异常'}")
    print(f"API集成: {'✅ 正常' if integration_ok else '❌ 异常'}")
    
    if all([local_ok, api_ok, integration_ok]):
        print("🎉 所有测试通过，分析器初始化正常")
    else:
        print("⚠️ 存在问题，需要进一步调试")

if __name__ == "__main__":
    main()
