#!/bin/bash

# 智能股票分析系统 - 快速部署脚本
# 适用于 macOS 和 Linux 系统

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "🚀 智能股票分析系统 - 快速部署脚本" $BLUE
print_message "================================================" $BLUE

# 检查 Node.js
print_message "📋 检查环境依赖..." $YELLOW
if ! command -v node &> /dev/null; then
    print_message "❌ 错误：未找到 Node.js" $RED
    print_message "请先安装 Node.js: https://nodejs.org/" $RED
    exit 1
fi

NODE_VERSION=$(node --version)
print_message "✅ Node.js 版本: $NODE_VERSION" $GREEN

# 检查 npm
if ! command -v npm &> /dev/null; then
    print_message "❌ 错误：未找到 npm" $RED
    exit 1
fi

NPM_VERSION=$(npm --version)
print_message "✅ npm 版本: $NPM_VERSION" $GREEN

# 检查项目文件
print_message "📂 检查项目文件..." $YELLOW
if [ ! -f "index.html" ]; then
    print_message "❌ 错误：未找到 index.html 文件" $RED
    print_message "请确保在项目根目录运行此脚本" $RED
    exit 1
fi

if [ ! -f "package.json" ]; then
    print_message "❌ 错误：未找到 package.json 文件" $RED
    exit 1
fi

print_message "✅ 项目文件检查通过" $GREEN

# 安装依赖
print_message "📦 安装项目依赖..." $YELLOW
if npm install; then
    print_message "✅ 依赖安装完成" $GREEN
else
    print_message "❌ 依赖安装失败" $RED
    exit 1
fi

# 验证 HTML
print_message "🔍 验证 HTML 文件..." $YELLOW
if npm run validate 2>/dev/null; then
    print_message "✅ HTML 验证通过" $GREEN
else
    print_message "⚠️  HTML 验证跳过（可选步骤）" $YELLOW
fi

# 优化资源文件
print_message "⚡ 优化资源文件..." $YELLOW
if npm run optimize 2>/dev/null; then
    print_message "✅ 资源优化完成" $GREEN
else
    print_message "⚠️  资源优化跳过（可选步骤）" $YELLOW
fi

# 检查 Wrangler CLI
print_message "🔧 检查 Cloudflare Wrangler..." $YELLOW
if ! command -v wrangler &> /dev/null; then
    print_message "📥 安装 Wrangler CLI..." $YELLOW
    if npm install -g wrangler; then
        print_message "✅ Wrangler CLI 安装完成" $GREEN
    else
        print_message "❌ Wrangler CLI 安装失败" $RED
        print_message "请手动安装: npm install -g wrangler" $RED
        exit 1
    fi
else
    WRANGLER_VERSION=$(wrangler --version)
    print_message "✅ Wrangler 版本: $WRANGLER_VERSION" $GREEN
fi

# 登录检查
print_message "🔐 检查 Cloudflare 登录状态..." $YELLOW
if wrangler whoami &> /dev/null; then
    USER_INFO=$(wrangler whoami)
    print_message "✅ 已登录 Cloudflare: $USER_INFO" $GREEN
else
    print_message "🔑 需要登录 Cloudflare..." $YELLOW
    print_message "请在浏览器中完成登录..." $BLUE
    if wrangler login; then
        print_message "✅ Cloudflare 登录成功" $GREEN
    else
        print_message "❌ Cloudflare 登录失败" $RED
        exit 1
    fi
fi

# 部署到 Cloudflare Pages
print_message "🌐 部署到 Cloudflare Pages..." $YELLOW
PROJECT_NAME="stock-analysis-landing"

print_message "项目名称: $PROJECT_NAME" $BLUE
print_message "开始上传文件..." $BLUE

if wrangler pages publish . --project-name "$PROJECT_NAME"; then
    print_message "🎉 部署成功！" $GREEN
    print_message "================================================" $GREEN
    print_message "✅ 智能股票分析系统展示页面已成功部署" $GREEN
    print_message "🌐 访问地址: https://$PROJECT_NAME.pages.dev" $BLUE
    print_message "📊 您可以在 Cloudflare Dashboard 中查看部署详情" $BLUE
    print_message "================================================" $GREEN
else
    print_message "❌ 部署失败" $RED
    print_message "请检查网络连接和 Cloudflare 账号权限" $RED
    exit 1
fi

# 可选：运行性能测试
read -p "是否运行性能测试？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_message "🚀 启动本地服务器进行性能测试..." $YELLOW
    npm run dev &
    SERVER_PID=$!
    
    sleep 5  # 等待服务器启动
    
    print_message "📊 运行 Lighthouse 测试..." $YELLOW
    if npm run lighthouse; then
        print_message "✅ 性能测试完成，请查看 lighthouse-report.html" $GREEN
    else
        print_message "⚠️  性能测试失败" $YELLOW
    fi
    
    # 停止本地服务器
    kill $SERVER_PID 2>/dev/null || true
fi

print_message "🎊 部署流程全部完成！" $GREEN
print_message "感谢使用智能股票分析系统！" $BLUE
