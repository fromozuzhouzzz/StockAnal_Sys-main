#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git历史清理脚本 - 移除敏感信息
解决GitHub Push Protection历史提交问题
"""

import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                              capture_output=capture_output, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {cmd}")
        print(f"错误: {e}")
        return None

def backup_current_state():
    """备份当前状态"""
    print("💾 创建当前状态备份...")
    
    # 创建备份分支
    result = run_command("git branch backup-before-history-cleanup")
    if result:
        print("✅ 备份分支已创建: backup-before-history-cleanup")
        return True
    return False

def check_git_status():
    """检查Git状态"""
    result = run_command("git status --porcelain")
    if result and result.stdout.strip():
        print("⚠️ 检测到未提交的更改:")
        print(result.stdout)
        return False
    return True

def get_problematic_commit():
    """获取问题提交信息"""
    commit_hash = "97cd180a97aeed0f56ff7047a7fefe172eabf820"
    
    # 检查提交是否存在
    result = run_command(f"git show --name-only {commit_hash}")
    if result:
        print(f"🔍 找到问题提交: {commit_hash}")
        print("修改的文件:")
        for line in result.stdout.split('\n'):
            if line.strip() and not line.startswith('commit') and not line.startswith('Author') and not line.startswith('Date'):
                print(f"  - {line}")
        return commit_hash
    else:
        print(f"❌ 未找到提交: {commit_hash}")
        return None

def method1_interactive_rebase():
    """方法1: 交互式rebase"""
    print("\n🔧 方法1: 使用交互式rebase修复历史")
    
    commit_hash = "97cd180a97aeed0f56ff7047a7fefe172eabf820"
    
    # 找到问题提交的父提交
    result = run_command(f"git rev-parse {commit_hash}^")
    if not result:
        print("❌ 无法找到父提交")
        return False
    
    parent_commit = result.stdout.strip()
    print(f"📍 父提交: {parent_commit}")
    
    print("\n📋 交互式rebase步骤:")
    print(f"1. 运行: git rebase -i {parent_commit}")
    print(f"2. 在编辑器中，将 {commit_hash[:8]} 对应行的 'pick' 改为 'edit'")
    print("3. 保存并退出编辑器")
    print("4. 修复 DATABASE_SETUP_GUIDE.md 文件中的敏感信息")
    print("5. 运行: git add DATABASE_SETUP_GUIDE.md")
    print("6. 运行: git commit --amend")
    print("7. 运行: git rebase --continue")
    
    return True

def method2_filter_branch():
    """方法2: 使用git filter-branch"""
    print("\n🔧 方法2: 使用git filter-branch清理历史")
    
    # 创建过滤脚本
    filter_script = """
import re
import sys

# 读取文件内容
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()

