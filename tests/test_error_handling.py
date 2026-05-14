import aiohttp
import asyncio
from pyyardian.async_client import AsyncYardianClient

async def main():
    # TEST 1: Wrong IP
    print("Testing connection to non-existent IP...")
    async with aiohttp.ClientSession() as session:
        try:
            await AsyncYardianClient.create(session, "192.168.1.254", "BAD_TOKEN")
        except Exception:
            print("SUCCESS: Library caught the network timeout/error.")

    # TEST 2: Bad Token on YP
    print("\nTesting bad token on YP (192.168.1.103)...")
    async with aiohttp.ClientSession() as session:
        try:
            await AsyncYardianClient.create(session, "192.168.1.103", "WRONG_TOKEN")
        except Exception:
            print("SUCCESS: Library caught the Unauthorized error.")

if __name__ == "__main__":
    asyncio.run(main())