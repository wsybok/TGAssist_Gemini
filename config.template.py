# Telegram Bot Token (从 @BotFather 获取)
TELEGRAM_TOKEN = "your_telegram_token_here"

# Google Gemini API Key (从 Google AI Studio 获取)
GEMINI_API_KEY = "your_gemini_api_key_here"

# Bot Owner ID (在 Telegram 中与 @userinfobot 对话获取)
BOT_OWNER_ID = 123456789  # 替换为你的 Telegram 用户 ID

# Webhook 设置
WEBHOOK_HOST = "tg.ai2fun.fun"  # 域名
WEBHOOK_PORT = 8443  # 内部端口
WEBHOOK_LISTEN = '0.0.0.0'  # 监听所有接口

# Webhook URL 路径
WEBHOOK_URL_PATH = f"/webhook/{TELEGRAM_TOKEN}"

# 完整的 Webhook URL
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/webhook/{TELEGRAM_TOKEN}" 