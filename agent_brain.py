from litellm import completion, stream_chunk_builder
from agent_memory import AgentMemory
from tool.tool_manager import ToolManager
from typing import Callable 
from pathlib import Path
import base64
import mimetypes
import re

IMG_PLACEHOLDER_PATTERN = re.compile(r"\{img:([^}]+)\}")

class AgentBrain:
    def __init__(self, llm_config: dict, memory: AgentMemory, tool_manager: ToolManager, stream_trace_reader: Callable[[str, str], None]):
        self._model = llm_config["model"]
        self._model_support_vision = llm_config["model_support_vision"]
        self._api_key = llm_config["api_key"]
        self._memory = memory
        self._tools_definition = tool_manager.get_tool_definition()
        self._stream_trace_reader = stream_trace_reader
    
    def _read_response_stream(self, stream):
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

            if reasoning:
                self._stream_trace_reader("reasoning", reasoning)
            if content:
                self._stream_trace_reader("content", content)
        return stream_chunk_builder(chunks).choices[0].message

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

    def think(self, prompt):
        try:
            content = self._prompt_to_content(prompt)
            need_support_vision = content and isinstance(content, list)
            model = self._model_support_vision if need_support_vision else self._model
            messages = self._memory.get_memory() + [{"role": "user", "content": content}]
            stream = completion(
                model = model,
                messages = messages,
                tools=self._tools_definition,
                api_key=self._api_key,
                stream=True,
            )
            self._memory.add_user_content(prompt)
            message = self._read_response_stream(stream)
            self._memory.add_agent_response(message)
            return message
        except Exception as e:
            return f"思考过程出错: {e}"