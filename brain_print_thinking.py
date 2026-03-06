from litellm import completion, stream_chunk_builder
import json
import platform
import base64
import mimetypes
import re
from pathlib import Path

IMG_PLACEHOLDER_PATTERN = re.compile(r"\{img:([^}]+)\}")

class AgentBrain:
    def __init__(self, tools):
        self.model = "zai/glm-4.6v"
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

    def _file_to_image_url(self, path: str) -> str:
        path = path.strip()
        if path.startswith("http"):
            # 网络图片直接返回
            return path
        # 本地图片使用data url格式返回base64内容
        p = Path(path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        raw = p.read_bytes()
        b64 = base64.standard_b64encode(raw).decode("ascii")
        mime, _ = mimetypes.guess_type(str(p))
        mime = mime or "application/octet-stream"
        return f"data:{mime};base64,{b64}"

    def _prompt_to_content(self, prompt: str) -> str | list:
        parts = IMG_PLACEHOLDER_PATTERN.split(prompt)
        if len(parts) == 1:
            return prompt
        content = []
        for i, seg in enumerate(parts):
            if not seg:
                continue
            if i % 2 == 1:
                path = seg.strip()
                content.append({"type": "image_url", "image_url": {"url": self._file_to_image_url(path)}})
            else:
                content.append({"type": "text", "text": seg})
        return content

    def _read_response_stream(self,stream):
        chunks = []
        is_thinking_start = False
        for chunk in stream:
            chunks.append(chunk)

            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning_content", None) or ""
            if not reasoning:
                continue

            if not is_thinking_start:
                is_thinking_start = True
                print("...思考中...")
            print(reasoning, end="", flush=True)
        if is_thinking_start:
            print("\n...思考结束...")
        return stream_chunk_builder(chunks, messages=self.messages).choices[0].message

    def think(self, prompt):
        try:
            content = self._prompt_to_content(prompt)
            self.messages.append({"role": "user", "content": content})

            stream = completion(
                model=self.model,
                messages=self.messages,
                tools=self.tools_definition,
                stream=True,
            )
            message = self._read_response_stream(stream)
            
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