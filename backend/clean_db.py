import asyncio
from app.db import connect_db, get_db


async def clean():
    await connect_db()
    db = get_db()

    collections = await db.list_collection_names()
    for name in collections:
        await db[name].drop()
        print(f"Dropped: {name}")

    print("\nDatabase is clean!")


asyncio.run(clean())