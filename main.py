from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from settings import (
    TELEGRAM_TOKEN, GEMINI_API_KEY, BOT_OWNER_ID,
    USE_WEBHOOK, WEBHOOK_HOST, WEBHOOK_PORT,
    WEBHOOK_LISTEN, WEBHOOK_URL_PATH, WEBHOOK_URL,
    DEFAULT_LANGUAGE
)
from utils.gemini_handler import GeminiHandler
from utils.db_handler import DatabaseHandler
from i18n.messages import MESSAGES
import asyncio
import json
import os

class TelegramBot:
    def __init__(self):
        self.gemini = GeminiHandler(GEMINI_API_KEY)
        self.db = DatabaseHandler()
        self.owner_id = BOT_OWNER_ID
        
    def get_message(self, key: str, user_id: int) -> str:
        """获取指定语言的消息"""
        lang = self.db.get_user_language(user_id)
        return MESSAGES[lang][key]
        
    async def lang(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理语言切换命令"""
        if not await self.check_owner(update):
            return
            
        if update.message.chat.type != 'private':
            await update.message.reply_text("请在私聊中使用此命令。")
            return
            
        keyboard = [
            [
                InlineKeyboardButton("中文 🇨🇳", callback_data="lang_zh"),
                InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            self.get_message('lang_select', update.effective_user.id),
            reply_markup=reply_markup
        )
        
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理回调查询"""
        if not await self.check_owner(update):
            return
            
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('lang_'):
            lang = query.data.split('_')[1]
            self.db.set_user_language(update.effective_user.id, lang)
            await query.edit_message_text(
                self.get_message('lang_changed', update.effective_user.id)
            )
        # ... 处理其他回调数据 ...

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """处理 /start 命令"""
        if not await self.check_owner(update):
            return
        await update.message.reply_text(
            self.get_message('start', update.effective_user.id)
        )

    async def check_owner(self, update: Update) -> bool:
        """检查是否是机器人所有者"""
        user_id = update.effective_user.id
        if user_id != self.owner_id:
            await update.message.reply_text("抱歉，您没有权限使用此机器人。")
            return False
        return True

    async def check_group_permission(self, update: Update) -> bool:
        """检查群组权限"""
        # 如果是私聊，只检查所有者权限
        if update.message.chat.type == 'private':
            return await self.check_owner(update)
        
        # 如果是群组消息
        chat_member = await update.message.chat.get_member(update.message.from_user.id)
        is_admin = chat_member.status in ['creator', 'administrator']
        
        # 只允许群主或管理员使用命令
        if not is_admin:
            await update.message.reply_text("抱歉，只有群组管理员才能使用此命令。")
            return False
        return True

    async def store_message(self, update: Update):
        """自动存储消息到数据库"""
        try:
            if update.message and update.message.text:
                print("\n=== 自动存储新消息 ===")
                
                # 获取发送者信息
                username = None
                if update.message.from_user:
                    username = update.message.from_user.username or update.message.from_user.first_name
                    print(f"发送者: {username}")
                
                # 获取消息信息
                chat_id = update.message.chat_id
                chat_type = update.message.chat.type
                chat_title = update.message.chat.title if chat_type in ['group', 'supergroup'] else 'Private Chat'
                print(f"群组: {chat_title} (ID: {chat_id})")
                print(f"消息: {update.message.text[:50]}...")
                
                # 如果是群组消息，更新群组信息
                if chat_type in ['group', 'supergroup']:
                    self.db.update_chat_info(chat_id, chat_title)
                
                # 存储消息
                self.db.store_message(
                    chat_id=chat_id,
                    user_id=update.message.from_user.id if update.message.from_user else 0,
                    username=username or "unknown",
                    message_text=update.message.text,
                    timestamp=update.message.date.isoformat()
                )
                print(f"消息已成功存储到数据库")
                
                # 检查是否需要进行群组分析
                if chat_type in ['group', 'supergroup'] and self.db.check_and_analyze_group(chat_id):
                    messages = self.db.get_chat_history(chat_id)
                    if messages:
                        formatted_messages = self._format_messages(messages)
                        system_prompt = self.db.get_system_prompt("background")
                        analysis = await self.gemini.analyze_group_history(formatted_messages, system_prompt)
                        self.db.store_analysis(chat_id, "background", analysis)
                        print(f"已完成群组自动分析")
                
        except Exception as e:
            print(f"存储消息时出错：{str(e)}")

    def _create_group_selection_keyboard(self, groups, action_prefix):
        """创建群组选择按钮"""
        keyboard = []
        for group_id, group_name in groups:
            callback_data = json.dumps({"action": action_prefix, "group_id": group_id})
            keyboard.append([InlineKeyboardButton(group_name, callback_data=callback_data)])
        return InlineKeyboardMarkup(keyboard)

    async def analyze_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /analyze 命令"""
        if not await self.check_owner(update):
            return
            
        if update.message.chat.type != 'private':
            await update.message.reply_text("请在私聊中使用此命令。")
            return

        # 获取用户加入的所有群组
        groups = self.db.get_all_groups()
        if not groups:
            await update.message.reply_text("未找到任何群组记录。")
            return

        reply_markup = self._create_group_selection_keyboard(groups, "analyze")
        await update.message.reply_text("请选择要分析的群组：", reply_markup=reply_markup)

    async def check_action_items(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /actions 命令"""
        if not await self.check_owner(update):
            return
            
        if update.message.chat.type != 'private':
            await update.message.reply_text("请在私聊中使用此命令。")
            return

        keyboard = [
            [InlineKeyboardButton("今日所有群组", callback_data=json.dumps({"action": "actions_today"}))],
            [InlineKeyboardButton("选择特定群组", callback_data=json.dumps({"action": "actions_select"}))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("请选择待办事项查看方式：", reply_markup=reply_markup)

    async def suggest_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /suggest 命令"""
        if not await self.check_owner(update):
            return
            
        if update.message.chat.type != 'private':
            await update.message.reply_text("请在私聊中使用此命令。")
            return

        groups = self.db.get_all_groups()
        if not groups:
            await update.message.reply_text("未找到任何群组记录。")
            return

        reply_markup = self._create_group_selection_keyboard(groups, "suggest")
        await update.message.reply_text("请选择要获取回复建议的群组：", reply_markup=reply_markup)

    def _format_messages(self, messages):
        """格式化消息记录"""
        formatted = []
        for username, text, timestamp in messages:
            formatted.append(f"[{timestamp}] {username}: {text}")
        return "\n".join(formatted)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理所有新消息"""
        try:
            if update.message and update.message.text:
                # 检查是否在等待新的prompt
                if "waiting_for_prompt" in context.user_data:
                    if not await self.check_owner(update):
                        return
                    prompt_type = context.user_data["waiting_for_prompt"]
                    if update.message.text == "/cancel":
                        await update.message.reply_text("已取消设置提示词。")
                    else:
                        self.db.update_system_prompt(prompt_type, update.message.text)
                        await update.message.reply_text("提示词已更新。")
                    del context.user_data["waiting_for_prompt"]
                    return

                # 检查新成员是否是机器人自己
                if update.message.new_chat_members:
                    for member in update.message.new_chat_members:
                        if member.id == context.bot.id:
                            # 检查是否是所有者添加的机器人
                            if update.message.from_user.id != self.owner_id:
                                await update.message.chat.leave()
                                return
                            await update.message.reply_text(
                                "你好！我是群组助手。我会自动记录群组消息，你可以在私聊中使用以下命令：\n"
                                "/analyze - 分析群组历史\n"
                                "/actions - 检查今日待办\n"
                                "/suggest - 建议回复\n"
                                "/delete - 删除群组记录\n"
                                "/setprompt - 设置AI提示词"
                            )
                            break

                # 自动存储所有消息（只存储所有者的群组消息）
                chat_member = await update.message.chat.get_member(self.owner_id)
                if chat_member.status in ['creator', 'administrator', 'member']:
                    await self.store_message(update)
                
        except Exception as e:
            print(f"处理消息时出错：{str(e)}")

    async def sync_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """同步群组历史消息"""
        if not await self.check_owner(update):
            return
            
        try:
            if update.message.chat.type != 'private':
                await update.message.reply_text("请在私聊中使用此命令。")
                return

            status_message = await update.message.reply_text("正在同步消息...")
            total_messages = 0
            
            # 从当前消息获取群组信息
            current_chat = update.message.chat
            if current_chat.type in ['group', 'supergroup']:
                chat_id = current_chat.id
                chat_title = current_chat.title
                
                print(f"\n开始同步群组：{chat_title} (ID: {chat_id})")
                
                # 更新群组信息
                self.db.update_chat_info(chat_id, chat_title)
                
                try:
                    # 获取历史消息
                    messages_to_store = []
                    offset = 0
                    limit = 100
                    
                    while True:
                        updates = await context.bot.get_updates(offset=offset, limit=limit)
                        if not updates:
                            break
                            
                        for update in updates:
                            if not update.message or update.message.chat.id != chat_id:
                                continue
                                
                            message = update.message
                            if not message.text:
                                continue
                                
                            username = None
                            if message.from_user:
                                username = message.from_user.username or message.from_user.first_name
                                
                            messages_to_store.append({
                                'chat_id': chat_id,
                                'user_id': message.from_user.id if message.from_user else 0,
                                'username': username or "unknown",
                                'message_text': message.text,
                                'timestamp': message.date.isoformat()
                            })
                            
                            if len(messages_to_store) >= 100:  # 批量存储
                                self.db.store_messages_batch(messages_to_store)
                                total_messages += len(messages_to_store)
                                messages_to_store = []
                                await status_message.edit_text(f"已同步 {total_messages} 条消息...")
                        
                        # 更新offset
                        offset = updates[-1].update_id + 1
                        
                        # 如果消息少于limit，说明已经到达末尾
                        if len(updates) < limit:
                            break
                    
                    # 存储剩余消息
                    if messages_to_store:
                        self.db.store_messages_batch(messages_to_store)
                        total_messages += len(messages_to_store)
                        await status_message.edit_text(f"已同步 {total_messages} 条消息...")
                        
                except Exception as e:
                    print(f"同步群组 {chat_title} 的消息时出错：{str(e)}")
            
            if total_messages > 0:
                await status_message.edit_text(f"同步完成！共同步了 {total_messages} 条消息。")
            else:
                await status_message.edit_text("未找到需要同步的消息。请确保我在群组中并且有足够的权限。")
            
        except Exception as e:
            print(f"同步消息时出错：{str(e)}")
            await update.message.reply_text(f"同步消息时出错：{str(e)}")

    async def import_json(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """从JSON文件导入聊天记录"""
        if not await self.check_owner(update):
            return
            
        try:
            if update.message.chat.type != 'private':
                await update.message.reply_text("请在私聊中使用此命令。")
                return
                
            # 检查是否有文件
            if not update.message.document:
                await update.message.reply_text(
                    "请发送Telegram导出的JSON格式聊天记录文件。\n"
                    "导出方法：\n"
                    "1. 在Telegram Desktop中打开群组\n"
                    "2. 点击右上角三点菜单\n"
                    "3. 选择'Export chat history'\n"
                    "4. 选择JSON格式\n"
                    "5. 下载并发送给我"
                )
                return
                
            # 检查文件类型
            if not update.message.document.file_name.endswith('.json'):
                await update.message.reply_text("请发送JSON格式的文件。")
                return
                
            status_message = await update.message.reply_text("正在处理聊天记录...")
            
            # 下载文件
            file = await context.bot.get_file(update.message.document.file_id)
            json_str = await file.download_as_bytearray()
            
            # 解析JSON
            try:
                chat_data = json.loads(json_str.decode('utf-8'))
            except json.JSONDecodeError:
                await status_message.edit_text("无法解析JSON文件，请确保文件格式正确。")
                return
                
            # 验证JSON结构
            if 'messages' not in chat_data:
                await status_message.edit_text("JSON文件格式不正确，找不到消息记录。")
                return
                
            # 获取群组信息
            chat_id = chat_data.get('id', 0)
            chat_name = chat_data.get('name', 'Unknown Group')
            
            # 检查群组是否存在
            exists, existing_count = self.db.check_chat_exists(chat_id)
            if exists:
                await status_message.edit_text(
                    f"检测到群组 {chat_name} (ID: {chat_id}) 已存在，"
                    f"当前有 {existing_count} 条消息。\n"
                    f"正在导入新消息..."
                )
            else:
                await status_message.edit_text(
                    f"正在导入群组 {chat_name} (ID: {chat_id}) 的消息..."
                )
            
            # 更新群组信息
            self.db.update_chat_info(chat_id, chat_name)
            
            # 处理消息
            messages_to_store = []
            total_messages = 0
            new_messages = 0
            
            for msg in chat_data['messages']:
                if msg.get('type') != 'message' or 'text' not in msg:
                    continue
                    
                # 处理文本内容
                text = msg['text']
                if isinstance(text, list):  # 处理富文本消息
                    text_parts = []
                    for part in text:
                        if isinstance(part, str):
                            text_parts.append(part)
                        elif isinstance(part, dict):
                            text_parts.append(part.get('text', ''))
                    text = ' '.join(text_parts)
                
                messages_to_store.append({
                    'chat_id': chat_id,
                    'user_id': msg.get('from_id', '').replace('user', '') if msg.get('from_id') else 0,
                    'username': msg.get('from', 'unknown'),
                    'message_text': text,
                    'timestamp': msg.get('date', '')
                })
                total_messages += 1
                
                if len(messages_to_store) >= 100:  # 批量存储
                    new_count = self.db.store_messages_batch(messages_to_store)
                    new_messages += new_count
                    messages_to_store = []
                    await status_message.edit_text(
                        f"正在导入消息...\n"
                        f"总消息数：{total_messages}\n"
                        f"新消息数：{new_messages}"
                    )
            
            # 存储剩余消息
            if messages_to_store:
                new_count = self.db.store_messages_batch(messages_to_store)
                new_messages += new_count
            
            await status_message.edit_text(
                f"导入完成！\n"
                f"群组：{chat_name}\n"
                f"总消息数：{total_messages}\n"
                f"新消息数：{new_messages}"
            )
            
        except Exception as e:
            print(f"导入JSON文件时出错：{str(e)}")
            await update.message.reply_text(f"导入JSON文件时出错：{str(e)}")

    async def delete_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /delete 命令"""
        if not await self.check_owner(update):
            return
            
        if update.message.chat.type != 'private':
            await update.message.reply_text("请在私聊中使用此命令。")
            return

        groups = self.db.get_all_groups()
        if not groups:
            await update.message.reply_text("未找到任何群组记录。")
            return

        reply_markup = self._create_group_selection_keyboard(groups, "delete")
        await update.message.reply_text("请选择要删除记录的群组：", reply_markup=reply_markup)

    async def set_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /setprompt 命令"""
        if not await self.check_owner(update):
            return
            
        if update.message.chat.type != 'private':
            await update.message.reply_text("请在私聊中使用此命令。")
            return

        keyboard = [
            [InlineKeyboardButton("分析群组历史", callback_data=json.dumps({"action": "setprompt", "type": "background"}))],
            [InlineKeyboardButton("检查今日待办", callback_data=json.dumps({"action": "setprompt", "type": "actions"}))],
            [InlineKeyboardButton("建议回复", callback_data=json.dumps({"action": "setprompt", "type": "suggestion"}))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("请选择要设置提示词的功能：", reply_markup=reply_markup)

    async def set_suggest_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置建议回复时使用的消息数量"""
        if not await self.check_owner(update):
            return
            
        if update.message.chat.type != 'private':
            await update.message.reply_text("请在私聊中使用此命令。")
            return
            
        try:
            count = int(context.args[0])
            if count < 2:
                await update.message.reply_text("消息数量必须大于等于2。")
                return
            if count > 50:
                await update.message.reply_text("消息数量不能超过50。")
                return
                
            context.user_data["suggest_message_count"] = count
            await update.message.reply_text(f"已设置建议回复时使用最近 {count} 条消息。")
            
        except (IndexError, ValueError):
            await update.message.reply_text(
                "请指定要使用的消息数量，例如：\n"
                "/setcount 10\n"
                "默认值为5，最小值为2，最大值为50。"
            )

    async def set_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /setmodel 命令"""
        if not await self.check_owner(update):
            return
            
        if update.message.chat.type != 'private':
            await update.message.reply_text("请在私聊中使用此命令。")
            return

        keyboard = []
        for model_name in self.gemini.AVAILABLE_MODELS:
            callback_data = json.dumps({"action": "setmodel", "model": model_name})
            text = f"{model_name} {'✓' if model_name == self.gemini.model_name else ''}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"当前使用的模型：{self.gemini.model_name}\n"
            "请选择要使用的模型：",
            reply_markup=reply_markup
        )

def main():
    # 打印环境变量信息用于调试
    print("\n=== 环境变量信息 ===")
    print(f"TELEGRAM_TOKEN: {'已设置' if TELEGRAM_TOKEN else '未设置'}")
    print(f"GEMINI_API_KEY: {'已设置' if GEMINI_API_KEY else '未设置'}")
    print(f"BOT_OWNER_ID: {BOT_OWNER_ID}")
    print(f"USE_WEBHOOK: {USE_WEBHOOK}")
    if USE_WEBHOOK:
        print(f"WEBHOOK_HOST: {WEBHOOK_HOST}")
        print(f"WEBHOOK_PORT: {WEBHOOK_PORT}")
        print(f"WEBHOOK_LISTEN: {WEBHOOK_LISTEN}")
        print(f"WEBHOOK_URL: {WEBHOOK_URL}")
    print("===================\n")

    bot = TelegramBot()
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .connection_pool_size(16)
        .connect_timeout(60.0)
        .read_timeout(60.0)
        .write_timeout(60.0)
        .pool_timeout(60.0)
        .build()
    )

    # 添加错误处理器
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        print(f"发生错误：{context.error}")

    application.add_error_handler(error_handler)

    # 添加命令处理器
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.start))  # 添加 help 命令
    application.add_handler(CommandHandler("lang", bot.lang))  # 确保 lang 命令被正确注册
    application.add_handler(CommandHandler("analyze", bot.analyze_history))
    application.add_handler(CommandHandler("actions", bot.check_action_items))
    application.add_handler(CommandHandler("suggest", bot.suggest_reply))
    application.add_handler(CommandHandler("sync", bot.sync_messages))
    application.add_handler(CommandHandler("import", bot.import_json))
    application.add_handler(CommandHandler("delete", bot.delete_chat))
    application.add_handler(CommandHandler("setprompt", bot.set_prompt))
    application.add_handler(CommandHandler("setcount", bot.set_suggest_count))
    application.add_handler(CommandHandler("setmodel", bot.set_model))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    # 添加消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, bot.import_json))

    # 根据配置决定使用 webhook 还是 polling
    if USE_WEBHOOK:
        print(f"正在以 Webhook 模式启动机器人...")
        print(f"Webhook URL: {WEBHOOK_URL}")
        print(f"监听地址: {WEBHOOK_LISTEN}:{WEBHOOK_PORT}{WEBHOOK_URL_PATH}")
        
        application.run_webhook(
            listen=WEBHOOK_LISTEN,
            port=WEBHOOK_PORT,
            url_path=WEBHOOK_URL_PATH,
            webhook_url=WEBHOOK_URL,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
            max_connections=100
        )
    else:
        print("正在以 Polling 模式启动机器人...")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )

if __name__ == '__main__':
    main() 