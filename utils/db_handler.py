import sqlite3
import json
from datetime import datetime
import os

class DatabaseHandler:
    def __init__(self, db_name="data/telegram_bot.db"):
        print(f"初始化数据库：{db_name}")
        self.db_name = db_name
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_name), exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    message_text TEXT,
                    timestamp DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    chat_title TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    analysis_type TEXT,
                    content TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_type TEXT UNIQUE,
                    prompt_text TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    language TEXT DEFAULT 'zh',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 初始化默认的system prompts
            cursor.execute('''
                INSERT OR IGNORE INTO system_prompts (prompt_type, prompt_text) VALUES
                ('background', '分析以下群组聊天记录，提供群组的背景信息：'),
                ('actions', '分析以下今日群组聊天记录，找出需要我执行的待办事项：'),
                ('suggestion', '根据以下最新消息，建议一个合适的回复：')
            ''')
            conn.commit()
            print("数据库初始化完成")

    def store_message(self, chat_id, user_id, username, message_text, timestamp):
        print(f"\n=== 存储新消息 ===")
        print(f"群组ID: {chat_id}")
        print(f"用户ID: {user_id}")
        print(f"用户名: {username}")
        print(f"消息内容: {message_text[:50]}...")
        print(f"时间戳: {timestamp}")
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (chat_id, user_id, username, message_text, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, user_id, username, message_text, timestamp))
            conn.commit()
            print(f"消息已存储，ID: {cursor.lastrowid}")

    def get_chat_history(self, chat_id):
        """获取群组历史消息"""
        print(f"\n=== 获取群组历史消息 ===")
        print(f"群组ID: {chat_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, message_text, timestamp
                FROM messages
                WHERE ABS(chat_id) = ABS(?)  -- 使用绝对值匹配
                ORDER BY timestamp ASC  -- 按时间正序排列
                LIMIT 100
            ''', (chat_id,))
            messages = cursor.fetchall()
            print(f"获取到 {len(messages)} 条消息")
            return messages

    def get_today_messages(self, chat_id):
        print(f"\n=== 获取今日消息 ===")
        print(f"群组ID: {chat_id}")
        today = datetime.now().date().isoformat()
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, message_text, timestamp
                FROM messages
                WHERE ABS(chat_id) = ABS(?) AND date(timestamp) = ?
                ORDER BY timestamp DESC
            ''', (chat_id, today))
            messages = cursor.fetchall()
            print(f"获取到 {len(messages)} 条今日消息")
            return messages

    def get_last_message(self, chat_id):
        print(f"\n=== 获取最后一条消息 ===")
        print(f"群组ID: {chat_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, message_text, timestamp
                FROM messages
                WHERE ABS(chat_id) = ABS(?)
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (chat_id,))
            message = cursor.fetchone()
            if message:
                print(f"找到最后一条消息：[{message[2]}] {message[0]}: {message[1][:50]}...")
            else:
                print("未找到任何消息")
            return message

    def get_unique_chats(self):
        print(f"\n=== 获取唯一群组列表 ===")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT chat_id
                FROM messages
                WHERE chat_id < 0  -- Telegram群组ID都是负数
                ORDER BY chat_id
            ''')
            chats = [row[0] for row in cursor.fetchall()]
            print(f"找到 {len(chats)} 个唯一群组")
            return chats

    def store_messages_batch(self, messages):
        """批量存储消息，支持去重"""
        print(f"\n=== 批量存储消息 ===")
        print(f"消息数量: {len(messages)}")
        
        if not messages:
            return 0
            
        # 获取群组ID和最新消息时间
        chat_id = messages[0]['chat_id']
        latest_time = self.get_latest_message_time(chat_id)
        
        # 如果数据库中没有该群组的消息，直接存储所有消息
        if not latest_time:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT INTO messages (chat_id, user_id, username, message_text, timestamp)
                    VALUES (:chat_id, :user_id, :username, :message_text, :timestamp)
                ''', messages)
                conn.commit()
                stored_count = cursor.rowcount
                print(f"新增 {stored_count} 条消息")
                return stored_count
        
        # 如果数据库中已有消息，只存储新消息
        new_messages = []
        for msg in messages:
            if msg['timestamp'] > latest_time:
                new_messages.append(msg)
        
        if new_messages:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT INTO messages (chat_id, user_id, username, message_text, timestamp)
                    VALUES (:chat_id, :user_id, :username, :message_text, :timestamp)
                ''', new_messages)
                conn.commit()
                stored_count = cursor.rowcount
                print(f"新增 {stored_count} 条消息")
                return stored_count
        else:
            print("没有新消息需要存储")
            return 0

    def get_all_groups(self):
        """获取所有群组信息"""
        print(f"\n=== 获取所有群组 ===")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                WITH group_ids AS (
                    SELECT DISTINCT ABS(chat_id) as abs_id,
                           FIRST_VALUE(chat_id) OVER (PARTITION BY ABS(chat_id) ORDER BY chat_id DESC) as chat_id
                    FROM messages
                )
                SELECT DISTINCT g.chat_id,
                       COALESCE(
                           (SELECT chat_title 
                            FROM chat_info 
                            WHERE chat_id = g.chat_id OR chat_id = -g.chat_id
                            ORDER BY last_updated DESC 
                            LIMIT 1),
                           'Unknown Group'
                       ) as chat_title
                FROM group_ids g
                ORDER BY ABS(g.chat_id)
            ''')
            groups = cursor.fetchall()
            print(f"找到 {len(groups)} 个群组")
            return groups

    def get_group_info(self, chat_id):
        """获取特定群组的信息"""
        print(f"\n=== 获取群组信息 ===")
        print(f"群组ID: {chat_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                WITH group_messages AS (
                    SELECT DISTINCT chat_id
                    FROM messages
                    WHERE ABS(chat_id) = ABS(?)
                    LIMIT 1
                )
                SELECT m.chat_id,
                       COALESCE(
                           (SELECT chat_title 
                            FROM chat_info 
                            WHERE chat_id = m.chat_id OR chat_id = -m.chat_id
                            ORDER BY last_updated DESC 
                            LIMIT 1),
                           'Unknown Group'
                       ) as chat_title
                FROM group_messages m
            ''', (chat_id,))
            group = cursor.fetchone()
            if group:
                print(f"找到群组：{group[1]}")
            else:
                print("未找到群组信息")
            return group

    def update_chat_info(self, chat_id, chat_title):
        """更新群组信息"""
        print(f"\n=== 更新群组信息 ===")
        print(f"群组ID: {chat_id}")
        print(f"群组名称: {chat_title}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # 确保chat_info表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    chat_title TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 插入新的群组信息
            cursor.execute('''
                INSERT INTO chat_info (chat_id, chat_title)
                VALUES (?, ?)
            ''', (chat_id, chat_title))
            conn.commit()
            print("群组信息已更新") 

    def check_chat_exists(self, chat_id):
        """检查群组是否存在"""
        print(f"\n=== 检查群组是否存在 ===")
        print(f"群组ID: {chat_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) 
                FROM messages 
                WHERE chat_id = ? OR chat_id = ?  -- 同时匹配正负群组ID
            ''', (chat_id, -abs(chat_id)))  # 同时查询正负ID
            count = cursor.fetchone()[0]
            exists = count > 0
            print(f"群组存在: {exists}, 现有消息数: {count}")
            return exists, count

    def store_analysis(self, chat_id, analysis_type, content):
        """存储分析结果"""
        print(f"\n=== 存储分析结果 ===")
        print(f"群组ID: {chat_id}")
        print(f"分析类型: {analysis_type}")
        print(f"分析内容: {content[:100]}...")
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analysis (chat_id, analysis_type, content)
                VALUES (?, ?, ?)
            ''', (chat_id, analysis_type, content))
            conn.commit()
            print(f"分析结果已存储，ID: {cursor.lastrowid}")
            return cursor.lastrowid

    def get_latest_analysis(self, chat_id, analysis_type):
        """获取最新的分析结果"""
        print(f"\n=== 获取最新分析结果 ===")
        print(f"群组ID: {chat_id}")
        print(f"分析类型: {analysis_type}")
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content, created_at
                FROM analysis
                WHERE chat_id = ? AND analysis_type = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (chat_id, analysis_type))
            result = cursor.fetchone()
            if result:
                print(f"找到分析结果，创建时间: {result[1]}")
                return result[0]
            else:
                print("未找到分析结果")
                return None

    def get_latest_message_time(self, chat_id):
        """获取群组最新消息时间"""
        print(f"\n=== 获取群组最新消息时间 ===")
        print(f"群组ID: {chat_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT MAX(timestamp)
                FROM messages
                WHERE ABS(chat_id) = ABS(?)
            ''', (chat_id,))
            latest_time = cursor.fetchone()[0]
            print(f"最新消息时间: {latest_time}")
            return latest_time

    def get_system_prompt(self, prompt_type):
        """获取指定类型的system prompt"""
        print(f"\n=== 获取System Prompt ===")
        print(f"类型: {prompt_type}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT prompt_text
                FROM system_prompts
                WHERE prompt_type = ?
            ''', (prompt_type,))
            result = cursor.fetchone()
            if result:
                print(f"找到prompt: {result[0][:50]}...")
                return result[0]
            else:
                print("未找到prompt")
                return None

    def update_system_prompt(self, prompt_type, prompt_text):
        """更新指定类型的system prompt"""
        print(f"\n=== 更新System Prompt ===")
        print(f"类型: {prompt_type}")
        print(f"内容: {prompt_text[:50]}...")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO system_prompts (prompt_type, prompt_text, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (prompt_type, prompt_text))
            conn.commit()
            print("System Prompt已更新")

    def delete_chat_history(self, chat_id):
        """删除指定群组的所有记录"""
        print(f"\n=== 删除群组记录 ===")
        print(f"群组ID: {chat_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # 删除消息记录
            cursor.execute('''
                DELETE FROM messages 
                WHERE ABS(chat_id) = ABS(?)
            ''', (chat_id,))
            deleted_messages = cursor.rowcount
            
            # 删除群组信息
            cursor.execute('''
                DELETE FROM chat_info 
                WHERE ABS(chat_id) = ABS(?)
            ''', (chat_id,))
            deleted_info = cursor.rowcount
            
            # 删除分析记录
            cursor.execute('''
                DELETE FROM analysis 
                WHERE ABS(chat_id) = ABS(?)
            ''', (chat_id,))
            deleted_analysis = cursor.rowcount
            
            conn.commit()
            print(f"已删除 {deleted_messages} 条消息记录")
            print(f"已删除 {deleted_info} 条群组信息")
            print(f"已删除 {deleted_analysis} 条分析记录")
            return deleted_messages + deleted_info + deleted_analysis > 0

    def check_and_analyze_group(self, chat_id):
        """检查群组是否需要进行分析"""
        print(f"\n=== 检查群组是否需要分析 ===")
        print(f"群组ID: {chat_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # 检查消息数量
            cursor.execute('''
                SELECT COUNT(*) 
                FROM messages 
                WHERE ABS(chat_id) = ABS(?)
            ''', (chat_id,))
            message_count = cursor.fetchone()[0]
            
            # 检查是否已有分析结果
            cursor.execute('''
                SELECT created_at
                FROM analysis
                WHERE ABS(chat_id) = ABS(?) AND analysis_type = 'background'
                ORDER BY created_at DESC
                LIMIT 1
            ''', (chat_id,))
            last_analysis = cursor.fetchone()
            
            # 如果消息数量大于20且没有分析记录，或者最后一次分析后又有新消息
            if message_count >= 20:
                if not last_analysis:
                    print(f"群组有 {message_count} 条消息，需要进行首次分析")
                    return True
                else:
                    # 检查最后一次分析后是否有新消息
                    cursor.execute('''
                        SELECT COUNT(*)
                        FROM messages
                        WHERE ABS(chat_id) = ABS(?) AND created_at > ?
                    ''', (chat_id, last_analysis[0]))
                    new_messages = cursor.fetchone()[0]
                    if new_messages >= 20:
                        print(f"群组在上次分析后有 {new_messages} 条新消息，需要重新分析")
                        return True
            
            print("群组暂不需要分析")
            return False

    def get_background_analysis(self, chat_id):
        """获取群组的背景分析"""
        print(f"\n=== 获取群组背景分析 ===")
        print(f"群组ID: {chat_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content
                FROM analysis
                WHERE ABS(chat_id) = ABS(?) AND analysis_type = 'background'
                ORDER BY created_at DESC
                LIMIT 1
            ''', (chat_id,))
            result = cursor.fetchone()
            if result:
                print("找到群组背景分析")
                return result[0]
            else:
                print("未找到群组背景分析")
                return None

    def get_user_language(self, user_id: int) -> str:
        """获取用户的语言偏好"""
        print(f"\n=== 获取用户语言偏好 ===")
        print(f"用户ID: {user_id}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT language
                FROM user_preferences
                WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            language = result[0] if result else 'zh'
            print(f"用户语言: {language}")
            return language

    def set_user_language(self, user_id: int, language: str) -> None:
        """设置用户的语言偏好"""
        print(f"\n=== 设置用户语言偏好 ===")
        print(f"用户ID: {user_id}")
        print(f"语言: {language}")
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences (user_id, language, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, language))
            conn.commit()
            print("用户语言偏好已更新")
 