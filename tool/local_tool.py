from tool.tool_manager import Tool, ToolProvider
from docstring_parser import parse as parse_docstring
import json
import os

class LocalTool(Tool):
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
                "name": self.get_name(),
                "description": self._doc_info.short_description or "",
                "parameters": {"type": "object", "properties": self._params, "required": self._required_params}
            }
        }

    def exec(self, arguments):
        func = getattr(self._tool, self._function_name)
        return json.dumps(func(**arguments))

class LocalToolProvider(ToolProvider):
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

    
    def get_tools(self) -> list[Tool]:
        tools = []
        for function_name in dir(self):
            if function_name.startswith("_") or function_name == "get_tools":
                continue
            attr = getattr(self, function_name)
            if not callable(attr):
                continue
            func = getattr(self.__class__, function_name, None)
            if func is None:
                continue
            tools.append(LocalTool(self, function_name, func))
        return tools