from litellm import completion, stream_chunk_builder
import json
import platform
import base64
import mimetypes
import re
from pathlib import Path

IMG_PLACEHOLDER_PATTERN = re.compile(r"\{img:([^}]+)\}")

class AgentBrain:
    async def init(self, tools):
        self._model = "zai/glm-4.6v"
        self._tools = tools
        self._tools_definition = await tools.get_tool_definition_for_json()
        self._messages = [{"role": "system", "content": self._get_system_prompt()},]

    def _get_system_prompt(self):
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

    def _read_response_stream(self, stream, in_deep_thinking=False):
        chunks = []
        for chunk in stream:
            chunks.append(chunk)

            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            reasoning = getattr(delta, "reasoning_content", None) or ""
            content = getattr(delta, "content", None) or ""
            if not reasoning and not content:
                continue

            if not in_deep_thinking:
                in_deep_thinking = True
                print("...深度思考中...")
            if reasoning:
                print(reasoning, end="", flush=True)
            if content:
                print(content, end="", flush=True)
        return stream_chunk_builder(chunks, messages=self._messages).choices[0].message

    async def think(self, prompt, in_deep_thinking=False):
        try:
            content = self._prompt_to_content(prompt)
            self._messages.append({"role": "user", "content": content})

            stream = completion(
                model=self._model,
                messages=self._messages,
                tools=self._tools_definition,
                stream=True,
            )
            message = self._read_response_stream(stream, in_deep_thinking)

            self._messages.append(self._parse_response_message(message))
            self._save_log()
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    args = tool_call.function.arguments
                    if isinstance(args, str):
                        args = json.loads(args)
                    content = await self._tools.exec(tool_call.function.name, args)
                    self._messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": content,
                    })
                return await self.think("思考执行结果并决定下一步行动.", True)
            else:
                print("\n...深度思考结束...\n")
                print(message.content)
        except Exception as e:
            print(f"思考过程出错: {e}")

    def _parse_response_message(self, message):
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

    def _save_log(self):
        with open("log.txt", "a") as f:
            f.write(json.dumps(self._messages, indent=4, ensure_ascii=False))