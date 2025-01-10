import google.generativeai as genai
import json

class GeminiHandler:
    AVAILABLE_MODELS = {
        'gemini-pro': 'gemini-pro',
        'gemini-exp-1206': 'gemini-exp-1206',
        'gemini-2.0-flash-exp': 'gemini-2.0-flash-exp'
    }
    DEFAULT_MODEL = 'gemini-2.0-flash-exp'

    def __init__(self, api_key, model_name=None):
        print(f"初始化 Gemini API...")
        genai.configure(api_key=api_key)
        
        # 使用指定的模型或默认模型
        self.model_name = model_name if model_name in self.AVAILABLE_MODELS else self.DEFAULT_MODEL
        self.model = genai.GenerativeModel(self.model_name)
        print(f"Gemini API 初始化完成，使用模型：{self.model_name}")

    def set_model(self, model_name):
        """切换到指定的模型"""
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"不支持的模型：{model_name}。可用模型：{list(self.AVAILABLE_MODELS.keys())}")
        
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        print(f"已切换到模型：{model_name}")

    async def analyze_group_history(self, messages, system_prompt=None):
        print(f"\n=== 开始分析群组历史 ===")
        print(f"使用模型：{self.model_name}")
        print(f"输入消息原始内容：\n{messages}")
        print(f"输入消息长度：{len(messages)} 字符")
        prompt = f"{system_prompt or '分析以下群组聊天记录，提供群组的背景信息：'}\n{messages}"
        print(f"完整的 Prompt：\n{prompt}")
        try:
            print("正在调用 Gemini API...")
            response = self.model.generate_content(prompt)
            print(f"Gemini API 响应原始内容：")
            print(json.dumps(response.candidates[0].content.parts[0].text, ensure_ascii=False, indent=2))
            print(f"Gemini 响应文本：\n{response.text}")
            return response.text
        except Exception as e:
            print(f"Gemini API 调用出错：{str(e)}")
            print(f"错误类型：{type(e)}")
            return f"分析过程中出错：{str(e)}"

    async def find_action_items(self, messages, system_prompt=None):
        print(f"\n=== 开始查找待办事项 ===")
        print(f"使用模型：{self.model_name}")
        print(f"输入消息原始内容：\n{messages}")
        print(f"输入消息长度：{len(messages)} 字符")
        prompt = f"{system_prompt or '分析以下今日群组聊天记录，找出需要我执行的待办事项：'}\n{messages}"
        print(f"完整的 Prompt：\n{prompt}")
        try:
            print("正在调用 Gemini API...")
            response = self.model.generate_content(prompt)
            print(f"Gemini API 响应原始内容：")
            print(json.dumps(response.candidates[0].content.parts[0].text, ensure_ascii=False, indent=2))
            print(f"Gemini 响应文本：\n{response.text}")
            return response.text
        except Exception as e:
            print(f"Gemini API 调用出错：{str(e)}")
            print(f"错误类型：{type(e)}")
            print(f"错误详情：")
            print(f"消息内容：{messages[:200]}...")  # 只打印前200个字符
            print(f"系统提示词：{system_prompt[:200]}...")  # 只打印前200个字符
            return f"分析过程中出错：{str(e)}"

    async def suggest_reply(self, last_message, system_prompt=None):
        print(f"\n=== 开始生成回复建议 ===")
        print(f"使用模型：{self.model_name}")
        print(f"输入消息原始内容：\n{last_message}")
        print(f"输入消息长度：{len(last_message)} 字符")
        prompt = f"{system_prompt or '根据以下最新消息，建议一个合适的回复：'}\n{last_message}"
        print(f"完整的 Prompt：\n{prompt}")
        try:
            print("正在调用 Gemini API...")
            response = self.model.generate_content(prompt)
            print(f"Gemini API 响应原始内容：")
            print(json.dumps(response.candidates[0].content.parts[0].text, ensure_ascii=False, indent=2))
            print(f"Gemini 响应文本：\n{response.text}")
            return response.text
        except Exception as e:
            print(f"Gemini API 调用出错：{str(e)}")
            print(f"错误类型：{type(e)}")
            return f"生成建议时出错：{str(e)}" 