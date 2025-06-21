#!/bin/bash

# 快速修复脚本 - 强制更新和重启服务

echo "🚀 开始快速修复..."
echo "================================"

# 1. 检查当前目录
echo "📁 当前目录: $(pwd)"

# 2. 检查关键文件是否存在
echo "🔍 检查关键文件..."
files=("templates/capital_flow.html" "static/md3-styles.css" "templates/layout.html")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file 存在"
        echo "   📅 修改时间: $(stat -c %y "$file" 2>/dev/null || stat -f %Sm "$file" 2>/dev/null || echo "无法获取")"
    else
        echo "   ❌ $file 不存在"
    fi
done

# 3. 添加时间戳到CSS文件
echo "⏰ 更新CSS版本号..."
current_time=$(date +"%Y%m%d-%H%M%S")
if [ -f "templates/layout.html" ]; then
    # 备份原文件
    cp templates/layout.html templates/layout.html.backup
    
    # 更新版本号
    sed -i.bak "s/md3-styles\.css?v=[^\"']*/md3-styles.css?v=$current_time/g" templates/layout.html
    echo "   ✅ CSS版本号已更新为: $current_time"
else
    echo "   ❌ layout.html 文件不存在"
fi

# 4. 检查Python进程
echo "🐍 检查Python进程..."
python_pids=$(pgrep -f "python.*web_server.py" || pgrep -f "python.*app.py" || echo "")
if [ -n "$python_pids" ]; then
    echo "   📋 发现Python进程: $python_pids"
    echo "   🔄 重启Python服务..."
    kill $python_pids 2>/dev/null
    sleep 2
    echo "   ✅ Python进程已重启"
else
    echo "   ℹ️  未发现运行中的Python进程"
fi

# 5. 清理缓存文件
echo "🧹 清理缓存..."
if [ -d "__pycache__" ]; then
    rm -rf __pycache__
    echo "   ✅ 已清理 __pycache__"
fi

if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo "   ✅ 已清理 .pytest_cache"
fi

# 6. 生成验证报告
echo "📊 生成验证报告..."
if command -v python3 &> /dev/null; then
    python3 deployment_check.py
elif command -v python &> /dev/null; then
    python deployment_check.py
else
    echo "   ⚠️  Python未找到，跳过验证报告"
fi

echo ""
echo "================================"
echo "🎉 快速修复完成！"
echo ""
echo "📋 下一步操作:"
echo "1. 强制刷新浏览器 (Ctrl+F5 或 Cmd+Shift+R)"
echo "2. 访问 /test_fix 页面验证修复效果"
echo "3. 如果使用Docker，请重启容器"
echo "4. 如果使用云服务，请重新部署应用"
echo ""
echo "🔗 验证链接:"
echo "   - 主页: http://localhost:5000/"
echo "   - 资金流向: http://localhost:5000/capital_flow"
echo "   - 验证页面: http://localhost:5000/test_fix"
echo ""
