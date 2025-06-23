#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 部署脚本 - 部署到 Hugging Face Spaces
"""

import os
import sys
from huggingface_hub import HfApi, upload_folder

def main():
    """主部署函数"""
    try:
        # 验证环境变量
        required_vars = ['HF_TOKEN', 'HF_SPACE']
        for var in required_vars:
            if not os.environ.get(var):
                print(f"❌ 错误: {var} 环境变量未设置")
                sys.exit(1)
        
        # 初始化 HF API
        api = HfApi(token=os.environ["HF_TOKEN"])

        # 获取 Space 信息
        space_id = os.environ["HF_SPACE"]
        print(f"🔍 检查 Space: {space_id}")

        # 检查 Space 是否存在
        try:
            space_info = api.space_info(space_id)
            print(f"✅ Space 存在: {space_info.id}")
        except Exception as e:
            print(f"❌ Space 不存在或无法访问: {e}")
            sys.exit(1)

        # 上传文件到 Space
        print("📤 开始上传文件...")

        # 定义要忽略的文件和目录
        ignore_patterns = [
            ".git*",
            "__pycache__",
            "*.pyc",
            ".env.example",
            ".env-example",
            "logs/",
            "data/news/",
            ".pytest_cache",
            "tests/",
            "docs/",
            "images/",
            "*.log",
            "fly.toml",
            "render.yaml",
            "railway.json",
            "vercel.json",
            "Dockerfile",
            "docker-compose.yml",
            "start.sh",
            "部署检查清单.md",
            "hf_deployment_check.py",
            "deploy_to_hf.py",
            "test_*.py",
            "GITHUB_ACTIONS_FIX.md"
        ]

        # 获取提交哈希
        github_sha = os.environ.get('GITHUB_SHA', 'unknown')
        commit_short = github_sha[:7] if github_sha != 'unknown' else 'unknown'
        commit_message = f"Auto-deploy from GitHub Actions - {commit_short}"
        
        print(f"📝 提交信息: {commit_message}")
        print(f"🔍 GITHUB_SHA: {github_sha}")

        # 上传整个项目到 Space
        upload_folder(
            folder_path=".",
            repo_id=space_id,
            repo_type="space",
            token=os.environ["HF_TOKEN"],
            ignore_patterns=ignore_patterns,
            commit_message=commit_message
        )

        print("✅ 部署完成!")
        print(f"🌐 访问地址: https://huggingface.co/spaces/{space_id}")

    except Exception as e:
        print(f"❌ 部署失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
