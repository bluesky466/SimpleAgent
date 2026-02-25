
from zhipuai import ZhipuAI
import os
import json
import platform

class AgentBrain:
    def __init__(self, tools):
        self.model = "glm-4.7"
        self.tools = tools
        self.client = ZhipuAI(api_key=os.environ.get("ZAI_API_KEY"))
        self.tools_definition = "\n".join(tools.get_definition_for_prompt())
        self.messages = [{"role": "system", "content": self.__get_system_prompt()},]
    
    def __get_system_prompt(self):
        runtime = f"{platform.system()} {platform.machine()}, Python {platform.python_version()}"
        return f"""
        你是一个AI智能助手.

        ## 运行环境
        {runtime}

        ## 可用工具列表
        {self.tools_definition}

        ## 工具调用方法
        直接返回以下json格式的工具调用参数，不要包含任何其他内容:
        {{
            "tool_name": "工具名称",
            "tool_args": {{
                "参数名称": "参数值"
            }}
        }}"""
    def think(self, prompt):
        try:
            self.messages.append({"role": "user", "content": prompt})
            message = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            ).choices[0].message
            self.messages.append(self.parse_response_message("assistant", message))
            if message.content.startswith("{") or message.content.startswith("```json"):
                tool_call = json.loads(message.content.strip("```json").strip("```"))
                self.messages.append({
                    "role": "tool",
                    "tool_name": tool_call["tool_name"],
                    "tool_args": tool_call["tool_args"],
                    "content": self.tools.exec(tool_call["tool_name"], tool_call["tool_args"]),
                })
                return self.think("思考执行结果并决定下一步行动.")
            else:
                return message.content
        except Exception as e:
            return f"思考过程出错: {e}"
    
    def parse_response_message(self, role, message):
        result = {
            "role": role,
            "content": message.content,
        }
        return result