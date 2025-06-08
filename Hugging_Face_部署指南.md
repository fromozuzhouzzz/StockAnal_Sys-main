# 智能分析系统 - Hugging Face Spaces 部署指南

## 📋 部署前准备

### 1. 注册 Hugging Face 账号
- 访问 [Hugging Face](https://huggingface.co/) 
- 点击右上角 "Sign Up" 注册账号
- 验证邮箱并完成注册

### 2. 准备 API 密钥
- **OpenAI API Key**（必需）：用于AI分析功能
  - 访问 [OpenAI Platform](https://platform.openai.com/)
  - 注册账号并获取 API Key
- **Tavily API Key**（可选）：用于新闻搜索
  - 访问 [Tavily](https://tavily.com/) 获取免费 API Key

## 🚀 部署步骤

### 方法一：通过 Git 部署（推荐）

#### 步骤 1：创建新的 Space
1. 登录 Hugging Face
2. 点击右上角头像 → "New Space"
3. 填写信息：
   - **Space name**: `stock-analysis-system`（或您喜欢的名称）
   - **License**: MIT
   - **SDK**: 选择 "Gradio"
   - **Hardware**: 选择 "CPU basic"（免费）
4. 点击 "Create Space"

#### 步骤 2：克隆仓库到本地
```bash
# 克隆您的 Hugging Face Space
git clone https://huggingface.co/spaces/您的用户名/stock-analysis-system
cd stock-analysis-system

# 添加项目文件
# 将本项目的所有文件复制到这个目录
```

#### 步骤 3：准备部署文件
将以下文件复制到 Space 目录：
- `app.py`（入口文件）
- `web_server.py`（主应用）
- `requirements.txt`（依赖列表）
- `README_HF.md` → 重命名为 `README.md`
- 所有 `.py` 分析模块文件
- `templates/` 目录
- `static/` 目录

#### 步骤 4：配置环境变量
1. 在 Hugging Face Space 页面，点击 "Settings"
2. 在 "Variables" 部分添加以下环境变量：
   ```
   OPENAI_API_KEY = 您的OpenAI API密钥
   OPENAI_API_URL = https://api.openai.com/v1
   OPENAI_API_MODEL = gpt-4o
   NEWS_MODEL = gpt-4o
   USE_DATABASE = False
   USE_REDIS_CACHE = False
   ```

#### 步骤 5：推送代码
```bash
git add .
git commit -m "Initial deployment to Hugging Face Spaces"
git push
```

### 方法二：通过 Web 界面部署

#### 步骤 1：创建 Space（同方法一）

#### 步骤 2：上传文件
1. 在 Space 页面点击 "Files" 标签
2. 点击 "Add file" → "Upload files"
3. 依次上传以下关键文件：
   - `app.py`
   - `requirements.txt`
   - `README_HF.md`（重命名为 README.md）
   - 所有 `.py` 模块文件

#### 步骤 3：创建目录结构
通过 "Add file" → "Create a new file" 创建：
- `templates/` 目录下的所有 HTML 文件
- `static/` 目录下的 CSS 和其他静态文件

#### 步骤 4：配置环境变量（同方法一步骤4）

## ⚙️ 配置说明

### 必需的环境变量
| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-...` |
| `OPENAI_API_URL` | OpenAI API 端点 | `https://api.openai.com/v1` |
| `OPENAI_API_MODEL` | 使用的模型 | `gpt-4o` |

### 可选的环境变量
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `NEWS_MODEL` | 新闻分析模型 | `gpt-4o` |
| `TAVILY_API_KEY` | Tavily 搜索 API | 无 |
| `USE_DATABASE` | 是否使用数据库 | `False` |
| `USE_REDIS_CACHE` | 是否使用 Redis | `False` |

## 🔧 部署后配置

### 1. 检查部署状态
- 部署完成后，Hugging Face 会自动构建应用
- 在 "Logs" 标签查看构建日志
- 等待状态变为 "Running"

### 2. 测试功能
1. 访问您的 Space URL：`https://huggingface.co/spaces/您的用户名/space名称`
2. 测试基本功能：
   - 访问主页
   - 输入股票代码进行分析
   - 检查各个功能模块

### 3. 性能优化
- **冷启动**：首次访问可能需要等待几分钟
- **超时设置**：Hugging Face Spaces 有执行时间限制
- **内存限制**：免费版本有内存限制，避免同时处理过多请求

## 🐛 常见问题解决

### 1. 构建失败
**问题**：依赖安装失败
**解决**：
- 检查 `requirements.txt` 格式
- 移除不兼容的依赖（如 `psycopg2-binary`）
- 使用更稳定的包版本

### 2. 应用无法启动
**问题**：`app.py` 找不到或错误
**解决**：
- 确保 `app.py` 在根目录
- 检查导入路径是否正确
- 查看错误日志定位问题

### 3. API 调用失败
**问题**：OpenAI API 密钥无效
**解决**：
- 检查环境变量设置
- 确认 API 密钥有效且有余额
- 检查 API 端点 URL

### 4. 功能异常
**问题**：某些功能不工作
**解决**：
- 检查是否所有必需文件都已上传
- 确认模板文件路径正确
- 查看应用日志排查错误

## 📈 使用建议

### 1. 成本控制
- 使用免费的 CPU 硬件
- 合理设置 API 调用频率
- 监控 OpenAI API 使用量

### 2. 用户体验
- 添加加载提示
- 设置合理的超时时间
- 提供错误处理信息

### 3. 安全考虑
- 不要在代码中硬编码 API 密钥
- 使用环境变量管理敏感信息
- 定期更新依赖包

## 🔄 更新部署

### 通过 Git 更新
```bash
# 拉取最新代码
git pull

# 修改文件后提交
git add .
git commit -m "Update application"
git push
```

### 通过 Web 界面更新
1. 在 Space 页面直接编辑文件
2. 或上传新版本文件覆盖

## 📞 获取帮助

如果遇到问题：
1. 查看 Hugging Face Spaces [官方文档](https://huggingface.co/docs/hub/spaces)
2. 检查应用日志获取错误信息
3. 在项目 GitHub 仓库提交 Issue

---

**祝您部署成功！** 🎉
