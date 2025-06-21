# index_industry_analyzer.py
import akshare as ak
import pandas as pd
import numpy as np
import threading


class IndexIndustryAnalyzer:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.data_cache = {}

    def analyze_index(self, index_code, limit=30):
        """分析指数整体情况"""
        try:
            cache_key = f"index_{index_code}"
            if cache_key in self.data_cache:
                cache_time, cached_result = self.data_cache[cache_key]
                # 如果缓存时间在1小时内，直接返回
                if (pd.Timestamp.now() - cache_time).total_seconds() < 3600:
                    return cached_result

            # 获取指数成分股
            if index_code == '000300':
                # 沪深300成分股
                stocks = ak.index_stock_cons_weight_csindex(symbol="000300")
                index_name = "沪深300"
            elif index_code == '000905':
                # 中证500成分股
                stocks = ak.index_stock_cons_weight_csindex(symbol="000905")
                index_name = "中证500"
            elif index_code == '000852':
                # 中证1000成分股
                stocks = ak.index_stock_cons_weight_csindex(symbol="000852")
                index_name = "中证1000"
            elif index_code == '000001':
                # 上证指数
                stocks = ak.index_stock_cons_weight_csindex(symbol="000001")
                index_name = "上证指数"
            else:
                return {"error": "不支持的指数代码"}

            # 提取股票代码列表和权重
            stock_list = []
            if '成分券代码' in stocks.columns:
                stock_list = stocks['成分券代码'].tolist()
                weights = stocks['权重(%)'].tolist() if '权重(%)' in stocks.columns else [1] * len(stock_list)
            else:
                return {"error": "获取指数成分股失败"}

            # 限制分析的股票数量以提高性能
            if limit and len(stock_list) > limit:
                # 按权重排序，取前limit只权重最大的股票
                stock_weights = list(zip(stock_list, weights))
                stock_weights.sort(key=lambda x: x[1], reverse=True)
                stock_list = [s[0] for s in stock_weights[:limit]]
                weights = [s[1] for s in stock_weights[:limit]]

            # 多线程分析股票
            results = []
            threads = []
            results_lock = threading.Lock()

            def analyze_stock(stock_code, weight):
                try:
                    # 分析股票
                    result = self.analyzer.quick_analyze_stock(stock_code)
                    result['weight'] = weight

                    with results_lock:
                        results.append(result)
                except Exception as e:
                    print(f"分析股票 {stock_code} 时出错: {str(e)}")

            # 创建并启动线程
            for i, stock_code in enumerate(stock_list):
                weight = weights[i] if i < len(weights) else 1
                thread = threading.Thread(target=analyze_stock, args=(stock_code, weight))
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            # 计算指数整体情况
            total_weight = sum([r.get('weight', 1) for r in results])

            # 计算加权评分
            index_score = 0
            if total_weight > 0:
                index_score = sum([r.get('score', 0) * r.get('weight', 1) for r in results]) / total_weight

            # 计算其他指标
            up_count = sum(1 for r in results if r.get('price_change', 0) > 0)
            down_count = sum(1 for r in results if r.get('price_change', 0) < 0)
            flat_count = len(results) - up_count - down_count

            # 计算涨跌股比例
            up_ratio = up_count / len(results) if len(results) > 0 else 0

            # 计算加权平均涨跌幅
            weighted_change = 0
            if total_weight > 0:
                weighted_change = sum([r.get('price_change', 0) * r.get('weight', 1) for r in results]) / total_weight

            # 按评分对股票排序
            results.sort(key=lambda x: x.get('score', 0), reverse=True)

            # 整理结果
            index_analysis = {
                "index_code": index_code,
                "index_name": index_name,
                "score": round(index_score, 2),
                "stock_count": len(results),
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "up_ratio": up_ratio,
                "weighted_change": weighted_change,
                "top_stocks": results[:5] if len(results) >= 5 else results,
                "results": results
            }

            # 缓存结果
            self.data_cache[cache_key] = (pd.Timestamp.now(), index_analysis)

            return index_analysis

        except Exception as e:
            print(f"分析指数整体情况时出错: {str(e)}")
            return {"error": f"分析指数时出错: {str(e)}"}

    def analyze_industry(self, industry, limit=30):
        """分析行业整体情况"""
        try:
            cache_key = f"industry_{industry}"
            if cache_key in self.data_cache:
                cache_time, cached_result = self.data_cache[cache_key]
                # 如果缓存时间在1小时内，直接返回
                if (pd.Timestamp.now() - cache_time).total_seconds() < 3600:
                    return cached_result

            # 获取行业成分股
            stocks = ak.stock_board_industry_cons_em(symbol=industry)

            # 提取股票代码列表
            stock_list = stocks['代码'].tolist() if '代码' in stocks.columns else []

            if not stock_list:
                return {"error": "获取行业成分股失败"}

            # 限制分析的股票数量以提高性能
            if limit and len(stock_list) > limit:
                stock_list = stock_list[:limit]

            # 多线程分析股票
            results = []
            threads = []
            results_lock = threading.Lock()

            def analyze_stock(stock_code):
                try:
                    # 分析股票
                    result = self.analyzer.quick_analyze_stock(stock_code)

                    with results_lock:
                        results.append(result)
                except Exception as e:
                    print(f"分析股票 {stock_code} 时出错: {str(e)}")

            # 创建并启动线程
            for stock_code in stock_list:
                thread = threading.Thread(target=analyze_stock, args=(stock_code,))
                threads.append(thread)
                thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()

            # 计算行业整体情况
            if not results:
                return {"error": "分析行业股票失败"}

            # 计算平均评分
            industry_score = sum([r.get('score', 0) for r in results]) / len(results)

            # 计算其他指标
            up_count = sum(1 for r in results if r.get('price_change', 0) > 0)
            down_count = sum(1 for r in results if r.get('price_change', 0) < 0)
            flat_count = len(results) - up_count - down_count

            # 计算涨跌股比例
            up_ratio = up_count / len(results)

            # 计算平均涨跌幅
            avg_change = sum([r.get('price_change', 0) for r in results]) / len(results)

            # 按评分对股票排序
            results.sort(key=lambda x: x.get('score', 0), reverse=True)

            # 整理结果
            industry_analysis = {
                "industry": industry,
                "score": round(industry_score, 2),
                "stock_count": len(results),
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "up_ratio": up_ratio,
                "avg_change": avg_change,
                "top_stocks": results[:5] if len(results) >= 5 else results,
                "results": results
            }

            # 缓存结果
            self.data_cache[cache_key] = (pd.Timestamp.now(), industry_analysis)

            return industry_analysis

        except Exception as e:
            print(f"分析行业整体情况时出错: {str(e)}")
            return {"error": f"分析行业时出错: {str(e)}"}

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
                    # 简化分析，只获取基本指标
                    industry_info = ak.stock_board_industry_hist_em(symbol=industry, period="3m")

                    # 计算行业涨跌幅
                    if not industry_info.empty:
                        latest = industry_info.iloc[0]
                        change = latest['涨跌幅'] if '涨跌幅' in latest.index else 0

                        industry_results.append({
                            "industry": industry,
                            "change": change,
                            "volume": latest['成交量'] if '成交量' in latest.index else 0,
                            "turnover": latest['成交额'] if '成交额' in latest.index else 0
                        })
                except Exception as e:
                    print(f"分析行业 {industry} 时出错: {str(e)}")

            # 按涨跌幅排序
            industry_results.sort(key=lambda x: x.get('change', 0), reverse=True)

            return {
                "count": len(industry_results),
                "top_industries": industry_results[:5] if len(industry_results) >= 5 else industry_results,
                "bottom_industries": industry_results[-5:] if len(industry_results) >= 5 else [],
                "results": industry_results
            }

        except Exception as e:
            print(f"比较行业表现时出错: {str(e)}")
            return {"error": f"比较行业表现时出错: {str(e)}"}