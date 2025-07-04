#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
替代方案批量股票分析程序
尝试不同的请求参数组合来避免API服务端错误
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class AlternativeBatchAnalyzer:
    """替代方案批量分析器"""
    
    def __init__(self):
        self.api_url = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
        self.api_key = "UZXJfw3YNX80DLfN"
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
        # 不同的请求参数组合
        self.request_variants = [
            {
                "name": "完整分析",
                "params": {
                    "analysis_depth": "full",
                    "include_ai_analysis": True
                }
            },
            {
                "name": "基础分析",
                "params": {
                    "analysis_depth": "basic",
                    "include_ai_analysis": False
                }
            },
            {
                "name": "简化分析",
                "params": {
                    "analysis_depth": "simple",
                    "include_ai_analysis": False
                }
            },
            {
                "name": "最小分析",
                "params": {}
            }
        ]
    
    def convert_stock_code(self, sec_id: str) -> str:
        """转换股票代码格式"""
        if pd.isna(sec_id) or not isinstance(sec_id, str):
            return ""
            
        if sec_id.endswith('.XSHE'):
            return sec_id.replace('.XSHE', '.SZ')
        elif sec_id.endswith('.XSHG'):
            return sec_id.replace('.XSHG', '.SH')
        else:
            return sec_id
    
    def test_api_variants(self, stock_code: str) -> Optional[Dict]:
        """测试不同的API请求参数组合"""
        print(f"   测试不同的请求参数组合...")
        
        for i, variant in enumerate(self.request_variants, 1):
            print(f"   尝试 {i}/{len(self.request_variants)}: {variant['name']}")
            
            # 构建请求参数
            payload = {
                "stock_code": stock_code,
                "market_type": "A"
            }
            payload.update(variant['params'])
            
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )
                
                print(f"     状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success', False):
                        print(f"     ✅ 成功! 使用参数: {variant['name']}")
                        return {
                            'success': True,
                            'data': result.get('data', {}),
                            'variant': variant['name'],
                            'params': variant['params']
                        }
                    else:
                        print(f"     ❌ API返回失败: {result.get('message', '未知错误')}")
                
                elif response.status_code == 500:
                    error_info = self._parse_500_error(response)
                    print(f"     ❌ 500错误: {error_info['message']}")
                
                else:
                    print(f"     ❌ HTTP错误: {response.status_code}")
                
            except Exception as e:
                print(f"     ❌ 异常: {e}")
            
            # 短暂延迟
            time.sleep(1)
        
        print(f"   ❌ 所有参数组合都失败")
        return None
    
    def _parse_500_error(self, response) -> Dict:
        """解析500错误的详细信息"""
        try:
            error_data = response.json()
            error_details = error_data.get('error', {})
            return {
                'message': error_details.get('message', '服务器内部错误'),
                'code': error_details.get('code', 'INTERNAL_SERVER_ERROR'),
                'details': error_details.get('details', {})
            }
        except:
            return {
                'message': '服务器内部错误（无法解析错误信息）',
                'code': 'PARSE_ERROR',
                'details': {}
            }
    
    def analyze_with_fallback(self, stock_code: str, original_code: str) -> Dict:
        """使用降级策略分析股票"""
        # 首先尝试标准请求
        standard_payload = {
            "stock_code": stock_code,
            "market_type": "A",
            "analysis_depth": "full",
            "include_ai_analysis": True
        }
        
        try:
            print(f"   尝试标准请求...")
            response = requests.post(
                self.api_url,
                json=standard_payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    print(f"   ✅ 标准请求成功")
                    return self._extract_success_data(result, original_code, stock_code, "标准分析")
            
            print(f"   ⚠️ 标准请求失败 (状态码: {response.status_code})")
            
        except Exception as e:
            print(f"   ⚠️ 标准请求异常: {e}")
        
        # 如果标准请求失败，尝试其他参数组合
        variant_result = self.test_api_variants(stock_code)
        if variant_result and variant_result['success']:
            return self._extract_success_data(
                {'data': variant_result['data']}, 
                original_code, 
                stock_code, 
                variant_result['variant']
            )
        
        # 所有尝试都失败，返回失败记录
        return self._create_failed_record(original_code, stock_code, "所有API请求都失败")
    
    def _extract_success_data(self, result: Dict, original_code: str, 
                            converted_code: str, analysis_type: str) -> Dict:
        """从成功的API响应中提取数据"""
        try:
            data = result.get('data', {})
            basic_info = data.get('basic_info', {})
            scores = data.get('scores', {})
            risk_assessment = data.get('risk_assessment', {})
            
            return {
                'original_code': original_code,
                'converted_code': converted_code,
                'stock_name': basic_info.get('name', ''),
                'current_price': basic_info.get('current_price', 0),
                'change_percent': basic_info.get('change_percent', 0),
                'overall_score': scores.get('overall_score', 0),
                'technical_score': scores.get('technical_score', 0),
                'fundamental_score': scores.get('fundamental_score', 0),
                'risk_score': scores.get('risk_score', 0),
                'risk_level': risk_assessment.get('risk_level', ''),
                'analysis_type': analysis_type,
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }
        except Exception as e:
            print(f"   ⚠️ 数据提取失败: {e}")
            return self._create_failed_record(original_code, converted_code, f"数据提取失败: {str(e)}")
    
    def _create_failed_record(self, original_code: str, converted_code: str, error_msg: str) -> Dict:
        """创建失败记录"""
        return {
            'original_code': original_code,
            'converted_code': converted_code,
            'stock_name': '分析失败',
            'current_price': 0,
            'change_percent': 0,
            'overall_score': 0,
            'technical_score': 0,
            'fundamental_score': 0,
            'risk_score': 0,
            'risk_level': '未知',
            'analysis_type': '失败',
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'failed',
            'error_message': error_msg
        }
    
    def process_csv_file(self, csv_file: str) -> bool:
        """处理CSV文件"""
        print(f"=== 替代方案批量股票分析程序 ===")
        print(f"开始时间: {datetime.now()}")
        print(f"策略: 尝试多种请求参数组合")
        
        # 读取CSV文件
        try:
            df = pd.read_csv(csv_file)
            print(f"✅ 成功读取CSV文件: {len(df)} 行")
            
            if 'secID' not in df.columns:
                print("❌ 错误: 未找到 'secID' 列")
                return False
            
            stocks = df[df['secID'].notna() & (df['secID'] != '')]['secID'].tolist()
            print(f"有效股票代码: {len(stocks)} 个")
            
        except Exception as e:
            print(f"❌ CSV文件读取失败: {e}")
            return False
        
        if not stocks:
            print("❌ 未找到有效的股票代码")
            return False
        
        # 批量分析
        print(f"\n开始批量分析...")
        results = []
        success_count = 0
        
        for i, original_code in enumerate(stocks, 1):
            print(f"\n[{i}/{len(stocks)}] 处理: {original_code}")
            
            # 转换代码
            converted_code = self.convert_stock_code(original_code)
            print(f"   转换为: {converted_code}")
            
            if not converted_code:
                print("   ❌ 代码转换失败")
                results.append(self._create_failed_record(original_code, "", "代码转换失败"))
                continue
            
            # 分析股票
            result = self.analyze_with_fallback(converted_code, original_code)
            results.append(result)
            
            # 显示结果
            if result['status'] == 'success':
                success_count += 1
                print(f"   ✅ 成功 - 类型: {result['analysis_type']}, 评分: {result['overall_score']}")
            else:
                print(f"   ❌ 失败 - {result['error_message']}")
            
            # 延迟避免限流
            if i < len(stocks):
                time.sleep(3)  # 增加延迟
        
        # 保存结果
        self._save_results(results)
        
        # 显示统计
        total = len(results)
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        print(f"\n=== 分析完成 ===")
        print(f"总股票数: {total}")
        print(f"成功: {success_count}")
        print(f"失败: {total - success_count}")
        print(f"成功率: {success_rate:.1f}%")
        
        return True
    
    def _save_results(self, results: List[Dict]):
        """保存分析结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存所有结果
        output_file = f"alternative_batch_analysis_{timestamp}.csv"
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 结果已保存: {output_file}")
        
        # 分析成功的分析类型
        success_results = [r for r in results if r['status'] == 'success']
        if success_results:
            analysis_types = {}
            for r in success_results:
                analysis_type = r.get('analysis_type', '未知')
                analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1
            
            print(f"\n📊 成功分析类型统计:")
            for analysis_type, count in analysis_types.items():
                print(f"   {analysis_type}: {count} 只股票")

def main():
    """主函数"""
    analyzer = AlternativeBatchAnalyzer()
    
    # 检查CSV文件
    csv_file = "list3.csv"
    if not pd.io.common.file_exists(csv_file):
        print(f"❌ CSV文件不存在: {csv_file}")
        return
    
    # 开始分析
    success = analyzer.process_csv_file(csv_file)
    
    if success:
        print(f"\n🎉 替代方案分析完成!")
    else:
        print(f"\n❌ 替代方案分析失败!")

if __name__ == "__main__":
    main()
