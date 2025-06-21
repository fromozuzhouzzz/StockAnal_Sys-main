#!/bin/bash
# Railway MySQL快速部署脚本

echo "🚀 Railway MySQL快速部署工具"
echo "================================"

# 检查Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI未安装"
    echo "💡 安装方法: npm install -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI已安装"

# 登录检查
if ! railway whoami &> /dev/null; then
    echo "🔐 请先登录Railway..."
    railway login
fi

echo "✅ Railway登录状态正常"

# 检查项目状态
echo "📋 检查项目状态..."
railway status

# 设置环境变量
echo "⚙️ 配置环境变量..."

# 基础配置
railway variables set USE_DATABASE=True
railway variables set FLASK_ENV=production
railway variables set PORT=8080

# 生成SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
railway variables set SECRET_KEY="$SECRET_KEY"

# 缓存配置
railway variables set CACHE_DEFAULT_TTL=900
railway variables set REALTIME_DATA_TTL=300
railway variables set BASIC_INFO_TTL=604800
railway variables set FINANCIAL_DATA_TTL=7776000
railway variables set CAPITAL_FLOW_TTL=86400

# 数据库连接池配置
railway variables set DATABASE_POOL_SIZE=5
railway variables set DATABASE_POOL_RECYCLE=1800
railway variables set DATABASE_POOL_TIMEOUT=20

echo "✅ 环境变量配置完成"

# 检查MySQL服务
echo "🗄️ 检查MySQL服务..."
if railway services | grep -q mysql; then
    echo "✅ MySQL服务已存在"
    # 设置DATABASE_URL使用Railway MySQL服务
    railway variables set DATABASE_URL='${{MySQL.DATABASE_URL}}'
else
    echo "➕ 添加MySQL服务..."
    railway add mysql
    echo "✅ MySQL服务已添加"
    # 设置DATABASE_URL使用Railway MySQL服务
    railway variables set DATABASE_URL='${{MySQL.DATABASE_URL}}'
fi

# 显示当前配置
echo "📋 当前环境变量:"
railway variables

# 部署应用
echo "🚀 开始部署..."
railway up

echo "✅ 部署完成！"
echo "🌐 访问应用: $(railway domain)"
echo "📊 查看日志: railway logs"
echo "⚙️ 管理项目: railway dashboard"
