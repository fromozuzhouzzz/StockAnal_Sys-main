import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Boolean
try:
    from sqlalchemy.dialects.mysql import DECIMAL
except ImportError:
    # 如果MySQL驱动不可用，使用通用的Numeric类型
    from sqlalchemy import Numeric as DECIMAL
from sqlalchemy import Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 读取配置
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/stock_analyzer.db')
USE_DATABASE = os.getenv('USE_DATABASE', 'False').lower() == 'true'

# 自动修复MySQL驱动配置
def fix_mysql_driver_url(url):
    """自动修复MySQL连接URL以使用pymysql驱动"""
    if url.startswith('mysql://') and '+pymysql' not in url:
        # 将 mysql:// 替换为 mysql+pymysql://
        url = url.replace('mysql://', 'mysql+pymysql://', 1)
        logger.info("自动修复MySQL驱动URL以使用pymysql")
    return url

DATABASE_URL = fix_mysql_driver_url(DATABASE_URL)

# 初始化PyMySQL兼容性
def init_pymysql_compatibility():
    """初始化PyMySQL兼容性，使其能够替代MySQLdb"""
    try:
        import pymysql
        # 安装pymysql作为MySQLdb的替代品
        pymysql.install_as_MySQLdb()
        logger.info("PyMySQL兼容性初始化成功")
        return True
    except ImportError:
        logger.warning("PyMySQL未安装，MySQL功能可能不可用")
        return False
    except Exception as e:
        logger.warning(f"PyMySQL兼容性初始化失败: {e}")
        return False

# 如果使用MySQL，初始化PyMySQL兼容性
if 'mysql' in DATABASE_URL.lower():
    init_pymysql_compatibility()

# 数据库连接池配置
DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))
DATABASE_POOL_RECYCLE = int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))
DATABASE_POOL_TIMEOUT = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))

# 缓存配置
CACHE_DEFAULT_TTL = int(os.getenv('CACHE_DEFAULT_TTL', '900'))  # 15分钟
REALTIME_DATA_TTL = int(os.getenv('REALTIME_DATA_TTL', '300'))  # 5分钟
BASIC_INFO_TTL = int(os.getenv('BASIC_INFO_TTL', '604800'))  # 7天
FINANCIAL_DATA_TTL = int(os.getenv('FINANCIAL_DATA_TTL', '7776000'))  # 90天

# 创建引擎，添加连接池配置
if 'mysql' in DATABASE_URL.lower():
    engine = create_engine(
        DATABASE_URL,
        pool_size=DATABASE_POOL_SIZE,
        pool_recycle=DATABASE_POOL_RECYCLE,
        pool_timeout=DATABASE_POOL_TIMEOUT,
        pool_pre_ping=True,  # 验证连接有效性
        echo=False  # 生产环境关闭SQL日志
    )
else:
    # SQLite配置
    engine = create_engine(DATABASE_URL, echo=False)

Base = declarative_base()


# 定义模型
class StockInfo(Base):
    __tablename__ = 'stock_info'

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50))
    market_type = Column(String(5))
    industry = Column(String(50))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'market_type': self.market_type,
            'industry': self.industry,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class AnalysisResult(Base):
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False, index=True)
    market_type = Column(String(5))
    analysis_date = Column(DateTime, default=datetime.now)
    score = Column(Float)
    recommendation = Column(String(100))
    technical_data = Column(JSON)
    fundamental_data = Column(JSON)
    capital_flow_data = Column(JSON)
    ai_analysis = Column(Text)

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'market_type': self.market_type,
            'analysis_date': self.analysis_date.strftime('%Y-%m-%d %H:%M:%S') if self.analysis_date else None,
            'score': self.score,
            'recommendation': self.recommendation,
            'technical_data': self.technical_data,
            'fundamental_data': self.fundamental_data,
            'capital_flow_data': self.capital_flow_data,
            'ai_analysis': self.ai_analysis
        }


class Portfolio(Base):
    __tablename__ = 'portfolios'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), nullable=False, index=True)
    name = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    stocks = Column(JSON)  # 存储股票列表的JSON

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'stocks': self.stocks
        }


# ==================== 数据缓存相关模型 ====================

class StockBasicInfo(Base):
    """股票基本信息缓存表"""
    __tablename__ = 'stock_basic_info_cache'

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(100))
    market_type = Column(String(5), nullable=False)  # A, HK, US
    industry = Column(String(100))
    sector = Column(String(100))
    list_date = Column(String(10))  # 上市日期
    total_share = Column(Float)  # 总股本
    float_share = Column(Float)  # 流通股本
    market_cap = Column(Float)  # 市值
    pe_ratio = Column(Float)  # 市盈率
    pb_ratio = Column(Float)  # 市净率
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime)  # 缓存过期时间

    # 创建复合索引
    __table_args__ = (
        Index('idx_stock_market', 'stock_code', 'market_type'),
        Index('idx_expires_at', 'expires_at'),
    )

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'market_type': self.market_type,
            'industry': self.industry,
            'sector': self.sector,
            'list_date': self.list_date,
            'total_share': self.total_share,
            'float_share': self.float_share,
            'market_cap': self.market_cap,
            'pe_ratio': self.pe_ratio,
            'pb_ratio': self.pb_ratio,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def is_expired(self):
        """检查缓存是否过期"""
        return self.expires_at and datetime.now() > self.expires_at


