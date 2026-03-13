import asyncio
from brain import AgentBrain
from tools import AgentTools


class SimpleAgent:
    def __init__(self):
        self._tools = AgentTools()
        self._brain = None
    
    async def run(self):
        async with self._tools.init():
            self._brain = AgentBrain()
            await self._brain.init(self._tools)
            while True:
                try:
                    user_input = input("请输入(Ctrl+C 退出): ")
                except (KeyboardInterrupt, EOFError):
                    print("\n再见!")
                    break
                if len(user_input) == 0:
                    continue
                print("." * 20)
                await self._brain.think(user_input)
                print("=" * 20)

if __name__ == "__main__":
    asyncio.run(SimpleAgent().run())