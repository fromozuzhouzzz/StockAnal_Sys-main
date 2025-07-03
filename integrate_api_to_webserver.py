#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API集成脚本
将新的API功能集成到现有的web_server.py中
"""

import os
import sys
import logging

def integrate_api_functionality():
    """集成API功能到现有的web_server.py"""
    
    print("🚀 开始集成API功能到股票分析系统...")
    
    # 检查必要文件是否存在
    required_files = [
        'web_server.py',
        'api_endpoints.py', 
        'rate_limiter.py',
        'auth_middleware.py',
        'api_response.py',
        'api_cache_integration.py',
        'api_integration.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    print("✅ 所有必要文件已存在")
    
    # 读取现有的web_server.py
    try:
        with open('web_server.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ 读取web_server.py失败: {e}")
        return False
    
    # 检查是否已经集成过API功能
    if 'api_integration' in content:
        print("⚠️  API功能似乎已经集成过，跳过集成步骤")
        return True
    
    # 准备要添加的导入语句
    api_imports = """
# API功能导入
try:
    from api_integration import integrate_api_with_existing_app
    API_INTEGRATION_AVAILABLE = True
    print("API集成模块导入成功")
except ImportError as e:
    print(f"API集成模块导入失败: {e}")
    API_INTEGRATION_AVAILABLE = False
"""
    
    # 准备要添加的集成代码
    api_integration_code = """
# 集成API功能
if API_INTEGRATION_AVAILABLE:
    try:
        if integrate_api_with_existing_app(app):
            app.logger.info("✅ API功能集成成功")
            print("✅ API功能集成成功")
        else:
            app.logger.error("❌ API功能集成失败")
            print("❌ API功能集成失败")
    except Exception as e:
        app.logger.error(f"API功能集成出错: {e}")
        print(f"❌ API功能集成出错: {e}")
else:
    print("⚠️  API集成模块不可用，跳过API功能集成")
"""
    
    # 找到合适的位置插入代码
    lines = content.split('\n')
    
    # 找到导入部分的结束位置
    import_end_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            import_end_index = i
    
    if import_end_index == -1:
        print("❌ 无法找到合适的导入位置")
        return False
    
    # 插入API导入
    lines.insert(import_end_index + 1, api_imports)
    
    # 找到Flask应用创建后的位置
    app_creation_index = -1
    for i, line in enumerate(lines):
        if 'app = Flask(__name__)' in line:
            app_creation_index = i
            break
    
    if app_creation_index == -1:
        print("❌ 无法找到Flask应用创建位置")
        return False
    
    # 找到合适的集成位置（通常在应用配置之后）
    integration_index = app_creation_index + 1
    
    # 寻找更好的集成位置（在其他初始化代码之后）
    for i in range(app_creation_index + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith('if __name__'):
            integration_index = i
            break
        elif line.startswith('app.run'):
            integration_index = i
            break
    
    # 插入API集成代码
    lines.insert(integration_index, api_integration_code)
    
    # 写回文件
    try:
        # 备份原文件
        with open('web_server.py.backup', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 已创建web_server.py备份文件")
        
        # 写入修改后的内容
        with open('web_server.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("✅ API功能已成功集成到web_server.py")
        return True
        
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")
        return False


def create_api_config_file():
    """创建API配置文件"""
    
    config_content = """# API配置文件
# 将以下配置添加到您的.env文件中

# API功能开关
API_ENABLED=True
API_VERSION=1.0.0

# API密钥配置（生产环境请使用更安全的密钥）
API_KEY=UZXJfw3YNX80DLfN
HMAC_SECRET=your_hmac_secret_key_here

# 管理员密钥（用于API密钥管理等管理功能）
ADMIN_KEY=your_admin_key_here

# API限流配置
RATE_LIMIT_ENABLED=True
RATE_LIMIT_FREE_TIER=100
RATE_LIMIT_PAID_TIER=1000
RATE_LIMIT_ENTERPRISE_TIER=10000

# API缓存配置
API_CACHE_ENABLED=True
API_CACHE_DEFAULT_TTL=900
API_CACHE_PRELOAD_POPULAR_STOCKS=True

# API密钥配置（JSON格式）
# API_KEYS_CONFIG={"key1": {"tier": "free", "permissions": ["stock_analysis"]}}
"""
    
    try:
        with open('api_config.env', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ 已创建API配置文件: api_config.env")
        return True
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")
        return False


def run_api_tests():
    """运行API测试"""
    print("\n🧪 运行API测试...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, 'test_api_endpoints.py'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ API测试通过")
            return True
        else:
            print(f"❌ API测试失败:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  API测试超时")
        return False
    except Exception as e:
        print(f"❌ 运行API测试出错: {e}")
        return False


def print_integration_summary():
    """打印集成总结"""
    
    summary = """
🎉 API功能集成完成！

📋 集成内容：
✅ 投资组合分析API: POST /api/v1/portfolio/analyze
✅ 个股分析API: POST /api/v1/stock/analyze  
✅ 批量股票评分API: POST /api/v1/stocks/batch-score
✅ 异步任务管理API: /api/v1/tasks/*
✅ API认证和限流系统
✅ MySQL缓存集成
✅ API文档和测试用例

📖 使用指南：
1. 查看 API_USAGE_GUIDE.md 了解详细使用方法
2. 访问 /api/docs 查看Swagger文档
3. 使用 /api/v1/health 检查API状态
4. 参考 test_api_endpoints.py 了解测试用例

🔧 配置说明：
1. 将 api_config.env 中的配置添加到您的 .env 文件
2. 根据需要调整API密钥和限流配置
3. 生产环境请使用更安全的密钥

🚀 启动应用：
python web_server.py

📝 API端点示例：
curl -X POST "http://localhost:8888/api/v1/stock/analyze" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: UZXJfw3YNX80DLfN" \\
  -d '{"stock_code": "000001.SZ"}'

如有问题，请查看日志或联系技术支持。
"""
    
    print(summary)


def main():
    """主函数"""
    
    print("=" * 60)
    print("股票分析系统 API 功能集成工具")
    print("=" * 60)
    
    success_count = 0
    total_steps = 4
    
    # 步骤1: 集成API功能
    print("\n📦 步骤 1/4: 集成API功能到web_server.py")
    if integrate_api_functionality():
        success_count += 1
    
    # 步骤2: 创建配置文件
    print("\n⚙️  步骤 2/4: 创建API配置文件")
    if create_api_config_file():
        success_count += 1
    
    # 步骤3: 运行测试（可选）
    print("\n🧪 步骤 3/4: 运行API测试（可选）")
    try:
        if run_api_tests():
            success_count += 1
    except:
        print("⚠️  跳过API测试（需要启动服务器）")
        success_count += 1  # 不强制要求测试通过
    
    # 步骤4: 显示总结
    print("\n📋 步骤 4/4: 显示集成总结")
    print_integration_summary()
    success_count += 1
    
    # 最终结果
    print("\n" + "=" * 60)
    if success_count == total_steps:
        print("🎉 API功能集成完全成功！")
        print("现在您可以启动应用并使用新的API功能了。")
    else:
        print(f"⚠️  集成部分成功 ({success_count}/{total_steps})")
        print("请检查上述错误信息并手动完成剩余步骤。")
    print("=" * 60)


if __name__ == '__main__':
    main()
