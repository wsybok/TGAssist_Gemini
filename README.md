# TGAssist Bot

[English](#english) | [中文](#中文)

## English

TGAssist is a Telegram bot powered by Google Gemini AI that helps you manage group chats more efficiently.

### Features

- Message analysis and summarization
- Action item tracking
- Smart reply suggestions
- Historical message synchronization
- Chat log import/export
- Multi-language support (English/Chinese)

### Setup

1. Clone the repository
```bash
git clone https://github.com/wsybok/TGAssist_Gemini.git
cd TGAssist_Gemini
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment variables
```bash
cp .env.template .env
# Edit .env with your configuration
```

4. Run the bot
```bash
python main.py
```

### Docker Deployment

```bash
docker compose up -d
```

### Commands

- `/start` - Show welcome message
- `/analyze` - Analyze group history
- `/actions` - Check action items
- `/suggest` - Get reply suggestions
- `/sync` - Sync historical messages
- `/import` - Import chat logs
- `/delete` - Delete chat records
- `/setprompt` - Set prompt
- `/setcount` - Set suggestion count
- `/setmodel` - Set model
- `/lang` - Change language

## 中文

TGAssist 是一个基于 Google Gemini AI 的 Telegram 机器人，帮助您更高效地管理群聊。

### 功能特点

- 消息分析和总结
- 待办事项跟踪
- 智能回复建议
- 历史消息同步
- 聊天记录导入/导出
- 多语言支持（中文/英文）

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/wsybok/TGAssist_Gemini.git
cd TGAssist_Gemini
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.template .env
# 编辑 .env 文件，填入配置信息
```

4. 运行机器人
```bash
python main.py
```

### Docker 部署

```bash
docker compose up -d
```

### 命令列表

- `/start` - 显示欢迎信息
- `/analyze` - 分析群组历史消息
- `/actions` - 检查待办事项
- `/suggest` - 获取回复建议
- `/sync` - 同步历史消息
- `/import` - 导入聊天记录
- `/delete` - 删除聊天记录
- `/setprompt` - 设置提示词
- `/setcount` - 设置建议数量
- `/setmodel` - 设置模型
- `/lang` - 切换语言 
