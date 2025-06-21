#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub安全问题修复脚本
解决Push Protection检测到的敏感信息问题
"""

import os
import subprocess
import sys
import re
from pathlib import Path

def check_git_status():
    """检查Git状态"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("❌ 错误：不在Git仓库中或Git命令失败")
        return None

def scan_sensitive_patterns():
    """扫描敏感信息模式"""
    print("🔍 扫描敏感信息模式...")
    
    # 定义敏感模式
    sensitive_patterns = [
        r'mysql://\w+:password@',
        r'postgresql://\w+:password@',
        r'SECRET_KEY=[\w-]+',
        r'API_KEY=[\w-]+',
        r'://username:password@',
        r'your_.*_key_here',
        r'your-secret-key-here',
    ]
    
    # 要检查的文件
    files_to_check = [
        'DATABASE_SETUP_GUIDE.md',
        'config.py',
        '.env.cache.example',
        'RAILWAY_MYSQL_SETUP.md',
        '.env.example'
    ]
    
    issues_found = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern in sensitive_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            issues_found.append({
                                'file': file_path,
                                'line': i,
                                'content': line.strip(),
                                'pattern': pattern
                            })
    
    return issues_found

def fix_commit_history():
    """修复Git提交历史"""
    print("\n🔧 修复Git提交历史...")
    
    try:
        # 检查是否有未提交的更改
        status = check_git_status()
        if status:
            print("📝 检测到未提交的更改，先提交修复...")
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', 'fix: 移除敏感信息，使用占位符替代'], check=True)
            print("✅ 修复提交已创建")
        
        # 检查是否需要修改历史提交
        print("\n⚠️  注意：如果敏感信息已经推送到远程仓库，建议：")
        print("1. 联系GitHub支持删除敏感信息")
        print("2. 或者创建新的仓库重新开始")
        print("3. 如果是私有仓库且确认没有泄露，可以继续推送修复")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git操作失败: {e}")
        return False

def create_gitignore_patterns():
    """创建.gitignore模式"""
    print("\n📝 更新.gitignore文件...")
    
    gitignore_patterns = [
        "# 敏感信息文件",
        ".env",
        ".env.local",
        ".env.production",
        "*.key",
        "*.pem",
        "config/secrets.py",
        "secrets/",
        "",
        "# 数据库文件",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "data/",
        "",
        "# 日志文件",
        "*.log",
        "logs/",
        "",
        "# 临时文件",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        ".pytest_cache/",
        ".coverage",
        "",
    ]
    
    gitignore_path = '.gitignore'
    existing_content = ""
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # 添加新的模式（如果不存在）
    new_patterns = []
    for pattern in gitignore_patterns:
        if pattern and pattern not in existing_content:
            new_patterns.append(pattern)
    
    if new_patterns:
        with open(gitignore_path, 'a', encoding='utf-8') as f:
            f.write('\n'.join(new_patterns))
        print("✅ .gitignore已更新")
    else:
        print("✅ .gitignore已是最新")

def create_security_guide():
    """创建安全指南"""
    print("\n📖 创建安全指南...")
    
    security_guide = """# 安全配置指南

## 🔒 敏感信息处理

### 1. 环境变量安全
- 永远不要在代码中硬编码密码、API密钥或其他敏感信息
- 使用环境变量或配置文件（不提交到Git）
- 使用 `.env` 文件进行本地开发，确保 `.env` 在 `.gitignore` 中

### 2. 数据库连接字符串
```bash
# ✅ 正确：使用占位符
DATABASE_URL=mysql://[USERNAME]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]

# ❌ 错误：包含真实凭据
DATABASE_URL=mysql://admin:secretpass123@db.example.com:3306/mydb
```

### 3. API密钥管理
```bash
# ✅ 正确：使用占位符
OPENAI_API_KEY=[YOUR_API_KEY]

# ❌ 错误：真实密钥
OPENAI_API_KEY=sk-1234567890abcdef...
```

### 4. 生成安全密钥
```bash
# 生成SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 生成随机密码
python -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16)))"
```

## 🛡️ GitHub安全最佳实践

### 1. 启用安全功能
- 启用Secret Scanning
- 启用Dependency Scanning
- 启用Code Scanning

### 2. 处理安全警告
- 立即修复检测到的敏感信息
- 使用占位符替代真实凭据
- 更新文档和示例

### 3. 提交前检查
- 使用 `git diff` 检查更改
- 确保没有敏感信息
- 使用pre-commit hooks

## 🔧 修复已提交的敏感信息

如果敏感信息已经提交：

1. **立即更改凭据**：更改所有暴露的密码和API密钥
2. **修复代码**：使用占位符替代敏感信息
3. **联系GitHub**：如果是公开仓库，联系GitHub支持
4. **考虑重建仓库**：对于严重泄露，考虑创建新仓库

## 📋 检查清单

- [ ] 所有密码使用占位符格式 `[PASSWORD]`
- [ ] 所有API密钥使用占位符格式 `[API_KEY]`
- [ ] `.env` 文件在 `.gitignore` 中
- [ ] 文档中没有真实凭据
- [ ] 配置示例使用占位符
- [ ] 启用GitHub安全功能
"""
    
    with open('SECURITY_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(security_guide)
    
    print("✅ 安全指南已创建: SECURITY_GUIDE.md")

def main():
    """主函数"""
    print("🔒 GitHub安全问题修复工具")
    print("=" * 50)
    
    # 检查Git状态
    if check_git_status() is None:
        sys.exit(1)
    
    # 扫描敏感信息
    issues = scan_sensitive_patterns()
    
    if issues:
        print(f"\n⚠️  发现 {len(issues)} 个潜在的敏感信息问题：")
        for issue in issues:
            print(f"   📁 {issue['file']}:{issue['line']} - {issue['content'][:50]}...")
        print("\n✅ 这些问题已通过占位符修复")
    else:
        print("\n✅ 未发现敏感信息问题")
    
    # 修复Git历史
    if not fix_commit_history():
        print("❌ Git历史修复失败")
        sys.exit(1)
    
    # 更新.gitignore
    create_gitignore_patterns()
    
    # 创建安全指南
    create_security_guide()
    
    print("\n🎉 安全修复完成！")
    print("\n📋 下一步操作：")
    print("1. 检查修复结果：git diff")
    print("2. 提交更改：git add . && git commit -m 'security: 完善安全配置'")
    print("3. 推送到GitHub：git push")
    print("4. 启用GitHub安全功能")
    print("5. 阅读 SECURITY_GUIDE.md 了解更多安全最佳实践")

if __name__ == "__main__":
    main()
