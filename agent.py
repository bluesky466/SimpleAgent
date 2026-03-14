import asyncio
import json
import os
from brain import AgentBrain
from tool.tool_manager import ToolManager
from tool.local_tool import LocalToolProvider
from tool.mcp_tool import McpToolProvider

class SimpleAgent:
    def __init__(self):
        self._config = self._load_config()
        self._tool_manager = ToolManager()
        self._brain = AgentBrain()
        self._local_tool_provider = LocalToolProvider()
        self._mcp_tool_provider = McpToolProvider()
    
    def _load_config(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(script_dir, "config.json"), "r") as f:
            return json.load(f)
    
    async def run(self):
        async with self._mcp_tool_provider.init(self._config["mcp"]):
            await self._tool_manager.add_tool_provider(self._local_tool_provider)
            await self._tool_manager.add_tool_provider(self._mcp_tool_provider)

            await self._brain.init(self._config["llm"], self._tool_manager)
            while True:
                user_input = input("请输入(Ctrl+C 退出): ")
                if len(user_input) == 0:
                    continue
                print("." * 20)
                await self._brain.think(user_input)
                print("=" * 20)

if __name__ == "__main__":
    try:
        asyncio.run(SimpleAgent().run())
    except (KeyboardInterrupt, EOFError):
        print("\n再见!")