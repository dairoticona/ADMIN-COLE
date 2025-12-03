import asyncio
from app.core.database import connect_to_mongo, get_database
from app.core.config import settings

async def verify():
    await connect_to_mongo()
    db = get_database()
    user = await db["users"].find_one({"username": "brandon"})
    if user:
        print(f"User found: {user['username']}, Role: {user['role']}")
    else:
        print("User not found")

if __name__ == "__main__":
    asyncio.run(verify())
