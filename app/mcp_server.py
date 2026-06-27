from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("EcoSort-MCP-Server")

@mcp.tool()
def search_municipal_database(location: str, material: str) -> str:
    """Searches the local municipal database for recycling rules for a specific material."""
    # Mock data
    if "san francisco" in location.lower() or "sf" in location.lower():
        if "plastic" in material.lower():
            return "San Francisco: Clean rigid plastics go in the blue recycling bin. Soft plastics (bags, wrap) must be dropped off at special collection sites."
        elif "compost" in material.lower() or "food" in material.lower():
            return "San Francisco: Food scraps and compostable plastics go in the green compost bin."
        return f"San Francisco: General guidelines apply. If not recyclable or compostable, place in black trash bin."
    else:
        return f"Database query for {location} returned no specific rules. Please check your local city website."

@mcp.tool()
def get_compost_locations(zip_code: str) -> str:
    """Finds nearby community compost drop-off locations for a given zip code."""
    return f"Found 3 compost drop-off locations near {zip_code}:\n1. Community Garden (0.5 miles)\n2. Farmers Market (1.2 miles)\n3. Central Recycling Center (3.0 miles)"

@mcp.tool()
def calculate_carbon_saved(material: str, weight_lbs: float) -> str:
    """Calculates estimated carbon emissions saved by recycling/composting the item."""
    # Mock calculation
    co2_per_lb = 1.5 if "plastic" in material.lower() else 0.5
    saved = weight_lbs * co2_per_lb
    return f"Recycling {weight_lbs} lbs of {material} saves approximately {saved:.2f} lbs of CO2 emissions."

if __name__ == "__main__":
    mcp.run(transport='stdio')
