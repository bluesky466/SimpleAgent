from tool.tool_manager import Tool, ToolProvider
from fastmcp import Client
from fastmcp.client.transports import StdioTransport, SSETransport, StreamableHttpTransport
import contextlib

class McpTool(Tool):
    def __init__(self, client, tool):
        self._client = client
        self._description = tool.description or ""
        self._tool_name = tool.name
        self._input_schema = tool.inputSchema
    
    async def get_name(self) -> str:
        return f"MCP${self._client.initialize_result.serverInfo.name}${self._tool_name}"
    
    async def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {"name": await self.get_name(), "description": self._description, "parameters": self._input_schema}
        }
    
    async def exec(self, arguments):
        result = await self._client.call_tool(self._tool_name, arguments)
        return result.data or f"{result}"

class McpResource(Tool):
    def __init__(self, client, tool):
        self._client = client
        self._resource_description = tool.description or ""
        self._resource_uri = tool.uri.unicode_string()
    
    async def get_name(self) -> str:
        return f"MCP${self._client.initialize_result.serverInfo.name}${self._resource_uri}"
    
    async def get_definition(self) -> dict:
        return {
            "type": "function",
            "function": {"name": await self.get_name(), "description": self._resource_description, "parameters": {}}
        }

    async def exec(self, _):
        result = await self._client.read_resource(self._resource_uri)
        return [r.model_dump_json() for r in result]

class McpToolProvider(ToolProvider):
    def __init__(self):
        self._mcp_clients = []
    
    def _make_transport(self, mcp_name, mcp_config):
        if "url" in mcp_config:
            url = mcp_config["url"]
            headers = mcp_config.get("headers") or {}
            transport_type = mcp_config.get("transport", "sse" if "/sse" in url else "http")
            if transport_type == "sse":
                return SSETransport(url=url, headers=headers)
            return StreamableHttpTransport(url=url, headers=headers)
        elif "command" in mcp_config:
            command = mcp_config["command"]
            args = mcp_config.get("args", [])
            env = mcp_config.get("env") or None
            return StdioTransport(command=command, args=args, env=env)

    @contextlib.asynccontextmanager
    async def init(self, mcp_config):
        for mcp_name, mcp_config in mcp_config.items():
            transport = self._make_transport(mcp_name, mcp_config)
            self._mcp_clients.append(Client(transport))

        async with contextlib.AsyncExitStack() as stack:
            for client in self._mcp_clients:
                await stack.enter_async_context(client)
            yield self

    async def get_tools(self) -> list[Tool]:
        tools = []
        for client in self._mcp_clients:
            capabilities = client.initialize_result.capabilities
            if capabilities.tools:
                for tool in await client.list_tools():
                    tools.append(McpTool(client, tool))
            if capabilities.resources:
                for resource in await client.list_resources():
                    tools.append(McpResource(client, resource))
        return tools