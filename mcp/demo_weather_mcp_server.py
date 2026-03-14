from fastmcp import FastMCP,Context
from fastmcp.resources import ResourceContent
mcp = FastMCP("demo-weather-server")

@mcp.tool
async def get_weather(city: str) -> dict:
	"""Get the current weather for a city. should get support cities from resource weather://citys first"""
	weather_data = {
		"guangzhou": {"temp": 72, "condition": "sunny"},
		"shanghai": {"temp": 59, "condition": "cloudy"},
		"beijing": {"temp": 68, "condition": "rainy"},
	}

	city_lower = city.lower()
	if city_lower in weather_data:
		return {"city": city, **weather_data[city_lower]}
	else:
		return {"city": city, "temp": "unknown", "condition": "unknown", "error": "city not supported"}
	
@mcp.resource("weather://citys")
def citys() -> str:
	"""Get the list of cities."""
	return [ResourceContent("guangzhou"), ResourceContent("shanghai"), ResourceContent("beijing")]

if __name__ == "__main__":
	mcp.run(transport="stdio")