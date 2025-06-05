#!/bin/bash

# 股票分析系统快速部署脚本

set -e

echo "🚀 股票分析系统部署脚本"
echo "=========================="

# 检查是否安装了必要的工具
check_requirements() {
    echo "📋 检查部署要求..."
    
    if ! command -v git &> /dev/null; then
        echo "❌ Git 未安装，请先安装 Git"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 未安装，请先安装 Python 3.7+"
        exit 1
    fi
    
    echo "✅ 基础要求检查完成"
}

# 设置环境变量
setup_env() {
    echo "⚙️  设置环境变量..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 已创建 .env 文件，请编辑并填入你的 API 密钥："
        echo "   - OPENAI_API_KEY"
        echo "   - TAVILY_API_KEY (可选)"
        echo ""
        read -p "按回车键继续，或 Ctrl+C 退出去编辑 .env 文件..."
    fi
}

# 本地测试部署
deploy_local() {
    echo "🏠 本地测试部署..."
    
    # 安装依赖
    echo "📦 安装 Python 依赖..."
    pip install -r requirements.txt
    
    # 运行测试
    echo "🧪 运行基础测试..."
    python -c "import flask, pandas, numpy, akshare; print('✅ 核心依赖检查通过')"
    
    # 启动服务
    echo "🌟 启动本地服务..."
    echo "访问地址: http://localhost:8888"
    python start_cloud.py
}

# Railway 部署指南
deploy_railway() {
    echo "🚂 Railway 部署指南"
    echo "==================="
    echo "1. 访问 https://railway.app"
    echo "2. 使用 GitHub 账号登录"
    echo "3. 点击 'New Project' -> 'Deploy from GitHub repo'"
    echo "4. 选择这个仓库"
    echo "5. 添加 PostgreSQL 数据库服务"
    echo "6. 设置环境变量："
    echo "   OPENAI_API_KEY=你的密钥"
    echo "   OPENAI_API_MODEL=gpt-4o"
    echo "   USE_DATABASE=true"
    echo "7. 等待部署完成"
    echo ""
    echo "💡 Railway 提供每月 $5 免费额度，足够运行这个应用"
}

# Render 部署指南
deploy_render() {
    echo "🎨 Render 部署指南"
    echo "=================="
    echo "1. 访问 https://render.com"
    echo "2. 使用 GitHub 账号登录"
    echo "3. 点击 'New' -> 'Web Service'"
    echo "4. 连接 GitHub 仓库"
    echo "5. 创建 PostgreSQL 数据库"
    echo "6. 在 Web Service 中设置环境变量"
    echo "7. 部署会自动开始"
    echo ""
    echo "💡 Render 提供 750 小时/月免费时长"
}

# Fly.io 部署指南
deploy_fly() {
    echo "🪰 Fly.io 部署指南"
    echo "=================="
    echo "1. 安装 Fly CLI: https://fly.io/docs/getting-started/installing-flyctl/"
    echo "2. 注册账号: fly auth signup"
    echo "3. 在项目目录运行: fly launch"
    echo "4. 创建存储卷: fly volumes create stock_data --size 1"
    echo "5. 设置环境变量: fly secrets set OPENAI_API_KEY=你的密钥"
    echo "6. 部署: fly deploy"
    echo ""
    echo "💡 Fly.io 免费层包含 3 个小应用"
}

# 主菜单
main_menu() {
    echo ""
    echo "请选择部署方式："
    echo "1) 本地测试部署"
    echo "2) Railway 部署指南"
    echo "3) Render 部署指南"
    echo "4) Fly.io 部署指南"
    echo "5) 退出"
    echo ""
    read -p "请输入选项 (1-5): " choice
    
    case $choice in
        1)
            deploy_local
            ;;
        2)
            deploy_railway
            ;;
        3)
            deploy_render
            ;;
        4)
            deploy_fly
            ;;
        5)
            echo "👋 再见！"
            exit 0
            ;;
        *)
            echo "❌ 无效选项，请重新选择"
            main_menu
            ;;
    esac
}

# 主函数
main() {
    check_requirements
    setup_env
    main_menu
}

# 运行主函数
main
