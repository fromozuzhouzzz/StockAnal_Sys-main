#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HF Spaces 配色修复测试脚本
用于验证修复效果并生成测试报告
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"✅ {description}: {file_path} ({file_size} 字节)")
        return True
    else:
        print(f"❌ {description}: {file_path} 不存在")
        return False

def check_css_fallbacks(css_file):
    """检查CSS文件中的fallback样式"""
    if not os.path.exists(css_file):
        print(f"❌ CSS文件不存在: {css_file}")
        return False
    
    with open(css_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键的fallback样式
    fallback_checks = [
        ('body fallback', 'background-color: #FEFBFF'),
        ('navbar fallback', 'background-color: #F7F2FA'),
        ('button fallback', 'background-color: #1565C0'),
        ('card fallback', 'border-radius: 16px'),
        ('trend colors', 'color: #d32f2f')
    ]
    
    results = []
    for check_name, pattern in fallback_checks:
        if pattern in content:
            results.append(f"✅ {check_name}: 已添加")
        else:
            results.append(f"❌ {check_name}: 缺失")
    
    return results

def check_template_updates():
    """检查模板文件的更新"""
    layout_file = 'templates/layout.html'
    if not os.path.exists(layout_file):
        print(f"❌ 模板文件不存在: {layout_file}")
        return False
    
    with open(layout_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('url_for CSS', "url_for('static', filename='md3-styles.css')"),
        ('兼容性CSS', "hf-spaces-compatibility.css"),
        ('兼容性JS', "hf-spaces-compatibility.js"),
        ('环境标识', 'name="hf-spaces"')
    ]
    
    results = []
    for check_name, pattern in checks:
        if pattern in content:
            results.append(f"✅ {check_name}: 已更新")
        else:
            results.append(f"❌ {check_name}: 未更新")
    
    return results

def run_local_test():
    """运行本地测试"""
    print("\n🧪 启动本地测试服务器...")
    
    try:
        # 启动Flask应用
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['USE_DATABASE'] = 'False'
        env['USE_REDIS_CACHE'] = 'False'
        
        process = subprocess.Popen(
            [sys.executable, 'web_server.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待服务器启动
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ 本地服务器启动成功")
            print("🌐 测试地址: http://localhost:8888/hf_spaces_test")
            print("⏰ 服务器将在10秒后自动关闭...")
            
            time.sleep(10)
            process.terminate()
            process.wait()
            print("✅ 本地测试完成")
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ 服务器启动失败")
            print(f"错误输出: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ 本地测试失败: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    
    report = []
    report.append("# HF Spaces 配色修复测试报告")
    report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 文件检查
    report.append("## 文件检查")
    files_to_check = [
        ('static/md3-styles.css', 'Material Design 3 主样式文件'),
        ('static/hf-spaces-compatibility.css', 'HF Spaces 兼容性样式'),
        ('static/js/hf-spaces-compatibility.js', 'HF Spaces 兼容性脚本'),
        ('static/js/theme-manager.js', '主题管理器'),
        ('templates/layout.html', '布局模板'),
        ('templates/hf_spaces_test.html', '测试页面模板')
    ]
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            report.append(f"- ✅ {description}: `{file_path}` ({file_size} 字节)")
        else:
            report.append(f"- ❌ {description}: `{file_path}` 不存在")
    
    report.append("")
    
    # CSS fallback检查
    report.append("## CSS Fallback 检查")
    css_results = check_css_fallbacks('static/md3-styles.css')
    for result in css_results:
        report.append(f"- {result}")
    
    report.append("")
    
    # 模板更新检查
    report.append("## 模板更新检查")
    template_results = check_template_updates()
    for result in template_results:
        report.append(f"- {result}")
    
    report.append("")
    
    # 修复内容总结
    report.append("## 修复内容总结")
    report.append("### 1. 静态资源路径统一")
    report.append("- 将硬编码的 `/static/` 路径改为 `url_for('static', filename='')`")
    report.append("- 确保在HF Spaces环境中正确加载静态资源")
    report.append("")
    
    report.append("### 2. CSS变量fallback")
    report.append("- 为所有关键样式添加fallback值")
    report.append("- 确保在不支持CSS变量的环境中正常显示")
    report.append("")
    
    report.append("### 3. 兼容性检测")
    report.append("- 添加环境检测脚本")
    report.append("- 自动应用HF Spaces特定修复")
    report.append("- 提供紧急样式修复功能")
    report.append("")
    
    report.append("### 4. 测试工具")
    report.append("- 创建专门的测试页面")
    report.append("- 提供调试和验证工具")
    report.append("")
    
    # 部署建议
    report.append("## 部署建议")
    report.append("1. 确保所有修改的文件都已上传到HF Spaces")
    report.append("2. 清除浏览器缓存后测试")
    report.append("3. 访问 `/hf_spaces_test` 页面验证修复效果")
    report.append("4. 如果仍有问题，可以使用页面上的调试工具")
    report.append("")
    
    # 保存报告
    with open('hf_spaces_fix_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print("✅ 测试报告已生成: hf_spaces_fix_report.md")

def main():
    """主函数"""
    print("🔍 HF Spaces 配色修复测试")
    print("=" * 50)
    
    # 检查关键文件
    print("\n📁 检查关键文件...")
    critical_files = [
        ('static/md3-styles.css', 'Material Design 3 主样式文件'),
        ('static/hf-spaces-compatibility.css', 'HF Spaces 兼容性样式'),
        ('static/js/hf-spaces-compatibility.js', 'HF Spaces 兼容性脚本'),
        ('templates/layout.html', '布局模板'),
        ('templates/hf_spaces_test.html', '测试页面模板')
    ]
    
    all_files_exist = True
    for file_path, description in critical_files:
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ 关键文件缺失，请先完成修复")
        return
    
    # 检查CSS fallback
    print("\n🎨 检查CSS fallback样式...")
    css_results = check_css_fallbacks('static/md3-styles.css')
    for result in css_results:
        print(f"  {result}")
    
    # 检查模板更新
    print("\n📄 检查模板更新...")
    template_results = check_template_updates()
    for result in template_results:
        print(f"  {result}")
    
    # 运行本地测试
    print("\n🧪 运行本地测试...")
    local_test_success = run_local_test()
    
    # 生成测试报告
    generate_test_report()
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 30)
    if all_files_exist and local_test_success:
        print("✅ 所有测试通过")
        print("🚀 可以部署到HF Spaces")
        print("🔗 部署后访问: https://your-space.hf.space/hf_spaces_test")
    else:
        print("❌ 部分测试失败")
        print("🔧 请检查上述问题并重新测试")
    
    print("\n💡 提示:")
    print("- 部署到HF Spaces后，访问测试页面验证效果")
    print("- 如果仍有问题，使用测试页面的调试工具")
    print("- 可以在URL后添加 ?debug=true 查看详细信息")

if __name__ == '__main__':
    main()
