from agent_brain import AgentBrain
from agent_memory import AgentMemory
import json
import os

class SimpleAgent:
    def __init__(self, config: dict):
        self._memory = AgentMemory()
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
            print(response)
            print("=" * 20)
        
def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, "config.json"), "r") as f:
        return json.load(f)
        
if __name__ == "__main__":
    my_agent = SimpleAgent(load_config())
    my_agent.run()