# 替换敏感信息
replacements = [
    (r'mysql://username:password@hostname:port/database', 'mysql://[USERNAME]:[PASSWORD]@[HOST]:[PORT]/[DB]'),
    (r'mysql://\w+:password@[\w\.-]+:\d+/\w+', 'mysql://[USERNAME]:[PASSWORD]@[HOST]:[PORT]/[DB]'),
    (r'your_openai_api_key_here', '[YOUR_OPENAI_API_KEY]'),
    (r'your-secret-key-here', '[YOUR_SECRET_KEY]'),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

# 写回文件
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write(content)
"""
    
    # 保存过滤脚本
    with open('filter_sensitive.py', 'w') as f:
        f.write(filter_script)
    
    print("📝 过滤脚本已创建: filter_sensitive.py")
    
    # 构建filter-branch命令
    cmd = '''git filter-branch --tree-filter '
if [ -f "DATABASE_SETUP_GUIDE.md" ]; then
    python filter_sensitive.py DATABASE_SETUP_GUIDE.md
fi
if [ -f "config.py" ]; then
    python filter_sensitive.py config.py
fi
if [ -f ".env.example" ]; then
    python filter_sensitive.py .env.example
fi
' --all'''
    
    print("🔄 运行filter-branch命令...")
    print("⚠️ 这可能需要几分钟时间...")
    
    result = run_command(cmd, check=False)
    
    # 清理临时文件
    if os.path.exists('filter_sensitive.py'):
        os.remove('filter_sensitive.py')
    
    if result and result.returncode == 0:
        print("✅ Git历史已清理")
        return True
    else:
        print("❌ filter-branch执行失败")
        return False

def method3_new_repository():
    """方法3: 创建新仓库"""
    print("\n🔧 方法3: 创建干净的新仓库")
    
    print("📋 新仓库创建步骤:")
    print("1. 在GitHub创建新的空仓库")
    print("2. 克隆新仓库到本地")
    print("3. 复制当前修复后的文件到新仓库")
    print("4. 提交并推送到新仓库")
    print("5. 更新所有引用到新仓库")
    
    # 创建复制脚本
    copy_script = """#!/bin/bash
# 复制文件到新仓库的脚本

NEW_REPO_PATH="$1"

if [ -z "$NEW_REPO_PATH" ]; then
    echo "用法: $0 <新仓库路径>"
    exit 1
fi

# 要复制的文件和目录
FILES_TO_COPY=(
    "*.py"
    "*.md"
    "*.txt"
    "*.yml"
    "*.yaml"
    "*.json"
    "templates/"
    "static/"
    "data/"
    ".gitignore"
)

echo "📁 复制文件到新仓库..."

for item in "${FILES_TO_COPY[@]}"; do
    if ls $item 1> /dev/null 2>&1; then
        cp -r $item "$NEW_REPO_PATH/"
        echo "✅ 已复制: $item"
    fi
done

echo "🎉 文件复制完成！"
echo "📋 下一步:"
echo "1. cd $NEW_REPO_PATH"
echo "2. git add ."
echo "3. git commit -m 'Initial commit with security fixes'"
echo "4. git push"
"""
    
    with open('copy_to_new_repo.sh', 'w') as f:
        f.write(copy_script)
    
    # 设置执行权限
    os.chmod('copy_to_new_repo.sh', 0o755)
    
    print("✅ 复制脚本已创建: copy_to_new_repo.sh")
    
    return True

def method4_squash_commits():
    """方法4: 压缩所有提交"""
    print("\n🔧 方法4: 压缩所有提交为单个提交")
    
    # 获取第一个提交
    result = run_command("git rev-list --max-parents=0 HEAD")
    if not result:
        print("❌ 无法获取初始提交")
        return False
    
    first_commit = result.stdout.strip()
    print(f"📍 初始提交: {first_commit}")
    
    print("📋 压缩提交步骤:")
    print(f"1. git reset --soft {first_commit}")
    print("2. git commit -m 'feat: 股票分析系统数据缓存架构改进'")
    print("3. git push --force-with-lease")
    
    return True

def recommend_solution():
    """推荐解决方案"""
    print("\n💡 推荐解决方案:")
    print("=" * 50)
    
    print("🥇 **最推荐**: 方法3 - 创建新仓库")
    print("   优点: 完全干净，无历史包袱")
    print("   缺点: 失去Git历史")
    print("   适用: 项目较新，历史不重要")
    
    print("\n🥈 **次推荐**: 方法4 - 压缩提交")
    print("   优点: 简单快速，保留最终状态")
    print("   缺点: 失去详细历史")
    print("   适用: 希望保持简洁历史")
    
    print("\n🥉 **高级用户**: 方法1 - 交互式rebase")
    print("   优点: 精确控制，保留有用历史")
    print("   缺点: 复杂，需要Git经验")
    print("   适用: 重要项目，需要保留历史")

def main():
    """主函数"""
    print("🔒 Git历史清理工具")
    print("解决GitHub Push Protection历史提交问题")
    print("=" * 50)
    
    # 检查Git状态
    if not check_git_status():
        print("❌ 请先提交或暂存未完成的更改")
        return False
    
    # 创建备份
    if not backup_current_state():
        print("❌ 备份创建失败")
        return False
    
    # 检查问题提交
    problematic_commit = get_problematic_commit()
    if not problematic_commit:
        print("❌ 未找到问题提交")
        return False
    
    # 提供所有解决方案
    method1_interactive_rebase()
    method2_filter_branch()
    method3_new_repository()
    method4_squash_commits()
    
    # 推荐解决方案
    recommend_solution()
    
    print("\n⚠️ 重要提醒:")
    print("- 所有方法都会修改Git历史")
    print("- 执行前已创建备份分支: backup-before-history-cleanup")
    print("- 如果出错，可以恢复: git checkout backup-before-history-cleanup")
    print("- 建议先在测试分支上尝试")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
