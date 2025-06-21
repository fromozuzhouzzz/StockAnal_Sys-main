# Hugging Face Spaces 部署说明

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
