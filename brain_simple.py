from zhipuai import ZhipuAI
import os

class AgentBrain:
    def __init__(self):
        self.model = "glm-4.7"
        self.client = ZhipuAI(api_key=os.environ.get("ZAI_API_KEY"))

    def think(self, prompt):
        try:
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            ).choices[0].message
            return message.content
        except Exception as e:
            return f"思考过程出错: {e}"