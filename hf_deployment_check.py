#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Spaces 部署检查脚本
检查部署前的文件和配置是否正确
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (文件不存在)")
        return False

def check_directory_exists(dir_path, description):
    """检查目录是否存在"""
    if os.path.isdir(dir_path):
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (目录不存在)")
        return False

def check_requirements():
    """检查 requirements.txt 内容"""
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt 文件不存在")
        return False
    
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键依赖
    required_packages = [
        'flask',
        'pandas',
        'numpy',
        'akshare',
        'requests',
        'python-dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        if package not in content.lower():
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ requirements.txt 缺少关键依赖: {', '.join(missing_packages)}")
        return False
    else:
        print("✅ requirements.txt 包含所有关键依赖")
        return True

def check_app_py():
    """检查 app.py 文件"""
    if not os.path.exists('app.py'):
        print("❌ app.py 文件不存在")
        return False
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键内容
    checks = [
        ('from web_server import app', '导入主应用'),
        ('app.run(', '应用启动代码'),
        ('host="0.0.0.0"', '主机配置'),
        ('PORT', '端口配置')
    ]
    
    all_good = True
    for check_str, description in checks:
        if check_str in content:
            print(f"✅ app.py {description}: 正确")
        else:
            print(f"❌ app.py {description}: 缺失")
            all_good = False
    
    return all_good

def main():
    """主检查函数"""
    print("🔍 Hugging Face Spaces 部署检查")
    print("=" * 50)
    
    all_checks_passed = True
    
    # 检查核心文件
    print("\n📁 核心文件检查:")
    core_files = [
        ('app.py', 'Hugging Face Spaces 入口文件'),
        ('web_server.py', '主应用文件'),
        ('requirements.txt', '依赖文件'),
        ('README_HF.md', 'Hugging Face README'),
        ('.env.hf', 'Hugging Face 环境变量示例')
    ]
    
    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # 检查分析模块
    print("\n🔬 分析模块检查:")
    analysis_modules = [
        'stock_analyzer.py',
        'fundamental_analyzer.py',
        'capital_flow_analyzer.py',
        'scenario_predictor.py',
        'stock_qa.py',
        'risk_monitor.py',
        'industry_analyzer.py',
        'news_fetcher.py'
    ]
    
    for module in analysis_modules:
        if not check_file_exists(module, f'分析模块 {module}'):
            all_checks_passed = False
    
    # 检查目录结构
    print("\n📂 目录结构检查:")
    directories = [
        ('templates', '模板目录'),
        ('static', '静态文件目录')
    ]
    
    for dir_path, description in directories:
        if not check_directory_exists(dir_path, description):
            all_checks_passed = False
    
    # 检查模板文件
    print("\n📄 模板文件检查:")
    template_files = [
        'templates/index.html',
        'templates/dashboard.html',
        'templates/layout.html',
        'templates/stock_detail.html'
    ]
    
    for template in template_files:
        if not check_file_exists(template, f'模板文件 {template}'):
            all_checks_passed = False
    
    # 检查 requirements.txt
    print("\n📦 依赖检查:")
    if not check_requirements():
        all_checks_passed = False
    
    # 检查 app.py
    print("\n🚀 启动文件检查:")
    if not check_app_py():
        all_checks_passed = False
    
    # 总结
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 所有检查通过！可以开始部署到 Hugging Face Spaces")
        print("\n📋 下一步:")
        print("1. 在 Hugging Face 创建新的 Space")
        print("2. 选择 Gradio SDK")
        print("3. 上传所有文件")
        print("4. 在 Settings -> Variables 中配置环境变量")
        print("5. 等待部署完成")
    else:
        print("❌ 检查发现问题，请修复后再部署")
        print("\n💡 建议:")
        print("- 确保所有必需文件都存在")
        print("- 检查文件路径和名称是否正确")
        print("- 参考 Hugging_Face_部署指南.md 获取详细说明")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
