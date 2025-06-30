# kimiChatClient.py
import requests
import json
import os
import uuid
import aiohttp
import asyncio
from tools.codeRunner import CodeRunner


class KimiChatClient:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.session_id = str(uuid.uuid4())
        self.messages = [
            {"role": "system",
             "content": "你是 Kimi，由 Moonshot AI "
                        "提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI "
                        "为专有名词，不可翻译成其他语言。"}
        ]

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as file:
                return json.load(file)
        raise FileNotFoundError(f"配置文件 {self.config_file} 不存在")

    async def chat(self, user_msg, session_id=None, loading_chat=False, before_chats=None):
        api_key = self.config.get("ai_key")
        url = self.config.get("ai_url")
        if not api_key or not url:
            raise ValueError("配置文件中缺少必要的配置项")

        if session_id is None:
            session_id = self.session_id
            self.messages = [
                {"role": "system",
                 "content": "你是 Kimi，由 Moonshot AI "
                            "提供的人工智能助手，你更擅长中文和英文的对话。你会为用户提供安全，有帮助，准确的回答。同时，你会拒绝一切涉及恐怖主义，种族歧视，黄色暴力等问题的回答。Moonshot AI "
                            "为专有名词，不可翻译成其他语言。"},
                {"role": "user", "content": user_msg}
            ]
        else:
            if loading_chat and before_chats is not None:
                for chat in before_chats:
                    role = 'assistant'
                    message = chat['message']
                    if chat.get('from') == "me":
                        role = 'user'
                    self.messages.append({
                        "role": role,
                        "content": message
                    })
            self.messages.append({
                "role": "user",
                "content": user_msg
            })
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "moonshot-v1-128k",
            "messages": self.messages,
            "session_id": session_id,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "CodeRunner",
                        "description": "代码执行器，支持运行 python 和 javascript 代码",
                        "parameters": {
                            "properties": {
                                "language": {
                                    "type": "string",
                                    "enum": ["python", "javascript"]
                                },
                                "code": {
                                    "type": "string",
                                    "description": "代码写在这里"
                                }
                            },
                            "type": "object"
                        }
                    }
                }
            ],
            "temperature": 0.3
        }
        # response = requests.post(url, headers=headers, json=data)
        async with (aiohttp.ClientSession() as session):
            print("self.messages中会话条数为："+str(len(self.messages)))
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(result)
                    title = result.get('session_title', '')
                    content = result['choices'][0]['message']['content']
                    if result['choices'][0]['message'].get('tool_calls') is not None:
                        tool = result['choices'][0]['message']['tool_calls'][0]
                        if tool['type'] == 'function' and tool['id'].startswith("CodeRunner"):
                            arguments = tool['function']['arguments'].replace('\\n','<br>')
                            if arguments is not None:
                                parsed_arguments = json.loads(arguments)
                                result = CodeRunner(parsed_arguments['language'], parsed_arguments['code'])
                                print(result)
                                if 'output' in result:
                                    result_str = result['output']
                                elif 'error' in result:
                                    result_str = result['error']
                                else:
                                    result_str = str(result)
                                codeStr = '```' + parsed_arguments['language'] + '\n'+parsed_arguments['code']+'```'
                                content = '执行了以下代码：<br>' + codeStr + '<br>执行结果为:' + content + result_str
                                print("L116 content=", content)
                            # content = '执行了以下代码：<br>' + arguments + '<br>执行结果为:' + content
                    # self.messages.append({
                    #     "role": "assistant",
                    #     "content": content
                    # })
                    return {
                        "session_id": session_id,
                        "title": title,
                        "content": content
                    }
                else:
                    raise Exception(f"API 请求失败，状态码: {response.status}, {await response.text()}")


# 示例用法
if __name__ == "__main__":
    client = KimiChatClient()
    user_message = "你是谁？"
    try:
        response = client.chat(user_message)
        print("Kimi 的回答:", response)
    except Exception as e:
        print("发生错误:", e)
