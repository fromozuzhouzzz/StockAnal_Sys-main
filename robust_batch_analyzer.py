#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健壮的批量股票分析程序
专门处理API服务端错误，提供多种降级策略
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
import sys
from typing import Dict, List, Optional

class RobustBatchAnalyzer:
    """健壮的批量股票分析器"""
    
    def __init__(self):
        self.api_url = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
        self.api_key = "UZXJfw3YNX80DLfN"
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        
        # 配置参数
        self.timeout = 60
        self.max_retries = 3
        self.retry_delay = 3
        self.request_delay = 2  # 请求间隔
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'server_error_500': 0,
            'network_error': 0,
            'timeout_error': 0,
            'other_error': 0
        }
    
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
    
    def analyze_single_stock(self, stock_code: str, original_code: str) -> Dict:
        """分析单只股票，包含完善的错误处理"""
        self.stats['total'] += 1
        
        payload = {
            "stock_code": stock_code,
            "market_type": "A",
            "analysis_depth": "full",
            "include_ai_analysis": True
        }
        
        for attempt in range(self.max_retries):
            try:
                print(f"   尝试 {attempt + 1}/{self.max_retries}: {stock_code}")
                
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success', False):
                        self.stats['success'] += 1
                        return self._extract_success_data(result, original_code, stock_code)
                    else:
                        error_msg = result.get('message', '未知错误')
                        print(f"   ❌ API返回失败: {error_msg}")
                        return self._create_failed_record(original_code, stock_code, f"API失败: {error_msg}")
                
                elif response.status_code == 500:
                    self.stats['server_error_500'] += 1
                    error_info = self._parse_500_error(response)
                    print(f"   ⚠️ 服务器错误 (500): {error_info['message']}")
                    
                    # 对于500错误，不重试，直接返回错误记录
                    return self._create_failed_record(
                        original_code, stock_code, 
                        f"服务器内部错误: {error_info['message']}", 
                        error_type="server_error_500"
                    )
                
                else:
                    print(f"   ❌ HTTP错误: {response.status_code}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        self.stats['other_error'] += 1
                        return self._create_failed_record(
                            original_code, stock_code, 
                            f"HTTP {response.status_code}"
                        )
                
            except requests.exceptions.Timeout:
                self.stats['timeout_error'] += 1
                print(f"   ⏰ 请求超时")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return self._create_failed_record(original_code, stock_code, "请求超时")
                    
            except requests.exceptions.ConnectionError:
                self.stats['network_error'] += 1
                print(f"   🌐 网络连接错误")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return self._create_failed_record(original_code, stock_code, "网络连接错误")
                    
            except Exception as e:
                self.stats['other_error'] += 1
                print(f"   ❌ 未知异常: {e}")
                return self._create_failed_record(original_code, stock_code, f"异常: {str(e)}")
        
        # 如果所有重试都失败了
        return self._create_failed_record(original_code, stock_code, "所有重试都失败")
    
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
    
    def _extract_success_data(self, result: Dict, original_code: str, converted_code: str) -> Dict:
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
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }
        except Exception as e:
            print(f"   ⚠️ 数据提取失败: {e}")
            return self._create_failed_record(original_code, converted_code, f"数据提取失败: {str(e)}")
    
    def _create_failed_record(self, original_code: str, converted_code: str, 
                            error_msg: str, error_type: str = "unknown") -> Dict:
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
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'failed',
            'error_message': error_msg,
            'error_type': error_type
        }
    
    def process_csv_file(self, csv_file: str) -> bool:
        """处理CSV文件"""
        print(f"=== 健壮的批量股票分析程序 ===")
        print(f"开始时间: {datetime.now()}")
        print(f"API地址: {self.api_url}")
        
        # 1. 读取CSV文件
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
        
        # 2. 批量分析
        print(f"\n开始批量分析...")
        results = []
        
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
            result = self.analyze_single_stock(converted_code, original_code)
            results.append(result)
            
            # 显示结果
            if result['status'] == 'success':
                print(f"   ✅ 成功 - 评分: {result['overall_score']}")
            else:
                print(f"   ❌ 失败 - {result['error_message']}")
            
            # 延迟避免限流
            if i < len(stocks):
                time.sleep(self.request_delay)
        
        # 3. 保存结果
        self._save_results(results)
        
        # 4. 显示统计信息
        self._print_statistics()
        
        return True
    
    def _save_results(self, results: List[Dict]):
        """保存分析结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存所有结果
        all_results_file = f"robust_batch_analysis_all_{timestamp}.csv"
        results_df = pd.DataFrame(results)
        results_df.to_csv(all_results_file, index=False, encoding='utf-8-sig')
        print(f"\n✅ 所有结果已保存: {all_results_file}")
        
        # 分别保存成功和失败的结果
        success_results = [r for r in results if r['status'] == 'success']
        failed_results = [r for r in results if r['status'] == 'failed']
        
        if success_results:
            success_file = f"robust_batch_analysis_success_{timestamp}.csv"
            success_df = pd.DataFrame(success_results)
            success_df.to_csv(success_file, index=False, encoding='utf-8-sig')
            print(f"✅ 成功结果已保存: {success_file}")
        
        if failed_results:
            failed_file = f"robust_batch_analysis_failed_{timestamp}.csv"
            failed_df = pd.DataFrame(failed_results)
            failed_df.to_csv(failed_file, index=False, encoding='utf-8-sig')
            print(f"❌ 失败结果已保存: {failed_file}")
    
    def _print_statistics(self):
        """打印统计信息"""
        total = self.stats['total']
        success = self.stats['success']
        success_rate = (success / total * 100) if total > 0 else 0
        
        print(f"\n=== 分析统计 ===")
        print(f"总股票数: {total}")
        print(f"成功: {success}")
        print(f"失败: {total - success}")
        print(f"成功率: {success_rate:.1f}%")
        
        print(f"\n=== 错误分类 ===")
        print(f"服务器错误 (500): {self.stats['server_error_500']}")
        print(f"网络错误: {self.stats['network_error']}")
        print(f"超时错误: {self.stats['timeout_error']}")
        print(f"其他错误: {self.stats['other_error']}")
        
        print(f"\n=== 建议 ===")
        if self.stats['server_error_500'] > 0:
            print("⚠️ 检测到服务器内部错误，这是API服务端的问题")
            print("💡 建议: 联系API服务提供方修复服务端bug")
        
        if self.stats['network_error'] > 0:
            print("🌐 检测到网络连接问题")
            print("💡 建议: 检查网络连接稳定性")
        
        if self.stats['timeout_error'] > 0:
            print("⏰ 检测到超时问题")
            print("💡 建议: 增加超时时间或减少并发请求")

def main():
    """主函数"""
    analyzer = RobustBatchAnalyzer()
    
    # 检查CSV文件
    csv_file = "list3.csv"
    if not pd.io.common.file_exists(csv_file):
        print(f"❌ CSV文件不存在: {csv_file}")
        return
    
    # 开始分析
    success = analyzer.process_csv_file(csv_file)
    
    if success:
        print(f"\n🎉 批量分析完成!")
    else:
        print(f"\n❌ 批量分析失败!")

if __name__ == "__main__":
    main()
