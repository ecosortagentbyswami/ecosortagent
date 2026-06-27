import asyncio
from app.agent import root_agent

async def main():
    async for res in root_agent.run(node_input='I have an empty plastic water bottle and I live in San Francisco.'):
        print("RESULT:", res)

if __name__ == "__main__":
    asyncio.run(main())
