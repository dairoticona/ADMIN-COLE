import asyncio
from app.core.database import connect_to_mongo, get_database
from app.core.security import get_password_hash

async def fix_missing_passwords():
    print("Connecting to DB...")
    await connect_to_mongo()
    db = get_database()
    collection = db["users"]

    # Buscar usuarios que NO tengan el campo hashed_password o que sea null/vacio
    query = {
        "$or": [
            {"hashed_password": {"$exists": False}},
            {"hashed_password": None},
            {"hashed_password": ""}
        ]
    }
    
    count = await collection.count_documents(query)
    print(f"Found {count} users with missing/invalid password.")
    
    if count == 0:
        print("No users to fix.")
        return

    # Default password value
    default_pass_hash = get_password_hash("123456")
    
    cursor = collection.find(query)
    fixed_count = 0
    
    async for user in cursor:
        user_id = user["_id"]
        # Update with default password
        await collection.update_one(
            {"_id": user_id},
            {"$set": {"hashed_password": default_pass_hash}}
        )
        print(f"Fixed user {user.get('email', 'Unknown')} (ID: {user_id})")
        fixed_count += 1
        
    print(f"Finished. Fixed {fixed_count} users.")

if __name__ == "__main__":
    asyncio.run(fix_missing_passwords())
