from agent_brain import AgentBrain
from agent_memory import AgentMemory
from tool.tool_manager import ToolManager
from tool.local_tool import LocalToolProvider
import json
import os

class SimpleAgent:
    def __init__(self, config: dict):
        self._tool_manager = ToolManager()
        self._tool_manager.add_tool_provider(LocalToolProvider())
        self._memory = AgentMemory(self._tool_manager.get_tool_definition())
        self._brain = AgentBrain(config["llm"], self._memory)
        
    def run(self):
        while True:
            try:
                user_input = input("请输入(Ctrl+C 退出): ")
            except KeyboardInterrupt:
                print("\n再见!")
                break
            if len(user_input) == 0:
                continue
            print("." * 20)
            response = self._brain.think(user_input)

            while response.content.strip().startswith("{"):
                tool_call = json.loads(response.content.strip())
                tool_name = tool_call["tool_name"]
                tool_args = tool_call["tool_args"]
                result = self._tool_manager.exec(tool_name, tool_args)
                self._memory.add_tool_invoke_result(tool_name, tool_args, result)
                response = self._brain.think("思考执行结果并决定下一步行动.")
            print(response.content)
            print("=" * 20)
        
def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, "config.json"), "r") as f:
        return json.load(f)
        
if __name__ == "__main__":
    my_agent = SimpleAgent(load_config())
    my_agent.run()