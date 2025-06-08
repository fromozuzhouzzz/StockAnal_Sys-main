#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Spaces 部署准备脚本
自动准备部署所需的文件
"""

import os
import shutil
import sys
from pathlib import Path

def create_deployment_folder():
    """创建部署文件夹"""
    deployment_folder = "hf_deployment"
    
    # 如果文件夹存在，先删除
    if os.path.exists(deployment_folder):
        shutil.rmtree(deployment_folder)
    
    # 创建新文件夹
    os.makedirs(deployment_folder)
    print(f"✅ 创建部署文件夹: {deployment_folder}")
    
    return deployment_folder

def copy_files(deployment_folder):
    """复制必需的文件"""
    
    # 核心文件列表
    core_files = [
        'app.py',
        'web_server.py',
        'requirements.txt',
        'database.py',
        'auth_middleware.py'
    ]
    
    # 分析模块文件
    analysis_files = [
        'stock_analyzer.py',
        'fundamental_analyzer.py',
        'capital_flow_analyzer.py',
        'scenario_predictor.py',
        'stock_qa.py',
        'risk_monitor.py',
        'industry_analyzer.py',
        'index_industry_analyzer.py',
        'news_fetcher.py',
        'us_stock_service.py'
    ]
    
    # 复制核心文件
    print("\n📁 复制核心文件:")
    for file in core_files:
        if os.path.exists(file):
            shutil.copy2(file, deployment_folder)
            print(f"✅ 复制: {file}")
        else:
            print(f"⚠️  文件不存在: {file}")
    
    # 复制分析模块
    print("\n🔬 复制分析模块:")
    for file in analysis_files:
        if os.path.exists(file):
            shutil.copy2(file, deployment_folder)
            print(f"✅ 复制: {file}")
        else:
            print(f"⚠️  文件不存在: {file}")
    
    # 复制目录
    print("\n📂 复制目录:")
    directories = ['templates', 'static']
    for directory in directories:
        if os.path.exists(directory):
            dest_dir = os.path.join(deployment_folder, directory)
            shutil.copytree(directory, dest_dir)
            print(f"✅ 复制目录: {directory}")
        else:
            print(f"⚠️  目录不存在: {directory}")
    
    # 复制并重命名 README
    if os.path.exists('README_HF.md'):
        shutil.copy2('README_HF.md', os.path.join(deployment_folder, 'README.md'))
        print("✅ 复制并重命名: README_HF.md -> README.md")
    
    # 复制环境变量示例
    if os.path.exists('.env.hf'):
        shutil.copy2('.env.hf', os.path.join(deployment_folder, '.env.example'))
        print("✅ 复制环境变量示例: .env.hf -> .env.example")

def create_gitignore(deployment_folder):
    """创建 .gitignore 文件"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.env.local

# Logs
*.log
logs/

# Data
data/
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    
    gitignore_path = os.path.join(deployment_folder, '.gitignore')
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("✅ 创建 .gitignore 文件")

def create_deployment_instructions(deployment_folder):
    """创建部署说明文件"""
    instructions = """# Hugging Face Spaces 部署说明

## 📋 部署步骤

1. **创建 Hugging Face Space**
   - 访问 https://huggingface.co/
   - 点击 "New Space"
   - 选择 Gradio SDK
   - 选择 CPU basic (免费)

2. **上传文件**
   - 将此文件夹中的所有文件上传到 Space
   - 或使用 Git 克隆并推送

3. **配置环境变量**
   在 Space Settings -> Variables 中添加:
   ```
   OPENAI_API_KEY = 您的OpenAI API密钥
   OPENAI_API_URL = https://api.openai.com/v1
   OPENAI_API_MODEL = gpt-4o
   NEWS_MODEL = gpt-4o
   USE_DATABASE = False
   USE_REDIS_CACHE = False
   ```

4. **等待部署完成**
   - 查看 Logs 标签监控构建过程
   - 部署成功后即可访问应用

## ⚠️ 注意事项

- 确保 OpenAI API 密钥有效且有余额
- 首次访问可能需要等待冷启动
- 免费版本有使用限制

## 🔗 相关链接

- [Hugging Face Spaces 文档](https://huggingface.co/docs/hub/spaces)
- [项目 GitHub 仓库](https://github.com/LargeCupPanda/StockAnal_Sys)
"""
    
    instructions_path = os.path.join(deployment_folder, 'DEPLOYMENT_INSTRUCTIONS.md')
    with open(instructions_path, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("✅ 创建部署说明文件")

def main():
    """主函数"""
    print("🚀 准备 Hugging Face Spaces 部署文件")
    print("=" * 50)
    
    try:
        # 创建部署文件夹
        deployment_folder = create_deployment_folder()
        
        # 复制文件
        copy_files(deployment_folder)
        
        # 创建 .gitignore
        create_gitignore(deployment_folder)
        
        # 创建部署说明
        create_deployment_instructions(deployment_folder)
        
        print("\n" + "=" * 50)
        print("🎉 部署文件准备完成！")
        print(f"\n📁 部署文件位置: {deployment_folder}/")
        print("\n📋 下一步:")
        print("1. 查看 hf_deployment/ 文件夹中的所有文件")
        print("2. 阅读 DEPLOYMENT_INSTRUCTIONS.md 获取详细部署步骤")
        print("3. 在 Hugging Face 创建新的 Space")
        print("4. 上传所有文件并配置环境变量")
        
        # 显示文件列表
        print(f"\n📄 部署文件列表:")
        for root, dirs, files in os.walk(deployment_folder):
            level = root.replace(deployment_folder, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
    except Exception as e:
        print(f"❌ 准备部署文件时出错: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
