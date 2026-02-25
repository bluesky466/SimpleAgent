from zhipuai import ZhipuAI
import os

class AgentBrain:
    def __init__(self):
        self.model = "glm-4.7"
        self.client = ZhipuAI(api_key=os.environ.get("ZAI_API_KEY"))
        self.messages = [{"role": "system", "content": self.__get_system_prompt()},]
    
    def __get_system_prompt(self):
        return f"""
        你是一个AI智能助手.
        """
    def think(self, prompt):
        try:
            self.messages.append({"role": "user", "content": prompt})
            message = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            ).choices[0].message
            self.messages.append(self.parse_response_message("assistant", message))
            return message.content
        except Exception as e:
            return f"思考过程出错: {e}"
    
    def parse_response_message(self, role, message):
        result = {
            "role": role,
            "content": message.content,
        }
        return result