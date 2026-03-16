import json
from abc import ABC, abstractmethod

class Tool(ABC):
    @abstractmethod
    async def get_name(self) -> str:
        """获取工具名称"""
        pass

    @abstractmethod
    async def get_definition(self) -> dict:
        """获取工具定义"""
        pass

    @abstractmethod
    async def exec(self, arguments):
        """执行工具主逻辑"""
        pass

class ToolProvider(ABC):
    @abstractmethod
    def get_tools(self) -> list[Tool]:
        """获取工具列表"""
        pass

class ToolManager():
    def __init__(self):
        self._tool_providers = []
        self._tools = {}
    
    async def add_tool_provider(self, tool_provider: ToolProvider):
        self._tool_providers.append(tool_provider)
        for tool in await tool_provider.get_tools():
            self._tools[await tool.get_name()] = tool
    
    async def get_tool_definition(self):
        definition_list = []
        for tool in self._tools.values():
            definition_list.append(await tool.get_definition())
        return definition_list
    
    async def exec(self, func_name, arguments):
        print(f"调用工具: {func_name}, 参数: {arguments}")
        result = await self._tools[func_name].exec(arguments or {})
        result = json.dumps(result) if not isinstance(result, str) else result
        print(f"工具调用结果: {result}")
        return result