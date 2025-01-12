from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# Telegram Bot 配置
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))

# Webhook 配置
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "localhost")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))
WEBHOOK_LISTEN = os.getenv("WEBHOOK_LISTEN", "0.0.0.0")
WEBHOOK_URL_PATH = f"/webhook/{TELEGRAM_TOKEN}"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}/webhook/{TELEGRAM_TOKEN}"

# 语言配置
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "zh")

# 配置验证
def validate_config():
    """验证必要的配置是否存在"""
    required_vars = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "BOT_OWNER_ID": BOT_OWNER_ID
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        
    if BOT_OWNER_ID == 0:
        raise ValueError("BOT_OWNER_ID 无效") 