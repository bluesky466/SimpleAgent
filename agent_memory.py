import platform

class AgentMemory:
    def __init__(self):
        self._memory = [{"role": "system", "content": self._get_system_prompt()},]
    
    def _get_system_prompt(self):
        runtime = f"{platform.system()} {platform.machine()}, Python {platform.python_version()}"
        return f"""
        你是一个AI智能助手.

        ## 运行环境
        {runtime}"""

    def _parse_response_message(self, role: str, message):
        result = {
            "role": message.role,
            "content": getattr(message, "content", None),
            "reasoning_content": getattr(message, "reasoning_content", None),
        }
        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {"id":tc.id, "type":tc.type, "function":{"name":tc.function.name, "arguments":tc.function.arguments}} for tc in message.tool_calls
            ]
        return result

    def add_user_prompt(self, prompt: str):
        self._memory.append({"role": "user", "content": prompt})
    
    def add_agent_response(self, message):
        self._memory.append(self._parse_response_message("assistant", message))

    def add_tool_invoke_result(self, tool_call_id, tool_name: str, tool_args: dict, result: str):
        self._memory.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "arguments": tool_args,
            "content": result,
        })

    def get_memory(self):
        return self._memory