import asyncio
from agent_brain import AgentBrain
from agent_memory import AgentMemory
from tool.tool_manager import ToolManager
from tool.local_tool import LocalToolProvider
from tool.mcp_tool import McpToolProvider
from skill_loader import SkillLoader
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(SCRIPT_DIR, "skills")
MAX_TOOL_CALL_COUNT = 20

class SimpleAgent:
    def __init__(self, config: dict):
        self._config = config
        self._skill_loader = SkillLoader(SKILL_DIR)
        self._tool_manager = ToolManager()
        self._memory = AgentMemory(self._skill_loader)
        self._brain = AgentBrain()
        self._is_in_thinking = False
    
    def _stream_trace_reader(self, type: str, content: str):
        if not self._is_in_thinking:
            self._is_in_thinking = True
            print("...思考中...")
        print(content, end="", flush=True)
        
    async def run(self):
        local_tool_provider = LocalToolProvider(self._skill_loader)
        mcp_tool_provider = McpToolProvider()
        async with mcp_tool_provider.init(self._config["mcp"]):
            await self._tool_manager.add_tool_provider(local_tool_provider)
            await self._tool_manager.add_tool_provider(mcp_tool_provider)
            await self._brain.init(self._config["llm"], self._memory, self._tool_manager, self._stream_trace_reader)
            while True:
                user_input = input("请输入(Ctrl+C 退出): ")
                if len(user_input) == 0:
                    continue
                print("." * 20)
                response = self._brain.think(user_input)

                retry_count = MAX_TOOL_CALL_COUNT
                while hasattr(response, "tool_calls") and response.tool_calls and retry_count > 0:
                    for tool_call in response.tool_calls:
                        id = tool_call.id
                        tool_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        result = await self._tool_manager.exec(tool_name, args)
                        self._memory.add_tool_invoke_result(id, tool_name, args, result)
                    retry_count -= 1
                    response = self._brain.think("思考执行结果并决定下一步行动.")
                    if retry_count == 0:
                        self._is_in_thinking = False
                        print("\n...思考结束...")
                        response = self._brain.think("工具调用次数过多,请询问用户是否继续执行这个任务.")
                if self._is_in_thinking:
                    self._is_in_thinking = False
                    print("\n...思考结束...")
                print(response.content)
                print("=" * 20)
        
def load_config():
    with open(os.path.join(SCRIPT_DIR, "config.json"), "r") as f:
        return json.load(f)
        

if __name__ == "__main__":
    try:
        asyncio.run(SimpleAgent(load_config()).run())
    except (KeyboardInterrupt, EOFError):
        print("\n再见!")
