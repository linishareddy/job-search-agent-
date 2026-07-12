import asyncio
from config.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT suggestions FROM resume_tailoring LIMIT 1;"))
        for row in result:
            print("ResumeTailoring suggestions:", row[0])

asyncio.run(main())
