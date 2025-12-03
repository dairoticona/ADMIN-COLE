import asyncio
from app.core.database import connect_to_mongo, get_database

async def fix_admin_role():
    print("Fixing admin user role...")
    await connect_to_mongo()
    db = get_database()
    collection = db["users"]
    
    # Update admin user to have ADMIN role
    result = await collection.update_one(
        {"username": "admin"},
        {"$set": {
            "role": "ADMIN",
            "is_superuser": True
        }}
    )
    
    if result.modified_count > 0:
        print("✓ Admin user role updated to ADMIN")
    else:
        print("No changes needed or user not found")
    
    # Verify the update
    admin_user = await collection.find_one({"username": "admin"})
    if admin_user:
        print(f"Admin user role: {admin_user.get('role')}")
        print(f"Is superuser: {admin_user.get('is_superuser')}")

if __name__ == "__main__":
    asyncio.run(fix_admin_role())
