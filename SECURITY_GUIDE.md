# 安全配置指南

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
