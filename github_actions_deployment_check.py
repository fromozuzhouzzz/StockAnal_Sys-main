#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 自动部署到 Hugging Face Spaces 检查脚本
用于验证部署前的准备工作是否完成
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def print_header(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_section(title):
    """打印章节标题"""
    print(f"\n📋 {title}")
    print("-" * 40)

def check_file_exists(file_path, description=""):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {file_path} - {description}")
        return True
    else:
        print(f"❌ {file_path} - {description} (文件不存在)")
        return False

def check_directory_exists(dir_path, description=""):
    """检查目录是否存在"""
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        print(f"✅ {dir_path}/ - {description}")
        return True
    else:
        print(f"❌ {dir_path}/ - {description} (目录不存在)")
        return False

def check_github_workflow():
    """检查 GitHub Actions 工作流文件"""
    print_section("GitHub Actions 工作流检查")
    
    workflow_dir = ".github/workflows"
    workflow_file = ".github/workflows/deploy.yml"
    
    checks_passed = 0
    total_checks = 3
    
    # 检查目录结构
    if check_directory_exists(".github", "GitHub 配置目录"):
        checks_passed += 1
    
    if check_directory_exists(workflow_dir, "工作流目录"):
        checks_passed += 1
    
    # 检查工作流文件
    if check_file_exists(workflow_file, "部署工作流文件"):
        checks_passed += 1
        
        # 检查工作流文件内容
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            required_elements = [
                ('name:', '工作流名称'),
                ('on:', '触发条件'),
                ('HF_TOKEN', 'Hugging Face 令牌引用'),
                ('HF_SPACE', 'Hugging Face Space 引用'),
                ('huggingface_hub', 'HF Hub 依赖'),
                ('upload_folder', '上传函数调用')
            ]
            
            print("\n  📄 工作流文件内容检查:")
            for element, description in required_elements:
                if element in content:
                    print(f"    ✅ {description}")
                else:
                    print(f"    ❌ {description} (未找到)")
                    
        except Exception as e:
            print(f"    ⚠️ 无法读取工作流文件: {e}")
    
    return checks_passed, total_checks

def check_project_files():
    """检查项目必需文件"""
    print_section("项目文件检查")
    
    required_files = [
        ('app.py', 'Hugging Face Spaces 入口文件'),
        ('web_server.py', 'Flask 应用主文件'),
        ('requirements.txt', 'Python 依赖文件'),
        ('stock_analyzer.py', '股票分析核心模块')
    ]
    
    optional_files = [
        ('README.md', '项目说明文件'),
        ('README_HF.md', 'Hugging Face 专用说明文件'),
        ('.env.example', '环境变量示例文件'),
        ('.gitignore', 'Git 忽略文件')
    ]
    
    checks_passed = 0
    total_checks = len(required_files)
    
    print("  必需文件:")
    for file_path, description in required_files:
        if check_file_exists(file_path, description):
            checks_passed += 1
    
    print("\n  可选文件:")
    for file_path, description in optional_files:
        check_file_exists(file_path, description)
    
    return checks_passed, total_checks

def check_requirements_txt():
    """检查 requirements.txt 内容"""
    print_section("依赖文件检查")
    
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt 文件不存在")
        return 0, 1
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # 检查关键依赖
        required_packages = [
            'flask',
            'pandas',
            'numpy',
            'akshare',
            'requests',
            'python-dotenv'
        ]
        
        # 检查不兼容的依赖
        incompatible_packages = [
            'psycopg2-binary',
            'redis',
            'supervisor'
        ]
        
        print("  ✅ 关键依赖检查:")
        missing_packages = []
        for package in required_packages:
            if package in content:
                print(f"    ✅ {package}")
            else:
                print(f"    ❌ {package} (缺失)")
                missing_packages.append(package)
        
        print("\n  ⚠️ 不兼容依赖检查:")
        found_incompatible = []
        for package in incompatible_packages:
            if package in content:
                print(f"    ⚠️ {package} (可能在 HF Spaces 中不可用)")
                found_incompatible.append(package)
            else:
                print(f"    ✅ {package} (未使用)")
        
        if missing_packages:
            print(f"\n  ❌ 缺少关键依赖: {', '.join(missing_packages)}")
            return 0, 1
        elif found_incompatible:
            print(f"\n  ⚠️ 发现可能不兼容的依赖: {', '.join(found_incompatible)}")
            print("     建议在 requirements.txt 中注释这些依赖")
            return 1, 1
        else:
            print("\n  ✅ 依赖文件检查通过")
            return 1, 1
            
    except Exception as e:
        print(f"❌ 读取 requirements.txt 失败: {e}")
        return 0, 1

def check_app_py():
    """检查 app.py 配置"""
    print_section("入口文件检查")
    
    if not os.path.exists('app.py'):
        print("❌ app.py 文件不存在")
        return 0, 1
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        checks = [
            ('from web_server import app', '导入主应用'),
            ('USE_DATABASE', '数据库配置'),
            ('USE_REDIS_CACHE', 'Redis 缓存配置'),
            ('host=\'0.0.0.0\'', '主机配置'),
            ('port=', '端口配置')
        ]
        
        passed_checks = 0
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description}")
                passed_checks += 1
            else:
                print(f"  ❌ {description} (未找到)")
        
        if passed_checks >= 3:
            print("\n  ✅ app.py 配置基本正确")
            return 1, 1
        else:
            print("\n  ❌ app.py 配置可能有问题")
            return 0, 1
            
    except Exception as e:
        print(f"❌ 读取 app.py 失败: {e}")
        return 0, 1

