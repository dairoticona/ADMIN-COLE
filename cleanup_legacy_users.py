import asyncio
from app.core.database import connect_to_mongo, close_mongo_connection, get_database

async def cleanup():
    print("Connecting to DB...")
    await connect_to_mongo()
    db = get_database()
    collection = db["users"]
    
    print("Checking for users without hashed_password...")
    # Find users where hashed_password exists: false or is null or empty
    # MongoDB query for existence
    query = {"hashed_password": {"$exists": False}}
    count = await collection.count_documents(query)
    
    if count > 0:
        print(f"Found {count} invalid users. Deleting...")
        result = await collection.delete_many(query)
        print(f"Deleted {result.deleted_count} users.")
    else:
        print("No invalid users found (missing hashed_password).")
        
    # Also check for empty string just in case
    query_empty = {"hashed_password": ""}
    count_empty = await collection.count_documents(query_empty)
    if count_empty > 0:
        print(f"Found {count_empty} users with empty password. Deleting...")
        result = await collection.delete_many(query_empty)
        print(f"Deleted {result.deleted_count} users.")

    # Check for null
    query_null = {"hashed_password": None}
    count_null = await collection.count_documents(query_null)
    if count_null > 0:
        print(f"Found {count_null} users with NULL password. Deleting...")
        result = await collection.delete_many(query_null)
        print(f"Deleted {result.deleted_count} users.")

    # Backfill missing timestamps
    from datetime import datetime
    print("Backfilling missing timestamps...")
    result_update = await collection.update_many(
        {"created_at": {"$exists": False}},
        {"$set": {"created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}}
    )
    print(f"Updated {result_update.modified_count} users with missing timestamps.")

    await close_mongo_connection()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(cleanup())
