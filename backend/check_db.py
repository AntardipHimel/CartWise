import asyncio
from app.db import connect_db, get_db


async def check():
    await connect_db()
    db = get_db()
    
    collections = await db.list_collection_names()
    print("Collections:", collections)
    print()
    
    for name in collections:
        count = await db[name].count_documents({})
        print(f"  {name}: {count} documents")


asyncio.run(check())