class StockPriceHistory(Base):
    """股票历史价格数据缓存表"""
    __tablename__ = 'stock_price_history_cache'

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False, index=True)
    market_type = Column(String(5), nullable=False)
    trade_date = Column(String(10), nullable=False)  # YYYY-MM-DD格式
    open_price = Column(DECIMAL(10, 3))
    close_price = Column(DECIMAL(10, 3))
    high_price = Column(DECIMAL(10, 3))
    low_price = Column(DECIMAL(10, 3))
    volume = Column(Float)
    amount = Column(Float)  # 成交额
    change_pct = Column(Float)  # 涨跌幅
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 创建复合索引
    __table_args__ = (
        Index('idx_stock_date', 'stock_code', 'market_type', 'trade_date'),
        Index('idx_trade_date', 'trade_date'),
    )

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'market_type': self.market_type,
            'trade_date': self.trade_date,
            'open': float(self.open_price) if self.open_price else None,
            'close': float(self.close_price) if self.close_price else None,
            'high': float(self.high_price) if self.high_price else None,
            'low': float(self.low_price) if self.low_price else None,
            'volume': self.volume,
            'amount': self.amount,
            'change_pct': self.change_pct
        }


class StockRealtimeData(Base):
    """股票实时数据缓存表"""
    __tablename__ = 'stock_realtime_data_cache'

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False, index=True)
    market_type = Column(String(5), nullable=False)
    current_price = Column(DECIMAL(10, 3))
    change_amount = Column(DECIMAL(10, 3))  # 涨跌额
    change_pct = Column(Float)  # 涨跌幅
    volume = Column(Float)
    amount = Column(Float)  # 成交额
    turnover_rate = Column(Float)  # 换手率
    pe_ratio = Column(Float)  # 动态市盈率
    pb_ratio = Column(Float)  # 市净率
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime)  # 缓存过期时间

    # 创建复合索引
    __table_args__ = (
        Index('idx_stock_realtime', 'stock_code', 'market_type'),
        Index('idx_realtime_expires', 'expires_at'),
    )

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'market_type': self.market_type,
            'current_price': float(self.current_price) if self.current_price else None,
            'change_amount': float(self.change_amount) if self.change_amount else None,
            'change_pct': self.change_pct,
            'volume': self.volume,
            'amount': self.amount,
            'turnover_rate': self.turnover_rate,
            'pe_ratio': self.pe_ratio,
            'pb_ratio': self.pb_ratio,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def is_expired(self):
        """检查缓存是否过期"""
        return self.expires_at and datetime.now() > self.expires_at


class FinancialData(Base):
    """财务数据缓存表"""
    __tablename__ = 'financial_data_cache'

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False, index=True)
    market_type = Column(String(5), nullable=False)
    report_period = Column(String(10), nullable=False)  # 报告期 YYYY-Q1/Q2/Q3/Q4
    revenue = Column(Float)  # 营业收入
    net_profit = Column(Float)  # 净利润
    total_assets = Column(Float)  # 总资产
    total_equity = Column(Float)  # 股东权益
    roe = Column(Float)  # 净资产收益率
    roa = Column(Float)  # 总资产收益率
    gross_margin = Column(Float)  # 毛利率
    net_margin = Column(Float)  # 净利率
    debt_ratio = Column(Float)  # 资产负债率
    current_ratio = Column(Float)  # 流动比率
    eps = Column(Float)  # 每股收益
    bps = Column(Float)  # 每股净资产
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime)  # 缓存过期时间

    # 创建复合索引
    __table_args__ = (
        Index('idx_stock_financial', 'stock_code', 'market_type', 'report_period'),
        Index('idx_financial_expires', 'expires_at'),
    )

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'market_type': self.market_type,
            'report_period': self.report_period,
            'revenue': self.revenue,
            'net_profit': self.net_profit,
            'total_assets': self.total_assets,
            'total_equity': self.total_equity,
            'roe': self.roe,
            'roa': self.roa,
            'gross_margin': self.gross_margin,
            'net_margin': self.net_margin,
            'debt_ratio': self.debt_ratio,
            'current_ratio': self.current_ratio,
            'eps': self.eps,
            'bps': self.bps,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def is_expired(self):
        """检查缓存是否过期"""
        return self.expires_at and datetime.now() > self.expires_at


