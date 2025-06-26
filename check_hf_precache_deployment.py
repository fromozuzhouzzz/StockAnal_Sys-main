# -*- coding: utf-8 -*-
"""
检查Hugging Face Spaces部署中的预缓存功能
"""

import os
import re

def check_file_exists(file_path, description=""):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (不存在)")
        return False

def check_file_content(file_path, patterns, description=""):
    """检查文件内容是否包含指定模式"""
    if not os.path.exists(file_path):
        print(f"❌ {description}: {file_path} (文件不存在)")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_patterns = []
        for pattern_name, pattern in patterns.items():
            if not re.search(pattern, content, re.MULTILINE):
                missing_patterns.append(pattern_name)
        
        if missing_patterns:
            print(f"⚠️ {description}: {file_path}")
            for missing in missing_patterns:
                print(f"    缺少: {missing}")
            return False
        else:
            print(f"✅ {description}: {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ {description}: {file_path} (读取失败: {e})")
        return False

def check_hf_precache_deployment():
    """检查HF Spaces部署中的预缓存功能"""
    print("🔍 检查Hugging Face Spaces预缓存功能部署")
    print("=" * 60)
    
    hf_dir = "hf_deployment"
    all_checks_passed = True
    
    # 1. 检查核心文件是否存在
    print("\n📁 核心文件检查:")
    core_files = [
        (f"{hf_dir}/stock_precache_scheduler.py", "预缓存调度器"),
        (f"{hf_dir}/web_server.py", "主应用文件"),
        (f"{hf_dir}/test_precache_hf.py", "HF预缓存测试脚本")
    ]
    
    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # 2. 检查web_server.py中的预缓存相关代码
    print("\n🔧 web_server.py预缓存集成检查:")
    web_server_patterns = {
        "预缓存导入": r"from stock_precache_scheduler import.*precache_scheduler",
        "预缓存状态API": r"@app\.route\(['\"]\/api\/precache\/status['\"]",
        "手动预缓存API": r"@app\.route\(['\"]\/api\/precache\/manual['\"]",
        "预缓存初始化": r"init_precache_scheduler"
    }
    
    if not check_file_content(f"{hf_dir}/web_server.py", web_server_patterns, "web_server.py预缓存集成"):
        all_checks_passed = False
    
    # 3. 检查stock_precache_scheduler.py的完整性
    print("\n⚙️ 预缓存调度器完整性检查:")
    scheduler_patterns = {
        "调度器类": r"class StockPrecacheScheduler",
        "获取状态方法": r"def get_stats\(self\)",
        "手动预缓存方法": r"def manual_precache\(self",
        "初始化函数": r"def init_precache_scheduler\(\)",
        "HF兼容性": r"HF_SPACES_MODE.*SPACE_ID"
    }
    
    if not check_file_content(f"{hf_dir}/stock_precache_scheduler.py", scheduler_patterns, "预缓存调度器完整性"):
        all_checks_passed = False
    
    # 4. 检查依赖文件
    print("\n📦 依赖检查:")
    dependency_files = [
        (f"{hf_dir}/requirements.txt", "依赖文件"),
        (f"{hf_dir}/database.py", "数据库模块"),
        (f"{hf_dir}/stock_analyzer.py", "股票分析器")
    ]
    
    for file_path, description in dependency_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # 5. 生成部署建议
    print("\n" + "=" * 60)
    print("📊 检查结果总结")
    print("=" * 60)
    
    if all_checks_passed:
        print("✅ 所有检查通过！预缓存功能应该可以正常工作")
        print("\n🚀 下一步操作:")
        print("1. 将hf_deployment目录的内容部署到Hugging Face Spaces")
        print("2. 等待部署完成后，访问以下URL测试:")
        print("   https://huggingface.co/spaces/fromozu/stock-analysis/api/precache/status")
        print("3. 运行测试脚本验证功能:")
        print("   python hf_deployment/test_precache_hf.py")
    else:
        print("❌ 部分检查未通过，需要修复以下问题:")
        print("\n🔧 修复建议:")
        
        if not os.path.exists(f"{hf_dir}/stock_precache_scheduler.py"):
            print("1. 复制stock_precache_scheduler.py到hf_deployment目录")
        
        # 检查web_server.py是否需要更新
        web_server_path = f"{hf_dir}/web_server.py"
        if os.path.exists(web_server_path):
            with open(web_server_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "precache_scheduler" not in content:
                print("2. 更新hf_deployment/web_server.py，添加预缓存相关代码")
            
            if "/api/precache/status" not in content:
                print("3. 在hf_deployment/web_server.py中添加预缓存API路由")
        
        print("4. 重新部署到Hugging Face Spaces")
    
    # 6. 提供测试命令
    print("\n🧪 测试命令:")
    print("# 本地测试:")
    print("python check_hf_precache_deployment.py")
    print("python hf_deployment/test_precache_hf.py")
    print("\n# 远程测试:")
    print("curl 'https://huggingface.co/spaces/fromozu/stock-analysis/api/precache/status'")
    
    return all_checks_passed

def generate_deployment_checklist():
    """生成部署检查清单"""
    print("\n📋 Hugging Face Spaces预缓存功能部署清单:")
    print("=" * 60)
    
    checklist = [
        "□ 复制stock_precache_scheduler.py到hf_deployment目录",
        "□ 更新hf_deployment/web_server.py，添加预缓存导入",
        "□ 在hf_deployment/web_server.py中添加预缓存API路由",
        "□ 在hf_deployment/web_server.py中添加预缓存初始化代码",
        "□ 创建hf_deployment/test_precache_hf.py测试脚本",
        "□ 提交所有更改到Git仓库",
        "□ 推送到Hugging Face Spaces",
        "□ 等待部署完成",
        "□ 测试预缓存API可用性",
        "□ 验证预缓存功能正常工作"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print("\n💡 重要提示:")
    print("- Hugging Face Spaces环境可能有资源限制")
    print("- 预缓存任务建议使用较少的股票数量(5-20只)")
    print("- 定时任务在HF Spaces中可能不稳定，建议使用手动触发")

if __name__ == "__main__":
    # 运行检查
    result = check_hf_precache_deployment()
    
    # 生成部署清单
    generate_deployment_checklist()
    
    print(f"\n🎯 检查完成，结果: {'通过' if result else '需要修复'}")
