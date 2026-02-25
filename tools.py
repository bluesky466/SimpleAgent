import os
import json
from docstring_parser import parse as parse_docstring

class AgentTools:
    __TYPE_MAP = {"str": "string", "int": "integer", "float": "number", "bool": "boolean"}
    __EXCLUDED = {"get_definition_for_json", "get_definition_for_prompt", "exec"}

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
    
    def exec(self, func_name, arguments):
        func = getattr(self, func_name)
        return json.dumps(func(**arguments))

    def get_definition_for_json(self):
        tools_definition = []
        for attr_name in dir(self):
            if attr_name.startswith("_") or attr_name in self.__EXCLUDED:
                continue
            attr = getattr(self, attr_name)
            if not callable(attr):
                continue
            func = getattr(self.__class__, attr_name, None)
            if func is None:
                continue
            doc_info = parse_docstring(func.__doc__ or "")
            params, required_params = {}, []
            for param in doc_info.params:
                ann = func.__annotations__.get(param.arg_name)
                type_name = getattr(ann, "__name__", "string") if ann else "string"
                params[param.arg_name] = {
                    "type": self.__TYPE_MAP.get(type_name, type_name),
                    "description": param.description or ""
                }
                required_params.append(param.arg_name)
            tools_definition.append({
                "type": "function",
                "function": {
                    "name": attr_name,
                    "description": doc_info.short_description or "",
                    "parameters": {"type": "object", "properties": params, "required": required_params}
                }
            })
        return tools_definition

    def get_definition_for_prompt(self):
        tools_definition = []
        for attr_name in dir(self):
            if attr_name.startswith("_") or attr_name in self.__EXCLUDED:
                continue
            attr = getattr(self, attr_name)
            if not callable(attr):
                continue
            func = getattr(self.__class__, attr_name, None)
            if func is None:
                continue
            tools_definition.append(f"###{attr_name}\n{func.__doc__}")
        return tools_definition