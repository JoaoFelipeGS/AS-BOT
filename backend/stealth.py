import asyncio
import random

async def stealth(page):

    await asyncio.sleep(random.uniform(1.5, 3.5))

    try:
        await page.mouse.wheel(0, random.randint(200, 700))
    except:
        pass

    await asyncio.sleep(random.uniform(0.8, 2.0))

    try:
        await page.mouse.move(
            random.randint(200, 900),
            random.randint(200, 700),
            steps=10
        )
    except:
        pass

    await asyncio.sleep(random.uniform(0.5, 1.5))