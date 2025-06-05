# 股票分析系统部署指南

## 部署平台选择

由于该系统是基于 Python Flask 的复杂数据分析应用，**无法部署到 Cloudflare Workers**，因为：

1. Cloudflare Workers 不支持 Python
2. 内存限制（128MB）无法运行大型数据分析库
3. 无文件系统支持
4. CPU 时间限制不适合长时间数据处理

## 推荐的免费部署平台

### 1. Railway（推荐）⭐

**优势：**
- 支持 Python 和 PostgreSQL
- 每月 $5 免费额度
- 自动 HTTPS 和域名
- 支持环境变量管理

**部署步骤：**

1. 注册 [Railway](https://railway.app) 账号
2. 连接 GitHub 仓库
3. 创建新项目并选择仓库
4. 添加 PostgreSQL 数据库服务
5. 设置环境变量：
   ```
   OPENAI_API_KEY=your_api_key
   OPENAI_API_MODEL=gpt-4o
   USE_DATABASE=true
   ```
6. 部署会自动开始

### 2. Render（完全免费）

**优势：**
- 完全免费的 Web 服务
- 750 小时/月免费时长
- 自动 SSL 证书
- 支持 PostgreSQL

**部署步骤：**

1. 注册 [Render](https://render.com) 账号
2. 连接 GitHub 仓库
3. 创建 Web Service，选择仓库
4. 创建 PostgreSQL 数据库
5. 在 Web Service 中添加环境变量
6. 部署

### 3. Fly.io

**优势：**
- 免费层包含 3 个小应用
- 全球 CDN
- 支持持久化存储

**部署步骤：**

1. 安装 Fly CLI
2. 注册账号：`fly auth signup`
3. 在项目目录运行：`fly launch`
4. 创建存储卷：`fly volumes create stock_data --size 1`
5. 设置环境变量：`fly secrets set OPENAI_API_KEY=your_key`
6. 部署：`fly deploy`

## 环境变量配置

所有平台都需要设置以下环境变量：

```bash
# 必需的 API 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_MODEL=gpt-4o
NEWS_MODEL=gpt-4o

# 数据库配置
USE_DATABASE=true
DATABASE_URL=postgresql://user:pass@host:port/dbname

# 可选配置
TAVILY_API_KEY=your_tavily_key  # 用于新闻搜索
USE_REDIS_CACHE=false
PORT=8888
```

## 部署前准备

1. **获取 API 密钥：**
   - OpenAI API Key（必需）
   - Tavily API Key（可选，用于新闻搜索）

2. **复制环境变量文件：**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 API 密钥
   ```

3. **测试本地运行：**
   ```bash
   pip install -r requirements.txt
   python web_server.py
   ```

## 部署后配置

1. **数据库初始化：**
   - 系统会自动创建必要的数据表
   - 首次运行可能需要几分钟初始化

2. **功能测试：**
   - 访问首页检查界面加载
   - 测试股票分析功能
   - 检查 API 文档：`/api/docs`

3. **性能优化：**
   - 启用数据库缓存
   - 配置 Redis（如果平台支持）
   - 调整 worker 数量

## 故障排除

### 常见问题：

1. **内存不足：**
   - 减少 worker 数量
   - 优化数据处理逻辑

2. **API 超时：**
   - 检查 API 密钥是否正确
   - 确认网络连接正常

3. **数据库连接失败：**
   - 检查 DATABASE_URL 格式
   - 确认数据库服务正常运行

### 日志查看：

- **Railway：** 在项目面板查看部署日志
- **Render：** 在服务页面查看日志
- **Fly.io：** 使用 `fly logs` 命令

## 成本估算

| 平台 | 免费额度 | 超出费用 |
|------|----------|----------|
| Railway | $5/月 | 按使用量计费 |
| Render | 750小时/月 | $7/月 |
| Fly.io | 3个应用 | 按资源计费 |

## 推荐配置

对于这个股票分析系统，推荐使用 **Railway** 平台，因为：

1. 免费额度充足
2. PostgreSQL 数据库支持好
3. 部署简单，维护方便
4. 性能稳定，适合数据分析应用

## 下一步

选择合适的平台后，按照对应的部署步骤进行部署。如有问题，可以查看各平台的官方文档或联系技术支持。
