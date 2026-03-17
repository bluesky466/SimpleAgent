import platform

class AgentMemory:
    def __init__(self, tool_definition: str):
        self._memory = [{"role": "system", "content": self._get_system_prompt(tool_definition)},]
    
    def _get_system_prompt(self, tool_definition: str):
        runtime = f"{platform.system()} {platform.machine()}, Python {platform.python_version()}"
        return f"""
你是一个AI智能助手.

## 运行环境
{runtime}

## 可用工具列表
{tool_definition}

## 工具调用方法
当你需要调用工具的时候,严格按照下面格式输出,我会判断返回的第一个字符是'{{'且最后一个字符是'}}'就去调用工具:
{{
    "message":"你想说的话"
    "tool_name": "工具名称",
    "tool_args": {{
        "参数名称": "参数值"
    }}
}}"""
    def _parse_response_message(self, role: str, message):
        result = {
            "role": role,
            "content": message.content,
        }
        return result

    def add_user_prompt(self, prompt: str):
        self._memory.append({"role": "user", "content": prompt})
    
    def add_agent_response(self, message):
        self._memory.append(self._parse_response_message("assistant", message))

    def add_tool_invoke_result(self, tool_name: str, tool_args: dict, result: str):
        self._memory.append({
            "role": "tool",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "content": result,
        })

    def get_memory(self):
        return self._memory