# Telegram Bot Token (从 @BotFather 获取)
TELEGRAM_TOKEN = "your_telegram_token_here"

# Google Gemini API Key (从 Google AI Studio 获取)
GEMINI_API_KEY = "your_gemini_api_key_here"

# Webhook 设置
WEBHOOK_HOST = "your_domain.com"  # 你的域名
WEBHOOK_PORT = 8443  # 端口号 (推荐使用 443, 80, 88 或 8443)
WEBHOOK_LISTEN = '0.0.0.0'  # 监听所有接口

# SSL 证书设置
WEBHOOK_SSL_CERT = "path/to/cert.pem"  # SSL 证书路径
WEBHOOK_SSL_PRIV = "path/to/private.key"  # SSL 私钥路径

# Webhook URL 路径
WEBHOOK_URL_PATH = f"/webhook/{TELEGRAM_TOKEN}"

# 完整的 Webhook URL
WEBHOOK_URL = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_URL_PATH}" 