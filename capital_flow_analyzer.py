# capital_flow_analyzer.py
import logging
import traceback
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 导入新的数据访问层
from data_service import data_service


class CapitalFlowAnalyzer:
    def __init__(self):
        self.data_cache = {}
        self.stock_name_cache = {}  # 股票名称缓存
        self.max_retries = 3  # 最大重试次数
        self.api_timeout = 30  # API调用超时时间

        # 设置日志记录
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _retry_api_call(self, api_func, *args, **kwargs):
        """带重试机制的API调用"""
        for attempt in range(self.max_retries):
            try:
                return api_func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e)
                self.logger.warning(f"API调用第 {attempt + 1} 次尝试失败: {error_msg}")

                if attempt < self.max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    import time
                    time.sleep(wait_time)
                else:
                    raise e

    def get_stock_name_mapping(self):
        """获取股票代码到名称的映射"""
        try:
            # 检查缓存
            cache_key = "stock_name_mapping"
            if cache_key in self.stock_name_cache:
                cache_time, cached_data = self.stock_name_cache[cache_key]
                # 如果在24小时内有缓存数据，则返回缓存数据
                if (datetime.now() - cache_time).total_seconds() < 86400:
                    return cached_data

            self.logger.info("获取股票代码名称映射...")

            # 尝试获取A股股票基本信息
            stock_info = self._retry_api_call(ak.stock_info_a_code_name)

            # 创建代码到名称的映射
            name_mapping = {}
            if not stock_info.empty:
                # 检查列名
                if 'code' in stock_info.columns and 'name' in stock_info.columns:
                    for _, row in stock_info.iterrows():
                        code = str(row['code']).zfill(6)  # 确保代码为6位
                        name = row['name']
                        name_mapping[code] = name
                elif '代码' in stock_info.columns and '名称' in stock_info.columns:
                    for _, row in stock_info.iterrows():
                        code = str(row['代码']).zfill(6)  # 确保代码为6位
                        name = row['名称']
                        name_mapping[code] = name
                else:
                    self.logger.warning(f"股票信息DataFrame列名不符合预期: {stock_info.columns.tolist()}")

            # 缓存结果
            self.stock_name_cache[cache_key] = (datetime.now(), name_mapping)
            self.logger.info(f"成功获取 {len(name_mapping)} 个股票名称映射")

            return name_mapping

        except Exception as e:
            self.logger.error(f"获取股票名称映射失败: {str(e)}")
            # 返回一些常见股票的映射作为降级方案
            return self._get_fallback_stock_mapping()

    def _get_fallback_stock_mapping(self):
        """获取降级股票名称映射"""
        return {
            "000001": "平安银行", "000002": "万科A", "000858": "五粮液", "000725": "京东方A",
            "600519": "贵州茅台", "600036": "招商银行", "002415": "海康威视", "600276": "恒瑞医药",
            "000063": "中兴通讯", "002594": "比亚迪", "600887": "伊利股份", "000166": "申万宏源",
            "600031": "三一重工", "002304": "洋河股份", "600900": "长江电力", "000568": "泸州老窖",
            "002142": "宁波银行", "600585": "海螺水泥", "000338": "潍柴动力", "600000": "浦发银行",
            "601318": "中国平安", "000333": "美的集团", "601888": "中国中免", "600030": "中信证券",
            "601166": "兴业银行", "601398": "工商银行", "600028": "中国石化", "601988": "中国银行",
            "601857": "中国石油", "600019": "宝钢股份", "600050": "中国联通", "601328": "交通银行",
            "601668": "中国建筑", "601288": "农业银行", "000012": "南玻A", "000016": "深康佳A",
            "000021": "深科技", "000027": "深圳能源", "000039": "中集集团", "000060": "中金岭南",
            "000069": "华侨城A", "000100": "TCL科技", "000157": "中联重科", "000338": "潍柴动力"
        }

    def get_concept_fund_flow(self, period="10日排行"):
        """获取概念/行业资金流向数据，使用缓存机制"""
        try:
            self.logger.info(f"Getting concept fund flow for period: {period}")

            # 检查内存缓存
            cache_key = f"concept_fund_flow_{period}"
            if cache_key in self.data_cache:
                cache_time, cached_data = self.data_cache[cache_key]
                # 如果在最近一小时内有缓存数据，则返回缓存数据
                if (datetime.now() - cache_time).total_seconds() < 3600:
                    self.logger.info(f"使用缓存的概念资金流向数据: {period}")
                    return cached_data

            # 从akshare获取数据（带重试机制）
            concept_data = self._retry_api_call(ak.stock_fund_flow_concept, symbol=period)

            # 处理数据
            result = []
            for _, row in concept_data.iterrows():
                try:
                    # 列名可能有所不同，所以我们使用灵活的方法
                    item = {
                        "rank": int(row.get("序号", 0)),
                        "sector": row.get("行业", ""),
                        "company_count": int(row.get("公司家数", 0)),
                        "sector_index": float(row.get("行业指数", 0)),
                        "change_percent": self._parse_percent(row.get("阶段涨跌幅", "0%")),
                        "inflow": float(row.get("流入资金", 0)),
                        "outflow": float(row.get("流出资金", 0)),
                        "net_flow": float(row.get("净额", 0))
                    }
                    result.append(item)
                except Exception as e:
                    # self.logger.warning(f"Error processing row in concept fund flow: {str(e)}")
                    continue

            # 缓存结果
            self.data_cache[cache_key] = (datetime.now(), result)

            return result
        except Exception as e:
            self.logger.error(f"Error getting concept fund flow: {str(e)}")
            self.logger.error(traceback.format_exc())
            # 如果API调用失败则返回模拟数据
            return self._generate_mock_concept_fund_flow(period)

    def get_individual_fund_flow_rank(self, period="10日"):
        """获取个股资金流向排名"""
        try:
            self.logger.info(f"Getting individual fund flow ranking for period: {period}")

            # 检查缓存
            cache_key = f"individual_fund_flow_rank_{period}"
            if cache_key in self.data_cache:
                cache_time, cached_data = self.data_cache[cache_key]
                # 如果在最近一小时内有缓存数据，则返回缓存数据
                if (datetime.now() - cache_time).total_seconds() < 3600:
                    return cached_data

            # 从akshare获取数据
            stock_data = ak.stock_individual_fund_flow_rank(indicator=period)

            # 处理数据
            result = []
            for _, row in stock_data.iterrows():
                try:
                    # 根据不同时间段设置列名前缀
                    period_prefix = "" if period == "今日" else f"{period}"

                    item = {
                        "rank": int(row.get("序号", 0)),
                        "code": row.get("代码", ""),
                        "name": row.get("名称", ""),
                        "price": float(row.get("最新价", 0)),
                        "change_percent": float(row.get(f"{period_prefix}涨跌幅", 0)),
                        "main_net_inflow": float(row.get(f"{period_prefix}主力净流入-净额", 0)),
                        "main_net_inflow_percent": float(row.get(f"{period_prefix}主力净流入-净占比", 0)),
                        "super_large_net_inflow": float(row.get(f"{period_prefix}超大单净流入-净额", 0)),
                        "super_large_net_inflow_percent": float(row.get(f"{period_prefix}超大单净流入-净占比", 0)),
                        "large_net_inflow": float(row.get(f"{period_prefix}大单净流入-净额", 0)),
                        "large_net_inflow_percent": float(row.get(f"{period_prefix}大单净流入-净占比", 0)),
                        "medium_net_inflow": float(row.get(f"{period_prefix}中单净流入-净额", 0)),
                        "medium_net_inflow_percent": float(row.get(f"{period_prefix}中单净流入-净占比", 0)),
                        "small_net_inflow": float(row.get(f"{period_prefix}小单净流入-净额", 0)),
                        "small_net_inflow_percent": float(row.get(f"{period_prefix}小单净流入-净占比", 0))
                    }
                    result.append(item)
                except Exception as e:
                    self.logger.warning(f"Error processing row in individual fund flow rank: {str(e)}")
                    continue

            # 缓存结果
            self.data_cache[cache_key] = (datetime.now(), result)

            return result
        except Exception as e:
            self.logger.error(f"Error getting individual fund flow ranking: {str(e)}")
            self.logger.error(traceback.format_exc())
            # 如果API调用失败则返回模拟数据
            return self._generate_mock_individual_fund_flow_rank(period)

    def get_individual_fund_flow(self, stock_code, market_type="", re_date="10日"):
        """获取个股资金流向数据"""
        try:
            self.logger.info(f"Getting fund flow for stock: {stock_code}, market: {market_type}")

            # 检查缓存
            cache_key = f"individual_fund_flow_{stock_code}_{market_type}"
            if cache_key in self.data_cache:
                cache_time, cached_data = self.data_cache[cache_key]
                # 如果在一小时内有缓存数据，则返回缓存数据
                if (datetime.now() - cache_time).total_seconds() < 3600:
                    return cached_data

            # 如果未提供市场类型，则根据股票代码判断
            if not market_type:
                if stock_code.startswith('6'):
                    market_type = "sh"
                elif stock_code.startswith('0') or stock_code.startswith('3'):
                    market_type = "sz"
                else:
                    market_type = "sh"  # Default to Shanghai

            # 从akshare获取数据
            flow_data = ak.stock_individual_fund_flow(stock=stock_code, market=market_type)

            # 处理数据
            result = {
                "stock_code": stock_code,
                "data": []
            }

            for _, row in flow_data.iterrows():
                try:
                    item = {
                        "date": row.get("日期", ""),
                        "price": float(row.get("收盘价", 0)),
                        "change_percent": float(row.get("涨跌幅", 0)),
                        "main_net_inflow": float(row.get("主力净流入-净额", 0)),
                        "main_net_inflow_percent": float(row.get("主力净流入-净占比", 0)),
                        "super_large_net_inflow": float(row.get("超大单净流入-净额", 0)),
                        "super_large_net_inflow_percent": float(row.get("超大单净流入-净占比", 0)),
                        "large_net_inflow": float(row.get("大单净流入-净额", 0)),
                        "large_net_inflow_percent": float(row.get("大单净流入-净占比", 0)),
                        "medium_net_inflow": float(row.get("中单净流入-净额", 0)),
                        "medium_net_inflow_percent": float(row.get("中单净流入-净占比", 0)),
                        "small_net_inflow": float(row.get("小单净流入-净额", 0)),
                        "small_net_inflow_percent": float(row.get("小单净流入-净占比", 0))
                    }
                    result["data"].append(item)
                except Exception as e:
                    self.logger.warning(f"Error processing row in individual fund flow: {str(e)}")
                    continue

            # 计算汇总统计数据
            if result["data"]:
                # 最近数据 (最近10天)
                recent_data = result["data"][:min(10, len(result["data"]))]

                result["summary"] = {
                    "recent_days": len(recent_data),
                    "total_main_net_inflow": sum(item["main_net_inflow"] for item in recent_data),
                    "avg_main_net_inflow_percent": np.mean(
                        [item["main_net_inflow_percent"] for item in recent_data]),
                    "positive_days": sum(1 for item in recent_data if item["main_net_inflow"] > 0),
                    "negative_days": sum(1 for item in recent_data if item["main_net_inflow"] <= 0)
                }

            # Cache the result
            self.data_cache[cache_key] = (datetime.now(), result)

            return result
        except Exception as e:
            self.logger.error(f"Error getting individual fund flow: {str(e)}")
            self.logger.error(traceback.format_exc())
            # 如果API调用失败则返回模拟数据
            return self._generate_mock_individual_fund_flow(stock_code, market_type)

    def get_sector_stocks(self, sector):
        """获取特定行业的股票，带重试机制和详细错误处理"""
        try:
            self.logger.info(f"正在获取行业 '{sector}' 的成分股数据")

            # 检查缓存
            cache_key = f"sector_stocks_{sector}"
            if cache_key in self.data_cache:
                cache_time, cached_data = self.data_cache[cache_key]
                # 如果在一小时内有缓存数据，则返回缓存数据
                if (datetime.now() - cache_time).total_seconds() < 3600:
                    self.logger.info(f"使用缓存的行业成分股数据: {sector}")
                    return cached_data

            # 尝试多种API接口获取数据
            api_methods = [
                # 方法1：使用行业板块成分股接口
                lambda: self._retry_api_call(ak.stock_board_industry_cons_em, symbol=sector),
                # 方法2：尝试概念板块成分股接口
                lambda: self._retry_api_call(ak.stock_board_concept_cons_em, symbol=sector)
            ]

            for i, api_method in enumerate(api_methods):
                try:
                    self.logger.info(f"尝试API方法 {i+1} 获取 '{sector}' 成分股")
                    stocks = api_method()

                    # 验证数据有效性
                    if stocks is None or stocks.empty:
                        self.logger.warning(f"API方法 {i+1} 返回空数据")
                        continue

                    # 检查必要的列是否存在
                    required_columns = ['代码']
                    if not all(col in stocks.columns for col in required_columns):
                        self.logger.warning(f"API方法 {i+1} 返回数据缺少必要列: {stocks.columns.tolist()}")
                        continue

                    # 处理数据
                    result = []
                    processed_count = 0
                    for _, row in stocks.iterrows():
                        try:
                            # 获取股票代码和名称
                            stock_code = str(row.get("代码", "")).strip()
                            stock_name = str(row.get("名称", "")).strip()

                            # 验证股票代码格式
                            if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
                                continue

                            item = {
                                "code": stock_code,
                                "name": stock_name if stock_name else f"股票{stock_code}",
                                "price": float(row.get("最新价", 0)) if pd.notna(row.get("最新价")) else 0.0,
                                "change_percent": float(row.get("涨跌幅", 0)) if pd.notna(row.get("涨跌幅")) else 0.0,
                                "main_net_inflow": 0,  # 资金流向数据需要单独获取
                                "main_net_inflow_percent": 0
                            }
                            result.append(item)
                            processed_count += 1
                        except Exception as e:
                            self.logger.warning(f"处理股票数据行时出错: {str(e)}")
                            continue

                    if result:
                        self.logger.info(f"成功从API方法 {i+1} 获取到 {processed_count} 只 '{sector}' 成分股")
                        # 缓存结果
                        self.data_cache[cache_key] = (datetime.now(), result)
                        return result
                    else:
                        self.logger.warning(f"API方法 {i+1} 处理后无有效数据")

                except Exception as e:
                    self.logger.warning(f"API方法 {i+1} 调用失败: {str(e)}")
                    continue

            # 所有API方法都失败，使用模拟数据
            self.logger.warning(f"所有API方法都失败，使用模拟数据生成 '{sector}' 成分股")
            result = self._generate_mock_sector_stocks(sector)
            self.data_cache[cache_key] = (datetime.now(), result)
            return result

        except Exception as e:
            self.logger.error(f"获取行业成分股时发生严重错误: {str(e)}")
            self.logger.error(traceback.format_exc())
            # 最终降级方案
            return self._generate_mock_sector_stocks(sector)

    def calculate_capital_flow_score(self, stock_code, market_type=""):
        """计算股票资金流向评分"""
        try:
            self.logger.info(f"Calculating capital flow score for stock: {stock_code}")

            # 获取个股资金流向数据
            fund_flow = self.get_individual_fund_flow(stock_code, market_type)

            if not fund_flow or not fund_flow.get("data") or not fund_flow.get("summary"):
                return {
                    "total": 0,
                    "main_force": 0,
                    "large_order": 0,
                    "small_order": 0,
                    "details": {}
                }

            # Extract summary statistics
            summary = fund_flow["summary"]
            recent_days = summary["recent_days"]
            total_main_net_inflow = summary["total_main_net_inflow"]
            avg_main_net_inflow_percent = summary["avg_main_net_inflow_percent"]
            positive_days = summary["positive_days"]

            # Calculate main force score (0-40)
            main_force_score = 0

            # 基于净流入百分比的评分
            if avg_main_net_inflow_percent > 3:
                main_force_score += 20
            elif avg_main_net_inflow_percent > 1:
                main_force_score += 15
            elif avg_main_net_inflow_percent > 0:
                main_force_score += 10

            # 基于上涨天数的评分
            positive_ratio = positive_days / recent_days if recent_days > 0 else 0
            if positive_ratio > 0.7:
                main_force_score += 20
            elif positive_ratio > 0.5:
                main_force_score += 15
            elif positive_ratio > 0.3:
                main_force_score += 10

            # 计算大单评分（0-30分）
            large_order_score = 0

            # 分析超大单和大单交易
            recent_super_large = [item["super_large_net_inflow"] for item in
                                   fund_flow["data"][:recent_days]]
            recent_large = [item["large_net_inflow"] for item in fund_flow["data"][:recent_days]]

            super_large_positive = sum(1 for x in recent_super_large if x > 0)
            large_positive = sum(1 for x in recent_large if x > 0)

            # 基于超大单的评分
            super_large_ratio = super_large_positive / recent_days if recent_days > 0 else 0
            if super_large_ratio > 0.7:
                large_order_score += 15
            elif super_large_ratio > 0.5:
                large_order_score += 10
            elif super_large_ratio > 0.3:
                large_order_score += 5

            # 基于大单的评分
            large_ratio = large_positive / recent_days if recent_days > 0 else 0
            if large_ratio > 0.7:
                large_order_score += 15
            elif large_ratio > 0.5:
                large_order_score += 10
            elif large_ratio > 0.3:
                large_order_score += 5

            # 计算小单评分（0-30分）
            small_order_score = 0

            # 分析中单和小单交易
            recent_medium = [item["medium_net_inflow"] for item in fund_flow["data"][:recent_days]]
            recent_small = [item["small_net_inflow"] for item in fund_flow["data"][:recent_days]]

            medium_positive = sum(1 for x in recent_medium if x > 0)
            small_positive = sum(1 for x in recent_small if x > 0)

            # 基于中单的评分
            medium_ratio = medium_positive / recent_days if recent_days > 0 else 0
            if medium_ratio > 0.7:
                small_order_score += 15
            elif medium_ratio > 0.5:
                small_order_score += 10
            elif medium_ratio > 0.3:
                small_order_score += 5

            # 基于小单的评分
            small_ratio = small_positive / recent_days if recent_days > 0 else 0
            if small_ratio > 0.7:
                small_order_score += 15
            elif small_ratio > 0.5:
                small_order_score += 10
            elif small_ratio > 0.3:
                small_order_score += 5

            # 计算总评分
            total_score = main_force_score + large_order_score + small_order_score

            return {
                "total": total_score,
                "main_force": main_force_score,
                "large_order": large_order_score,
                "small_order": small_order_score,
                "details": fund_flow
            }
        except Exception as e:
            self.logger.error(f"Error calculating capital flow score: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "total": 0,
                "main_force": 0,
                "large_order": 0,
                "small_order": 0,
                "details": {},
                "error": str(e)
            }

    def _parse_percent(self, percent_str):
        """将百分比字符串转换为浮点数"""
        try:
            if isinstance(percent_str, str) and '%' in percent_str:
                return float(percent_str.replace('%', ''))
            return float(percent_str)
        except (ValueError, TypeError):
            return 0.0

    def _generate_mock_concept_fund_flow(self, period):
        """生成模拟概念资金流向数据"""
        # self.logger.warning(f"Generating mock concept fund flow data for period: {period}")

        sectors = [
            "新能源", "医药", "半导体", "芯片", "人工智能", "大数据", "云计算", "5G",
            "汽车", "消费", "金融", "互联网", "游戏", "农业", "化工", "建筑", "军工",
            "钢铁", "有色金属", "煤炭", "石油"
        ]

        result = []
        for i, sector in enumerate(sectors):
            # 随机数据 - 前半部分为正，后半部分为负
            is_positive = i < len(sectors) // 2

            inflow = round(np.random.uniform(10, 50), 2) if is_positive else round(
                np.random.uniform(5, 20), 2)
            outflow = round(np.random.uniform(5, 20), 2) if is_positive else round(
                np.random.uniform(10, 50), 2)
            net_flow = round(inflow - outflow, 2)

            change_percent = round(np.random.uniform(0, 5), 2) if is_positive else round(
                np.random.uniform(-5, 0), 2)

            item = {
                "rank": i + 1,
                "sector": sector,
                "company_count": np.random.randint(10, 100),
                "sector_index": round(np.random.uniform(1000, 5000), 2),
                "change_percent": change_percent,
                "inflow": inflow,
                "outflow": outflow,
                "net_flow": net_flow
            }
            result.append(item)

        # 按净流入降序排序
        return sorted(result, key=lambda x: x["net_flow"], reverse=True)

    def _generate_mock_individual_fund_flow_rank(self, period):
        """生成模拟个股资金流向排名数据"""
        # self.logger.warning(f"Generating mock individual fund flow ranking data for period: {period}")

        # Sample stock data
        stocks = [
            {"code": "600000", "name": "浦发银行"}, {"code": "600036", "name": "招商银行"},
            {"code": "601318", "name": "中国平安"}, {"code": "600519", "name": "贵州茅台"},
            {"code": "000858", "name": "五粮液"}, {"code": "000333", "name": "美的集团"},
            {"code": "600276", "name": "恒瑞医药"}, {"code": "601888", "name": "中国中免"},
            {"code": "600030", "name": "中信证券"}, {"code": "601166", "name": "兴业银行"},
            {"code": "600887", "name": "伊利股份"}, {"code": "601398", "name": "工商银行"},
            {"code": "600028", "name": "中国石化"}, {"code": "601988", "name": "中国银行"},
            {"code": "601857", "name": "中国石油"}, {"code": "600019", "name": "宝钢股份"},
            {"code": "600050", "name": "中国联通"}, {"code": "601328", "name": "交通银行"},
            {"code": "601668", "name": "中国建筑"}, {"code": "601288", "name": "农业银行"}
        ]

        result = []
        for i, stock in enumerate(stocks):
            # 随机数据 - 前半部分为正，后半部分为负
            is_positive = i < len(stocks) // 2

            main_net_inflow = round(np.random.uniform(1e6, 5e7), 2) if is_positive else round(
                np.random.uniform(-5e7, -1e6), 2)
            main_net_inflow_percent = round(np.random.uniform(1, 10), 2) if is_positive else round(
                np.random.uniform(-10, -1), 2)

            super_large_net_inflow = round(main_net_inflow * np.random.uniform(0.3, 0.5), 2)
            super_large_net_inflow_percent = round(main_net_inflow_percent * np.random.uniform(0.3, 0.5), 2)

            large_net_inflow = round(main_net_inflow * np.random.uniform(0.3, 0.5), 2)
            large_net_inflow_percent = round(main_net_inflow_percent * np.random.uniform(0.3, 0.5), 2)

            medium_net_inflow = round(np.random.uniform(-1e6, 1e6), 2)
            medium_net_inflow_percent = round(np.random.uniform(-2, 2), 2)

            small_net_inflow = round(np.random.uniform(-1e6, 1e6), 2)
            small_net_inflow_percent = round(np.random.uniform(-2, 2), 2)

            change_percent = round(np.random.uniform(0, 5), 2) if is_positive else round(np.random.uniform(-5, 0), 2)

            item = {
                "rank": i + 1,
                "code": stock["code"],
                "name": stock["name"],
                "price": round(np.random.uniform(10, 100), 2),
                "change_percent": change_percent,
                "main_net_inflow": main_net_inflow,
                "main_net_inflow_percent": main_net_inflow_percent,
                "super_large_net_inflow": super_large_net_inflow,
                "super_large_net_inflow_percent": super_large_net_inflow_percent,
                "large_net_inflow": large_net_inflow,
                "large_net_inflow_percent": large_net_inflow_percent,
                "medium_net_inflow": medium_net_inflow,
                "medium_net_inflow_percent": medium_net_inflow_percent,
                "small_net_inflow": small_net_inflow,
                "small_net_inflow_percent": small_net_inflow_percent
            }
            result.append(item)

        # 按主力净流入降序排序
        return sorted(result, key=lambda x: x["main_net_inflow"], reverse=True)

    def _generate_mock_individual_fund_flow(self, stock_code, market_type):
        """生成模拟个股资金流向数据"""
        # self.logger.warning(f"Generating mock individual fund flow data for stock: {stock_code}")

        # 生成30天的模拟数据
        end_date = datetime.now()

        result = {
            "stock_code": stock_code,
            "data": []
        }

        # 创建模拟价格趋势（使用合理的随机游走）
        base_price = np.random.uniform(10, 100)
        current_price = base_price

        for i in range(30):
            date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')

            # 随机价格变化（-2%到+2%）
            change_percent = np.random.uniform(-2, 2)
            price = round(current_price * (1 + change_percent / 100), 2)
            current_price = price

            # 随机资金流向数据，与价格变化有一定相关性
            is_positive = change_percent > 0

            main_net_inflow = round(np.random.uniform(1e5, 5e6), 2) if is_positive else round(
                np.random.uniform(-5e6, -1e5), 2)
            main_net_inflow_percent = round(np.random.uniform(1, 5), 2) if is_positive else round(
                np.random.uniform(-5, -1), 2)

            super_large_net_inflow = round(main_net_inflow * np.random.uniform(0.3, 0.5), 2)
            super_large_net_inflow_percent = round(main_net_inflow_percent * np.random.uniform(0.3, 0.5), 2)

            large_net_inflow = round(main_net_inflow * np.random.uniform(0.3, 0.5), 2)
            large_net_inflow_percent = round(main_net_inflow_percent * np.random.uniform(0.3, 0.5), 2)

            medium_net_inflow = round(np.random.uniform(-1e5, 1e5), 2)
            medium_net_inflow_percent = round(np.random.uniform(-2, 2), 2)

            small_net_inflow = round(np.random.uniform(-1e5, 1e5), 2)
            small_net_inflow_percent = round(np.random.uniform(-2, 2), 2)

            item = {
                "date": date,
                "price": price,
                "change_percent": round(change_percent, 2),
                "main_net_inflow": main_net_inflow,
                "main_net_inflow_percent": main_net_inflow_percent,
                "super_large_net_inflow": super_large_net_inflow,
                "super_large_net_inflow_percent": super_large_net_inflow_percent,
                "large_net_inflow": large_net_inflow,
                "large_net_inflow_percent": large_net_inflow_percent,
                "medium_net_inflow": medium_net_inflow,
                "medium_net_inflow_percent": medium_net_inflow_percent,
                "small_net_inflow": small_net_inflow,
                "small_net_inflow_percent": small_net_inflow_percent
            }
            result["data"].append(item)

        # 按日期降序排序（最新的在前）
        result["data"].sort(key=lambda x: x["date"], reverse=True)

        # 计算汇总统计数据
        recent_data = result["data"][:10]

        result["summary"] = {
            "recent_days": len(recent_data),
            "total_main_net_inflow": sum(item["main_net_inflow"] for item in recent_data),
            "avg_main_net_inflow_percent": np.mean([item["main_net_inflow_percent"] for item in recent_data]),
            "positive_days": sum(1 for item in recent_data if item["main_net_inflow"] > 0),
            "negative_days": sum(1 for item in recent_data if item["main_net_inflow"] <= 0)
        }

        return result

    def _generate_mock_sector_stocks(self, sector):
        """生成模拟行业股票数据，使用真实的股票代码和名称"""
        self.logger.warning(f"使用模拟数据生成 {sector} 行业股票")

        # 获取股票名称映射
        stock_name_mapping = self.get_stock_name_mapping()

        # 从映射中获取可用的股票代码列表
        available_stocks = list(stock_name_mapping.keys())

        # 如果没有获取到股票映射，使用降级方案
        if not available_stocks:
            available_stocks = list(self._get_fallback_stock_mapping().keys())
            stock_name_mapping = self._get_fallback_stock_mapping()

        # 要生成的股票数量（从可用股票中随机选择）
        num_stocks = min(np.random.randint(20, 40), len(available_stocks))

        # 随机选择股票代码
        selected_stocks = np.random.choice(available_stocks, size=num_stocks, replace=False)

        result = []
        for i, stock_code in enumerate(selected_stocks):
            change_percent = round(np.random.uniform(-5, 5), 2)

            # 获取真实的股票名称
            stock_name = stock_name_mapping.get(stock_code, f"{sector}股票{i + 1}")

            item = {
                "code": stock_code,
                "name": stock_name,
                "price": round(np.random.uniform(10, 100), 2),
                "change_percent": change_percent,
                "main_net_inflow": round(np.random.uniform(-1e6, 1e6), 2),
                "main_net_inflow_percent": round(np.random.uniform(-5, 5), 2)
            }
            result.append(item)

        # 按主力净流入降序排序
        return sorted(result, key=lambda x: x["main_net_inflow"], reverse=True)