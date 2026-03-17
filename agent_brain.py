from zhipuai import ZhipuAI

class AgentBrain:
    def __init__(self, llm_config: dict):
        self._model = llm_config["model"]
        self._client = ZhipuAI(api_key=llm_config["api_key"])

    def think(self, prompt):
        try:
            message = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            ).choices[0].message
            return message.content
        except Exception as e:
            return f"思考过程出错: {e}"