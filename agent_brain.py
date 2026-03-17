from zhipuai import ZhipuAI

class AgentBrain:
    def __init__(self, llm_config: dict):
        self._model = llm_config["model"]
        self._client = ZhipuAI(api_key=llm_config["api_key"])
        self._messages = [{"role": "system", "content": self._get_system_prompt()},]
    
    def _get_system_prompt(self):
        return f"""
        你是一个AI智能助手.
        """

    def _parse_response_message(self, role, message):
        result = {
            "role": role,
            "content": message.content,
        }
        return result

    def think(self, prompt):
        try:
            self._messages.append({"role": "user", "content": prompt})
            message = self._client.chat.completions.create(
                model=self._model,
                messages=self._messages,
            ).choices[0].message
            self._messages.append(self._parse_response_message("assistant", message))
            return message.content
        except Exception as e:
            return f"思考过程出错: {e}"