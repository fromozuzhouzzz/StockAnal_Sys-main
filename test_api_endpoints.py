# -*- coding: utf-8 -*-
"""
API端点测试用例
测试新增的API接口功能
"""

import unittest
import json
import time
import requests
from typing import Dict, Any

class APITestCase(unittest.TestCase):
    """API测试基类"""
    
    def setUp(self):
        self.base_url = "http://localhost:8888"
        self.api_key = "UZXJfw3YNX80DLfN"  # 测试用API密钥
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
    
    def make_request(self, method: str, endpoint: str, data: Dict = None) -> requests.Response:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"
        
        if method.upper() == "GET":
            return requests.get(url, headers=self.headers)
        elif method.upper() == "POST":
            return requests.post(url, headers=self.headers, json=data)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
    
    def assert_api_success(self, response: requests.Response):
        """断言API响应成功"""
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success', False))
        self.assertIn('data', data)
        self.assertIn('meta', data)


class PortfolioAnalysisTest(APITestCase):
    """投资组合分析API测试"""
    
    def test_portfolio_analysis_success(self):
        """测试投资组合分析成功案例"""
        data = {
            "stocks": [
                {
                    "stock_code": "000001.SZ",
                    "weight": 0.4,
                    "market_type": "A"
                },
                {
                    "stock_code": "600000.SH",
                    "weight": 0.6,
                    "market_type": "A"
                }
            ],
            "analysis_params": {
                "risk_preference": "moderate",
                "time_horizon": "medium"
            }
        }
        
        response = self.make_request("POST", "/api/v1/portfolio/analyze", data)
        self.assert_api_success(response)
        
        result = response.json()
        portfolio_data = result['data']
        
        # 验证返回数据结构
        self.assertIn('portfolio_score', portfolio_data)
        self.assertIn('risk_level', portfolio_data)
        self.assertIn('risk_analysis', portfolio_data)
        self.assertIn('recommendations', portfolio_data)
        self.assertIn('individual_stocks', portfolio_data)
        
        # 验证评分范围
        self.assertGreaterEqual(portfolio_data['portfolio_score'], 0)
        self.assertLessEqual(portfolio_data['portfolio_score'], 100)
        
        # 验证个股数据
        self.assertEqual(len(portfolio_data['individual_stocks']), 2)
    
    def test_portfolio_analysis_invalid_stock_code(self):
        """测试无效股票代码"""
        data = {
            "stocks": [
                {
                    "stock_code": "INVALID001",
                    "weight": 1.0,
                    "market_type": "A"
                }
            ]
        }
        
        response = self.make_request("POST", "/api/v1/portfolio/analyze", data)
        self.assertEqual(response.status_code, 400)
        
        result = response.json()
        self.assertFalse(result.get('success', True))
        self.assertEqual(result['error']['code'], 'INVALID_STOCK_CODE')
    
    def test_portfolio_analysis_empty_stocks(self):
        """测试空股票列表"""
        data = {"stocks": []}
        
        response = self.make_request("POST", "/api/v1/portfolio/analyze", data)
        self.assertEqual(response.status_code, 400)
        
        result = response.json()
        self.assertFalse(result.get('success', True))
    
    def test_portfolio_analysis_too_many_stocks(self):
        """测试股票数量过多"""
        stocks = []
        for i in range(51):  # 超过50只限制
            stocks.append({
                "stock_code": f"00000{i:02d}.SZ",
                "weight": 1.0/51,
                "market_type": "A"
            })
        
        data = {"stocks": stocks}
        
        response = self.make_request("POST", "/api/v1/portfolio/analyze", data)
        self.assertEqual(response.status_code, 400)
        
        result = response.json()
        self.assertEqual(result['error']['code'], 'PORTFOLIO_TOO_LARGE')


class StockAnalysisTest(APITestCase):
    """个股分析API测试"""
    
    def test_stock_analysis_success(self):
        """测试个股分析成功案例"""
        data = {
            "stock_code": "000001.SZ",
            "market_type": "A",
            "analysis_depth": "full",
            "include_ai_analysis": True
        }
        
        response = self.make_request("POST", "/api/v1/stock/analyze", data)
        self.assert_api_success(response)
        
        result = response.json()
        stock_data = result['data']
        
        # 验证返回数据结构
        self.assertIn('stock_info', stock_data)
        self.assertIn('analysis_result', stock_data)
        self.assertIn('technical_analysis', stock_data)
        self.assertIn('fundamental_analysis', stock_data)
        self.assertIn('risk_assessment', stock_data)
        
        # 验证股票信息
        stock_info = stock_data['stock_info']
        self.assertEqual(stock_info['stock_code'], '000001.SZ')
        self.assertEqual(stock_info['market_type'], 'A')
        
        # 验证分析结果
        analysis_result = stock_data['analysis_result']
        self.assertIn('overall_score', analysis_result)
        self.assertGreaterEqual(analysis_result['overall_score'], 0)
        self.assertLessEqual(analysis_result['overall_score'], 100)
    
    def test_stock_analysis_quick_mode(self):
        """测试快速分析模式"""
        data = {
            "stock_code": "600000.SH",
            "analysis_depth": "quick",
            "include_ai_analysis": False
        }
        
        response = self.make_request("POST", "/api/v1/stock/analyze", data)
        self.assert_api_success(response)
        
        result = response.json()
        # 快速模式应该不包含AI分析
        self.assertNotIn('ai_analysis', result['data'])
    
    def test_stock_analysis_invalid_code(self):
        """测试无效股票代码"""
        data = {"stock_code": "INVALID"}
        
        response = self.make_request("POST", "/api/v1/stock/analyze", data)
        self.assertEqual(response.status_code, 400)
        
        result = response.json()
        self.assertEqual(result['error']['code'], 'INVALID_STOCK_CODE')


