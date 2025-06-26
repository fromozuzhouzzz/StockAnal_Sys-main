# -*- coding: utf-8 -*-
"""
股票数据预缓存调度器
用于定时预缓存上证指数成分股数据，提升市场扫描性能
"""

import time
import threading
import logging
from datetime import datetime, timedelta
import traceback
import os

# 尝试导入可选依赖
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    ak = None

try:
    from data_service import data_service
    DATA_SERVICE_AVAILABLE = True
except ImportError:
    DATA_SERVICE_AVAILABLE = False
    data_service = None

try:
    from database import get_session, StockBasicInfo, StockPriceHistory
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Hugging Face Spaces 兼容性检查
HF_SPACES_MODE = os.getenv('SPACE_ID') is not None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('precache_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StockPrecacheScheduler:
    """股票数据预缓存调度器"""

    def __init__(self):
        self.is_running = False
        self.scheduler_thread = None
        self.precache_stats = {
            'last_run': None,
            'total_stocks': 0,
            'success_count': 0,
            'failed_count': 0,
            'duration': 0
        }
        self.scheduled_time = "00:00"  # 默认凌晨12点执行
    
    def get_index_stocks(self, index_code='000300'):
        """获取指数成分股列表"""
        try:
            logger.info(f"开始获取指数 {index_code} 成分股列表")

            if AKSHARE_AVAILABLE and ak:
                if index_code == '000300':  # 沪深300
                    df = ak.index_stock_cons(symbol="000300")
                    stock_codes = df['品种代码'].tolist()
                elif index_code == '000001':  # 上证指数
                    df = ak.index_stock_cons(symbol="000001")
                    stock_codes = df['品种代码'].tolist()
                elif index_code == '399001':  # 深证成指
                    df = ak.index_stock_cons(symbol="399001")
                    stock_codes = df['品种代码'].tolist()
                else:
                    # 默认使用沪深300前50只股票
                    df = ak.index_stock_cons(symbol="000300")
                    stock_codes = df['品种代码'].head(50).tolist()

                logger.info(f"成功获取 {len(stock_codes)} 只成分股")
                return stock_codes
            else:
                logger.warning("AKShare不可用，使用预定义股票列表")
                raise Exception("AKShare不可用")

        except Exception as e:
            logger.error(f"获取指数成分股失败: {e}")
            # 返回一些常见的大盘股作为备选
            return [
                '000001', '000002', '600000', '600036', '000858',
                '002415', '000063', '600519', '000166', '600276',
                '600887', '000725', '002304', '600031', '000568',
                '600104', '002142', '600009', '000776', '600028'
            ]
    
    def precache_stock_data(self, stock_code, market_type='A'):
        """预缓存单只股票的数据"""
        try:
            logger.debug(f"开始预缓存股票 {stock_code} 数据")

            if not DATA_SERVICE_AVAILABLE or not data_service:
                logger.warning("数据服务不可用，跳过预缓存")
                return False

            # 1. 预缓存基本信息
            basic_info = data_service.get_stock_basic_info(stock_code, market_type)
            if basic_info:
                logger.debug(f"股票 {stock_code} 基本信息缓存成功")

            # 2. 预缓存历史价格数据（最近1年）
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            price_data = data_service.get_stock_price_history(
                stock_code, market_type, start_date, end_date
            )
            if price_data is not None and len(price_data) > 0:
                logger.debug(f"股票 {stock_code} 价格历史数据缓存成功，共 {len(price_data)} 条记录")

            # 3. 预缓存实时数据
            realtime_data = data_service.get_stock_realtime_data(stock_code, market_type)
            if realtime_data:
                logger.debug(f"股票 {stock_code} 实时数据缓存成功")

            return True

        except Exception as e:
            logger.error(f"预缓存股票 {stock_code} 数据失败: {e}")
            return False
    
    def run_precache_task(self, index_code='000300', max_stocks=100):
        """执行预缓存任务"""
        start_time = time.time()
        logger.info("="*60)
        logger.info("🚀 开始执行股票数据预缓存任务")
        logger.info("="*60)
        
        try:
            # 获取指数成分股
            stock_codes = self.get_index_stocks(index_code)
            
            # 限制股票数量
            if len(stock_codes) > max_stocks:
                stock_codes = stock_codes[:max_stocks]
                logger.info(f"限制预缓存股票数量为 {max_stocks} 只")
            
            total_stocks = len(stock_codes)
            success_count = 0
            failed_count = 0
            
            logger.info(f"开始预缓存 {total_stocks} 只股票的数据")
            
            # 分批处理，避免过度占用资源
            batch_size = 10
            for i in range(0, total_stocks, batch_size):
                batch = stock_codes[i:i + batch_size]
                logger.info(f"处理批次 {i//batch_size + 1}/{(total_stocks + batch_size - 1)//batch_size}")
                
                for stock_code in batch:
                    try:
                        if self.precache_stock_data(stock_code):
                            success_count += 1
                            logger.info(f"✅ {stock_code} 预缓存成功 ({success_count}/{total_stocks})")
                        else:
                            failed_count += 1
                            logger.warning(f"❌ {stock_code} 预缓存失败 ({failed_count}/{total_stocks})")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"❌ {stock_code} 预缓存异常: {e}")
                
                # 批次间休息，避免API限流
                if i + batch_size < total_stocks:
                    time.sleep(2)
            
            # 更新统计信息
            duration = time.time() - start_time
            self.precache_stats.update({
                'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_stocks': total_stocks,
                'success_count': success_count,
                'failed_count': failed_count,
                'duration': duration
            })
            
            logger.info("="*60)
            logger.info("📊 预缓存任务完成统计")
            logger.info("="*60)
            logger.info(f"总股票数: {total_stocks}")
            logger.info(f"成功缓存: {success_count}")
            logger.info(f"失败数量: {failed_count}")
            logger.info(f"成功率: {(success_count/total_stocks*100):.1f}%")
            logger.info(f"总耗时: {duration:.1f}秒")
            logger.info(f"平均每只: {duration/total_stocks:.2f}秒")
            
        except Exception as e:
            logger.error(f"预缓存任务执行失败: {e}")
            logger.error(traceback.format_exc())
    
    def schedule_daily_precache(self, time_str="00:00", index_code='000300'):
        """安排每日预缓存任务"""
        logger.info(f"安排每日 {time_str} 执行预缓存任务")

        self.scheduled_time = time_str
        self.index_code = index_code

        logger.info(f"预缓存任务已安排在每天 {time_str} 执行")
    
    def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return

        self.is_running = True

        def run_scheduler():
            logger.info("预缓存调度器启动")
            while self.is_running:
                try:
                    # 检查是否到了执行时间
                    current_time = datetime.now().strftime("%H:%M")
                    if current_time == self.scheduled_time:
                        logger.info("到达预定时间，开始执行预缓存任务")
                        self.run_precache_task(getattr(self, 'index_code', '000300'))
                        # 等待一分钟，避免重复执行
                        time.sleep(60)

                    time.sleep(30)  # 每30秒检查一次
                except Exception as e:
                    logger.error(f"调度器运行异常: {e}")
                    time.sleep(60)
            logger.info("预缓存调度器停止")

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("预缓存调度器已启动")
    
    def stop_scheduler(self):
        """停止调度器"""
        if not self.is_running:
            logger.warning("调度器未在运行")
            return
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("预缓存调度器已停止")
    
    def get_stats(self):
        """获取预缓存统计信息"""
        return self.precache_stats.copy()
    
    def manual_precache(self, index_code='000300', max_stocks=50):
        """手动执行预缓存任务"""
        logger.info("手动执行预缓存任务")
        self.run_precache_task(index_code, max_stocks)

# 全局调度器实例
precache_scheduler = StockPrecacheScheduler()

def init_precache_scheduler():
    """初始化预缓存调度器"""
    try:
        # 在Hugging Face Spaces环境中，可能不需要启动调度器
        if HF_SPACES_MODE:
            logger.info("检测到Hugging Face Spaces环境，跳过自动调度器启动")
            return True
        
        # 安排每天凌晨12点执行预缓存
        precache_scheduler.schedule_daily_precache("00:00", "000300")
        
        # 启动调度器
        precache_scheduler.start_scheduler()
        
        logger.info("股票数据预缓存调度器初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"预缓存调度器初始化失败: {e}")
        return False

if __name__ == "__main__":
    # 测试预缓存功能
    scheduler = StockPrecacheScheduler()
    
    # 手动执行一次预缓存（测试用，只缓存10只股票）
    scheduler.manual_precache("000300", 10)
    
    # 显示统计信息
    stats = scheduler.get_stats()
    print("\n预缓存统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
