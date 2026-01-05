import asyncio
from app.core.database import get_database, connect_to_mongo
from bson import ObjectId

async def main():
    print("Connecting to DB...")
    await connect_to_mongo()
    db = get_database()
    collection = db["libretas"]
    
    count = await collection.count_documents({})
    print(f"Total Libretas found: {count}")
    
    cursor = collection.find({})
    async for doc in cursor:
        print(f"ID: {doc.get('_id')} (Type: {type(doc.get('_id'))}) | Estudiante: {doc.get('estudiante_id')} | Estado: {doc.get('estado_documento')}")


if __name__ == "__main__":
    asyncio.run(main())