class BatchScoreTest(APITestCase):
    """批量评分API测试"""
    
    def test_batch_score_success(self):
        """测试批量评分成功案例"""
        data = {
            "stock_codes": ["000001.SZ", "600000.SH", "000002.SZ"],
            "market_type": "A",
            "min_score": 50,
            "sort_by": "score",
            "sort_order": "desc"
        }
        
        response = self.make_request("POST", "/api/v1/stocks/batch-score", data)
        self.assert_api_success(response)
        
        result = response.json()
        batch_data = result['data']
        
        # 验证返回数据结构
        self.assertIn('total_analyzed', batch_data)
        self.assertIn('qualified_count', batch_data)
        self.assertIn('results', batch_data)
        
        # 验证分析数量
        self.assertEqual(batch_data['total_analyzed'], 3)
        
        # 验证结果排序
        results = batch_data['results']
        if len(results) > 1:
            for i in range(len(results) - 1):
                self.assertGreaterEqual(results[i]['score'], results[i+1]['score'])
    
    def test_batch_score_with_filter(self):
        """测试带过滤条件的批量评分"""
        data = {
            "stock_codes": ["000001.SZ", "600000.SH"],
            "min_score": 80  # 高分过滤
        }
        
        response = self.make_request("POST", "/api/v1/stocks/batch-score", data)
        self.assert_api_success(response)
        
        result = response.json()
        # 所有返回的股票评分都应该 >= 80
        for stock in result['data']['results']:
            self.assertGreaterEqual(stock['score'], 80)


class TaskManagementTest(APITestCase):
    """任务管理API测试"""
    
    def test_create_task_success(self):
        """测试创建任务成功"""
        data = {
            "task_type": "stock_analysis",
            "params": {
                "stock_code": "000001.SZ",
                "market_type": "A"
            }
        }
        
        response = self.make_request("POST", "/api/v1/tasks", data)
        self.assertEqual(response.status_code, 201)
        
        result = response.json()
        self.assertTrue(result.get('success'))
        
        task_data = result['data']
        self.assertIn('task_id', task_data)
        self.assertIn('task_type', task_data)
        self.assertEqual(task_data['status'], 'pending')
        
        # 保存任务ID用于后续测试
        self.task_id = task_data['task_id']
    
    def test_get_task_status(self):
        """测试查询任务状态"""
        # 先创建一个任务
        self.test_create_task_success()
        
        response = self.make_request("GET", f"/api/v1/tasks/{self.task_id}")
        self.assert_api_success(response)
        
        result = response.json()
        task_data = result['data']
        
        self.assertEqual(task_data['task_id'], self.task_id)
        self.assertIn('status', task_data)
        self.assertIn('progress', task_data)
    
    def test_get_nonexistent_task(self):
        """测试查询不存在的任务"""
        fake_task_id = "nonexistent-task-id"
        
        response = self.make_request("GET", f"/api/v1/tasks/{fake_task_id}")
        self.assertEqual(response.status_code, 404)
        
        result = response.json()
        self.assertEqual(result['error']['code'], 'TASK_NOT_FOUND')


class AuthenticationTest(APITestCase):
    """认证测试"""
    
    def test_missing_api_key(self):
        """测试缺少API密钥"""
        headers = {"Content-Type": "application/json"}  # 不包含API密钥
        
        response = requests.post(
            f"{self.base_url}/api/v1/stock/analyze",
            headers=headers,
            json={"stock_code": "000001.SZ"}
        )
        
        self.assertEqual(response.status_code, 401)
        result = response.json()
        self.assertEqual(result['error']['code'], 'MISSING_API_KEY')
    
    def test_invalid_api_key(self):
        """测试无效API密钥"""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": "invalid_key"
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/stock/analyze",
            headers=headers,
            json={"stock_code": "000001.SZ"}
        )
        
        self.assertEqual(response.status_code, 403)
        result = response.json()
        self.assertEqual(result['error']['code'], 'INVALID_API_KEY')


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
