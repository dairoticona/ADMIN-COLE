import asyncio
from app.core.database import connect_to_mongo, get_database

async def fix_users():
    print("Starting database migration...")
    await connect_to_mongo()
    db = get_database()
    collection = db["users"]
    
    users = collection.find({})
    count = 0
    async for user in users:
        update_fields = {}
        
        # Fix Role - Default to PADRE if missing
        if "role" not in user:
            # Si es el super admin brandon, asegurar que sea ADMIN
            if user.get("username") == "brandon":
                update_fields["role"] = "ADMIN"
                update_fields["is_superuser"] = True
            else:
                update_fields["role"] = "PADRE"
            
        # Fix Name - Split full_name if nombre/apellido missing
        if "nombre" not in user or "apellido" not in user:
            full_name = user.get("full_name", "Usuario Desconocido")
            if not full_name:
                full_name = user.get("username", "Usuario")
                
            parts = full_name.split(" ", 1)
            if len(parts) >= 2:
                update_fields["nombre"] = parts[0]
                update_fields["apellido"] = parts[1]
            else:
                update_fields["nombre"] = parts[0]
                update_fields["apellido"] = "."
        
        if update_fields:
            await collection.update_one(
                {"_id": user["_id"]},
                {"$set": update_fields}
            )
            print(f"Updated user: {user.get('username', 'unknown')} -> {update_fields}")
            count += 1
            
    print(f"Migration completed. Updated {count} users.")

if __name__ == "__main__":
    asyncio.run(fix_users())
