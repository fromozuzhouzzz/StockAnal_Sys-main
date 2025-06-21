# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - 股票市场数据分析系统
开发者：熊猫大侠
版本：v2.1.0
许可证：MIT License
"""
# fundamental_analyzer.py
import akshare as ak
import pandas as pd
import numpy as np
import logging
import time

# 导入新的数据访问层
from data_service import data_service


class FundamentalAnalyzer:
    def __init__(self):
        """初始化基础分析类"""
        self.data_cache = {}

    def get_financial_indicators(self, stock_code):
        """获取财务指标数据"""
        try:
            # 获取基本财务指标
            financial_data = ak.stock_financial_analysis_indicator(symbol=stock_code,start_year="2022")

            # 获取最新估值指标
            valuation = ak.stock_value_em(symbol=stock_code)

            # 整合数据
            indicators = {
                'pe_ttm': float(valuation['PE(TTM)'].iloc[0]),
                'pb': float(valuation['市净率'].iloc[0]),
                'ps_ttm': float(valuation['市销率'].iloc[0]),
                'roe': float(financial_data['加权净资产收益率(%)'].iloc[0]),
                'gross_margin': float(financial_data['销售毛利率(%)'].iloc[0]),
                'net_profit_margin': float(financial_data['总资产净利润率(%)'].iloc[0]),
                'debt_ratio': float(financial_data['资产负债率(%)'].iloc[0])
            }

            return indicators
        except Exception as e:
            print(f"获取财务指标出错: {str(e)}")
            return {}

    def get_growth_data(self, stock_code):
        """获取成长性数据"""
        try:
            # 获取历年财务数据
            financial_data = ak.stock_financial_abstract(symbol=stock_code)

            # 计算各项成长率
            revenue = financial_data['营业收入'].astype(float)
            net_profit = financial_data['净利润'].astype(float)

            growth = {
                'revenue_growth_3y': self._calculate_cagr(revenue, 3),
                'profit_growth_3y': self._calculate_cagr(net_profit, 3),
                'revenue_growth_5y': self._calculate_cagr(revenue, 5),
                'profit_growth_5y': self._calculate_cagr(net_profit, 5)
            }

            return growth
        except Exception as e:
            print(f"获取成长数据出错: {str(e)}")
            return {}

    def _calculate_cagr(self, series, years):
        """计算复合年增长率"""
        if len(series) < years:
            return None

        latest = series.iloc[0]
        earlier = series.iloc[min(years, len(series) - 1)]

        if earlier <= 0:
            return None

        return ((latest / earlier) ** (1 / years) - 1) * 100

    def calculate_fundamental_score(self, stock_code):
        """计算基本面综合评分"""
        indicators = self.get_financial_indicators(stock_code)
        growth = self.get_growth_data(stock_code)

        # 估值评分 (30分)
        valuation_score = 0
        if 'pe_ttm' in indicators and indicators['pe_ttm'] > 0:
            pe = indicators['pe_ttm']
            if pe < 15:
                valuation_score += 25
            elif pe < 25:
                valuation_score += 20
            elif pe < 35:
                valuation_score += 15
            elif pe < 50:
                valuation_score += 10
            else:
                valuation_score += 5

        # 财务健康评分 (40分)
        financial_score = 0
        if 'roe' in indicators:
            roe = indicators['roe']
            if roe > 20:
                financial_score += 15
            elif roe > 15:
                financial_score += 12
            elif roe > 10:
                financial_score += 8
            elif roe > 5:
                financial_score += 4

        if 'debt_ratio' in indicators:
            debt_ratio = indicators['debt_ratio']
            if debt_ratio < 30:
                financial_score += 15
            elif debt_ratio < 50:
                financial_score += 10
            elif debt_ratio < 70:
                financial_score += 5

        # 成长性评分 (30分)
        growth_score = 0
        if 'revenue_growth_3y' in growth and growth['revenue_growth_3y']:
            rev_growth = growth['revenue_growth_3y']
            if rev_growth > 30:
                growth_score += 15
            elif rev_growth > 20:
                growth_score += 12
            elif rev_growth > 10:
                growth_score += 8
            elif rev_growth > 0:
                growth_score += 4

        if 'profit_growth_3y' in growth and growth['profit_growth_3y']:
            profit_growth = growth['profit_growth_3y']
            if profit_growth > 30:
                growth_score += 15
            elif profit_growth > 20:
                growth_score += 12
            elif profit_growth > 10:
                growth_score += 8
            elif profit_growth > 0:
                growth_score += 4

        # 计算总分
        total_score = valuation_score + financial_score + growth_score

        return {
            'total': total_score,
            'valuation': valuation_score,
            'financial_health': financial_score,
            'growth': growth_score,
            'details': {
                'indicators': indicators,
                'growth': growth
            }
        }