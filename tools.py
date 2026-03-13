import os
import json
import contextlib
from docstring_parser import parse as parse_docstring
from fastmcp import Client

class LocalToolExecWrapper:
    __TYPE_MAP = {"str": "string", "int": "integer", "float": "number", "bool": "boolean"}

    def __init__(self, tool, function_name, function):
        self._tool = tool
        self._function_name = function_name
        self._function = function
        self._doc_info = parse_docstring(function.__doc__ or "")
        self._params = {}
        self._required_params = []

        for param in self._doc_info.params:
            ann = function.__annotations__.get(param.arg_name)
            type_name = getattr(ann, "__name__", "string") if ann else "string"
            self._params[param.arg_name] = {
                "type": self.__TYPE_MAP.get(type_name, type_name),
                "description": param.description or ""
            }
            self._required_params.append(param.arg_name)
    
    def get_name(self) -> str:
        return self._function_name
    
    def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self._function_name,
                "description": self._doc_info.short_description or "",
                "parameters": {"type": "object", "properties": self._params, "required": self._required_params}
            }
        }

    async def exec(self, arguments):
        func = getattr(self._tool, self._function_name)
        return json.dumps(func(**arguments))

class MCPToolExecWrapper:
    def __init__(self, client, tool):
        self._client = client
        self._description = tool.description or ""
        self._tool_name = tool.name
        self._input_schema = tool.inputSchema
    
    def get_name(self) -> str:
        return f"MCP_{self._client.name}@{self._tool_name}"
    
    def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {"name": self.get_name(), "description": self._description, "parameters": self._input_schema}
        }
    
    async def exec(self, arguments):
        result = await self._client.call_tool(self._tool_name, arguments)
        return result.data

class MCPResourceExecWrapper:
    def __init__(self, client, tool):
        self._client = client
        self._resource_description = tool.description or ""
        self._resource_uri = tool.uri.unicode_string()
    
    def get_name(self) -> str:
        return f"MCP_{self._client.name}@{self._resource_uri}"
    
    def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {"name": self.get_name(), "description": self._resource_description, "parameters": {}}
        }

    async def exec(self, _):
        result = await self._client.read_resource(self._resource_uri)
        return [r.model_dump_json() for r in result]


class AgentTools:
    _EXCLUDED = {"init", "get_tool_definition_for_json", "exec"}

    def __init__(self):
        self._mcp_clients = []
        self._tool_exec_wrappers = {}

    @contextlib.asynccontextmanager
    async def init(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mcp_dir = os.path.join(script_dir, "mcp")
        for file in os.listdir(mcp_dir):
            if file.endswith(".py"):
                self._mcp_clients.append(Client(f"mcp/{file}"))
        async with contextlib.AsyncExitStack() as stack:
            for client in self._mcp_clients:
                await stack.enter_async_context(client)
            yield self
    
    async def get_tool_definition_for_json(self):
        definition_list = []
        for wrapper in self._get_local_tool_exec_wrappers():
            self._tool_exec_wrappers[wrapper.get_name()] = wrapper
            definition_list.append(wrapper.get_definition())
        for wrapper in await self._get_mcp_tool_exec_wrappers():
            self._tool_exec_wrappers[wrapper.get_name()] = wrapper
            definition_list.append(wrapper.get_definition())
        return definition_list

    async def exec(self, func_name, arguments):
        try:
            print(f"调用工具: {func_name}, 参数: {arguments}")
            result = await self._tool_exec_wrappers[func_name].exec(arguments or {})
            result = json.dumps(result) if not isinstance(result, str) else result
            print(f"工具调用结果: {result}")
            return result
        except Exception as e:
            raise ValueError(f"未知工具或 MCP 调用失败: {func_name}")

    def _get_local_tool_exec_wrappers(self):
        wrappers = []
        for function_name in dir(self):
            if function_name.startswith("_") or function_name in self._EXCLUDED:
                continue
            attr = getattr(self, function_name)
            if not callable(attr):
                continue
            func = getattr(self.__class__, function_name, None)
            if func is None:
                continue
            wrappers.append(LocalToolExecWrapper(self, function_name, func))
        return wrappers
    
    async def _get_mcp_tool_exec_wrappers(self):
        wrappers = []
        for client in self._mcp_clients:
            for tool in await client.list_tools():
                wrappers.append(MCPToolExecWrapper(client, tool))
            for resource in await client.list_resources():
                wrappers.append(MCPResourceExecWrapper(client, resource))
        return wrappers

    def list_dir(self, path: str):
        """
        列出指定目录下的文件和目录
        Args:
            path: 要列出的目录路径
        Returns:
            目录下的文件和目录列表
        """
        expanded_path = os.path.expanduser(path)
        try:
            return os.listdir(expanded_path)
        except FileNotFoundError as e:
            return str(e)
    
    def read_file(self, path: str):
        """
        读取指定文件的内容
        Args:
            path: 要读取的文件路径
        Returns:
            文件内容
        """
        with open(os.path.expanduser(path), "r") as f:
            return f.read()
    
    def write_file(self, path: str, content: str):
        """
        写入内容到指定文件
        Args:
            path: 要写入的文件路径
            content: 要写入的内容
        """
        with open(os.path.expanduser(path), "w") as f:
            f.write(content)