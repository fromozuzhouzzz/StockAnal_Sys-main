# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - 股票市场数据分析系统
开发者：熊猫大侠
版本：v2.1.0
许可证：MIT License
"""
# risk_monitor.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class RiskMonitor:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def analyze_stock_risk(self, stock_code, market_type='A'):
        """分析单只股票的风险"""
        try:
            # 获取股票数据和技术指标
            df = self.analyzer.get_stock_data(stock_code, market_type)
            df = self.analyzer.calculate_indicators(df)

            # 计算各类风险指标
            volatility_risk = self._analyze_volatility_risk(df)
            trend_risk = self._analyze_trend_risk(df)
            reversal_risk = self._analyze_reversal_risk(df)
            volume_risk = self._analyze_volume_risk(df)

            # 综合评估总体风险
            total_risk_score = (
                    volatility_risk['score'] * 0.3 +
                    trend_risk['score'] * 0.3 +
                    reversal_risk['score'] * 0.25 +
                    volume_risk['score'] * 0.15
            )

            # 确定风险等级
            if total_risk_score >= 80:
                risk_level = "极高"
            elif total_risk_score >= 60:
                risk_level = "高"
            elif total_risk_score >= 40:
                risk_level = "中等"
            elif total_risk_score >= 20:
                risk_level = "低"
            else:
                risk_level = "极低"

            # 生成风险警报
            alerts = []

            if volatility_risk['score'] >= 70:
                alerts.append({
                    "type": "volatility",
                    "level": "高",
                    "message": f"波动率风险较高 ({volatility_risk['value']:.2f}%)，可能面临大幅波动"
                })

            if trend_risk['score'] >= 70:
                alerts.append({
                    "type": "trend",
                    "level": "高",
                    "message": f"趋势风险较高，当前处于{trend_risk['trend']}趋势，可能面临加速下跌"
                })

            if reversal_risk['score'] >= 70:
                alerts.append({
                    "type": "reversal",
                    "level": "高",
                    "message": f"趋势反转风险较高，技术指标显示可能{reversal_risk['direction']}反转"
                })

            if volume_risk['score'] >= 70:
                alerts.append({
                    "type": "volume",
                    "level": "高",
                    "message": f"成交量异常，{volume_risk['pattern']}，可能预示价格波动"
                })

            return {
                "total_risk_score": total_risk_score,
                "risk_level": risk_level,
                "volatility_risk": volatility_risk,
                "trend_risk": trend_risk,
                "reversal_risk": reversal_risk,
                "volume_risk": volume_risk,
                "alerts": alerts
            }

        except Exception as e:
            print(f"分析股票风险出错: {str(e)}")
            return {
                "error": f"分析风险时出错: {str(e)}"
            }

    def _analyze_volatility_risk(self, df):
        """分析波动率风险"""
        # 计算近期波动率
        recent_volatility = df.iloc[-1]['Volatility']

        # 计算波动率变化
        avg_volatility = df['Volatility'].mean()
        volatility_change = recent_volatility / avg_volatility - 1

        # 评估风险分数
        if recent_volatility > 5 and volatility_change > 0.5:
            score = 90  # 极高风险
        elif recent_volatility > 4 and volatility_change > 0.3:
            score = 75  # 高风险
        elif recent_volatility > 3 and volatility_change > 0.1:
            score = 60  # 中高风险
        elif recent_volatility > 2:
            score = 40  # 中等风险
        elif recent_volatility > 1:
            score = 20  # 低风险
        else:
            score = 0  # 极低风险

        return {
            "score": score,
            "value": recent_volatility,
            "change": volatility_change * 100,
            "risk_level": "高" if score >= 60 else "中" if score >= 30 else "低"
        }

    def _analyze_trend_risk(self, df):
        """分析趋势风险"""
        # 获取均线数据
        ma5 = df.iloc[-1]['MA5']
        ma20 = df.iloc[-1]['MA20']
        ma60 = df.iloc[-1]['MA60']

        # 判断当前趋势
        if ma5 < ma20 < ma60:
            trend = "下降"

            # 判断下跌加速程度
            ma5_ma20_gap = (ma20 - ma5) / ma20 * 100

            if ma5_ma20_gap > 5:
                score = 90  # 极高风险
            elif ma5_ma20_gap > 3:
                score = 75  # 高风险
            elif ma5_ma20_gap > 1:
                score = 60  # 中高风险
            else:
                score = 50  # 中等风险

        elif ma5 > ma20 > ma60:
            trend = "上升"
            score = 20  # 低风险
        else:
            trend = "盘整"
            score = 40  # 中等风险

        return {
            "score": score,
            "trend": trend,
            "risk_level": "高" if score >= 60 else "中" if score >= 30 else "低"
        }

    def _analyze_reversal_risk(self, df):
        """分析趋势反转风险"""
        # 获取最新指标
        rsi = df.iloc[-1]['RSI']
        macd = df.iloc[-1]['MACD']
        signal = df.iloc[-1]['Signal']
        price = df.iloc[-1]['close']
        ma20 = df.iloc[-1]['MA20']

        # 判断潜在趋势反转信号
        reversal_signals = 0

        # RSI超买/超卖
        if rsi > 75:
            reversal_signals += 1
            direction = "向下"
        elif rsi < 25:
            reversal_signals += 1
            direction = "向上"
        else:
            direction = "无明确方向"

        # MACD死叉/金叉
        if macd > signal and df.iloc[-2]['MACD'] <= df.iloc[-2]['Signal']:
            reversal_signals += 1
            direction = "向上"
        elif macd < signal and df.iloc[-2]['MACD'] >= df.iloc[-2]['Signal']:
            reversal_signals += 1
            direction = "向下"

        # 价格与均线关系
        if price > ma20 * 1.1:
            reversal_signals += 1
            direction = "向下"
        elif price < ma20 * 0.9:
            reversal_signals += 1
            direction = "向上"

        # 评估风险分数
        if reversal_signals >= 3:
            score = 90  # 极高风险
        elif reversal_signals == 2:
            score = 70  # 高风险
        elif reversal_signals == 1:
            score = 40  # 中等风险
        else:
            score = 10  # 低风险

        return {
            "score": score,
            "reversal_signals": reversal_signals,
            "direction": direction,
            "risk_level": "高" if score >= 60 else "中" if score >= 30 else "低"
        }

    def _analyze_volume_risk(self, df):
        """分析成交量风险"""
        # 计算成交量变化
        recent_volume = df.iloc[-1]['volume']
        avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
        volume_ratio = recent_volume / avg_volume

        # 判断成交量模式
        if volume_ratio > 3:
            pattern = "成交量暴增"
            score = 90  # 极高风险
        elif volume_ratio > 2:
            pattern = "成交量显著放大"
            score = 70  # 高风险
        elif volume_ratio > 1.5:
            pattern = "成交量温和放大"
            score = 50  # 中等风险
        elif volume_ratio < 0.5:
            pattern = "成交量萎缩"
            score = 40  # 中低风险
        else:
            pattern = "成交量正常"
            score = 20  # 低风险

        # 价格与成交量背离分析
        price_change = (df.iloc[-1]['close'] - df.iloc[-5]['close']) / df.iloc[-5]['close']
        volume_change = (recent_volume - df.iloc[-5]['volume']) / df.iloc[-5]['volume']

        if price_change > 0.05 and volume_change < -0.3:
            pattern = "价量背离(价格上涨但量能萎缩)"
            score = max(score, 80)  # 提高风险评分
        elif price_change < -0.05 and volume_change < -0.3:
            pattern = "价量同向(价格下跌且量能萎缩)"
            score = max(score, 70)  # 提高风险评分
        elif price_change < -0.05 and volume_change > 0.5:
            pattern = "价量同向(价格下跌且量能放大)"
            score = max(score, 85)  # 提高风险评分

        return {
            "score": score,
            "volume_ratio": volume_ratio,
            "pattern": pattern,
            "risk_level": "高" if score >= 60 else "中" if score >= 30 else "低"
        }

    def analyze_portfolio_risk(self, portfolio):
        """分析投资组合整体风险"""
        try:
            if not portfolio or len(portfolio) == 0:
                return {"error": "投资组合为空"}

            # 分析每只股票的风险
            stock_risks = {}
            total_weight = 0
            weighted_risk_score = 0

            for stock in portfolio:
                stock_code = stock.get('stock_code')
                weight = stock.get('weight', 1)
                market_type = stock.get('market_type', 'A')

                if not stock_code:
                    continue

                # 分析股票风险
                risk = self.analyze_stock_risk(stock_code, market_type)
                stock_risks[stock_code] = risk

                # 计算加权风险分数
                total_weight += weight
                weighted_risk_score += risk.get('total_risk_score', 50) * weight

            # 计算组合总风险分数
            if total_weight > 0:
                portfolio_risk_score = weighted_risk_score / total_weight
            else:
                portfolio_risk_score = 0

            # 确定风险等级
            if portfolio_risk_score >= 80:
                risk_level = "极高"
            elif portfolio_risk_score >= 60:
                risk_level = "高"
            elif portfolio_risk_score >= 40:
                risk_level = "中等"
            elif portfolio_risk_score >= 20:
                risk_level = "低"
            else:
                risk_level = "极低"

            # 收集高风险股票
            high_risk_stocks = [
                {
                    "stock_code": code,
                    "risk_score": risk.get('total_risk_score', 0),
                    "risk_level": risk.get('risk_level', '未知')
                }
                for code, risk in stock_risks.items()
                if risk.get('total_risk_score', 0) >= 60
            ]

            # 收集所有风险警报
            all_alerts = []
            for code, risk in stock_risks.items():
                for alert in risk.get('alerts', []):
                    all_alerts.append({
                        "stock_code": code,
                        **alert
                    })

            # 分析风险集中度
            risk_concentration = self._analyze_risk_concentration(portfolio, stock_risks)

            return {
                "portfolio_risk_score": portfolio_risk_score,
                "risk_level": risk_level,
                "high_risk_stocks": high_risk_stocks,
                "alerts": all_alerts,
                "risk_concentration": risk_concentration,
                "stock_risks": stock_risks
            }

        except Exception as e:
            print(f"分析投资组合风险出错: {str(e)}")
            return {
                "error": f"分析投资组合风险时出错: {str(e)}"
            }

    def _analyze_risk_concentration(self, portfolio, stock_risks):
        """分析风险集中度"""
        # 分析行业集中度
        industries = {}
        for stock in portfolio:
            stock_code = stock.get('stock_code')
            stock_info = self.analyzer.get_stock_info(stock_code)
            industry = stock_info.get('行业', '未知')
            weight = stock.get('weight', 1)

            if industry in industries:
                industries[industry] += weight
            else:
                industries[industry] = weight

        # 找出权重最大的行业
        max_industry = max(industries.items(), key=lambda x: x[1]) if industries else ('未知', 0)

        # 计算高风险股票总权重
        high_risk_weight = 0
        for stock in portfolio:
            stock_code = stock.get('stock_code')
            if stock_code in stock_risks and stock_risks[stock_code].get('total_risk_score', 0) >= 60:
                high_risk_weight += stock.get('weight', 1)

        return {
            "max_industry": max_industry[0],
            "max_industry_weight": max_industry[1],
            "high_risk_weight": high_risk_weight
        }