# -*- coding: utf-8 -*-
"""
智能分析系统（股票） - 股票市场数据分析系统
开发者：熊猫大侠
版本：v2.1.0
许可证：MIT License
"""
# industry_analyzer.py
import logging
import random
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class IndustryAnalyzer:
    def __init__(self):
        """初始化行业分析类"""
        self.data_cache = {}
        self.industry_code_map = {}  # 缓存行业名称到代码的映射

        # 设置日志记录
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def get_industry_fund_flow(self, symbol="即时"):
        """获取行业资金流向数据"""
        try:
            # 缓存键
            cache_key = f"industry_fund_flow_{symbol}"

            # 检查缓存
            if cache_key in self.data_cache:
                cache_time, cached_data = self.data_cache[cache_key]
                # 如果缓存时间在30分钟内，直接返回
                if (datetime.now() - cache_time).total_seconds() < 1800:
                    self.logger.info(f"从缓存获取行业资金流向数据: {symbol}")
                    return cached_data

            # 获取行业资金流向数据
            self.logger.info(f"从API获取行业资金流向数据: {symbol}")
            fund_flow_data = ak.stock_fund_flow_industry(symbol=symbol)

            # 打印列名以便调试
            self.logger.info(f"行业资金流向数据列名: {fund_flow_data.columns.tolist()}")

            # 转换为字典列表
            result = []

            if symbol == "即时":
                for _, row in fund_flow_data.iterrows():
                    try:
                        # 安全地将值转换为对应的类型
                        item = {
                            "rank": self._safe_int(row["序号"]),
                            "industry": str(row["行业"]),
                            "index": self._safe_float(row["行业指数"]),
                            "change": self._safe_percent(row["行业-涨跌幅"]),
                            "inflow": self._safe_float(row["流入资金"]),
                            "outflow": self._safe_float(row["流出资金"]),
                            "netFlow": self._safe_float(row["净额"]),
                            "companyCount": self._safe_int(row["公司家数"])
                        }

                        # 添加领涨股相关数据，如果存在
                        if "领涨股" in row:
                            item["leadingStock"] = str(row["领涨股"])
                        if "领涨股-涨跌幅" in row:
                            item["leadingStockChange"] = self._safe_percent(row["领涨股-涨跌幅"])
                        if "当前价" in row:
                            item["leadingStockPrice"] = self._safe_float(row["当前价"])

                        result.append(item)
                    except Exception as e:
                        self.logger.warning(f"处理行业资金流向数据行时出错: {str(e)}")
                        continue
            else:
                for _, row in fund_flow_data.iterrows():
                    try:
                        item = {
                            "rank": self._safe_int(row["序号"]),
                            "industry": str(row["行业"]),
                            "companyCount": self._safe_int(row["公司家数"]),
                            "index": self._safe_float(row["行业指数"]),
                            "change": self._safe_percent(row["阶段涨跌幅"]),
                            "inflow": self._safe_float(row["流入资金"]),
                            "outflow": self._safe_float(row["流出资金"]),
                            "netFlow": self._safe_float(row["净额"])
                        }
                        result.append(item)
                    except Exception as e:
                        self.logger.warning(f"处理行业资金流向数据行时出错: {str(e)}")
                        continue

            # 缓存结果
            self.data_cache[cache_key] = (datetime.now(), result)

            return result

        except Exception as e:
            self.logger.error(f"获取行业资金流向数据失败: {str(e)}")
            # 返回更详细的错误信息，包括堆栈跟踪
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def _safe_float(self, value):
        """安全地将值转换为浮点数"""
        try:
            if pd.isna(value):
                return 0.0
            return float(value)
        except:
            return 0.0

    def _safe_int(self, value):
        """安全地将值转换为整数"""
        try:
            if pd.isna(value):
                return 0
            return int(value)
        except:
            return 0

    def _safe_percent(self, value):
        """安全地将百分比值转换为字符串格式"""
        try:
            if pd.isna(value):
                return "0.00"

            # 如果是字符串并包含%，移除%符号
            if isinstance(value, str) and "%" in value:
                return value.replace("%", "")

            # 如果是数值，直接转换成字符串
            return str(float(value))
        except:
            return "0.00"

    def _get_industry_code(self, industry_name):
        """获取行业名称对应的板块代码"""
        try:
            # 如果已经缓存了行业代码映射，直接使用
            if not self.industry_code_map:
                # 获取东方财富行业板块名称及代码
                industry_list = ak.stock_board_industry_name_em()

                # 创建行业名称到代码的映射
                for _, row in industry_list.iterrows():
                    if '板块名称' in industry_list.columns and '板块代码' in industry_list.columns:
                        name = row['板块名称']
                        code = row['板块代码']
                        self.industry_code_map[name] = code

                self.logger.info(f"成功获取到 {len(self.industry_code_map)} 个行业代码映射")

            # 尝试精确匹配
            if industry_name in self.industry_code_map:
                return self.industry_code_map[industry_name]

            # 尝试模糊匹配
            for name, code in self.industry_code_map.items():
                if industry_name in name or name in industry_name:
                    self.logger.info(f"行业名称 '{industry_name}' 模糊匹配到 '{name}'，代码: {code}")
                    return code

            # 如果找不到匹配项，则返回None
            self.logger.warning(f"未找到行业 '{industry_name}' 对应的代码")
            return None

        except Exception as e:
            self.logger.error(f"获取行业代码时出错: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def get_industry_stocks(self, industry):
        """获取行业成分股"""
        try:
            # 缓存键
            cache_key = f"industry_stocks_{industry}"

            # 检查缓存
            if cache_key in self.data_cache:
                cache_time, cached_data = self.data_cache[cache_key]
                # 如果缓存时间在1小时内，直接返回
                if (datetime.now() - cache_time).total_seconds() < 3600:
                    self.logger.info(f"从缓存获取行业成分股: {industry}")
                    return cached_data

            # 获取行业成分股
            self.logger.info(f"获取 {industry} 行业成分股")

            result = []
            try:
                # 1. 首先尝试直接使用行业名称
                try:
                    stocks = ak.stock_board_industry_cons_em(symbol=industry)
                    self.logger.info(f"使用行业名称 '{industry}' 成功获取成分股")
                except Exception as direct_error:
                    self.logger.warning(f"使用行业名称获取成分股失败: {str(direct_error)}")
                    # 2. 尝试使用行业代码
                    industry_code = self._get_industry_code(industry)
                    if industry_code:
                        self.logger.info(f"尝试使用行业代码 {industry_code} 获取成分股")
                        stocks = ak.stock_board_industry_cons_em(symbol=industry_code)
                    else:
                        # 如果无法获取行业代码，抛出异常，进入模拟数据生成
                        raise ValueError(f"无法找到行业 '{industry}' 对应的代码")

                # 打印列名以便调试
                self.logger.info(f"行业成分股数据列名: {stocks.columns.tolist()}")

                # 转换为字典列表
                if not stocks.empty:
                    for _, row in stocks.iterrows():
                        try:
                            item = {
                                "code": str(row["代码"]),
                                "name": str(row["名称"]),
                                "price": self._safe_float(row["最新价"]),
                                "change": self._safe_float(row["涨跌幅"]),
                                "change_amount": self._safe_float(row["涨跌额"]) if "涨跌额" in row else 0.0,
                                "volume": self._safe_float(row["成交量"]) if "成交量" in row else 0.0,
                                "turnover": self._safe_float(row["成交额"]) if "成交额" in row else 0.0,
                                "amplitude": self._safe_float(row["振幅"]) if "振幅" in row else 0.0,
                                "turnover_rate": self._safe_float(row["换手率"]) if "换手率" in row else 0.0
                            }
                            result.append(item)
                        except Exception as e:
                            self.logger.warning(f"处理行业成分股数据行时出错: {str(e)}")
                            continue

            except Exception as e:
                # 3. 如果上述方法都失败，生成模拟数据
                self.logger.warning(f"无法通过API获取行业成分股，使用模拟数据: {str(e)}")
                result = self._generate_mock_industry_stocks(industry)

            # 缓存结果
            self.data_cache[cache_key] = (datetime.now(), result)

            return result

        except Exception as e:
            self.logger.error(f"获取行业成分股失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []

    def _generate_mock_industry_stocks(self, industry):
        """生成模拟的行业成分股数据"""
        self.logger.info(f"生成行业 {industry} 的模拟成分股数据")

        # 使用来自资金流向的行业数据获取该行业的基本信息
        fund_flow_data = self.get_industry_fund_flow("即时")
        industry_data = next((item for item in fund_flow_data if item["industry"] == industry), None)

        company_count = 20  # 默认值
        if industry_data and "companyCount" in industry_data:
            company_count = min(industry_data["companyCount"], 30)  # 限制最多30只股票

        # 生成模拟股票
        result = []
        for i in range(company_count):
            # 生成6位数字的股票代码，确保前缀是0或6
            prefix = "6" if i % 2 == 0 else "0"
            code = prefix + str(100000 + i).zfill(5)[-5:]

            # 生成股票价格和涨跌幅
            price = round(random.uniform(10, 100), 2)
            change = round(random.uniform(-5, 5), 2)

            # 生成成交量和成交额
            volume = round(random.uniform(100000, 10000000))
            turnover = round(volume * price / 10000, 2)  # 转换为万元

            # 生成换手率和振幅
            turnover_rate = round(random.uniform(0.5, 5), 2)
            amplitude = round(random.uniform(1, 10), 2)

            item = {
                "code": code,
                "name": f"{industry}股{i + 1}",
                "price": price,
                "change": change,
                "change_amount": round(price * change / 100, 2),
                "volume": volume,
                "turnover": turnover,
                "amplitude": amplitude,
                "turnover_rate": turnover_rate
            }
            result.append(item)

        # 按涨跌幅排序
        result.sort(key=lambda x: x["change"], reverse=True)

        return result

    def get_industry_detail(self, industry):
        """获取行业详细信息"""
        try:
            # 获取行业资金流向数据
            fund_flow_data = self.get_industry_fund_flow("即时")
            industry_data = next((item for item in fund_flow_data if item["industry"] == industry), None)

            if not industry_data:
                return None

            # 获取历史资金流向数据
            history_data = []

            for period in ["3日排行", "5日排行", "10日排行", "20日排行"]:
                period_data = self.get_industry_fund_flow(period)
                industry_period_data = next((item for item in period_data if item["industry"] == industry), None)

                if industry_period_data:
                    days = int(period.replace("日排行", ""))
                    date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

                    history_data.append({
                        "date": date,
                        "inflow": industry_period_data["inflow"],
                        "outflow": industry_period_data["outflow"],
                        "netFlow": industry_period_data["netFlow"],
                        "change": industry_period_data["change"]
                    })

            # 添加即时数据
            history_data.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "inflow": industry_data["inflow"],
                "outflow": industry_data["outflow"],
                "netFlow": industry_data["netFlow"],
                "change": industry_data["change"]
            })

            # 按日期排序
            history_data.sort(key=lambda x: x["date"])

            # 计算行业评分
            score = self.calculate_industry_score(industry_data, history_data)

            # 生成投资建议
            recommendation = self.generate_industry_recommendation(score, industry_data, history_data)

            # 构建结果
            result = {
                "industry": industry,
                "index": industry_data["index"],
                "change": industry_data["change"],
                "companyCount": industry_data["companyCount"],
                "inflow": industry_data["inflow"],
                "outflow": industry_data["outflow"],
                "netFlow": industry_data["netFlow"],
                "leadingStock": industry_data.get("leadingStock", ""),
                "leadingStockChange": industry_data.get("leadingStockChange", ""),
                "leadingStockPrice": industry_data.get("leadingStockPrice", 0),
                "score": score,
                "recommendation": recommendation,
                "flowHistory": history_data
            }

            return result

        except Exception as e:
            self.logger.error(f"获取行业详细信息失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def calculate_industry_score(self, industry_data, history_data):
        """计算行业评分"""
        try:
            # 基础分数为50分
            score = 50

            # 根据涨跌幅增减分数（-10到+10）
            change = float(industry_data["change"])
            if change > 3:
                score += 10
            elif change > 1:
                score += 5
            elif change < -3:
                score -= 10
            elif change < -1:
                score -= 5

            # 根据资金流向增减分数（-20到+20）
            netFlow = float(industry_data["netFlow"])

            if netFlow > 5:
                score += 20
            elif netFlow > 2:
                score += 15
            elif netFlow > 0:
                score += 10
            elif netFlow < -5:
                score -= 20
            elif netFlow < -2:
                score -= 15
            elif netFlow < 0:
                score -= 10

            # 根据历史资金流向趋势增减分数（-10到+10）
            if len(history_data) >= 2:
                net_flow_trend = 0
                for i in range(1, len(history_data)):
                    if float(history_data[i]["netFlow"]) > float(history_data[i - 1]["netFlow"]):
                        net_flow_trend += 1
                    else:
                        net_flow_trend -= 1

                if net_flow_trend > 0:
                    score += 10
                elif net_flow_trend < 0:
                    score -= 10

            # 限制分数在0-100之间
            score = max(0, min(100, score))

            return round(score)

        except Exception as e:
            self.logger.error(f"计算行业评分时出错: {str(e)}")
            return 50

    def generate_industry_recommendation(self, score, industry_data, history_data):
        """生成行业投资建议"""
        try:
            if score >= 80:
                return "行业景气度高，资金持续流入，建议积极配置"
            elif score >= 60:
                return "行业表现良好，建议适当加仓"
            elif score >= 40:
                return "行业表现一般，建议谨慎参与"
            else:
                return "行业下行趋势明显，建议减持规避风险"

        except Exception as e:
            self.logger.error(f"生成行业投资建议时出错: {str(e)}")
            return "无法生成投资建议"

    def compare_industries(self, limit=10):
        """比较不同行业的表现"""
        try:
            # 获取行业板块数据
            industry_data = ak.stock_board_industry_name_em()

            # 提取行业名称列表
            industries = industry_data['板块名称'].tolist() if '板块名称' in industry_data.columns else []

            if not industries:
                return {"error": "获取行业列表失败"}

            # 限制分析的行业数量
            industries = industries[:limit] if limit else industries

            # 分析各行业情况
            industry_results = []

            for industry in industries:
                try:
                    # 尝试获取行业板块代码
                    industry_code = None
                    for _, row in industry_data.iterrows():
                        if row['板块名称'] == industry:
                            industry_code = row['板块代码']
                            break

                    if not industry_code:
                        self.logger.warning(f"未找到行业 {industry} 的板块代码")
                        continue

                    # 尝试使用不同的参数来获取行业数据 - 不使用"3m"
                    try:
                        # 尝试不使用period参数
                        industry_info = ak.stock_board_industry_hist_em(symbol=industry_code)
                    except Exception as e1:
                        try:
                            # 尝试使用daily参数
                            industry_info = ak.stock_board_industry_hist_em(symbol=industry_code, period="daily")
                        except Exception as e2:
                            self.logger.warning(f"分析行业 {industry} 历史数据失败: {str(e1)}, {str(e2)}")
                            continue

                    # 计算行业涨跌幅
                    if not industry_info.empty:
                        latest = industry_info.iloc[0]

                        # 尝试获取涨跌幅，列名可能有变化
                        change = 0.0
                        if '涨跌幅' in latest.index:
                            change = latest['涨跌幅']
                        elif '涨跌幅' in industry_info.columns:
                            change = latest['涨跌幅']

                        # 尝试获取成交量和成交额
                        volume = 0.0
                        turnover = 0.0
                        if '成交量' in latest.index:
                            volume = latest['成交量']
                        elif '成交量' in industry_info.columns:
                            volume = latest['成交量']

                        if '成交额' in latest.index:
                            turnover = latest['成交额']
                        elif '成交额' in industry_info.columns:
                            turnover = latest['成交额']

                        industry_results.append({
                            "industry": industry,
                            "change": float(change) if change else 0.0,
                            "volume": float(volume) if volume else 0.0,
                            "turnover": float(turnover) if turnover else 0.0
                        })
                except Exception as e:
                    self.logger.error(f"分析行业 {industry} 时出错: {str(e)}")

            # 按涨跌幅排序
            industry_results.sort(key=lambda x: x.get('change', 0), reverse=True)

            return {
                "count": len(industry_results),
                "top_industries": industry_results[:5] if len(industry_results) >= 5 else industry_results,
                "bottom_industries": industry_results[-5:] if len(industry_results) >= 5 else [],
                "results": industry_results
            }

        except Exception as e:
            self.logger.error(f"比较行业表现时出错: {str(e)}")
            return {"error": f"比较行业表现时出错: {str(e)}"}