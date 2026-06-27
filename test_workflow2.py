import asyncio
import logging
from app.agent import root_agent

logging.basicConfig(level=logging.DEBUG)

async def main():
    try:
        async for event in root_agent.run(node_input='I have an empty plastic water bottle and I live in San Francisco.'):
            print("EVENT:", event)
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    asyncio.run(main())
