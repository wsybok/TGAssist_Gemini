# Telegram 群组助手机器人

这是一个基于 Python 的 Telegram 机器人，用于管理和分析群组聊天记录。它使用 Google Gemini AI 来提供智能分析和建议。

## 功能特点

- 自动记录群组消息
- 分析群组历史记录
- 检查今日待办事项
- 提供回复建议
- 支持导入导出聊天记录
- 自定义 AI 提示词
- 多种 AI 模型选择

## 安装步骤

### 方法一：直接安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/TGAssist_Gemini.git
cd TGAssist_Gemini
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置：
   - 复制 `config.template.py` 为 `config.py`
   - 在 `config.py` 中填入你的配置信息

5. SSL 证书：
   - 获取 SSL 证书（可以使用 Let's Encrypt）
   - 将证书文件路径添加到配置文件中

6. 启动机器人：
```bash
python main.py
```

### 方法二：Docker 部署

1. 准备工作：
   ```bash
   # 创建必要的目录
   mkdir -p data certs
   
   # 复制配置文件
   cp config.template.py config.py
   
   # 编辑配置文件
   nano config.py
   ```

2. 配置 SSL 证书：
   - 将 SSL 证书和私钥文件放在 `certs` 目录下
   - 在 `config.py` 中更新证书路径：
     ```python
     WEBHOOK_SSL_CERT = "/app/certs/cert.pem"
     WEBHOOK_SSL_PRIV = "/app/certs/private.key"
     ```

3. 使用 Docker Compose 启动：
   ```bash
   # 构建并启动容器
   docker-compose up -d
   
   # 查看日志
   docker-compose logs -f
   ```

4. 停止服务：
   ```bash
   docker-compose down
   ```

## 配置说明

### 必需配置
- `TELEGRAM_TOKEN`: 从 @BotFather 获取的机器人 token
- `GEMINI_API_KEY`: 从 Google AI Studio 获取的 API key

### Webhook 配置
- `WEBHOOK_HOST`: 你的域名
- `WEBHOOK_PORT`: 端口号（推荐 443, 80, 88 或 8443）
- `WEBHOOK_SSL_CERT`: SSL 证书路径
- `WEBHOOK_SSL_PRIV`: SSL 私钥路径

## 使用说明

机器人支持以下命令：
- `/start` - 显示帮助信息
- `/analyze` - 分析群组历史
- `/actions` - 检查今日待办
- `/suggest` - 建议回复
- `/setcount` - 设置建议回复时使用的消息数量
- `/sync` - 同步群组历史消息
- `/import` - 导入 Telegram 导出的 JSON 聊天记录
- `/delete` - 删除群组记录
- `/setprompt` - 设置 AI 提示词
- `/setmodel` - 切换 AI 模型

## 生产环境部署

### 方法一：使用 systemd（Linux）

1. 创建服务文件：
```bash
sudo nano /etc/systemd/system/tgassist.service
```

添加以下内容：
```ini
[Unit]
Description=Telegram Assistant Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/tgassist
Environment=PYTHONPATH=/path/to/tgassist
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. 启动服务：
```bash
sudo systemctl start tgassist
sudo systemctl enable tgassist
```

### 方法二：使用 Docker（推荐）

1. 确保安装了 Docker 和 Docker Compose：
```bash
# 安装 Docker（如果未安装）
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose（如果未安装）
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. 启动服务：
```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

3. 自动更新（可选）：
   - 使用 Watchtower 自动更新 Docker 容器：
   ```bash
   docker run -d \
     --name watchtower \
     --restart always \
     -v /var/run/docker.sock:/var/run/docker.sock \
     containrrr/watchtower \
     --cleanup --interval 86400
   ```

## 数据备份

### Docker 环境

1. 备份数据：
```bash
# 停止服务
docker-compose down

# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 重启服务
docker-compose up -d
```

2. 恢复数据：
```bash
# 停止服务
docker-compose down

# 恢复数据
tar -xzf backup-20240101.tar.gz

# 重启服务
docker-compose up -d
```

## 注意事项

- 确保服务器有足够的存储空间用于数据库
- 定期备份数据库文件
- 保护好配置文件中的敏感信息
- 确保 SSL 证书始终有效
- 使用 Docker 部署时，建议将数据目录挂载到主机上
- 定期检查日志确保服务正常运行

## 许可证

MIT License 
