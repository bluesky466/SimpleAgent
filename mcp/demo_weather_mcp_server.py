from mcp.server.fastmcp import FastMCP
import logging

logging.getLogger("mcp").setLevel(logging.WARNING)
mcp = FastMCP("demo-weather-server")

@mcp.tool()
async def get_weather(city: str) -> dict:
	"""Get the current weather for a city. should get support cities from resource weather://citys first"""
	weather_data = {
		"guangzhou": {"temp": 22, "condition": "sunny"},
		"shanghai": {"temp": 15, "condition": "cloudy"},
		"beijing": {"temp": 12, "condition": "rainy"},
	}

	city_lower = city.lower()
	if city_lower in weather_data:
		return {"city": city, **weather_data[city_lower]}
	else:
		return {"city": city, "temp": "unknown", "condition": "unknown", "error": "city not supported"}
	
@mcp.resource("weather://citys")
def citys() -> list[str]:
	"""Get the list of cities."""
	return ["guangzhou", "shanghai", "beijing"]

if __name__ == "__main__":
	mcp.run(transport="stdio")