def check_git_status():
    """检查 Git 状态"""
    print_section("Git 状态检查")
    
    try:
        # 检查是否在 Git 仓库中
        result = subprocess.run(['git', 'status'], 
                              capture_output=True, text=True, check=True)
        
        print("  ✅ 当前在 Git 仓库中")
        
        # 检查是否有未提交的更改
        if "nothing to commit" in result.stdout:
            print("  ✅ 没有未提交的更改")
        else:
            print("  ⚠️ 有未提交的更改")
            print("     建议先提交所有更改再进行部署")
        
        # 检查当前分支
        branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                     capture_output=True, text=True, check=True)
        current_branch = branch_result.stdout.strip()
        print(f"  📍 当前分支: {current_branch}")
        
        if current_branch in ['main', 'master']:
            print("  ✅ 在主分支上，推送后会触发自动部署")
        else:
            print("  ⚠️ 不在主分支上，需要合并到 main/master 分支才会触发部署")
        
        return 1, 1
        
    except subprocess.CalledProcessError:
        print("  ❌ 不在 Git 仓库中或 Git 命令失败")
        print("     请确保项目已初始化为 Git 仓库")
        return 0, 1
    except FileNotFoundError:
        print("  ❌ 未找到 Git 命令")
        print("     请确保已安装 Git")
        return 0, 1

def print_github_secrets_guide():
    """打印 GitHub Secrets 设置指南"""
    print_section("GitHub Secrets 设置指南")
    
    print("  📝 需要在 GitHub 仓库中设置以下 Secrets:")
    print("     1. 进入 GitHub 仓库 → Settings → Secrets and variables → Actions")
    print("     2. 点击 'New repository secret' 添加以下密钥:")
    print()
    print("     🔑 HF_TOKEN")
    print("        - Name: HF_TOKEN")
    print("        - Secret: 您的 Hugging Face 访问令牌")
    print("        - 获取方式: HF 网站 → Settings → Access Tokens → New token (Write 权限)")
    print()
    print("     🔑 HF_SPACE")
    print("        - Name: HF_SPACE")
    print("        - Secret: 您的用户名/space名称 (例如: johndoe/stock-analysis-system)")
    print()
    print("     🔑 可选的 API 密钥 (如果需要 AI 功能):")
    print("        - OPENAI_API_KEY: 您的 OpenAI API 密钥")
    print("        - OPENAI_API_URL: API 端点地址")
    print("        - OPENAI_API_MODEL: 使用的模型名称")

def print_next_steps():
    """打印后续步骤"""
    print_section("后续步骤")
    
    print("  🚀 部署步骤:")
    print("     1. 确保所有检查项都通过")
    print("     2. 在 Hugging Face 创建 Space")
    print("     3. 获取 HF 访问令牌并设置 GitHub Secrets")
    print("     4. 推送代码到 main 分支触发自动部署")
    print("     5. 在 GitHub Actions 页面监控部署进度")
    print("     6. 访问 HF Space 查看部署结果")
    print()
    print("  📚 参考文档:")
    print("     - 详细教程: GitHub_Actions_HF_部署教程.md")
    print("     - 快速指南: 快速部署指南.md")

def main():
    """主函数"""
    print_header("GitHub Actions 自动部署检查")
    print("🔍 检查项目是否准备好自动部署到 Hugging Face Spaces")
    
    total_passed = 0
    total_checks = 0
    
    # 执行各项检查
    passed, checks = check_github_workflow()
    total_passed += passed
    total_checks += checks
    
    passed, checks = check_project_files()
    total_passed += passed
    total_checks += checks
    
    passed, checks = check_requirements_txt()
    total_passed += passed
    total_checks += checks
    
    passed, checks = check_app_py()
    total_passed += passed
    total_checks += checks
    
    passed, checks = check_git_status()
    total_passed += passed
    total_checks += checks
    
    # 打印总结
    print_header("检查结果总结")
    
    success_rate = (total_passed / total_checks) * 100 if total_checks > 0 else 0
    
    print(f"📊 检查通过率: {total_passed}/{total_checks} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 恭喜！您的项目已准备好进行自动部署！")
        print_github_secrets_guide()
        print_next_steps()
    elif success_rate >= 60:
        print("⚠️ 项目基本准备就绪，但还有一些问题需要解决")
        print("   请根据上述检查结果修复问题后再进行部署")
    else:
        print("❌ 项目还没有准备好进行部署")
        print("   请根据检查结果修复所有问题")
    
    print(f"\n{'='*60}")
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())