class CapitalFlowData(Base):
    """资金流向数据缓存表"""
    __tablename__ = 'capital_flow_data_cache'

    id = Column(Integer, primary_key=True)
    stock_code = Column(String(10), nullable=False, index=True)
    market_type = Column(String(5), nullable=False)
    trade_date = Column(String(10), nullable=False)  # YYYY-MM-DD格式
    main_inflow = Column(Float)  # 主力流入
    main_outflow = Column(Float)  # 主力流出
    main_net_flow = Column(Float)  # 主力净流入
    retail_inflow = Column(Float)  # 散户流入
    retail_outflow = Column(Float)  # 散户流出
    retail_net_flow = Column(Float)  # 散户净流入
    north_flow = Column(Float)  # 北向资金流入
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expires_at = Column(DateTime)  # 缓存过期时间

    # 创建复合索引
    __table_args__ = (
        Index('idx_stock_flow_date', 'stock_code', 'market_type', 'trade_date'),
        Index('idx_flow_expires', 'expires_at'),
    )

    def to_dict(self):
        return {
            'stock_code': self.stock_code,
            'market_type': self.market_type,
            'trade_date': self.trade_date,
            'main_inflow': self.main_inflow,
            'main_outflow': self.main_outflow,
            'main_net_flow': self.main_net_flow,
            'retail_inflow': self.retail_inflow,
            'retail_outflow': self.retail_outflow,
            'retail_net_flow': self.retail_net_flow,
            'north_flow': self.north_flow,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def is_expired(self):
        """检查缓存是否过期"""
        return self.expires_at and datetime.now() > self.expires_at


# 创建会话工厂
Session = sessionmaker(bind=engine)


# ==================== 数据库管理功能 ====================

def init_db():
    """初始化数据库"""
    try:
        Base.metadata.create_all(engine)
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def get_session():
    """获取数据库会话"""
    return Session()


def test_connection():
    """测试数据库连接"""
    try:
        session = get_session()
        session.execute("SELECT 1")
        session.close()
        logger.info("数据库连接测试成功")
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False


def cleanup_expired_cache():
    """清理过期的缓存数据"""
    if not USE_DATABASE:
        return

    try:
        session = get_session()
        current_time = datetime.now()

        # 清理过期的实时数据
        expired_realtime = session.query(StockRealtimeData).filter(
            StockRealtimeData.expires_at < current_time
        ).count()
        session.query(StockRealtimeData).filter(
            StockRealtimeData.expires_at < current_time
        ).delete()

        # 清理过期的基本信息
        expired_basic = session.query(StockBasicInfo).filter(
            StockBasicInfo.expires_at < current_time
        ).count()
        session.query(StockBasicInfo).filter(
            StockBasicInfo.expires_at < current_time
        ).delete()

        # 清理过期的财务数据
        expired_financial = session.query(FinancialData).filter(
            FinancialData.expires_at < current_time
        ).count()
        session.query(FinancialData).filter(
            FinancialData.expires_at < current_time
        ).delete()

        # 清理过期的资金流向数据
        expired_flow = session.query(CapitalFlowData).filter(
            CapitalFlowData.expires_at < current_time
        ).count()
        session.query(CapitalFlowData).filter(
            CapitalFlowData.expires_at < current_time
        ).delete()

        session.commit()
        session.close()

        total_cleaned = expired_realtime + expired_basic + expired_financial + expired_flow
        if total_cleaned > 0:
            logger.info(f"清理过期缓存数据: 实时数据{expired_realtime}条, "
                       f"基本信息{expired_basic}条, 财务数据{expired_financial}条, "
                       f"资金流向{expired_flow}条")

    except Exception as e:
        logger.error(f"清理过期缓存失败: {e}")


def get_cache_stats():
    """获取缓存统计信息"""
    if not USE_DATABASE:
        return {}

    try:
        session = get_session()

        stats = {
            'basic_info_count': session.query(StockBasicInfo).count(),
            'price_history_count': session.query(StockPriceHistory).count(),
            'realtime_data_count': session.query(StockRealtimeData).count(),
            'financial_data_count': session.query(FinancialData).count(),
            'capital_flow_count': session.query(CapitalFlowData).count(),
        }

        # 计算过期数据数量
        current_time = datetime.now()
        stats['expired_basic_info'] = session.query(StockBasicInfo).filter(
            StockBasicInfo.expires_at < current_time
        ).count()
        stats['expired_realtime'] = session.query(StockRealtimeData).filter(
            StockRealtimeData.expires_at < current_time
        ).count()
        stats['expired_financial'] = session.query(FinancialData).filter(
            FinancialData.expires_at < current_time
        ).count()
        stats['expired_flow'] = session.query(CapitalFlowData).filter(
            CapitalFlowData.expires_at < current_time
        ).count()

        session.close()
        return stats

    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        return {}


# 如果启用数据库，则初始化
if USE_DATABASE:
    try:
        init_db()
        if test_connection():
            logger.info("数据库缓存系统启动成功")
        else:
            logger.warning("数据库连接失败，将使用内存缓存")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        logger.warning("将使用内存缓存作为降级方案")