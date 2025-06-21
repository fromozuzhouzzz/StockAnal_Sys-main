#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Railway快速修复脚本
"""

import os
import time
import subprocess
import datetime

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ 成功")
            if result.stdout.strip():
                print(f"   📄 输出: {result.stdout.strip()}")
        else:
            print(f"   ❌ 失败: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def update_version_number():
    """更新CSS版本号"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    layout_file = "templates/layout.html"
    
    if os.path.exists(layout_file):
        with open(layout_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新版本号
        import re
        pattern = r'md3-styles\.css\?v=[^"\']*'
        replacement = f'md3-styles.css?v={timestamp}'
        new_content = re.sub(pattern, replacement, content)
        
        with open(layout_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"   ✅ CSS版本号已更新为: {timestamp}")
        return True
    else:
        print(f"   ❌ {layout_file} 文件不存在")
        return False

def main():
    print("🚂 Railway快速修复脚本")
    print("=" * 50)
    print(f"🕐 开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 检查Git状态
    print("\n📋 步骤1: 检查Git状态")
    run_command("git status --porcelain", "检查未提交的更改")
    
    # 2. 更新版本号
    print("\n📋 步骤2: 更新CSS版本号")
    update_version_number()
    
    # 3. 添加所有更改
    print("\n📋 步骤3: 添加所有更改到Git")
    run_command("git add .", "添加所有文件")
    
    # 4. 提交更改
    print("\n📋 步骤4: 提交更改")
    commit_message = f"Fix table alignment and colors - Railway deployment {datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_command(f'git commit -m "{commit_message}"', "提交更改")
    
    # 5. 推送到远程仓库
    print("\n📋 步骤5: 推送到Railway")
    if run_command("git push origin main", "推送到main分支"):
        print("   🎉 代码已推送到Railway！")
    else:
        # 尝试其他分支名
        run_command("git push origin master", "推送到master分支")
    
    # 6. 等待部署
    print("\n📋 步骤6: 等待Railway部署")
    print("   ⏳ Railway正在自动部署，请等待3-5分钟...")
    print("   🌐 您可以在Railway控制台查看部署进度")
    
    # 7. 生成验证清单
    print("\n📋 步骤7: 验证清单")
    print("   请在5分钟后执行以下验证步骤：")
    print("   1. 强制刷新浏览器 (Ctrl+F5)")
    print("   2. 或使用无痕模式访问网站")
    print("   3. 检查表格列对齐是否正确")
    print("   4. 检查涨跌幅颜色是否为红涨绿跌")
    print("   5. 访问 /test_fix 页面进行详细验证")
    
    print("\n" + "=" * 50)
    print("🎉 Railway快速修复脚本执行完成！")
    print(f"🕐 完成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🔗 验证链接:")
    print("   - 主页: https://your-app.railway.app/")
    print("   - 资金流向: https://your-app.railway.app/capital_flow")
    print("   - 验证页面: https://your-app.railway.app/test_fix")
    print("\n💡 提示: 如果5分钟后仍有问题，请检查Railway部署日志")

if __name__ == "__main__":
    main()
