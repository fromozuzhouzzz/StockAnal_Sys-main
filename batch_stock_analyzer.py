#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量股票分析程序
读取CSV文件中的股票代码，调用股票分析API，并保存分析结果
"""

import pandas as pd
import requests
import json
import time
import os
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatchStockAnalyzer:
    """批量股票分析器"""
    
    def __init__(self, api_url: str, api_key: str):
        """
        初始化分析器
        
        Args:
            api_url: API接口地址
            api_key: API密钥
        """
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        })
        
        # 请求配置
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 2
        
    def convert_stock_code(self, sec_id: str) -> str:
        """
        转换股票代码格式
        
        Args:
            sec_id: 原始股票代码 (如: 000001.XSHE, 600000.XSHG)
            
        Returns:
            转换后的股票代码 (如: 000001.SZ, 600000.SH)
        """
        if pd.isna(sec_id) or not isinstance(sec_id, str):
            return ""
            
        if sec_id.endswith('.XSHE'):
            return sec_id.replace('.XSHE', '.SZ')
        elif sec_id.endswith('.XSHG'):
            return sec_id.replace('.XSHG', '.SH')
        else:
            logger.warning(f"未知的股票代码格式: {sec_id}")
            return sec_id
    
    def analyze_single_stock(self, stock_code: str) -> Optional[Dict]:
        """
        分析单只股票
        
        Args:
            stock_code: 股票代码
            
        Returns:
            分析结果字典，失败时返回None
        """
        payload = {
            "stock_code": stock_code,
            "market_type": "A",
            "analysis_depth": "full",
            "include_ai_analysis": True
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"正在分析股票 {stock_code} (尝试 {attempt + 1}/{self.max_retries})")
                
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success', False):
                        logger.info(f"股票 {stock_code} 分析成功")
                        return result.get('data', {})
                    else:
                        logger.error(f"股票 {stock_code} 分析失败: {result.get('message', '未知错误')}")
                        return None
                else:
                    logger.error(f"股票 {stock_code} API请求失败: HTTP {response.status_code}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                logger.error(f"股票 {stock_code} 请求超时")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"股票 {stock_code} 请求异常: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return None
                
            except Exception as e:
                logger.error(f"股票 {stock_code} 分析出现未知错误: {str(e)}")
                return None
        
        return None
    
    def extract_key_metrics(self, analysis_data: Dict, original_code: str, converted_code: str) -> Dict:
        """
        提取关键分析指标
        
        Args:
            analysis_data: API返回的分析数据
            original_code: 原始股票代码
            converted_code: 转换后的股票代码
            
        Returns:
            提取的关键指标字典
        """
        metrics = {
            'original_code': original_code,
            'converted_code': converted_code,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 提取基本信息
        basic_info = analysis_data.get('basic_info', {})
        metrics.update({
            'stock_name': basic_info.get('name', ''),
            'current_price': basic_info.get('current_price', 0),
            'change_percent': basic_info.get('change_percent', 0)
        })
        
        # 提取评分信息
        scores = analysis_data.get('scores', {})
        metrics.update({
            'overall_score': scores.get('overall_score', 0),
            'technical_score': scores.get('technical_score', 0),
            'fundamental_score': scores.get('fundamental_score', 0),
            'risk_score': scores.get('risk_score', 0)
        })
        
        # 提取风险评估
        risk_assessment = analysis_data.get('risk_assessment', {})
        metrics.update({
            'risk_level': risk_assessment.get('risk_level', ''),
            'volatility': risk_assessment.get('volatility', 0),
            'beta': risk_assessment.get('beta', 0)
        })
        
        # 提取技术分析
        technical = analysis_data.get('technical_analysis', {})
        metrics.update({
            'trend': technical.get('trend', ''),
            'support_level': technical.get('support_level', 0),
            'resistance_level': technical.get('resistance_level', 0)
        })
        
        # 提取基本面分析
        fundamental = analysis_data.get('fundamental_analysis', {})
        metrics.update({
            'pe_ratio': fundamental.get('pe_ratio', 0),
            'pb_ratio': fundamental.get('pb_ratio', 0),
            'roe': fundamental.get('roe', 0),
            'debt_ratio': fundamental.get('debt_ratio', 0)
        })
        
        # 提取AI分析结论
        ai_analysis = analysis_data.get('ai_analysis', {})
        metrics.update({
            'ai_recommendation': ai_analysis.get('recommendation', ''),
            'ai_confidence': ai_analysis.get('confidence', 0),
            'ai_summary': ai_analysis.get('summary', '')
        })
        
        return metrics

    def process_csv_file(self, csv_file_path: str, output_file_path: str = None) -> bool:
        """
        处理CSV文件中的所有股票

        Args:
            csv_file_path: 输入CSV文件路径
            output_file_path: 输出CSV文件路径，默认为 'batch_analysis_results.csv'

        Returns:
            处理是否成功
        """
        if output_file_path is None:
            output_file_path = f'batch_analysis_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        try:
            # 读取CSV文件
            logger.info(f"正在读取CSV文件: {csv_file_path}")
            df = pd.read_csv(csv_file_path)

            if 'secID' not in df.columns:
                logger.error("CSV文件中未找到 'secID' 列")
                return False

            # 过滤有效的股票代码
            valid_stocks = df[df['secID'].notna() & (df['secID'] != '')]['secID'].tolist()
            logger.info(f"找到 {len(valid_stocks)} 只有效股票")

            if not valid_stocks:
                logger.error("未找到有效的股票代码")
                return False

            # 批量分析
            results = []
            failed_stocks = []

            with tqdm(total=len(valid_stocks), desc="分析进度") as pbar:
                for original_code in valid_stocks:
                    # 转换股票代码
                    converted_code = self.convert_stock_code(original_code)

                    if not converted_code:
                        logger.warning(f"跳过无效股票代码: {original_code}")
                        failed_stocks.append({
                            'original_code': original_code,
                            'error': '无效的股票代码格式'
                        })
                        pbar.update(1)
                        continue

                    # 分析股票
                    analysis_data = self.analyze_single_stock(converted_code)

                    if analysis_data:
                        # 提取关键指标
                        metrics = self.extract_key_metrics(analysis_data, original_code, converted_code)
                        results.append(metrics)
                    else:
                        failed_stocks.append({
                            'original_code': original_code,
                            'converted_code': converted_code,
                            'error': 'API分析失败'
                        })

                    pbar.update(1)

                    # 添加延迟避免API限流
                    time.sleep(0.5)

            # 保存结果
            if results:
                results_df = pd.DataFrame(results)
                results_df.to_csv(output_file_path, index=False, encoding='utf-8-sig')
                logger.info(f"分析结果已保存到: {output_file_path}")
                logger.info(f"成功分析 {len(results)} 只股票")

            # 保存失败记录
            if failed_stocks:
                failed_df = pd.DataFrame(failed_stocks)
                failed_file = output_file_path.replace('.csv', '_failed.csv')
                failed_df.to_csv(failed_file, index=False, encoding='utf-8-sig')
                logger.warning(f"失败记录已保存到: {failed_file}")
                logger.warning(f"失败 {len(failed_stocks)} 只股票")

            # 生成分析报告
            self.generate_summary_report(len(valid_stocks), len(results), len(failed_stocks), output_file_path)

            return True

        except Exception as e:
            logger.error(f"处理CSV文件时出现错误: {str(e)}")
            return False

    def generate_summary_report(self, total: int, success: int, failed: int, output_file: str):
        """生成分析摘要报告"""
        success_rate = (success / total * 100) if total > 0 else 0

        report = f"""
=== 批量股票分析报告 ===
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总股票数: {total}
成功分析: {success}
分析失败: {failed}
成功率: {success_rate:.2f}%
结果文件: {output_file}
========================
"""

        logger.info(report)

        # 保存报告到文件
        report_file = output_file.replace('.csv', '_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)


def main():
    """主函数"""
    # 配置参数
    API_URL = "https://fromozu-stock-analysis.hf.space/api/v1/stock/analyze"
    API_KEY = "UZXJfw3YNX80DLfN"
    CSV_FILE_PATH = "list3.csv"

    # 检查CSV文件是否存在
    if not os.path.exists(CSV_FILE_PATH):
        logger.error(f"CSV文件不存在: {CSV_FILE_PATH}")
        return

    # 创建分析器
    analyzer = BatchStockAnalyzer(API_URL, API_KEY)

    # 开始批量分析
    logger.info("开始批量股票分析...")
    success = analyzer.process_csv_file(CSV_FILE_PATH)

    if success:
        logger.info("批量分析完成!")
    else:
        logger.error("批量分析失败!")


if __name__ == "__main__":
    main()
