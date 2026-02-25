# from brain_simple import AgentBrain
# from brain_with_memory import AgentBrain
# from brain_with_tool_use_prompt import AgentBrain
from brain_with_tool_use_tools import AgentBrain
from tools import AgentTools

class SimpleAgent:
    def __init__(self):
        self.tools = AgentTools()
        # self.brain = AgentBrain()
        self.brain = AgentBrain(self.tools)
    
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
            response = self.brain.think(user_input)
            print(response)
            print("=" * 20)
        
if __name__ == "__main__":
    my_agent = SimpleAgent()
    my_agent.run()