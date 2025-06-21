# Railway MySQL部署配置指南

## 🚨 问题描述

在Railway平台部署时遇到MySQL驱动错误：
```
ModuleNotFoundError: No module named 'MySQLdb'
```

这是因为SQLAlchemy默认尝试使用MySQLdb驱动，但我们使用的是pymysql。

## 🛠️ 解决方案

### 方案1：修改DATABASE_URL格式（推荐）

在Railway项目的环境变量设置中，将DATABASE_URL从：
```
mysql://[USERNAME]:[PASSWORD]@[HOSTNAME]:[PORT]/[DATABASE]
```

修改为：
```
mysql+pymysql://[USERNAME]:[PASSWORD]@[HOSTNAME]:[PORT]/[DATABASE]
```

**关键点**：添加`+pymysql`来明确指定使用pymysql驱动。

### 方案2：使用Railway MySQL服务

1. 在Railway项目中添加MySQL服务：
   ```bash
   railway add mysql
   ```

2. 设置环境变量：
   ```bash
   USE_DATABASE=True
   DATABASE_URL=${{MySQL.DATABASE_URL}}
   ```

3. Railway会自动提供正确格式的连接字符串。

### 方案3：手动配置完整环境变量

在Railway项目设置中添加以下环境变量：

```bash
# 数据库配置
USE_DATABASE=True
DATABASE_URL=mysql+pymysql://[USERNAME]:[PASSWORD]@[HOSTNAME]:[PORT]/[DATABASE]

# 连接池配置
DATABASE_POOL_SIZE=10
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_TIMEOUT=30

# 缓存配置
CACHE_DEFAULT_TTL=900
REALTIME_DATA_TTL=300
BASIC_INFO_TTL=604800
FINANCIAL_DATA_TTL=7776000
CAPITAL_FLOW_TTL=86400

# 应用配置
SECRET_KEY=[YOUR_SECRET_KEY]
FLASK_ENV=production
PORT=8080
```

## 🔧 自动修复脚本

我们已经在代码中添加了自动修复功能：

1. **database.py** - 自动检测和修复DATABASE_URL格式
2. **start_with_cache.py** - 启动时自动初始化PyMySQL兼容性
3. **railway_mysql_fix.py** - 独立的修复验证脚本

## 📋 部署步骤

### 1. 准备Railway项目

```bash
# 登录Railway
railway login

# 创建新项目或连接现有项目
railway init
```

### 2. 添加MySQL服务

```bash
# 添加MySQL服务
railway add mysql

# 查看服务状态
railway status
```

### 3. 配置环境变量

在Railway Dashboard中设置：

```bash
USE_DATABASE=True
DATABASE_URL=${{MySQL.DATABASE_URL}}
SECRET_KEY=your-generated-secret-key
```

### 4. 部署应用

```bash
# 部署到Railway
railway up
```

## 🧪 验证部署

### 1. 检查部署日志

在Railway Dashboard中查看部署日志，确认：
- ✅ PyMySQL兼容性初始化成功
- ✅ 数据库连接成功
- ✅ 应用启动成功

### 2. 运行验证脚本

```bash
# 本地验证（可选）
python railway_mysql_fix.py
```

### 3. 测试应用功能

访问部署的应用URL，测试：
- 股票数据获取
- 缓存功能
- 数据库连接

## 🚨 常见问题排查

### 问题1：仍然出现MySQLdb错误

**解决方案**：
1. 确认DATABASE_URL包含`+pymysql`
2. 检查requirements.txt包含`pymysql>=1.0.0`
3. 重新部署应用

### 问题2：数据库连接超时

**解决方案**：
1. 检查MySQL服务是否正常运行
2. 验证连接参数（主机、端口、用户名、密码）
3. 调整连接池配置

### 问题3：权限错误

**解决方案**：
1. 确认数据库用户有足够权限
2. 检查数据库名称是否存在
3. 验证SSL配置（如果需要）

## 📊 性能优化建议

### 1. 连接池配置

```bash
DATABASE_POOL_SIZE=5          # Railway免费层建议较小值
DATABASE_POOL_RECYCLE=1800    # 30分钟回收连接
DATABASE_POOL_TIMEOUT=20      # 20秒连接超时
```

### 2. 缓存策略

```bash
CACHE_DEFAULT_TTL=600         # 10分钟默认缓存
MEMORY_CACHE_SIZE=500         # 较小的内存缓存
```

### 3. 监控配置

```bash
LOG_LEVEL=INFO                # 生产环境日志级别
ECHO_SQL=False                # 关闭SQL日志
```

## 🔒 安全配置

### 1. 生成安全密钥

```bash
# 生成SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. 数据库安全

- 使用强密码
- 启用SSL连接（如果支持）
- 限制数据库访问IP

### 3. 环境变量安全

- 不要在代码中硬编码敏感信息
- 使用Railway的环境变量管理
- 定期轮换密钥和密码

## 📞 技术支持

如果仍然遇到问题：

1. **检查日志**：查看Railway部署日志中的详细错误信息
2. **验证配置**：确认所有环境变量设置正确
3. **测试连接**：使用独立脚本测试数据库连接
4. **查看文档**：参考DATABASE_SETUP_GUIDE.md获取更多信息

## ✅ 成功部署检查清单

- [ ] requirements.txt包含pymysql>=1.0.0
- [ ] DATABASE_URL格式正确（包含+pymysql）
- [ ] USE_DATABASE=True
- [ ] SECRET_KEY已设置
- [ ] MySQL服务正常运行
- [ ] 应用成功启动
- [ ] 数据库连接正常
- [ ] 缓存功能工作正常

完成以上检查后，您的股票分析系统应该能在Railway平台上成功运行！🎉
