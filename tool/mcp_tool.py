from tool.tool_manager import Tool, ToolProvider
from mcp import ClientSession, ClientSessionGroup
from mcp.client.session_group import StdioServerParameters,  SseServerParameters, StreamableHttpParameters
from mcp.types import Tool as McpToolType, Resource as McpResourceType
import contextlib
import logging

logging.getLogger("mcp").setLevel(logging.WARNING)

def _component_name(name: str, server_name: str) -> str:
    return f"MCP${server_name}${name}"

class McpTool(Tool):
    def __init__(self, session: ClientSession, server_name: str, tool: McpToolType):
        self._session = session
        self._server_name = server_name
        self._tool = tool
        self._display_name = _component_name(tool.name, server_name)

    async def get_name(self) -> str:
        return self._display_name

    async def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self._display_name,
                "description": self._tool.description or "",
                "parameters": self._tool.inputSchema,
            },
        }

    async def exec(self, arguments):
        result = await self._session.call_tool(self._tool.name, arguments or {})
        return [c.model_dump_json() for c in result.content]


class McpResource(Tool):
    def __init__(self, session: ClientSession, server_name: str, resource: McpResourceType):
        self._session = session
        self._server_name = server_name
        self._resource = resource
        self._display_name = _component_name(resource.uri.unicode_string(), server_name)

    async def get_name(self) -> str:
        return self._display_name

    async def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self._display_name,
                "description": self._resource.description or "",
                "parameters": {},
            },
        }

    async def exec(self, _):
        result = await self._session.read_resource(self._resource.uri)
        return [c.model_dump_json() for c in result.contents]


class McpToolProvider(ToolProvider):
    def __init__(self):
        self._tools = []

    def _make_server_params(self, mcp_name: str, config: dict):
        if "url" in config:
            url = config["url"]
            headers = config.get("headers") or {}
            transport = config.get("transport", "sse" if "/sse" in url else "http")
            if transport == "sse":
                return SseServerParameters(url=url, headers=headers)
            return StreamableHttpParameters(url=url, headers=headers)
        if "command" in config:
            return StdioServerParameters(
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env"),
                cwd=config.get("cwd"),
            )
        raise ValueError(f"mcp config '{mcp_name}' must have 'url' or 'command'")

    @contextlib.asynccontextmanager
    async def init(self, mcp_config: dict):
        component_name_hook = lambda name, server_info: _component_name(name, server_info.name)
        async with ClientSessionGroup(component_name_hook=component_name_hook) as group:
            self._group = group
            for mcp_name, cfg in mcp_config.items():
                params = self._make_server_params(mcp_name, cfg)
                session = await group.connect_to_server(params)
                capabilities = session.get_server_capabilities()

                if capabilities.tools:
                    tools_result = await session.list_tools()
                    for tool in tools_result.tools or []:
                        self._tools.append(McpTool(session, mcp_name, tool))

                if capabilities.resources:
                    resources_result = await session.list_resources()
                    for resource in resources_result.resources or []:
                        self._tools.append(McpResource(session, mcp_name, resource))
            yield self

    async def get_tools(self) -> list[Tool]:
        return self._tools
