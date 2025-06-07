# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - 股票市场数据分析系统
开发者：熊猫大侠
版本：v2.1.0
许可证：MIT License
"""
# scenario_predictor.py
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import openai
import logging
from logging.handlers import RotatingFileHandler
"""

"""

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ScenarioPredictor:
    def __init__(self, analyzer, openai_api_key=None, openai_model=None):
        self.analyzer = analyzer
        self.openai_api_key = os.getenv('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
        self.openai_api_url = os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1')
        self.openai_model = os.getenv('OPENAI_API_MODEL', 'gemini-2.0-pro-exp-02-05')
        # logging.info(f"scenario_predictor初始化完成：「{self.openai_api_key} {self.openai_api_url} {self.openai_model}」")

    def generate_scenarios(self, stock_code, market_type='A', days=60):
        """生成乐观、中性、悲观三种市场情景预测"""
        try:
            # 获取股票数据和技术指标
            df = self.analyzer.get_stock_data(stock_code, market_type)
            df = self.analyzer.calculate_indicators(df)

            # 获取股票信息
            stock_info = self.analyzer.get_stock_info(stock_code)

            # 计算基础数据
            current_price = df.iloc[-1]['close']
            avg_volatility = df['Volatility'].mean()

            # 根据历史波动率计算情景
            scenarios = self._calculate_scenarios(df, days)

            # 使用AI生成各情景的分析
            if self.openai_api_key:
                ai_analysis = self._generate_ai_analysis(stock_code, stock_info, df, scenarios)
                scenarios.update(ai_analysis)

            # logging.info(f"返回前的情景预测：{scenarios}")
            return scenarios
        except Exception as e:
            # logging.info(f"生成情景预测出错: {str(e)}")
            return {}

    def _calculate_scenarios(self, df, days):
        """基于历史数据计算三种情景的价格预测"""
        current_price = df.iloc[-1]['close']

        # 计算历史波动率和移动均线
        volatility = df['Volatility'].mean() / 100  # 转换为小数
        daily_volatility = volatility / np.sqrt(252)  # 转换为日波动率
        ma20 = df.iloc[-1]['MA20']
        ma60 = df.iloc[-1]['MA60']

        # 计算乐观情景（上涨至压力位或突破）
        optimistic_return = 0.15  # 15%上涨
        if df.iloc[-1]['BB_upper'] > current_price:
            optimistic_target = df.iloc[-1]['BB_upper'] * 1.05  # 突破上轨5%
        else:
            optimistic_target = current_price * (1 + optimistic_return)

        # 计算中性情景（震荡，围绕当前价格或20日均线波动）
        neutral_target = (current_price + ma20) / 2

        # 计算悲观情景（下跌至支撑位或跌破）
        pessimistic_return = -0.12  # 12%下跌
        if df.iloc[-1]['BB_lower'] < current_price:
            pessimistic_target = df.iloc[-1]['BB_lower'] * 0.95  # 跌破下轨5%
        else:
            pessimistic_target = current_price * (1 + pessimistic_return)

        # 计算预期时间
        time_periods = np.arange(1, days + 1)

        # 生成乐观路径
        opt_path = [current_price]
        for _ in range(days):
            daily_return = (optimistic_target / current_price) ** (1 / days) - 1
            random_component = np.random.normal(0, daily_volatility)
            new_price = opt_path[-1] * (1 + daily_return + random_component / 2)
            opt_path.append(new_price)

        # 生成中性路径
        neu_path = [current_price]
        for _ in range(days):
            daily_return = (neutral_target / current_price) ** (1 / days) - 1
            random_component = np.random.normal(0, daily_volatility)
            new_price = neu_path[-1] * (1 + daily_return + random_component)
            neu_path.append(new_price)

        # 生成悲观路径
        pes_path = [current_price]
        for _ in range(days):
            daily_return = (pessimistic_target / current_price) ** (1 / days) - 1
            random_component = np.random.normal(0, daily_volatility)
            new_price = pes_path[-1] * (1 + daily_return + random_component / 2)
            pes_path.append(new_price)

        # 生成日期序列
        start_date = datetime.now()
        dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days + 1)]

        # 组织结果
        return {
            'current_price': current_price,
            'optimistic': {
                'target_price': optimistic_target,
                'change_percent': (optimistic_target / current_price - 1) * 100,
                'path': dict(zip(dates, opt_path))
            },
            'neutral': {
                'target_price': neutral_target,
                'change_percent': (neutral_target / current_price - 1) * 100,
                'path': dict(zip(dates, neu_path))
            },
            'pessimistic': {
                'target_price': pessimistic_target,
                'change_percent': (pessimistic_target / current_price - 1) * 100,
                'path': dict(zip(dates, pes_path))
            }
        }

    def _generate_ai_analysis(self, stock_code, stock_info, df, scenarios):
        """使用AI生成各情景的分析说明，包含风险和机会因素"""
        try:
            openai.api_key = self.openai_api_key
            openai.api_base = self.openai_api_url
    
            # 提取关键数据
            current_price = df.iloc[-1]['close']
            ma5 = df.iloc[-1]['MA5']
            ma20 = df.iloc[-1]['MA20']
            ma60 = df.iloc[-1]['MA60']
            rsi = df.iloc[-1]['RSI']
            macd = df.iloc[-1]['MACD']
            signal = df.iloc[-1]['Signal']
    
            # 构建提示词，增加对风险和机会因素的要求
            prompt = f"""分析股票{stock_code}（{stock_info.get('股票名称', '未知')}）的三种市场情景:
    
    1. 当前数据:
    - 当前价格: {current_price}
    - 均线: MA5={ma5}, MA20={ma20}, MA60={ma60}
    - RSI: {rsi}
    - MACD: {macd}, Signal: {signal}
    
    2. 预测目标价:
    - 乐观情景: {scenarios['optimistic']['target_price']:.2f} ({scenarios['optimistic']['change_percent']:.2f}%)
    - 中性情景: {scenarios['neutral']['target_price']:.2f} ({scenarios['neutral']['change_percent']:.2f}%)
    - 悲观情景: {scenarios['pessimistic']['target_price']:.2f} ({scenarios['pessimistic']['change_percent']:.2f}%)
    
    请提供以下内容，格式为JSON:
    {{
    "optimistic_analysis": "乐观情景分析(100字以内)...",
    "neutral_analysis": "中性情景分析(100字以内)...",
    "pessimistic_analysis": "悲观情景分析(100字以内)...",
    "risk_factors": ["主要风险因素1", "主要风险因素2", "主要风险因素3", "主要风险因素4", "主要风险因素5"],
    "opportunity_factors": ["主要机会因素1", "主要机会因素2", "主要机会因素3", "主要机会因素4", "主要机会因素5"]
    }}
    
    风险和机会因素应该具体说明，每条5-15个字，简明扼要。
    """
    
            # 调用AI API
            response = openai.ChatCompletion.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "你是专业的股票分析师，擅长技术分析和情景预测。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
    
            # 解析AI回复
            import json
            try:
                analysis = json.loads(response.choices[0].message.content)
                # 确保返回的JSON包含所需的所有字段
                if "risk_factors" not in analysis:
                    analysis["risk_factors"] = self._get_default_risk_factors()
                if "opportunity_factors" not in analysis:
                    analysis["opportunity_factors"] = self._get_default_opportunity_factors()
                return analysis
            except:
                # 如果解析失败，尝试从文本中提取JSON
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response.choices[0].message.content)
                if json_match:
                    json_str = json_match.group(1)
                    try:
                        analysis = json.loads(json_str)
                        # 确保包含所需的所有字段
                        if "risk_factors" not in analysis:
                            analysis["risk_factors"] = self._get_default_risk_factors()
                        if "opportunity_factors" not in analysis:
                            analysis["opportunity_factors"] = self._get_default_opportunity_factors()
                        return analysis
                    except:
                        # JSON解析失败时返回默认值
                        return self._get_default_analysis()
                else:
                    # 无法提取JSON时返回默认值
                    return self._get_default_analysis()
        except Exception as e:
            print(f"生成AI分析出错: {str(e)}")
            return self._get_default_analysis()
    
    def _get_default_risk_factors(self):
        """返回默认的风险因素"""
        return [
            "宏观经济下行压力增大",
            "行业政策收紧可能性",
            "原材料价格上涨",
            "市场竞争加剧",
            "技术迭代风险"
        ]
    
    def _get_default_opportunity_factors(self):
        """返回默认的机会因素"""
        return [
            "行业景气度持续向好",
            "公司新产品上市",
            "成本控制措施见效",
            "产能扩张计划",
            "国际市场开拓机会"
        ]
    
    def _get_default_analysis(self):
        """返回默认的分析结果（包含风险和机会因素）"""
        return {
            "optimistic_analysis": "乐观情景分析暂无",
            "neutral_analysis": "中性情景分析暂无",
            "pessimistic_analysis": "悲观情景分析暂无",
            "risk_factors": self._get_default_risk_factors(),
            "opportunity_factors": self._get_default_opportunity_factors()
        }
    
    
    
    
    
    



























































