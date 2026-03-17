from zhipuai import ZhipuAI
from agent_memory import AgentMemory

class AgentBrain:
    def __init__(self, llm_config: dict, memory: AgentMemory):
        self._model = llm_config["model"]
        self._client = ZhipuAI(api_key=llm_config["api_key"])
        self._memory = memory

    def think(self, prompt):
        try:
            self._memory.add_user_prompt(prompt)
            message = self._client.chat.completions.create(
                model = self._model,
                messages = self._memory.get_memory(),
            ).choices[0].message
            self._memory.add_agent_response(message)
            return message
        except Exception as e:
            return f"思考过程出错: {e}"