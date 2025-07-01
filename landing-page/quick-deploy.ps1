# 智能股票分析系统 - 快速部署脚本 (Windows PowerShell)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 颜色函数
function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorMessage "🚀 智能股票分析系统 - 快速部署脚本" "Blue"
Write-ColorMessage "================================================" "Blue"

try {
    # 检查 Node.js
    Write-ColorMessage "📋 检查环境依赖..." "Yellow"
    
    try {
        $nodeVersion = node --version
        Write-ColorMessage "✅ Node.js 版本: $nodeVersion" "Green"
    }
    catch {
        Write-ColorMessage "❌ 错误：未找到 Node.js" "Red"
        Write-ColorMessage "请先安装 Node.js: https://nodejs.org/" "Red"
        exit 1
    }

    # 检查 npm
    try {
        $npmVersion = npm --version
        Write-ColorMessage "✅ npm 版本: $npmVersion" "Green"
    }
    catch {
        Write-ColorMessage "❌ 错误：未找到 npm" "Red"
        exit 1
    }

    # 检查项目文件
    Write-ColorMessage "📂 检查项目文件..." "Yellow"
    
    if (-not (Test-Path "index.html")) {
        Write-ColorMessage "❌ 错误：未找到 index.html 文件" "Red"
        Write-ColorMessage "请确保在项目根目录运行此脚本" "Red"
        exit 1
    }

    if (-not (Test-Path "package.json")) {
        Write-ColorMessage "❌ 错误：未找到 package.json 文件" "Red"
        exit 1
    }

    Write-ColorMessage "✅ 项目文件检查通过" "Green"

    # 安装依赖
    Write-ColorMessage "📦 安装项目依赖..." "Yellow"
    npm install
    Write-ColorMessage "✅ 依赖安装完成" "Green"

    # 验证 HTML
    Write-ColorMessage "🔍 验证 HTML 文件..." "Yellow"
    try {
        npm run validate 2>$null
        Write-ColorMessage "✅ HTML 验证通过" "Green"
    }
    catch {
        Write-ColorMessage "⚠️  HTML 验证跳过（可选步骤）" "Yellow"
    }

    # 优化资源文件
    Write-ColorMessage "⚡ 优化资源文件..." "Yellow"
    try {
        npm run optimize 2>$null
        Write-ColorMessage "✅ 资源优化完成" "Green"
    }
    catch {
        Write-ColorMessage "⚠️  资源优化跳过（可选步骤）" "Yellow"
    }

    # 检查 Wrangler CLI
    Write-ColorMessage "🔧 检查 Cloudflare Wrangler..." "Yellow"
    
    try {
        $wranglerVersion = wrangler --version
        Write-ColorMessage "✅ Wrangler 版本: $wranglerVersion" "Green"
    }
    catch {
        Write-ColorMessage "📥 安装 Wrangler CLI..." "Yellow"
        npm install -g wrangler
        Write-ColorMessage "✅ Wrangler CLI 安装完成" "Green"
    }

    # 登录检查
    Write-ColorMessage "🔐 检查 Cloudflare 登录状态..." "Yellow"
    
    try {
        $userInfo = wrangler whoami 2>$null
        Write-ColorMessage "✅ 已登录 Cloudflare: $userInfo" "Green"
    }
    catch {
        Write-ColorMessage "🔑 需要登录 Cloudflare..." "Yellow"
        Write-ColorMessage "请在浏览器中完成登录..." "Blue"
        wrangler login
        Write-ColorMessage "✅ Cloudflare 登录成功" "Green"
    }

    # 部署到 Cloudflare Pages
    Write-ColorMessage "🌐 部署到 Cloudflare Pages..." "Yellow"
    $projectName = "stock-analysis-landing"

    Write-ColorMessage "项目名称: $projectName" "Blue"
    Write-ColorMessage "开始上传文件..." "Blue"

    wrangler pages publish . --project-name $projectName

    Write-ColorMessage "🎉 部署成功！" "Green"
    Write-ColorMessage "================================================" "Green"
    Write-ColorMessage "✅ 智能股票分析系统展示页面已成功部署" "Green"
    Write-ColorMessage "🌐 访问地址: https://$projectName.pages.dev" "Blue"
    Write-ColorMessage "📊 您可以在 Cloudflare Dashboard 中查看部署详情" "Blue"
    Write-ColorMessage "================================================" "Green"

    # 可选：运行性能测试
    $runTest = Read-Host "是否运行性能测试？(y/N)"
    if ($runTest -eq "y" -or $runTest -eq "Y") {
        Write-ColorMessage "🚀 启动本地服务器进行性能测试..." "Yellow"
        
        # 启动本地服务器（后台）
        $serverJob = Start-Job -ScriptBlock { npm run dev }
        
        Start-Sleep -Seconds 5  # 等待服务器启动
        
        Write-ColorMessage "📊 运行 Lighthouse 测试..." "Yellow"
        try {
            npm run lighthouse
            Write-ColorMessage "✅ 性能测试完成，请查看 lighthouse-report.html" "Green"
        }
        catch {
            Write-ColorMessage "⚠️  性能测试失败" "Yellow"
        }
        
        # 停止本地服务器
        Stop-Job $serverJob -ErrorAction SilentlyContinue
        Remove-Job $serverJob -ErrorAction SilentlyContinue
    }

    Write-ColorMessage "🎊 部署流程全部完成！" "Green"
    Write-ColorMessage "感谢使用智能股票分析系统！" "Blue"

}
catch {
    Write-ColorMessage "❌ 部署过程中发生错误: $($_.Exception.Message)" "Red"
    Write-ColorMessage "请检查网络连接和 Cloudflare 账号权限" "Red"
    exit 1
}

# 暂停以查看结果
Write-ColorMessage "按任意键退出..." "Gray"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
