from litellm import completion
import json
import platform

class AgentBrain:
    def __init__(self, tools):
        self.model = "zai/glm-4.7"
        self.tools = tools
        self.tools_definition = tools.get_definition_for_json()
        self.messages = [{"role": "system", "content": self.__get_system_prompt()},]

    def __get_system_prompt(self):
        runtime = f"{platform.system()} {platform.machine()}, Python {platform.python_version()}"
        return f"""
        你是一个AI智能助手.

        ## 运行环境
        {runtime}
        """

    def think(self, prompt):
        try:
            self.messages.append({"role": "user", "content": prompt})

            message = completion(
                model=self.model,
                messages=self.messages,
                tools=self.tools_definition
            ).choices[0].message
            self.messages.append(self.parse_response_message(message))
            self.save_log()
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    args = tool_call.function.arguments
                    if isinstance(args, str):
                        args = json.loads(args)

                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": self.tools.exec(tool_call.function.name, args),
                    })
                return self.think("思考执行结果并决定下一步行动.")
            else:
                return message.content
        except Exception as e:
            return f"思考过程出错: {e}"

    def parse_response_message(self, message):
        result = {
            "role": message.role,
            "content": message.content,
            "reasoning_content": message.reasoning_content,
        }
        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {"id":tc.id, "type":tc.type, "function":{"name":tc.function.name, "arguments":tc.function.arguments}} for tc in message.tool_calls
            ]
        return result

    def save_log(self):
        with open("log.txt", "a") as f:
            f.write(json.dumps(self.messages, indent=4, ensure_ascii=False))