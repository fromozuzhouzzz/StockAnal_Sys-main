# -*- coding: utf-8 -*-
"""
HF Spaces 部署验证脚本
验证股票分析系统在Hugging Face Spaces环境中的部署状态和性能
"""

import os
import sys
import time
import logging
import requests
import json
from datetime import datetime
from typing import Dict, List

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HFDeploymentVerifier:
    """HF Spaces部署验证器"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or "https://fromozu-stock-analysis.hf.space"
        self.api_key = "UZXJfw3YNX80DLfN"  # 测试用API密钥
        self.verification_results = {}
        
    def verify_environment(self):
        """验证环境配置"""
        logger.info("🔍 验证HF Spaces环境配置...")
        
        env_checks = {
            'hf_spaces_detected': any(os.getenv(var) for var in ['SPACE_ID', 'SPACE_AUTHOR_NAME', 'HF_HOME']),
            'port_configured': os.getenv('PORT') is not None,
            'database_config': os.getenv('USE_DATABASE', 'False').lower(),
            'redis_config': os.getenv('USE_REDIS_CACHE', 'False').lower(),
            'timeout_config': {
                'api_timeout': os.getenv('API_TIMEOUT', '30'),
                'analysis_timeout': os.getenv('ANALYSIS_TIMEOUT', '45'),
                'request_timeout': os.getenv('REQUEST_TIMEOUT', '60')
            }
        }
        
        self.verification_results['environment'] = env_checks
        
        logger.info(f"✅ 环境验证完成: HF Spaces {'已检测' if env_checks['hf_spaces_detected'] else '未检测'}")
        return env_checks
    
    def verify_api_endpoints(self):
        """验证API端点"""
        logger.info("🔍 验证API端点可用性...")
        
        endpoints = [
            {'path': '/', 'method': 'GET', 'name': '主页'},
            {'path': '/api/health', 'method': 'GET', 'name': '健康检查'},
            {'path': '/api/v1/stock/analyze', 'method': 'POST', 'name': '股票分析API'},
        ]
        
        api_results = {}
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint['path']}"
                
                if endpoint['method'] == 'GET':
                    response = requests.get(url, timeout=30)
                elif endpoint['method'] == 'POST':
                    # 测试股票分析API
                    headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
                    data = {'stock_code': '000001', 'analysis_depth': 'quick'}
                    response = requests.post(url, json=data, headers=headers, timeout=180)
                
                api_results[endpoint['name']] = {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'success': response.status_code == 200,
                    'url': url
                }
                
                logger.info(f"✅ {endpoint['name']}: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                
            except requests.exceptions.Timeout:
                api_results[endpoint['name']] = {
                    'error': 'timeout',
                    'success': False,
                    'url': url
                }
                logger.error(f"❌ {endpoint['name']}: 超时")
                
            except Exception as e:
                api_results[endpoint['name']] = {
                    'error': str(e),
                    'success': False,
                    'url': url
                }
                logger.error(f"❌ {endpoint['name']}: {e}")
        
        self.verification_results['api_endpoints'] = api_results
        return api_results
    
    def verify_performance_optimization(self):
        """验证性能优化效果"""
        logger.info("🔍 验证性能优化效果...")
        
        try:
            # 测试批量分析性能
            url = f"{self.base_url}/api/v1/batch/analyze"
            headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
            
            test_stocks = ['000001', '000002', '600036', '600519', '000858']
            data = {
                'stock_codes': test_stocks,
                'analysis_depth': 'quick',
                'min_score': 0
            }
            
            start_time = time.time()
            response = requests.post(url, json=data, headers=headers, timeout=300)
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                success_count = len(result_data.get('results', []))
                
                performance_metrics = {
                    'total_time': total_time,
                    'stocks_analyzed': success_count,
                    'avg_time_per_stock': total_time / max(success_count, 1),
                    'success_rate': success_count / len(test_stocks) * 100,
                    'optimization_effective': total_time < 120  # 期望2分钟内完成5只股票
                }
                
                logger.info(f"✅ 批量分析: {success_count}/{len(test_stocks)}只股票, 耗时{total_time:.2f}秒")
                
            else:
                performance_metrics = {
                    'error': f"HTTP {response.status_code}",
                    'response_text': response.text[:200]
                }
                logger.error(f"❌ 批量分析失败: {response.status_code}")
        
        except Exception as e:
            performance_metrics = {'error': str(e)}
            logger.error(f"❌ 性能测试失败: {e}")
        
        self.verification_results['performance'] = performance_metrics
        return performance_metrics
    
    def verify_timeout_handling(self):
        """验证超时处理"""
        logger.info("🔍 验证超时处理...")
        
        try:
            # 测试长时间分析任务
            url = f"{self.base_url}/api/v1/stock/analyze"
            headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
            data = {
                'stock_code': '000001',
                'analysis_depth': 'comprehensive',  # 使用复杂分析模式
                'include_ai_analysis': False
            }
            
            start_time = time.time()
            response = requests.post(url, json=data, headers=headers, timeout=200)
            response_time = time.time() - start_time
            
            timeout_results = {
                'response_time': response_time,
                'status_code': response.status_code,
                'timeout_handled': response_time < 180,  # 期望在180秒内完成
                'success': response.status_code == 200
            }
            
            if response.status_code == 200:
                logger.info(f"✅ 超时处理: 分析完成，耗时{response_time:.2f}秒")
            else:
                logger.warning(f"⚠️ 超时处理: HTTP {response.status_code}, 耗时{response_time:.2f}秒")
        
        except requests.exceptions.Timeout:
            timeout_results = {
                'error': 'timeout_exceeded',
                'timeout_handled': False
            }
            logger.error("❌ 超时处理: 请求超时")
        
        except Exception as e:
            timeout_results = {'error': str(e)}
            logger.error(f"❌ 超时测试失败: {e}")
        
        self.verification_results['timeout_handling'] = timeout_results
        return timeout_results
    
    def verify_error_handling(self):
        """验证错误处理"""
        logger.info("🔍 验证错误处理...")
        
        error_tests = [
            {
                'name': '无效股票代码',
                'data': {'stock_code': 'INVALID', 'analysis_depth': 'quick'},
                'expected_status': [400, 422, 200]  # 可能返回错误或包含错误信息的200
            },
            {
                'name': '缺少API密钥',
                'data': {'stock_code': '000001', 'analysis_depth': 'quick'},
                'headers': {},  # 不包含API密钥
                'expected_status': [401, 403]
            }
        ]
        
        error_results = {}
        
        for test in error_tests:
            try:
                url = f"{self.base_url}/api/v1/stock/analyze"
                headers = test.get('headers', {'X-API-Key': self.api_key, 'Content-Type': 'application/json'})
                
                response = requests.post(url, json=test['data'], headers=headers, timeout=30)
                
                error_results[test['name']] = {
                    'status_code': response.status_code,
                    'expected_status': test['expected_status'],
                    'handled_correctly': response.status_code in test['expected_status'],
                    'response_has_error_info': 'error' in response.text.lower()
                }
                
                status = "✅" if response.status_code in test['expected_status'] else "❌"
                logger.info(f"{status} {test['name']}: HTTP {response.status_code}")
                
            except Exception as e:
                error_results[test['name']] = {'error': str(e)}
                logger.error(f"❌ {test['name']}: {e}")
        
        self.verification_results['error_handling'] = error_results
        return error_results
    
    def run_full_verification(self):
        """运行完整验证"""
        logger.info("🚀 开始HF Spaces部署验证...")
        
        start_time = time.time()
        
        # 运行各项验证
        self.verify_environment()
        self.verify_api_endpoints()
        self.verify_performance_optimization()
        self.verify_timeout_handling()
        self.verify_error_handling()
        
        total_time = time.time() - start_time
        
        # 生成验证摘要
        self.verification_results['verification_summary'] = {
            'total_verification_time': total_time,
            'verification_timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'overall_status': self._calculate_overall_status()
        }
        
        logger.info(f"✅ 验证完成，总耗时: {total_time:.2f}秒")
        
        return self.verification_results
    
    def _calculate_overall_status(self):
        """计算总体状态"""
        critical_checks = [
            self.verification_results.get('api_endpoints', {}).get('主页', {}).get('success', False),
            self.verification_results.get('api_endpoints', {}).get('股票分析API', {}).get('success', False),
            self.verification_results.get('performance', {}).get('optimization_effective', False)
        ]
        
        if all(critical_checks):
            return 'healthy'
        elif any(critical_checks):
            return 'partial'
        else:
            return 'failed'
    
    def generate_report(self, filepath: str = None):
        """生成验证报告"""
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"hf_deployment_verification_{timestamp}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.verification_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 验证报告已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ 保存验证报告失败: {e}")
            return None


def main():
    """主函数"""
    print("🔧 HF Spaces 部署验证")
    print("=" * 50)
    
    # 创建验证器
    verifier = HFDeploymentVerifier()
    
    # 运行验证
    results = verifier.run_full_verification()
    
    # 生成报告
    report_file = verifier.generate_report()
    
    # 打印摘要
    print("\n📊 验证结果摘要:")
    print("=" * 50)
    
    summary = results.get('verification_summary', {})
    overall_status = summary.get('overall_status', 'unknown')
    
    status_emoji = {
        'healthy': '✅',
        'partial': '⚠️',
        'failed': '❌',
        'unknown': '❓'
    }
    
    print(f"总体状态: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")
    print(f"验证时间: {summary.get('total_verification_time', 0):.2f}秒")
    print(f"目标URL: {summary.get('base_url', 'N/A')}")
    
    if report_file:
        print(f"详细报告: {report_file}")
    
    # 显示关键指标
    if 'performance' in results:
        perf = results['performance']
        if 'total_time' in perf:
            print(f"\n🚀 性能指标:")
            print(f"  批量分析时间: {perf.get('total_time', 0):.2f}秒")
            print(f"  成功率: {perf.get('success_rate', 0):.1f}%")
            print(f"  平均每股时间: {perf.get('avg_time_per_stock', 0):.2f}秒")


if __name__ == "__main__":
    main()
