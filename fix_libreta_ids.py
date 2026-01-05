import asyncio
from app.core.database import get_database, connect_to_mongo
from bson import ObjectId

async def main():
    print("Connecting to DB...")
    await connect_to_mongo()
    db = get_database()
    collection = db["libretas"]
    
    # Find all documents (we'll check type in python since mongo query by type is simpler here)
    cursor = collection.find({})
    
    fixed_count = 0
    async for doc in cursor:
        doc_id = doc["_id"]
        
        if isinstance(doc_id, str):
            print(f"Found bad ID: {doc_id}")
            
            # Create new ID object
            try:
                new_oid = ObjectId(doc_id)
            except Exception:
                print(f"Skipping invalid hex string: {doc_id}")
                continue
                
            # Prepare new doc
            new_doc = doc.copy()
            new_doc["_id"] = new_oid
            
            # Transaction-like approach
            try:
                # 1. Insert new
                await collection.insert_one(new_doc)
                # 2. Delete old
                await collection.delete_one({"_id": doc_id})
                print(f"Fixed document {doc_id} -> {new_oid}")
                fixed_count += 1
            except Exception as e:
                print(f"Error fixing {doc_id}: {e}")

    print(f"Migration complete. Fixed {fixed_count} documents.")

if __name__ == "__main__":
    asyncio.run(main())
