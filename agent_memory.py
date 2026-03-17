from zhipuai import ZhipuAI
import platform

class AgentMemory:
    def __init__(self):
        self._memory = [{"role": "system", "content": self._get_system_prompt()},]
    
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

    def add_user_prompt(self, prompt):
        self._memory.append({"role": "user", "content": prompt})
    
    def add_agent_response(self, message):
        self._memory.append(self._parse_response_message("assistant", message))
    
    def get_memory(self):
        return self._memory