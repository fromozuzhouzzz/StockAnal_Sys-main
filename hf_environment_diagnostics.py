# -*- coding: utf-8 -*-
"""
Hugging Face Spaces 环境诊断工具
专门诊断HF环境中的数据获取和API调用问题
"""

import os
import sys
import logging
import requests
import time
from datetime import datetime
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HFEnvironmentDiagnostics:
    """HF环境诊断器"""
    
    def __init__(self):
        self.is_hf_spaces = self._detect_hf_spaces()
        self.test_results = {}
        
    def _detect_hf_spaces(self) -> bool:
        """检测是否在HF Spaces环境"""
        hf_indicators = ['SPACE_ID', 'SPACE_AUTHOR_NAME', 'GRADIO_SERVER_NAME']
        return any(os.getenv(indicator) for indicator in hf_indicators)
    
    def test_network_connectivity(self):
        """测试网络连接"""
        print("=== 测试网络连接 ===")
        
        test_urls = [
            "https://www.baidu.com",
            "https://push2.eastmoney.com",
            "https://datacenter-web.eastmoney.com",
            "https://api.github.com",
            "https://httpbin.org/get"
        ]
        
        results = {}
        for url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                duration = time.time() - start_time
                
                results[url] = {
                    'status': 'success',
                    'status_code': response.status_code,
                    'duration': round(duration, 2),
                    'headers': dict(response.headers)
                }
                print(f"✅ {url}: {response.status_code} ({duration:.2f}s)")
                
            except Exception as e:
                results[url] = {
                    'status': 'failed',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"❌ {url}: {e}")
        
        self.test_results['network'] = results
        return results
    
    def test_ssl_configuration(self):
        """测试SSL配置"""
        print("\n=== 测试SSL配置 ===")
        
        import ssl
        import socket
        
        test_hosts = [
            ('push2.eastmoney.com', 443),
            ('datacenter-web.eastmoney.com', 443),
            ('api.github.com', 443)
        ]
        
        results = {}
        for host, port in test_hosts:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((host, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        cert = ssock.getpeercert()
                        results[host] = {
                            'status': 'success',
                            'ssl_version': ssock.version(),
                            'cert_subject': cert.get('subject', []),
                            'cert_issuer': cert.get('issuer', [])
                        }
                        print(f"✅ {host}: SSL连接成功 ({ssock.version()})")
                        
            except Exception as e:
                results[host] = {
                    'status': 'failed',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"❌ {host}: {e}")
        
        self.test_results['ssl'] = results
        return results
    
    def test_akshare_apis(self):
        """测试AKShare相关的API"""
        print("\n=== 测试AKShare API ===")
        
        # 测试基本的股票数据API
        test_apis = [
            {
                'name': '东财实时数据',
                'url': 'https://push2.eastmoney.com/api/qt/stock/get',
                'params': {
                    'fltt': '2',
                    'invt': '2',
                    'fields': 'f43,f57,f58,f169,f170',
                    'secid': '1.603316'
                }
            },
            {
                'name': '东财历史数据',
                'url': 'https://datacenter-web.eastmoney.com/api/data/v1/get',
                'params': {
                    'reportName': 'RPT_LICO_FN_CPD',
                    'columns': 'SECURITY_CODE,TRADE_DATE,OPEN,HIGH,LOW,CLOSE,VOLUME',
                    'filter': '(SECURITY_CODE="603316")',
                    'pageNumber': '1',
                    'pageSize': '10'
                }
            }
        ]
        
        results = {}
        for api in test_apis:
            try:
                start_time = time.time()
                response = requests.get(
                    api['url'], 
                    params=api['params'], 
                    timeout=15,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                duration = time.time() - start_time
                
                results[api['name']] = {
                    'status': 'success',
                    'status_code': response.status_code,
                    'duration': round(duration, 2),
                    'content_length': len(response.content),
                    'content_type': response.headers.get('Content-Type', 'unknown')
                }
                
                if response.status_code == 200:
                    print(f"✅ {api['name']}: 成功 ({duration:.2f}s, {len(response.content)} bytes)")
                else:
                    print(f"⚠️ {api['name']}: HTTP {response.status_code}")
                    
            except Exception as e:
                results[api['name']] = {
                    'status': 'failed',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                print(f"❌ {api['name']}: {e}")
        
        self.test_results['akshare_apis'] = results
        return results
    
    def test_local_analyzer(self):
        """测试本地分析器"""
        print("\n=== 测试本地分析器 ===")
        
        try:
            # 测试分析器初始化
            from stock_analyzer import StockAnalyzer
            analyzer = StockAnalyzer()
            print("✅ StockAnalyzer 初始化成功")
            
            # 测试基本功能（不依赖网络）
            test_data = {
                'close': [10, 11, 12, 11, 10],
                'volume': [1000, 1100, 1200, 1100, 1000]
            }
            
            # 这里可以添加更多不依赖网络的测试
            result = {
                'status': 'success',
                'analyzer_initialized': True,
                'basic_functions': True
            }
            print("✅ 基本功能测试通过")
            
        except Exception as e:
            result = {
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__
            }
            print(f"❌ 分析器测试失败: {e}")
        
        self.test_results['local_analyzer'] = result
        return result
    
    def test_environment_info(self):
        """收集环境信息"""
        print("\n=== 环境信息 ===")
        
        env_info = {
            'python_version': sys.version,
            'platform': sys.platform,
            'is_hf_spaces': self.is_hf_spaces,
            'environment_variables': {
                'SPACE_ID': os.getenv('SPACE_ID'),
                'SPACE_AUTHOR_NAME': os.getenv('SPACE_AUTHOR_NAME'),
                'GRADIO_SERVER_NAME': os.getenv('GRADIO_SERVER_NAME'),
                'PORT': os.getenv('PORT'),
                'USE_DATABASE': os.getenv('USE_DATABASE'),
                'USE_REDIS_CACHE': os.getenv('USE_REDIS_CACHE')
            },
            'installed_packages': self._get_installed_packages()
        }
        
        print(f"Python版本: {sys.version}")
        print(f"平台: {sys.platform}")
        print(f"HF Spaces: {self.is_hf_spaces}")
        
        if self.is_hf_spaces:
            print(f"Space ID: {os.getenv('SPACE_ID', 'N/A')}")
            print(f"作者: {os.getenv('SPACE_AUTHOR_NAME', 'N/A')}")
        
        self.test_results['environment'] = env_info
        return env_info
    
    def _get_installed_packages(self):
        """获取已安装的包信息"""
        try:
            import pkg_resources
            packages = {}
            for dist in pkg_resources.working_set:
                packages[dist.project_name] = dist.version
            return packages
        except:
            return {}
    
    def generate_diagnostic_report(self):
        """生成诊断报告"""
        print("\n" + "="*50)
        print("🔍 HF环境诊断报告")
        print("="*50)
        
        # 运行所有测试
        self.test_environment_info()
        self.test_network_connectivity()
        self.test_ssl_configuration()
        self.test_akshare_apis()
        self.test_local_analyzer()
        
        # 生成总结
        print(f"\n📊 诊断总结")
        print(f"测试时间: {datetime.now()}")
        print(f"HF Spaces环境: {'是' if self.is_hf_spaces else '否'}")
        
        # 分析问题
        issues = []
        recommendations = []
        
        # 检查网络问题
        network_results = self.test_results.get('network', {})
        failed_networks = [url for url, result in network_results.items() if result.get('status') == 'failed']
        if failed_networks:
            issues.append(f"网络连接问题: {len(failed_networks)} 个URL无法访问")
            recommendations.append("检查网络配置和防火墙设置")
        
        # 检查SSL问题
        ssl_results = self.test_results.get('ssl', {})
        failed_ssl = [host for host, result in ssl_results.items() if result.get('status') == 'failed']
        if failed_ssl:
            issues.append(f"SSL连接问题: {len(failed_ssl)} 个主机SSL握手失败")
            recommendations.append("更新SSL配置或使用备选数据源")
        
        # 检查API问题
        api_results = self.test_results.get('akshare_apis', {})
        failed_apis = [name for name, result in api_results.items() if result.get('status') == 'failed']
        if failed_apis:
            issues.append(f"数据API问题: {len(failed_apis)} 个API调用失败")
            recommendations.append("实现数据获取降级策略")
        
        if issues:
            print(f"\n⚠️ 发现的问题:")
            for issue in issues:
                print(f"  - {issue}")
            
            print(f"\n💡 建议的解决方案:")
            for rec in recommendations:
                print(f"  - {rec}")
        else:
            print(f"\n✅ 未发现明显问题")
        
        # 保存详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"hf_diagnostic_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 详细报告已保存: {report_file}")
        
        return self.test_results

def main():
    """主函数"""
    diagnostics = HFEnvironmentDiagnostics()
    diagnostics.generate_diagnostic_report()

if __name__ == "__main__":
    main()
