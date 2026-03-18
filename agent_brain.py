from litellm import completion, stream_chunk_builder
from agent_memory import AgentMemory
from tool.tool_manager import ToolManager
from typing import Callable 

class AgentBrain:
    def __init__(self, llm_config: dict, memory: AgentMemory, tool_manager: ToolManager, stream_trace_reader: Callable[[str, str], None]):
        self._model = llm_config["model"]
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

    def think(self, prompt):
        try:
            self._memory.add_user_prompt(prompt)
            stream = completion(
                model = self._model,
                messages = self._memory.get_memory(),
                tools=self._tools_definition,
                api_key=self._api_key,
                stream=True,
            )
            message = self._read_response_stream(stream)
            self._memory.add_agent_response(message)
            return message
        except Exception as e:
            return f"思考过程出错: {e}"