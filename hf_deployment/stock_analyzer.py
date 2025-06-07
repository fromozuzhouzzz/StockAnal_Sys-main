# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - 股票市场数据分析系统
修改：熊猫大侠
版本：v2.1.0
许可证：MIT License
"""
# stock_analyzer.py
import time
import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import requests
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import logging
import math
import json
import threading

# 线程局部存储
thread_local = threading.local()


class StockAnalyzer:
    """
    股票分析器 - 原有API保持不变，内部实现增强
    """

    def __init__(self, initial_cash=1000000):
        # 设置日志
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # 加载环境变量
        load_dotenv()

        # 设置 OpenAI API (原 Gemini API)
        self.openai_api_key = os.getenv('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
        self.openai_api_url = os.getenv('OPENAI_API_URL', 'https://api.openai.com/v1')
        self.openai_model = os.getenv('OPENAI_API_MODEL', 'gemini-2.0-pro-exp-02-05')
        self.function_call_model = os.getenv('FUNCTION_CALL_MODEL','gpt-4o')
        self.news_model = os.getenv('NEWS_MODEL')

        # 配置参数
        self.params = {
            'ma_periods': {'short': 5, 'medium': 20, 'long': 60},
            'rsi_period': 14,
            'bollinger_period': 20,
            'bollinger_std': 2,
            'volume_ma_period': 20,
            'atr_period': 14
        }

        # 添加缓存初始化
        self.data_cache = {}

        # JSON匹配标志
        self.json_match_flag = True
    def get_stock_data(self, stock_code, market_type='A', start_date=None, end_date=None):
        """获取股票数据"""
        import akshare as ak

        self.logger.info(f"开始获取股票 {stock_code} 数据，市场类型: {market_type}")

        cache_key = f"{stock_code}_{market_type}_{start_date}_{end_date}_price"
        if cache_key in self.data_cache:
            cached_df = self.data_cache[cache_key]
            # 创建一个副本以避免修改缓存数据
            # 并确保副本的日期类型为datetime
            result = cached_df.copy()
            # If 'date' column exists but is not datetime, convert it
            if 'date' in result.columns and not pd.api.types.is_datetime64_any_dtype(result['date']):
                try:
                    result['date'] = pd.to_datetime(result['date'])
                except Exception as e:
                    self.logger.warning(f"无法将日期列转换为datetime格式: {str(e)}")
            return result

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')

        try:
            # 根据市场类型获取数据
            if market_type == 'A':
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
            elif market_type == 'HK':
                df = ak.stock_hk_daily(
                    symbol=stock_code,
                    adjust="qfq"
                )
            elif market_type == 'US':
                df = ak.stock_us_hist(
                    symbol=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
            else:
                raise ValueError(f"不支持的市场类型: {market_type}")

            # 重命名列名以匹配分析需求
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount"
            })

            # 确保日期格式正确
            df['date'] = pd.to_datetime(df['date'])

            # 数据类型转换
            numeric_columns = ['open', 'close', 'high', 'low', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 删除空值
            df = df.dropna()

            result = df.sort_values('date')

            # 缓存原始数据（包含datetime类型）
            self.data_cache[cache_key] = result.copy()

            return result

        except Exception as e:
            self.logger.error(f"获取股票数据失败: {e}")
            raise Exception(f"获取股票数据失败: {e}")

    def get_north_flow_history(self, stock_code, start_date=None, end_date=None):
        """获取单个股票的北向资金历史持股数据"""
        try:
            import akshare as ak

            # 获取历史持股数据
            if start_date is None and end_date is None:
                # 默认获取近90天数据
                north_hist_data = ak.stock_hsgt_hist_em(symbol=stock_code)
            else:
                north_hist_data = ak.stock_hsgt_hist_em(symbol=stock_code, start_date=start_date, end_date=end_date)

            if north_hist_data.empty:
                return {"history": []}

            # 转换为列表格式返回
            history = []
            for _, row in north_hist_data.iterrows():
                history.append({
                    "date": row.get('日期', ''),
                    "holding": float(row.get('持股数', 0)) if '持股数' in row else 0,
                    "ratio": float(row.get('持股比例', 0)) if '持股比例' in row else 0,
                    "change": float(row.get('持股变动', 0)) if '持股变动' in row else 0,
                    "market_value": float(row.get('持股市值', 0)) if '持股市值' in row else 0
                })

            return {"history": history}
        except Exception as e:
            self.logger.error(f"获取北向资金历史数据出错: {str(e)}")
            return {"history": []}

    def calculate_ema(self, series, period):
        """计算指数移动平均线"""
        return series.ewm(span=period, adjust=False).mean()

    def calculate_rsi(self, series, period):
        """计算RSI指标"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, series):
        """计算MACD指标"""
        exp1 = series.ewm(span=12, adjust=False).mean()
        exp2 = series.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        return macd, signal, hist

    def calculate_bollinger_bands(self, series, period, std_dev):
        """计算布林带"""
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    def calculate_atr(self, df, period):
        """计算ATR指标"""
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def format_indicator_data(self, df):
        """格式化指标数据，控制小数位数"""

        # 格式化价格数据 (2位小数)
        price_columns = ['open', 'close', 'high', 'low', 'MA5', 'MA20', 'MA60', 'BB_upper', 'BB_middle', 'BB_lower']
        for col in price_columns:
            if col in df.columns:
                df[col] = df[col].round(2)

        # 格式化MACD相关指标 (3位小数)
        macd_columns = ['MACD', 'Signal', 'MACD_hist']
        for col in macd_columns:
            if col in df.columns:
                df[col] = df[col].round(3)

        # 格式化其他技术指标 (2位小数)
        other_columns = ['RSI', 'Volatility', 'ROC', 'Volume_Ratio']
        for col in other_columns:
            if col in df.columns:
                df[col] = df[col].round(2)

        return df

    def calculate_indicators(self, df):
        """计算技术指标"""

        try:
            # 计算移动平均线
            df['MA5'] = self.calculate_ema(df['close'], self.params['ma_periods']['short'])
            df['MA20'] = self.calculate_ema(df['close'], self.params['ma_periods']['medium'])
            df['MA60'] = self.calculate_ema(df['close'], self.params['ma_periods']['long'])

            # 计算RSI
            df['RSI'] = self.calculate_rsi(df['close'], self.params['rsi_period'])

            # 计算MACD
            df['MACD'], df['Signal'], df['MACD_hist'] = self.calculate_macd(df['close'])

            # 计算布林带
            df['BB_upper'], df['BB_middle'], df['BB_lower'] = self.calculate_bollinger_bands(
                df['close'],
                self.params['bollinger_period'],
                self.params['bollinger_std']
            )

            # 成交量分析
            df['Volume_MA'] = df['volume'].rolling(window=self.params['volume_ma_period']).mean()
            df['Volume_Ratio'] = df['volume'] / df['Volume_MA']

            # 计算ATR和波动率
            df['ATR'] = self.calculate_atr(df, self.params['atr_period'])
            df['Volatility'] = df['ATR'] / df['close'] * 100

            # 动量指标
            df['ROC'] = df['close'].pct_change(periods=10) * 100

            # 格式化数据
            df = self.format_indicator_data(df)

            return df

        except Exception as e:
            self.logger.error(f"计算技术指标时出错: {str(e)}")
            raise

    def calculate_score(self, df, market_type='A'):
        """
        计算股票评分 - 使用时空共振交易系统增强
        根据不同的市场特征调整评分权重和标准
        """
        try:
            score = 0
            latest = df.iloc[-1]
            prev_days = min(30, len(df) - 1)  # Get the most recent 30 days or all available data

            # 时空共振框架 - 维度1：多时间框架分析
            # 基础权重配置
            weights = {
                'trend': 0.30,  # 趋势因子权重（日线级别）
                'volatility': 0.15,  # 波动率因子权重
                'technical': 0.25,  # 技术指标因子权重
                'volume': 0.20,  # 成交量因子权重（能量守恒维度）
                'momentum': 0.10  # 动量因子权重（周线级别）
            }

            # 根据市场类型调整权重（维度1：时间框架嵌套）
            if market_type == 'US':
                # 美股优先考虑长期趋势
                weights['trend'] = 0.35
                weights['volatility'] = 0.10
                weights['momentum'] = 0.15
            elif market_type == 'HK':
                # 港股调整波动率和成交量权重
                weights['volatility'] = 0.20
                weights['volume'] = 0.25

            # 1. 趋势评分（最高30分）- 日线级别分析
            trend_score = 0

            # 均线评估 - "三线形态"分析
            if latest['MA5'] > latest['MA20'] and latest['MA20'] > latest['MA60']:
                # 完美多头排列（维度1：日线形态）
                trend_score += 15
            elif latest['MA5'] > latest['MA20']:
                # 短期上升趋势（维度1：5分钟形态）
                trend_score += 10
            elif latest['MA20'] > latest['MA60']:
                # 中期上升趋势
                trend_score += 5

            # 价格位置评估
            if latest['close'] > latest['MA5']:
                trend_score += 5
            if latest['close'] > latest['MA20']:
                trend_score += 5
            if latest['close'] > latest['MA60']:
                trend_score += 5

            # 确保不超过最高分数限制
            trend_score = min(30, trend_score)

            # 2. 波动率评分（最高15分）- 维度2：过滤
            volatility_score = 0

            # 适度的波动率最理想
            volatility = latest['Volatility']
            if 1.0 <= volatility <= 2.5:
                # 最佳波动率范围
                volatility_score += 15
            elif 2.5 < volatility <= 4.0:
                # 较高波动率，次优选择
                volatility_score += 10
            elif volatility < 1.0:
                # 波动率过低，缺乏能量
                volatility_score += 5
            else:
                # 波动率过高，风险较大
                volatility_score += 0

            # 3. 技术指标评分（最高25分）- "峰值检测系统"
            technical_score = 0

            # RSI指标评估（10分）
            rsi = latest['RSI']
            if 40 <= rsi <= 60:
                # 中性区域，趋势稳定
                technical_score += 7
            elif 30 <= rsi < 40 or 60 < rsi <= 70:
                # 阈值区域，可能出现反转信号
                technical_score += 10
            elif rsi < 30:
                # 超卖区域，可能出现买入机会
                technical_score += 8
            elif rsi > 70:
                # 超买区域，可能存在卖出风险
                technical_score += 2

            # MACD指标评估（10分）- "峰值预警信号"
            if latest['MACD'] > latest['Signal'] and latest['MACD_hist'] > 0:
                # MACD金叉且柱状图为正
                technical_score += 10
            elif latest['MACD'] > latest['Signal']:
                # MACD金叉
                technical_score += 8
            elif latest['MACD'] < latest['Signal'] and latest['MACD_hist'] < 0:
                # MACD死叉且柱状图为负
                technical_score += 0
            elif latest['MACD_hist'] > df.iloc[-2]['MACD_hist']:
                # MACD柱状图增长，可能出现反转信号
                technical_score += 5

            # 布林带位置评估（5分）
            bb_position = (latest['close'] - latest['BB_lower']) / (latest['BB_upper'] - latest['BB_lower'])
            if 0.3 <= bb_position <= 0.7:
                # 价格在布林带中间区域，趋势稳定
                technical_score += 3
            elif bb_position < 0.2:
                # 价格接近下轨，可能超卖
                technical_score += 5
            elif bb_position > 0.8:
                # 价格接近上轨，可能超买
                technical_score += 1

            # 确保最大分数限制
            technical_score = min(25, technical_score)

            # 4. 成交量评分（最高20分）- "能量守恒维度"
            volume_score = 0

            # 成交量趋势分析
            recent_vol_ratio = [df.iloc[-i]['Volume_Ratio'] for i in range(1, min(6, len(df)))]
            avg_vol_ratio = sum(recent_vol_ratio) / len(recent_vol_ratio)

            if avg_vol_ratio > 1.5 and latest['close'] > df.iloc[-2]['close']:
                # 成交量放大且价格上涨 - "成交量能量阈值突破"
                volume_score += 20
            elif avg_vol_ratio > 1.2 and latest['close'] > df.iloc[-2]['close']:
                # 成交量和价格同步上涨
                volume_score += 15
            elif avg_vol_ratio < 0.8 and latest['close'] < df.iloc[-2]['close']:
                # 成交量和价格同步下跌，可能是健康回调
                volume_score += 10
            elif avg_vol_ratio > 1.2 and latest['close'] < df.iloc[-2]['close']:
                # 成交量增加但价格下跌，可能存在较大卖压
                volume_score += 0
            else:
                # 其他情况
                volume_score += 8

            # 5. 动量评分（最高10分）- 维度1：周线级别
            momentum_score = 0

            # ROC动量指标
            roc = latest['ROC']
            if roc > 5:
                # Strong upward momentum
                momentum_score += 10
            elif 2 <= roc <= 5:
                # Moderate upward momentum
                momentum_score += 8
            elif 0 <= roc < 2:
                # Weak upward momentum
                momentum_score += 5
            elif -2 <= roc < 0:
                # Weak downward momentum
                momentum_score += 3
            else:
                # Strong downward momentum
                momentum_score += 0

            # 根据加权因子计算总分 - “共振公式”
            final_score = (
                    trend_score * weights['trend'] / 0.30 +
                    volatility_score * weights['volatility'] / 0.15 +
                    technical_score * weights['technical'] / 0.25 +
                    volume_score * weights['volume'] / 0.20 +
                    momentum_score * weights['momentum'] / 0.10
            )

            # 特殊市场调整 - “市场适应机制”
            if market_type == 'US':
                # 美国市场额外调整因素
                # 检查是否为财报季
                is_earnings_season = self._is_earnings_season()
                if is_earnings_season:
                    # Earnings season has higher volatility, adjust score certainty
                    final_score = 0.9 * final_score + 5  # Slight regression to the mean

            elif market_type == 'HK':
                # 港股特殊调整
                # 检查A股联动效应
                a_share_linkage = self._check_a_share_linkage(df)
                if a_share_linkage > 0.7:  # High linkage
                    # 根据大陆市场情绪调整
                    mainland_sentiment = self._get_mainland_market_sentiment()
                    if mainland_sentiment > 0:
                        final_score += 5
                    else:
                        final_score -= 5

            # Ensure score remains within 0-100 range
            final_score = max(0, min(100, round(final_score)))

            # Store sub-scores for display
            self.score_details = {
                'trend': trend_score,
                'volatility': volatility_score,
                'technical': technical_score,
                'volume': volume_score,
                'momentum': momentum_score,
                'total': final_score
            }

            return final_score

        except Exception as e:
            self.logger.error(f"Error calculating score: {str(e)}")
            # Return neutral score on error
            return 50

    def calculate_position_size(self, stock_code, risk_percent=2.0, stop_loss_percent=5.0):
        """
        根据风险管理原则计算最佳仓位大小
        实施时空共振系统的“仓位大小公式”

        参数:
            stock_code: 要分析的股票代码
            risk_percent: 在此交易中承担风险的总资本百分比（默认为2％）
            stop_loss_percent: 从入场点的止损百分比（默认为5％）

        返回:
            仓位大小占总资本的百分比
        """
        try:
            # Get stock data
            df = self.get_stock_data(stock_code)
            df = self.calculate_indicators(df)

            # 获取波动率因子（来自维度3：能量守恒）
            latest = df.iloc[-1]
            volatility = latest['Volatility']

            # 计算波动率调整因子（较高波动率=较小仓位）
            volatility_factor = 1.0
            if volatility > 4.0:
                volatility_factor = 0.6  # Reduce position for high volatility stocks
            elif volatility > 2.5:
                volatility_factor = 0.8  # Slightly reduce position
            elif volatility < 1.0:
                volatility_factor = 1.2  # Can increase position for low volatility stocks

            # Calculate position size using risk formula
            # 公式：position_size = (风险金额) / (止损 * 波动率因子)
            position_size = (risk_percent) / (stop_loss_percent * volatility_factor)

            # 限制最大仓位为25％以实现多元化
            position_size = min(position_size, 25.0)

            return position_size

        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            # 返回保守的默认仓位大小（出错时）
            return 5.0

    def get_recommendation(self, score, market_type='A', technical_data=None, news_data=None):
        """
        根据得分和附加信息生成投资建议
        使用时空共振交易系统策略增强
        """
        try:
            # 1. Base recommendation logic - Dynamic threshold adjustment based on score
            if score >= 85:
                base_recommendation = '强烈建议买入'
                confidence = 'high'
                action = 'strong_buy'
            elif score >= 70:
                base_recommendation = '建议买入'
                confidence = 'medium_high'
                action = 'buy'
            elif score >= 55:
                base_recommendation = '谨慎买入'
                confidence = 'medium'
                action = 'cautious_buy'
            elif score >= 45:
                base_recommendation = '持观望态度'
                confidence = 'medium'
                action = 'hold'
            elif score >= 30:
                base_recommendation = '谨慎持有'
                confidence = 'medium'
                action = 'cautious_hold'
            elif score >= 15:
                base_recommendation = '建议减仓'
                confidence = 'medium_high'
                action = 'reduce'
            else:
                base_recommendation = '建议卖出'
                confidence = 'high'
                action = 'sell'

            # 2. Consider market characteristics (Dimension 1: Timeframe Nesting)
            market_adjustment = ""
            if market_type == 'US':
                # US market adjustment factors
                if self._is_earnings_season():
                    if confidence == 'high' or confidence == 'medium_high':
                        confidence = 'medium'
                        market_adjustment = "（财报季临近，波动可能加大，建议适当控制仓位）"

            elif market_type == 'HK':
                # HK market adjustment factors
                mainland_sentiment = self._get_mainland_market_sentiment()
                if mainland_sentiment < -0.3 and (action == 'buy' or action == 'strong_buy'):
                    action = 'cautious_buy'
                    confidence = 'medium'
                    market_adjustment = "（受大陆市场情绪影响，建议控制风险）"

            elif market_type == 'A':
                # A-share specific adjustment factors
                if technical_data and 'Volatility' in technical_data:
                    vol = technical_data.get('Volatility', 0)
                    if vol > 4.0 and (action == 'buy' or action == 'strong_buy'):
                        action = 'cautious_buy'
                        confidence = 'medium'
                        market_adjustment = "（市场波动较大，建议分批买入）"

            # 3. Consider market sentiment (Dimension 2: Filtering)
            sentiment_adjustment = ""
            if news_data and 'market_sentiment' in news_data:
                sentiment = news_data.get('market_sentiment', 'neutral')

                if sentiment == 'bullish' and action in ['hold', 'cautious_hold']:
                    action = 'cautious_buy'
                    sentiment_adjustment = "（市场氛围积极，可适当提高仓位）"

                elif sentiment == 'bearish' and action in ['buy', 'cautious_buy']:
                    action = 'hold'
                    sentiment_adjustment = "（市场氛围悲观，建议等待更好买点）"
            elif self.json_match_flag==False:
                import re

                # 如果JSON解析失败，尝试从原始内容中匹配市场情绪
                sentiment_pattern = r'(bullish|neutral|bearish)'
                sentiment_match = re.search(sentiment_pattern, news_data.get('original_content', ''))
                
                if sentiment_match:
                    sentiment_map = {
                        'bullish': 'bullish',
                        'neutral': 'neutral',
                        'bearish': 'bearish'
                    }
                    sentiment = sentiment_map.get(sentiment_match.group(1), 'neutral')
                    
                    if sentiment == 'bullish' and action in ['hold', 'cautious_hold']:
                        action = 'cautious_buy'
                        sentiment_adjustment = "（市场氛围积极，可适当提高仓位）"
                    elif sentiment == 'bearish' and action in ['buy', 'cautious_buy']:
                        action = 'hold'
                        sentiment_adjustment = "（市场氛围悲观，建议等待更好买点）"

                    
            # 4. Technical indicators adjustment (Dimension 2: "Peak Detection System")
            technical_adjustment = ""
            if technical_data:
                rsi = technical_data.get('RSI', 50)
                macd_signal = technical_data.get('MACD_signal', 'neutral')

                # RSI overbought/oversold adjustment
                if rsi > 80 and action in ['buy', 'strong_buy']:
                    action = 'hold'
                    technical_adjustment = "（RSI指标显示超买，建议等待回调）"
                elif rsi < 20 and action in ['sell', 'reduce']:
                    action = 'hold'
                    technical_adjustment = "（RSI指标显示超卖，可能存在反弹机会）"

                # MACD signal adjustment
                if macd_signal == 'bullish' and action in ['hold', 'cautious_hold']:
                    action = 'cautious_buy'
                    if not technical_adjustment:
                        technical_adjustment = "（MACD显示买入信号）"
                elif macd_signal == 'bearish' and action in ['cautious_buy', 'buy']:
                    action = 'hold'
                    if not technical_adjustment:
                        technical_adjustment = "（MACD显示卖出信号）"

            # 5. Convert adjusted action to final recommendation
            action_to_recommendation = {
                'strong_buy': '强烈建议买入',
                'buy': '建议买入',
                'cautious_buy': '谨慎买入',
                'hold': '持观望态度',
                'cautious_hold': '谨慎持有',
                'reduce': '建议减仓',
                'sell': '建议卖出'
            }

            final_recommendation = action_to_recommendation.get(action, base_recommendation)

            # 6. Combine all adjustment factors
            adjustments = " ".join(filter(None, [market_adjustment, sentiment_adjustment, technical_adjustment]))

            if adjustments:
                return f"{final_recommendation} {adjustments}"
            else:
                return final_recommendation

        except Exception as e:
            self.logger.error(f"Error generating investment recommendation: {str(e)}")
            # Return safe default recommendation on error
            return "无法提供明确建议，请结合多种因素谨慎决策"

    def check_consecutive_losses(self, trade_history, max_consecutive_losses=3):
        """
        实施“冷静期风险控制” - 连续亏损后停止交易

        参数:
            trade_history: 最近交易结果列表 (True 表示盈利, False 表示亏损)
            max_consecutive_losses: 允许的最大连续亏损次数

        返回:
            Boolean: True 如果应该暂停交易, False 如果可以继续交易
        """
        consecutive_losses = 0

        # Count consecutive losses from most recent trades
        for trade in reversed(trade_history):
            if not trade:  # If trade is a loss
                consecutive_losses += 1
            else:
                break  # Break on first profitable trade

        # Return True if we've hit max consecutive losses
        return consecutive_losses >= max_consecutive_losses

    def check_profit_taking(self, current_profit_percent, threshold=20.0):
        """
        当回报超过阈值时，实施获利了结机制
        属于“能量守恒维度”的一部分

        参数:
            current_profit_percent: 当前利润百分比
            threshold: 用于获利了结的利润百分比阈值

        返回:
            Float: 减少仓位的百分比 (0.0-1.0)
        """
        if current_profit_percent >= threshold:
            # If profit exceeds threshold, suggest reducing position by 50%
            return 0.5

        return 0.0  # No position reduction recommended

    def _is_earnings_season(self):
        """检查当前是否处于财报季(辅助函数)"""
        from datetime import datetime
        current_month = datetime.now().month
        # 美股财报季大致在1月、4月、7月和10月
        return current_month in [1, 4, 7, 10]

    def _check_a_share_linkage(self, df, window=20):
        """检查港股与A股的联动性(辅助函数)"""
        # 该函数需要获取对应的A股指数数据
        # 简化版实现:
        try:
            # 获取恒生指数与上证指数的相关系数
            # 实际实现中需要获取真实数据
            correlation = 0.6  # 示例值
            return correlation
        except:
            return 0.5  # 默认中等关联度

    def _get_mainland_market_sentiment(self):
        """获取中国大陆市场情绪(辅助函数)"""
        # 实际实现中需要分析上证指数、北向资金等因素
        try:
            # 简化版实现，返回-1到1之间的值，1表示积极情绪
            sentiment = 0.2  # 示例值
            return sentiment
        except:
            return 0  # 默认中性情绪

    def get_stock_news(self, stock_code, market_type='A', limit=5):
        """
        获取股票相关新闻和实时信息，通过OpenAI API调用function calling方式获取
        参数:
            stock_code: 股票代码
            market_type: 市场类型 (A/HK/US)
            limit: 返回的新闻条数上限
        返回:
            包含新闻和公告的字典
        """
        try:
            self.logger.info(f"获取股票 {stock_code} 的相关新闻和信息")

            # 缓存键
            cache_key = f"{stock_code}_{market_type}_news"
            if cache_key in self.data_cache and (
                    datetime.now() - self.data_cache[cache_key]['timestamp']).seconds < 3600:
                # 缓存1小时内的数据
                return self.data_cache[cache_key]['data']

            # 获取股票基本信息
            stock_info = self.get_stock_info(stock_code)
            stock_name = stock_info.get('股票名称', '未知')
            industry = stock_info.get('行业', '未知')

            # 构建新闻查询的prompt
            market_name = "A股" if market_type == 'A' else "港股" if market_type == 'HK' else "美股"
            query = f"""请帮我搜索以下股票的最新相关新闻和信息:
            股票名称: {stock_name}
            股票代码: {stock_code}
            市场: {market_name}
            行业: {industry}
            
            请使用search_news工具搜索相关新闻，然后只需要返回JSON格式。
            按照以下格式的JSON数据返回:
            {{
                "news": [
                    {{"title": "新闻标题", "date": "YYYY-MM-DD", "source": "新闻来源", "summary": "新闻摘要"}},
                    ...
                ],
                "announcements": [
                    {{"title": "公告标题", "date": "YYYY-MM-DD", "type": "公告类型"}},
                    ...
                ],
                "industry_news": [
                    {{"title": "行业新闻标题", "date": "YYYY-MM-DD", "summary": "新闻摘要"}},
                    ...
                ],
                "market_sentiment": "市场情绪(bullish/slightly_bullish/neutral/slightly_bearish/bearish)"
            }}
            注意只返回json数据，不要返回其他内容。
            """

            # 定义函数调用工具
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_news",
                        "description": "搜索股票相关的新闻和信息",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "搜索查询词，用于查找相关新闻"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                }
            ]

            # 使用线程和队列添加超时控制
            import queue
            import threading
            import json
            import openai
            import requests

            result_queue = queue.Queue()

            def search_news(query):
                """实际执行搜索的函数"""
                try:
                    # 获取API密钥
                    serp_api_key = os.getenv('SERP_API_KEY')
                    tavily_api_key = os.getenv('TAVILY_API_KEY')

                    if not serp_api_key and not tavily_api_key:
                        self.logger.error("未找到SERP_API_KEY或TAVILY_API_KEY环境变量")
                        return {"error": "未配置搜索API密钥"}

                    # 构建搜索查询
                    search_query = f"{stock_name} {stock_code} {market_name} 最新新闻 公告"
                    industry_query = f"{industry} {market_name} 行业动态 最新消息"

                    news_results = []
                    industry_news = []

                    # 如果配置了SERP API，使用SERP API搜索
                    if serp_api_key:
                        self.logger.info(f"使用SERP API搜索新闻: {search_query}")

                        # 调用SERP API获取股票新闻
                        url = "https://serpapi.com/search"
                        params = {
                            "engine": "google",
                            "q": search_query,
                            "api_key": serp_api_key,
                            "tbm": "nws",  # 新闻搜索
                            "num": limit * 2  # 获取更多结果以便筛选
                        }

                        response = requests.get(url, params=params)
                        search_results = response.json()

                        # 提取新闻结果
                        if "news_results" in search_results:
                            for item in search_results["news_results"][:limit]:
                                news_results.append({
                                    "title": item.get("title", ""),
                                    "date": item.get("date", ""),
                                    "source": item.get("source", ""),
                                    "link": item.get("link", ""),
                                    "snippet": item.get("snippet", "")
                                })

                        # 构建行业新闻查询
                        industry_params = {
                            "engine": "google",
                            "q": industry_query,
                            "api_key": serp_api_key,
                            "tbm": "nws",
                            "num": limit
                        }

                        industry_response = requests.get(url, params=industry_params)
                        industry_results = industry_response.json()

                        # 提取行业新闻
                        if "news_results" in industry_results:
                            for item in industry_results["news_results"][:limit]:
                                industry_news.append({
                                    "title": item.get("title", ""),
                                    "date": item.get("date", ""),
                                    "source": item.get("source", ""),
                                    "summary": item.get("snippet", "")
                                })

                    # 如果配置了Tavily API，使用Tavily API搜索
                    if tavily_api_key:
                        self.logger.info(f"使用Tavily API搜索新闻: {search_query}")

                        try:
                            from tavily import TavilyClient

                            client = TavilyClient(tavily_api_key)

                            # 搜索股票相关新闻
                            tavily_response = client.search(
                                query=search_query,
                                topic="finance",
                                search_depth="advanced"
                            )

                            # 提取新闻结果
                            if "results" in tavily_response:
                                for i, item in enumerate(tavily_response["results"][:limit]):
                                    # 从URL提取域名作为来源
                                    source = ""
                                    if item.get("url"):
                                        try:
                                            from urllib.parse import urlparse
                                            parsed_url = urlparse(item.get("url"))
                                            source = parsed_url.netloc
                                        except:
                                            source = item.get("url", "").split('/')[2] if item.get("url") else ""

                                    news_results.append({
                                        "title": item.get("title", ""),
                                        "date": datetime.now().strftime("%Y-%m-%d"),  # Tavily不提供日期，使用当前日期
                                        "source": source,
                                        "link": item.get("url", ""),
                                        "snippet": item.get("content", "")
                                    })

                            # 搜索行业相关新闻
                            tavily_industry_response = client.search(
                                query=industry_query,
                                topic="finance",
                                search_depth="advanced"
                            )

                            # 提取行业新闻结果
                            if "results" in tavily_industry_response:
                                for i, item in enumerate(tavily_industry_response["results"][:limit]):
                                    source = ""
                                    if item.get("url"):
                                        try:
                                            from urllib.parse import urlparse
                                            parsed_url = urlparse(item.get("url"))
                                            source = parsed_url.netloc
                                        except:
                                            source = item.get("url", "").split('/')[2] if item.get("url") else ""

                                    industry_news.append({
                                        "title": item.get("title", ""),
                                        "date": datetime.now().strftime("%Y-%m-%d"),
                                        "source": source,
                                        "summary": item.get("content", "")
                                    })

                            # 生成Tavily搜索结果的文本摘要（可用于调试）
                            tavily_summary = ""
                            if "results" in tavily_response:
                                for i, item in enumerate(tavily_response["results"][:limit]):
                                    tavily_summary += f"{i+1}、{item.get('title', '')}\n"
                                    tavily_summary += f"{item.get('content', '')}\n\n"

                            self.logger.info(f"Tavily搜索成功，获取到 {len(tavily_response.get('results', []))} 条新闻结果")

                        except ImportError:
                            self.logger.error("未安装Tavily客户端库，请使用pip install tavily-python安装")
                        except Exception as e:
                            self.logger.error(f"使用Tavily API搜索时出错: {str(e)}")
                            self.logger.error(traceback.format_exc())

                    # 移除可能的重复结果
                    unique_news = []
                    seen_titles = set()
                    for item in news_results:
                        title = item.get("title", "").strip()
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            unique_news.append(item)

                    unique_industry_news = []
                    seen_industry_titles = set()
                    for item in industry_news:
                        title = item.get("title", "").strip()
                        if title and title not in seen_industry_titles:
                            seen_industry_titles.add(title)
                            unique_industry_news.append(item)

                    # 获取公告信息 (这部分保持不变)
                    announcements = []

                    # 分析市场情绪 (保持原有逻辑)
                    sentiment_keywords = {
                        'bullish': ['上涨', '增长', '利好', '突破', '强势', '看好', '机会', '利润'],
                        'slightly_bullish': ['回升', '改善', '企稳', '向好', '期待'],
                        'neutral': ['稳定', '平稳', '持平', '不变'],
                        'slightly_bearish': ['回调', '承压', '谨慎', '风险', '下滑'],
                        'bearish': ['下跌', '亏损', '跌破', '利空', '警惕', '危机', '崩盘']
                    }

                    # 计算情绪得分
                    sentiment_scores = {k: 0 for k in sentiment_keywords.keys()}
                    all_text = " ".join([n.get("title", "") + " " + n.get("snippet", "") for n in unique_news])

                    for sentiment, keywords in sentiment_keywords.items():
                        for keyword in keywords:
                            if keyword in all_text:
                                sentiment_scores[sentiment] += 1

                    # 确定主导情绪
                    if not sentiment_scores or all(score == 0 for score in sentiment_scores.values()):
                        market_sentiment = "neutral"
                    else:
                        market_sentiment = max(sentiment_scores.items(), key=lambda x: x[1])[0]

                    self.logger.info(f"搜索完成，共获取到 {len(unique_news)} 条新闻和 {len(unique_industry_news)} 条行业新闻")

                    return {
                        "news": unique_news,
                        "announcements": announcements,
                        "industry_news": unique_industry_news,
                        "market_sentiment": market_sentiment
                    }

                except Exception as e:
                    self.logger.error(f"搜索新闻时出错: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    return {"error": str(e)}


            def call_api():
                try:
                    messages = [{"role": "user", "content": query}]
                    
                    # 第一步：调用模型，让它决定使用工具
                    response = openai.ChatCompletion.create(
                        model=self.function_call_model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.7,
                        max_tokens=1000,
                        stream=False,
                        timeout=120
                    )
                    
                    # 检查是否有工具调用
                    message = response["choices"][0]["message"]
                    
                    if "tool_calls" in message:
                        # 处理工具调用
                        tool_calls = message["tool_calls"]
                        
                        # 准备新的消息列表，包含工具调用结果
                        messages.append(message)  # 添加助手的消息
                        
                        for tool_call in tool_calls:
                            function_name = tool_call["function"]["name"]
                            function_args = json.loads(tool_call["function"]["arguments"])
                            
                            # 执行搜索
                            if function_name == "search_news":
                                search_query = function_args.get("query", f"{stock_name} {stock_code} 新闻")
                                function_response = search_news(search_query)
                                
                                # 添加工具响应到消息
                                messages.append({
                                    "tool_call_id": tool_call["id"],
                                    "role": "tool",
                                    "name": function_name,
                                    "content": json.dumps(function_response, ensure_ascii=False)
                                })
                        
                        # 第二步：让模型处理搜索结果并生成最终响应
                        second_response = openai.ChatCompletion.create(
                            model=self.news_model,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=4000,
                            stream=False,
                            timeout=120
                        )
                        
                        result_queue.put(second_response)
                    else:
                        # 如果模型没有选择使用工具，直接使用第一次响应
                        result_queue.put(response)
                        
                except Exception as e:
                    result_queue.put(e)

            # 启动API调用线程
            api_thread = threading.Thread(target=call_api)
            api_thread.daemon = True
            api_thread.start()

            # 等待结果，最多等待240秒
            try:
                result = result_queue.get(timeout=240)

                # 检查结果是否为异常
                if isinstance(result, Exception):
                    self.logger.error(f"获取新闻API调用失败: {str(result)}")
                    raise result

                # 提取回复内容
                content = result["choices"][0]["message"]["content"].strip()

                # 尝试解析JSON，但如果失败则保留原始内容
                try:
                    # 尝试直接解析JSON
                    news_data = json.loads(content)
                except json.JSONDecodeError:
                    # 如果直接解析失败，尝试提取JSON部分
                    import re
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                    if json_match:
                        json_str = json_match.group(1)
                        news_data = json.loads(json_str)
                        self.json_match_flag = True
                    else:
                        # 如果仍然无法提取JSON，尝试直接返回响应
                        self.logger.info(f"无法提取JSON，直接返回响应{content}")
                        self.json_match_flag = False
                        news_data = {}
                        news_data['original_content'] = content

                # 确保数据结构完整
                if not isinstance(news_data, dict):
                    news_data = {}
                
                for key in ['news', 'announcements', 'industry_news']:
                    if key not in news_data:
                        news_data[key] = []
                
                if 'market_sentiment' not in news_data:
                    news_data['market_sentiment'] = 'neutral'

                # 添加时间戳
                news_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # 缓存结果
                self.data_cache[cache_key] = {
                    'data': news_data,
                    'timestamp': datetime.now()
                }

                return news_data

            except queue.Empty:
                self.logger.warning("获取新闻API调用超时")
                return {
                    'news': [],
                    'announcements': [],
                    'industry_news': [],
                    'market_sentiment': 'neutral',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            except Exception as e:
                self.logger.error(f"处理新闻数据时出错: {str(e)}")
                return {
                    'news': [],
                    'announcements': [],
                    'industry_news': [],
                    'market_sentiment': 'neutral',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

        except Exception as e:
            self.logger.error(f"获取股票新闻时出错: {str(e)}")
            # 出错时返回空结果
            return {
                'news': [],
                'announcements': [],
                'industry_news': [],
                'market_sentiment': 'neutral',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def get_ai_analysis(self, df, stock_code, market_type='A'):
        """
        使用AI进行增强分析
        结合技术指标、实时新闻和行业信息

        参数:
            df: 股票历史数据DataFrame
            stock_code: 股票代码
            market_type: 市场类型(A/HK/US)

        返回:
            AI生成的分析报告文本
        """
        try:
            import openai
            import threading
            import queue

            # 设置API密钥和基础URL
            openai.api_key = self.openai_api_key
            openai.api_base = self.openai_api_url

            # 1. 获取最近K线数据
            recent_data = df.tail(20).to_dict('records')

            # 2. 计算技术指标摘要
            technical_summary = {
                'trend': 'upward' if df.iloc[-1]['MA5'] > df.iloc[-1]['MA20'] else 'downward',
                'volatility': f"{df.iloc[-1]['Volatility']:.2f}%",
                'volume_trend': 'increasing' if df.iloc[-1]['Volume_Ratio'] > 1 else 'decreasing',
                'rsi_level': df.iloc[-1]['RSI'],
                'macd_signal': 'bullish' if df.iloc[-1]['MACD'] > df.iloc[-1]['Signal'] else 'bearish',
                'bb_position': self._calculate_bb_position(df)
            }

            # 3. 获取支撑压力位
            sr_levels = self.identify_support_resistance(df)

            # 4. 获取股票基本信息
            stock_info = self.get_stock_info(stock_code)
            stock_name = stock_info.get('股票名称', '未知')
            industry = stock_info.get('行业', '未知')

            # 5. 获取相关新闻和实时信息 - 整合get_stock_news
            self.logger.info(f"获取 {stock_code} 的相关新闻和市场信息")
            news_data = self.get_stock_news(stock_code, market_type)

            # 6. 评分分解
            score = self.calculate_score(df, market_type)
            score_details = getattr(self, 'score_details', {'total': score})

            # 7. 获取投资建议
            # 传递技术指标和新闻数据给get_recommendation函数
            tech_data = {
                'RSI': technical_summary['rsi_level'],
                'MACD_signal': technical_summary['macd_signal'],
                'Volatility': df.iloc[-1]['Volatility']
            }
            recommendation = self.get_recommendation(score, market_type, tech_data, news_data)

            # 8. 构建更全面的prompt
            prompt = f"""作为专业的股票分析师，请对{stock_name}({stock_code})进行全面分析:

    1. 基本信息:
       - 股票名称: {stock_name}
       - 股票代码: {stock_code}
       - 行业: {industry}
       - 市场类型: {"A股" if market_type == 'A' else "港股" if market_type == 'HK' else "美股"}

    2. 技术指标摘要:
       - 趋势: {technical_summary['trend']}
       - 波动率: {technical_summary['volatility']}
       - 成交量趋势: {technical_summary['volume_trend']}
       - RSI: {technical_summary['rsi_level']:.2f}
       - MACD信号: {technical_summary['macd_signal']}
       - 布林带位置: {technical_summary['bb_position']}

    3. 支撑与压力位:
       - 短期支撑位: {', '.join([str(level) for level in sr_levels['support_levels']['short_term']])}
       - 中期支撑位: {', '.join([str(level) for level in sr_levels['support_levels']['medium_term']])}
       - 短期压力位: {', '.join([str(level) for level in sr_levels['resistance_levels']['short_term']])}
       - 中期压力位: {', '.join([str(level) for level in sr_levels['resistance_levels']['medium_term']])}

    4. 综合评分: {score_details['total']}分
       - 趋势评分: {score_details.get('trend', 0)}
       - 波动率评分: {score_details.get('volatility', 0)}
       - 技术指标评分: {score_details.get('technical', 0)}
       - 成交量评分: {score_details.get('volume', 0)}
       - 动量评分: {score_details.get('momentum', 0)}

    5. 投资建议: {recommendation}"""

            # 检查是否有JSON解析失败的情况
            if hasattr(self, 'json_match_flag') and not self.json_match_flag and 'original_content' in news_data:
                # 如果JSON解析失败，直接使用原始内容
                prompt += f"""

    6. 相关新闻和市场信息:
    {news_data.get('original_content', '无法获取相关新闻')}
    """
            else:
                # 正常情况下使用格式化的新闻数据
                prompt += f"""

    6. 近期相关新闻:
    {self._format_news_for_prompt(news_data.get('news', []))}

    7. 公司公告:
    {self._format_announcements_for_prompt(news_data.get('announcements', []))}

    8. 行业动态:
    {self._format_news_for_prompt(news_data.get('industry_news', []))}

    9. 市场情绪: {news_data.get('market_sentiment', 'neutral')}

    请提供以下内容:
    1. 技术面分析 - 详细分析价格走势、支撑压力位、主要技术指标的信号
    2. 行业和市场环境 - 结合新闻和行业动态分析公司所处环境
    3. 风险因素 - 识别潜在风险点
    4. 具体交易策略 - 给出明确的买入/卖出建议，包括入场点、止损位和目标价位
    5. 短期(1周)、中期(1-3个月)和长期(半年)展望

    请基于数据给出客观分析，不要过度乐观或悲观。分析应该包含具体数据和百分比，避免模糊表述。
    """

            messages = [{"role": "user", "content": prompt}]

            # 使用线程和队列添加超时控制
            result_queue = queue.Queue()

            def call_api():
                try:
                    response = openai.ChatCompletion.create(
                        model=self.openai_model,
                        messages=messages,
                        temperature=0.8,
                        max_tokens=4000,
                        stream=False,
                        timeout=180
                    )
                    result_queue.put(response)
                except Exception as e:
                    result_queue.put(e)

            # 启动API调用线程
            api_thread = threading.Thread(target=call_api)
            api_thread.daemon = True
            api_thread.start()

            # 等待结果，最多等待240秒
            try:
                result = result_queue.get(timeout=240)

                # 检查结果是否为异常
                if isinstance(result, Exception):
                    raise result

                # 提取助理回复
                assistant_reply = result["choices"][0]["message"]["content"].strip()
                return assistant_reply

            except queue.Empty:
                return "AI分析超时，无法获取分析结果。请稍后再试。"
            except Exception as e:
                return f"AI分析过程中发生错误: {str(e)}"

        except Exception as e:
            self.logger.error(f"AI分析发生错误: {str(e)}")
            return f"AI分析过程中发生错误，请稍后再试。错误信息: {str(e)}"

    def _calculate_bb_position(self, df):
        """计算价格在布林带中的位置"""
        latest = df.iloc[-1]
        bb_width = latest['BB_upper'] - latest['BB_lower']
        if bb_width == 0:
            return "middle"

        position = (latest['close'] - latest['BB_lower']) / bb_width

        if position < 0.2:
            return "near lower band (potential oversold)"
        elif position < 0.4:
            return "below middle band"
        elif position < 0.6:
            return "near middle band"
        elif position < 0.8:
            return "above middle band"
        else:
            return "near upper band (potential overbought)"

    def _format_news_for_prompt(self, news_list):
        """格式化新闻列表为prompt字符串"""
        if not news_list:
            return "   无最新相关新闻"

        formatted = ""
        for i, news in enumerate(news_list[:3]):  # 最多显示3条
            date = news.get('date', '')
            title = news.get('title', '')
            source = news.get('source', '')
            formatted += f"   {i + 1}. [{date}] {title} (来源: {source})\n"

        return formatted

    def _format_announcements_for_prompt(self, announcements):
        """格式化公告列表为prompt字符串"""
        if not announcements:
            return "   无最新公告"

        formatted = ""
        for i, ann in enumerate(announcements[:3]):  # 最多显示3条
            date = ann.get('date', '')
            title = ann.get('title', '')
            type_ = ann.get('type', '')
            formatted += f"   {i + 1}. [{date}] {title} (类型: {type_})\n"

        return formatted

    # 原有API：保持接口不变
    def analyze_stock(self, stock_code, market_type='A'):
        """分析单个股票"""
        try:
            # self.clear_cache(stock_code, market_type)
            # 获取股票数据
            df = self.get_stock_data(stock_code, market_type)
            self.logger.info(f"获取股票数据完成")
            # 计算技术指标
            df = self.calculate_indicators(df)
            self.logger.info(f"计算技术指标完成")
            # 评分系统
            score = self.calculate_score(df)
            self.logger.info(f"评分系统完成")
            # 获取最新数据
            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # 获取基本信息
            stock_info = self.get_stock_info(stock_code)
            stock_name = stock_info.get('股票名称', '未知')
            industry = stock_info.get('行业', '未知')

            # 生成报告（保持原有格式）
            report = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'industry': industry,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'score': score,
                'price': latest['close'],
                'price_change': (latest['close'] - prev['close']) / prev['close'] * 100,
                'ma_trend': 'UP' if latest['MA5'] > latest['MA20'] else 'DOWN',
                'rsi': latest['RSI'],
                'macd_signal': 'BUY' if latest['MACD'] > latest['Signal'] else 'SELL',
                'volume_status': '放量' if latest['Volume_Ratio'] > 1.5 else '平量',
                'recommendation': self.get_recommendation(score),
                'ai_analysis': self.get_ai_analysis(df, stock_code)
            }

            return report

        except Exception as e:
            self.logger.error(f"分析股票时出错: {str(e)}")
            raise

    # 原有API：保持接口不变
    def scan_market(self, stock_list, min_score=60, market_type='A'):
        """扫描市场，寻找符合条件的股票"""
        recommendations = []
        total_stocks = len(stock_list)

        self.logger.info(f"开始市场扫描，共 {total_stocks} 只股票")
        start_time = time.time()
        processed = 0

        # 批量处理，减少日志输出
        batch_size = 10
        for i in range(0, total_stocks, batch_size):
            batch = stock_list[i:i + batch_size]
            batch_results = []

            for stock_code in batch:
                try:
                    # 使用简化版分析以加快速度
                    report = self.quick_analyze_stock(stock_code, market_type)
                    if report['score'] >= min_score:
                        batch_results.append(report)
                except Exception as e:
                    self.logger.error(f"分析股票 {stock_code} 时出错: {str(e)}")
                    continue

            # 添加批处理结果
            recommendations.extend(batch_results)

            # 更新处理进度
            processed += len(batch)
            elapsed = time.time() - start_time
            remaining = (elapsed / processed) * (total_stocks - processed) if processed > 0 else 0

            self.logger.info(
                f"已处理 {processed}/{total_stocks} 只股票，耗时 {elapsed:.1f}秒，预计剩余 {remaining:.1f}秒")

        # 按得分排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        total_time = time.time() - start_time
        self.logger.info(
            f"市场扫描完成，共分析 {total_stocks} 只股票，找到 {len(recommendations)} 只符合条件的股票，总耗时 {total_time:.1f}秒")

        return recommendations

    # def quick_analyze_stock(self, stock_code, market_type='A'):
    #     """快速分析股票，用于市场扫描"""
    #     try:
    #         # 获取股票数据
    #         df = self.get_stock_data(stock_code, market_type)

    #         # 计算技术指标
    #         df = self.calculate_indicators(df)

    #         # 简化评分计算
    #         score = self.calculate_score(df)

    #         # 获取最新数据
    #         latest = df.iloc[-1]
    #         prev = df.iloc[-2] if len(df) > 1 else latest

    #         # 尝试获取股票名称和行业
    #         try:
    #             stock_info = self.get_stock_info(stock_code)
    #             stock_name = stock_info.get('股票名称', '未知')
    #             industry = stock_info.get('行业', '未知')
    #         except:
    #             stock_name = '未知'
    #             industry = '未知'

    #         # 生成简化报告
    #         report = {
    #             'stock_code': stock_code,
    #             'stock_name': stock_name,
    #             'industry': industry,
    #             'analysis_date': datetime.now().strftime('%Y-%m-%d'),
    #             'score': score,
    #             'price': float(latest['close']),
    #             'price_change': float((latest['close'] - prev['close']) / prev['close'] * 100),
    #             'ma_trend': 'UP' if latest['MA5'] > latest['MA20'] else 'DOWN',
    #             'rsi': float(latest['RSI']),
    #             'macd_signal': 'BUY' if latest['MACD'] > latest['Signal'] else 'SELL',
    #             'volume_status': '放量' if latest['Volume_Ratio'] > 1.5 else '平量',
    #             'recommendation': self.get_recommendation(score)
    #         }

    #         return report
    #     except Exception as e:
    #         self.logger.error(f"快速分析股票 {stock_code} 时出错: {str(e)}")
    #         raise

    def quick_analyze_stock(self, stock_code, market_type='A'):
        """快速分析股票，用于市场扫描"""
        try:
            # 获取股票数据
            df = self.get_stock_data(stock_code, market_type)

            # 计算技术指标
            df = self.calculate_indicators(df)

            # 简化评分计算
            score = self.calculate_score(df)

            # 获取最新数据
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            # 先获取股票信息再生成报告
            try:
                stock_info = self.get_stock_info(stock_code)
                stock_name = stock_info.get('股票名称', '未知')
                industry = stock_info.get('行业', '未知')

                # 添加日志
                self.logger.info(f"股票 {stock_code} 信息: 名称={stock_name}, 行业={industry}")
            except Exception as e:
                self.logger.error(f"获取股票 {stock_code} 信息时出错: {str(e)}")
                stock_name = '未知'
                industry = '未知'

            # 生成简化报告
            report = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'industry': industry,
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'score': score,
                'price': float(latest['close']),
                'price_change': float((latest['close'] - prev['close']) / prev['close'] * 100),
                'ma_trend': 'UP' if latest['MA5'] > latest['MA20'] else 'DOWN',
                'rsi': float(latest['RSI']),
                'macd_signal': 'BUY' if latest['MACD'] > latest['Signal'] else 'SELL',
                'volume_status': 'HIGH' if latest['Volume_Ratio'] > 1.5 else 'NORMAL',
                'recommendation': self.get_recommendation(score)
            }

            return report
        except Exception as e:
            self.logger.error(f"快速分析股票 {stock_code} 时出错: {str(e)}")
            raise

    # ======================== 新增功能 ========================#

    def get_stock_info(self, stock_code):
        """获取股票基本信息"""
        import akshare as ak

        cache_key = f"{stock_code}_info"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]

        try:
            # 获取A股股票基本信息
            stock_info = ak.stock_individual_info_em(symbol=stock_code)

            # 修改：使用列名而不是索引访问数据
            info_dict = {}
            for _, row in stock_info.iterrows():
                # 使用iloc安全地获取数据
                if len(row) >= 2:  # 确保有至少两列
                    info_dict[row.iloc[0]] = row.iloc[1]

            # 获取股票名称
            try:
                stock_name = ak.stock_info_a_code_name()

                # 检查数据框是否包含预期的列
                if '代码' in stock_name.columns and '名称' in stock_name.columns:
                    # 尝试找到匹配的股票代码
                    matched_stocks = stock_name[stock_name['代码'] == stock_code]
                    if not matched_stocks.empty:
                        name = matched_stocks['名称'].values[0]
                    else:
                        self.logger.warning(f"未找到股票代码 {stock_code} 的名称信息")
                        name = "未知"
                else:
                    # 尝试使用不同的列名
                    possible_code_columns = ['代码', 'code', 'symbol', '股票代码', 'stock_code']
                    possible_name_columns = ['名称', 'name', '股票名称', 'stock_name']

                    code_col = next((col for col in possible_code_columns if col in stock_name.columns), None)
                    name_col = next((col for col in possible_name_columns if col in stock_name.columns), None)

                    if code_col and name_col:
                        matched_stocks = stock_name[stock_name[code_col] == stock_code]
                        if not matched_stocks.empty:
                            name = matched_stocks[name_col].values[0]
                        else:
                            name = "未知"
                    else:
                        self.logger.warning(f"股票信息DataFrame结构不符合预期: {stock_name.columns.tolist()}")
                        name = "未知"
            except Exception as e:
                self.logger.error(f"获取股票名称时出错: {str(e)}")
                name = "未知"

            info_dict['股票名称'] = name

            # 确保基本字段存在
            if '行业' not in info_dict:
                info_dict['行业'] = "未知"
            if '地区' not in info_dict:
                info_dict['地区'] = "未知"

            # 增加更多日志来调试问题
            self.logger.info(f"获取到股票信息: 名称={name}, 行业={info_dict.get('行业', '未知')}")

            self.data_cache[cache_key] = info_dict
            return info_dict
        except Exception as e:
            self.logger.error(f"获取股票信息失败: {str(e)}")
            return {"股票名称": "未知", "行业": "未知", "地区": "未知"}

    def identify_support_resistance(self, df):
        """识别支撑位和压力位"""
        latest_price = df['close'].iloc[-1]

        # 使用布林带作为支撑压力参考
        support_levels = [df['BB_lower'].iloc[-1]]
        resistance_levels = [df['BB_upper'].iloc[-1]]

        # 添加主要均线作为支撑压力
        if latest_price < df['MA5'].iloc[-1]:
            resistance_levels.append(df['MA5'].iloc[-1])
        else:
            support_levels.append(df['MA5'].iloc[-1])

        if latest_price < df['MA20'].iloc[-1]:
            resistance_levels.append(df['MA20'].iloc[-1])
        else:
            support_levels.append(df['MA20'].iloc[-1])

        # 添加整数关口
        price_digits = len(str(int(latest_price)))
        base = 10 ** (price_digits - 1)

        lower_integer = math.floor(latest_price / base) * base
        upper_integer = math.ceil(latest_price / base) * base

        if lower_integer < latest_price:
            support_levels.append(lower_integer)
        if upper_integer > latest_price:
            resistance_levels.append(upper_integer)

        # 排序并格式化
        support_levels = sorted(set([round(x, 2) for x in support_levels if x < latest_price]), reverse=True)
        resistance_levels = sorted(set([round(x, 2) for x in resistance_levels if x > latest_price]))

        # 分类为短期和中期
        short_term_support = support_levels[:1] if support_levels else []
        medium_term_support = support_levels[1:2] if len(support_levels) > 1 else []
        short_term_resistance = resistance_levels[:1] if resistance_levels else []
        medium_term_resistance = resistance_levels[1:2] if len(resistance_levels) > 1 else []

        return {
            'support_levels': {
                'short_term': short_term_support,
                'medium_term': medium_term_support
            },
            'resistance_levels': {
                'short_term': short_term_resistance,
                'medium_term': medium_term_resistance
            }
        }

    def calculate_technical_score(self, df):
        """计算技术面评分 (0-40分)"""
        try:
            score = 0
            # 确保有足够的数据
            if len(df) < 2:
                self.logger.warning("数据不足，无法计算技术面评分")
                return {'total': 0, 'trend': 0, 'indicators': 0, 'support_resistance': 0, 'volatility_volume': 0}

            latest = df.iloc[-1]
            prev = df.iloc[-2]  # 获取前一个时间点的数据
            prev_close = prev['close']

            # 1. 趋势分析 (0-10分)
            trend_score = 0

            # 均线排列情况
            if latest['MA5'] > latest['MA20'] > latest['MA60']:  # 多头排列
                trend_score += 5
            elif latest['MA5'] < latest['MA20'] < latest['MA60']:  # 空头排列
                trend_score = 0
            else:  # 交叉状态
                if latest['MA5'] > latest['MA20']:
                    trend_score += 3
                if latest['MA20'] > latest['MA60']:
                    trend_score += 2

            # 价格与均线关系
            if latest['close'] > latest['MA5']:
                trend_score += 3
            elif latest['close'] > latest['MA20']:
                trend_score += 2

            # 限制最大值
            trend_score = min(trend_score, 10)
            score += trend_score

            # 2. 技术指标分析 (0-10分)
            indicator_score = 0

            # RSI
            if 40 <= latest['RSI'] <= 60:  # 中性
                indicator_score += 2
            elif 30 <= latest['RSI'] < 40 or 60 < latest['RSI'] <= 70:  # 边缘区域
                indicator_score += 4
            elif latest['RSI'] < 30:  # 超卖
                indicator_score += 5
            elif latest['RSI'] > 70:  # 超买
                indicator_score += 0

            # MACD
            if latest['MACD'] > latest['Signal']:  # MACD金叉或在零轴上方
                indicator_score += 3
            else:
                # 修复：比较当前和前一个时间点的MACD柱状图值
                if latest['MACD_hist'] > prev['MACD_hist']:  # 柱状图上升
                    indicator_score += 1

            # 限制最大值和最小值
            indicator_score = max(0, min(indicator_score, 10))
            score += indicator_score

            # 3. 支撑压力位分析 (0-10分)
            sr_score = 0

            # 识别支撑位和压力位
            middle_price = latest['close']
            upper_band = latest['BB_upper']
            lower_band = latest['BB_lower']

            # 距离布林带上下轨的距离
            upper_distance = (upper_band - middle_price) / middle_price * 100
            lower_distance = (middle_price - lower_band) / middle_price * 100

            if lower_distance < 2:  # 接近下轨
                sr_score += 5
            elif lower_distance < 5:
                sr_score += 3

            if upper_distance > 5:  # 距上轨较远
                sr_score += 5
            elif upper_distance > 2:
                sr_score += 2

            # 限制最大值
            sr_score = min(sr_score, 10)
            score += sr_score

            # 4. 波动性和成交量分析 (0-10分)
            vol_score = 0

            # 波动率分析
            if latest['Volatility'] < 2:  # 低波动率
                vol_score += 3
            elif latest['Volatility'] < 4:  # 中等波动率
                vol_score += 2

            # 成交量分析
            if 'Volume_Ratio' in df.columns:
                if latest['Volume_Ratio'] > 1.5 and latest['close'] > prev_close:  # 放量上涨
                    vol_score += 4
                elif latest['Volume_Ratio'] < 0.8 and latest['close'] < prev_close:  # 缩量下跌
                    vol_score += 3
                elif latest['Volume_Ratio'] > 1 and latest['close'] > prev_close:  # 普通放量上涨
                    vol_score += 2

            # 限制最大值
            vol_score = min(vol_score, 10)
            score += vol_score

            # 保存各个维度的分数
            technical_scores = {
                'total': score,
                'trend': trend_score,
                'indicators': indicator_score,
                'support_resistance': sr_score,
                'volatility_volume': vol_score
            }

            return technical_scores

        except Exception as e:
            self.logger.error(f"计算技术面评分时出错: {str(e)}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return {'total': 0, 'trend': 0, 'indicators': 0, 'support_resistance': 0, 'volatility_volume': 0}

    def perform_enhanced_analysis(self, stock_code, market_type='A'):
        """执行增强版分析"""
        try:
            # 记录开始时间，便于性能分析
            start_time = time.time()
            self.logger.info(f"开始执行股票 {stock_code} 的增强分析")

            # 获取股票数据
            df = self.get_stock_data(stock_code, market_type)
            data_time = time.time()
            self.logger.info(f"获取股票数据耗时: {data_time - start_time:.2f}秒")

            # 计算技术指标
            df = self.calculate_indicators(df)
            indicator_time = time.time()
            self.logger.info(f"计算技术指标耗时: {indicator_time - data_time:.2f}秒")

            # 获取最新数据
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            # 获取支撑压力位
            sr_levels = self.identify_support_resistance(df)

            # 计算技术面评分
            technical_score = self.calculate_technical_score(df)

            # 获取股票信息
            stock_info = self.get_stock_info(stock_code)

            # 确保technical_score包含必要的字段
            if 'total' not in technical_score:
                technical_score['total'] = 0

            # 生成增强版报告
            enhanced_report = {
                'basic_info': {
                    'stock_code': stock_code,
                    'stock_name': stock_info.get('股票名称', '未知'),
                    'industry': stock_info.get('行业', '未知'),
                    'analysis_date': datetime.now().strftime('%Y-%m-%d')
                },
                'price_data': {
                    'current_price': float(latest['close']),  # 确保是Python原生类型
                    'price_change': float((latest['close'] - prev['close']) / prev['close'] * 100),
                    'price_change_value': float(latest['close'] - prev['close'])
                },
                'technical_analysis': {
                    'trend': {
                        'ma_trend': 'UP' if latest['MA5'] > latest['MA20'] else 'DOWN',
                        'ma_status': "多头排列" if latest['MA5'] > latest['MA20'] > latest['MA60'] else
                        "空头排列" if latest['MA5'] < latest['MA20'] < latest['MA60'] else
                        "交叉状态",
                        'ma_values': {
                            'ma5': float(latest['MA5']),
                            'ma20': float(latest['MA20']),
                            'ma60': float(latest['MA60'])
                        }
                    },
                    'indicators': {
                        # 确保所有指标都存在并是原生类型
                        'rsi': float(latest['RSI']) if 'RSI' in latest else 50.0,
                        'macd': float(latest['MACD']) if 'MACD' in latest else 0.0,
                        'macd_signal': float(latest['Signal']) if 'Signal' in latest else 0.0,
                        'macd_histogram': float(latest['MACD_hist']) if 'MACD_hist' in latest else 0.0,
                        'volatility': float(latest['Volatility']) if 'Volatility' in latest else 0.0
                    },
                    'volume': {
                        'current_volume': float(latest['volume']) if 'volume' in latest else 0.0,
                        'volume_ratio': float(latest['Volume_Ratio']) if 'Volume_Ratio' in latest else 1.0,
                        'volume_status': '放量' if 'Volume_Ratio' in latest and latest['Volume_Ratio'] > 1.5 else '平量'
                    },
                    'support_resistance': sr_levels
                },
                'scores': technical_score,
                'recommendation': {
                    'action': self.get_recommendation(technical_score['total']),
                    'key_points': []
                },
                'ai_analysis': self.get_ai_analysis(df, stock_code)
            }

            # 最后检查并修复报告结构
            self._validate_and_fix_report(enhanced_report)

            # 在函数结束时记录总耗时
            end_time = time.time()
            self.logger.info(f"执行增强分析总耗时: {end_time - start_time:.2f}秒")

            return enhanced_report

        except Exception as e:
            self.logger.error(f"执行增强版分析时出错: {str(e)}")
            self.logger.error(traceback.format_exc())

            # 返回基础错误报告
            return {
                'basic_info': {
                    'stock_code': stock_code,
                    'stock_name': '分析失败',
                    'industry': '未知',
                    'analysis_date': datetime.now().strftime('%Y-%m-%d')
                },
                'price_data': {
                    'current_price': 0.0,
                    'price_change': 0.0,
                    'price_change_value': 0.0
                },
                'technical_analysis': {
                    'trend': {
                        'ma_trend': 'UNKNOWN',
                        'ma_status': '未知',
                        'ma_values': {'ma5': 0.0, 'ma20': 0.0, 'ma60': 0.0}
                    },
                    'indicators': {
                        'rsi': 50.0,
                        'macd': 0.0,
                        'macd_signal': 0.0,
                        'macd_histogram': 0.0,
                        'volatility': 0.0
                    },
                    'volume': {
                        'current_volume': 0.0,
                        'volume_ratio': 0.0,
                        'volume_status': 'NORMAL'
                    },
                    'support_resistance': {
                        'support_levels': {'short_term': [], 'medium_term': []},
                        'resistance_levels': {'short_term': [], 'medium_term': []}
                    }
                },
                'scores': {'total': 0},
                'recommendation': {'action': '分析出错，无法提供建议'},
                'ai_analysis': f"分析过程中出错: {str(e)}"
            }

            return error_report

    # 添加一个辅助方法确保报告结构完整
    def _validate_and_fix_report(self, report):
        """确保分析报告结构完整"""
        # 检查必要的顶级字段
        required_sections = ['basic_info', 'price_data', 'technical_analysis', 'scores', 'recommendation',
                             'ai_analysis']
        for section in required_sections:
            if section not in report:
                self.logger.warning(f"报告缺少 {section} 部分，添加空对象")
                report[section] = {}

        # 检查technical_analysis的结构
        if 'technical_analysis' in report:
            tech = report['technical_analysis']
            if not isinstance(tech, dict):
                report['technical_analysis'] = {}
                tech = report['technical_analysis']

            # 检查indicators部分
            if 'indicators' not in tech or not isinstance(tech['indicators'], dict):
                tech['indicators'] = {
                    'rsi': 50.0,
                    'macd': 0.0,
                    'macd_signal': 0.0,
                    'macd_histogram': 0.0,
                    'volatility': 0.0
                }

            # 转换所有指标为原生Python类型
            for key, value in tech['indicators'].items():
                try:
                    tech['indicators'][key] = float(value)
                except (TypeError, ValueError):
                    tech['indicators'][key] = 0.0