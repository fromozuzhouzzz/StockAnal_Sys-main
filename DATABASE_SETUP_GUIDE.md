# 股票分析系统数据库缓存配置指南

## 📋 概述

本指南将帮助您为股票分析系统配置MySQL数据库缓存，以提升系统性能和稳定性。

## 🎯 改进效果

- ⚡ **性能提升**: 响应时间从2-5秒降至100-200ms
- 📊 **API调用减少**: 减少80-90%的AKShare API调用
- 🛡️ **稳定性增强**: API不可用时仍可提供缓存数据
- 🔄 **并发支持**: 支持更多并发用户访问

## 🗄️ 推荐数据库服务

### 1. Aiven MySQL (推荐 - 免费)

**优势:**
- 免费层提供1个月试用
- 自动备份和监控
- SSL加密连接
- 简单易用的管理界面

**配置步骤:**
1. 访问 [Aiven.io](https://aiven.io)
2. 注册账户并选择MySQL服务
3. 选择免费层计划
4. 创建数据库实例
5. 获取连接信息

**连接字符串格式:**
```
mysql://[USERNAME]:[PASSWORD]@[HOSTNAME]:[PORT]/[DATABASE]?ssl-mode=REQUIRED
```

**示例格式:**
```
mysql://myuser:mypass123@mysql-server.example.com:3306/stockdb?ssl-mode=REQUIRED
```

### 2. PlanetScale (备选 - 免费)

**优势:**
- 无服务器MySQL
- 自动扩展
- 分支功能
- 免费层提供5GB存储

**配置步骤:**
1. 访问 [PlanetScale.com](https://planetscale.com)
2. 注册账户
3. 创建数据库
4. 生成连接密码
5. 获取连接字符串

### 3. Railway MySQL (备选)

**优势:**
- 与现有Railway部署集成
- 简单配置
- 按使用量付费

## ⚙️ 环境变量配置

在您的部署平台中设置以下环境变量：

### 必需配置
```bash
# 启用数据库缓存
USE_DATABASE=True

# 数据库连接URL (替换为您的实际连接信息)
DATABASE_URL=mysql+pymysql://[USERNAME]:[PASSWORD]@[HOSTNAME]:[PORT]/[DATABASE]

# 连接池配置
DATABASE_POOL_SIZE=10
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_TIMEOUT=30
```

### 缓存配置 (可选)
```bash
# 缓存时间配置 (秒)
CACHE_DEFAULT_TTL=900          # 15分钟
REALTIME_DATA_TTL=300          # 5分钟 - 实时数据
BASIC_INFO_TTL=604800          # 7天 - 股票基本信息
FINANCIAL_DATA_TTL=7776000     # 90天 - 财务数据
CAPITAL_FLOW_TTL=86400         # 1天 - 资金流向数据

# 内存缓存配置
MEMORY_CACHE_SIZE=1000         # 最大缓存条目数
```

## 🚀 部署平台配置

### Railway 部署

1. 在Railway项目中添加MySQL服务:
   ```bash
   railway add mysql
   ```

2. 设置环境变量:
   ```bash
   railway variables set USE_DATABASE=True
   railway variables set DATABASE_URL=${{MySQL.DATABASE_URL}}
   ```

3. 重新部署:
   ```bash
   railway up
   ```

### Hugging Face Spaces 部署

1. 在Spaces设置中添加环境变量:
   - `USE_DATABASE=True`
   - `DATABASE_URL=your_mysql_connection_string`

2. 重启Space以应用配置

### Render 部署

1. 在Render服务设置中添加环境变量
2. 连接外部MySQL数据库
3. 重新部署服务

## 🔧 本地开发配置

### 1. 创建 .env 文件
```bash
# 复制环境变量模板
cp .env.example .env
```

### 2. 编辑 .env 文件
```bash
# 数据库配置
USE_DATABASE=True
DATABASE_URL=mysql://[YOUR_USERNAME]:[YOUR_PASSWORD]@localhost:3306/stock_analyzer

# 或使用SQLite进行本地开发
# DATABASE_URL=sqlite:///data/stock_analyzer.db
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 初始化数据库
```bash
python -c "from database import init_db; init_db()"
```

## 📊 缓存策略说明

### 数据类型与缓存时间

| 数据类型 | 缓存时间 | 更新策略 | 说明 |
|---------|---------|---------|------|
| 历史价格数据 | 永久 | 增量更新 | 历史数据不变，只添加新数据 |
| 股票基本信息 | 7天 | 按需更新 | 基本信息变化较少 |
| 实时价格数据 | 5-15分钟 | 定时刷新 | 保持数据新鲜度 |
| 财务数据 | 90天 | 季度更新 | 财报发布周期 |
| 资金流向数据 | 1天 | 日更新 | 每日交易数据 |

### 智能缓存逻辑

1. **优先级检查**: 内存缓存 → 数据库缓存 → API调用
2. **新鲜度验证**: 检查缓存是否过期
3. **降级处理**: API失败时使用缓存数据
4. **自动清理**: 定期清理过期缓存

## 🔍 监控和维护

### 缓存统计查看
```python
from data_service import data_service
stats = data_service.get_cache_statistics()
print(stats)
```

### 手动清理缓存
```python
from database import cleanup_expired_cache
cleanup_expired_cache()
```

### 性能监控
- 查看应用日志中的缓存命中率
- 监控数据库连接数
- 观察API调用频率变化

## 🛠️ 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查连接字符串格式
   - 验证用户名密码
   - 确认网络连接

2. **缓存不生效**
   - 确认 `USE_DATABASE=True`
   - 检查数据库表是否创建
   - 查看应用日志

3. **性能没有提升**
   - 检查缓存命中率
   - 调整缓存时间配置
   - 监控数据库性能

### 日志分析
```bash
# 查看缓存相关日志
grep "cache" flask_app.log

# 查看数据库相关日志
grep "database" flask_app.log
```

## 📈 性能优化建议

1. **连接池配置**
   - 根据并发用户数调整 `DATABASE_POOL_SIZE`
   - 设置合适的 `DATABASE_POOL_RECYCLE` 时间

2. **缓存时间调优**
   - 根据数据更新频率调整TTL
   - 平衡数据新鲜度和性能

3. **索引优化**
   - 数据库会自动创建必要索引
   - 监控慢查询并优化

## 🔒 安全注意事项

1. **连接加密**
   - 使用SSL连接 (`ssl-mode=REQUIRED`)
   - 避免明文传输

2. **凭据管理**
   - 使用环境变量存储敏感信息
   - 定期轮换数据库密码

3. **访问控制**
   - 限制数据库访问IP
   - 使用最小权限原则

## 📞 技术支持

如果在配置过程中遇到问题，请：

1. 检查日志文件中的错误信息
2. 验证环境变量配置
3. 测试数据库连接
4. 查看本文档的故障排除部分

---

**注意**: 配置完成后，系统将自动在数据库和内存之间进行智能缓存管理，无需手动干预。
