from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from fastapi.encoders import jsonable_encoder

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType], collection_name: str):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A Pydantic model (schema) class
        * `collection_name`: MongoDB collection name
        """
        self.model = model
        self.collection_name = collection_name

    async def get(self, db: Any, id: Any) -> Optional[ModelType]:
        collection: AsyncIOMotorCollection = db[self.collection_name]
        try:
            oid = ObjectId(id)
        except Exception:
            return None
            
        doc = await collection.find_one({"_id": oid})
        if doc:
            return self.model(**doc)
        return None

    async def get_multi(
        self, db: Any, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        collection: AsyncIOMotorCollection = db[self.collection_name]
        cursor = collection.find().skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            results.append(self.model(**doc))
        return results

    async def create(self, db: Any, *, obj_in: CreateSchemaType) -> ModelType:
        collection: AsyncIOMotorCollection = db[self.collection_name]
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = await collection.insert_one(obj_in_data)
        
        # Fetch the created object
        created_doc = await collection.find_one({"_id": db_obj.inserted_id})
        return self.model(**created_doc)

    async def update(
        self,
        db: Any,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        collection: AsyncIOMotorCollection = db[self.collection_name]
        
        # Prepare update data
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # Update logic: only update fields that are present in update_data
        # Note: In a real app we might want to be careful about what we update
        
        # Create $set dict
        set_data = {k: v for k, v in update_data.items() if k in obj_data}
        if not set_data:
            return db_obj # Nothing to update
            
        await collection.update_one(
            {"_id": ObjectId(db_obj.id)},
            {"$set": set_data}
        )
        
        # Fetch updated
        updated_doc = await collection.find_one({"_id": ObjectId(db_obj.id)})
        return self.model(**updated_doc)

    async def remove(self, db: Any, *, id: str) -> Optional[ModelType]:
        collection: AsyncIOMotorCollection = db[self.collection_name]
        try:
            oid = ObjectId(id)
        except Exception:
            return None
            
        doc = await collection.find_one({"_id": oid})
        if not doc:
            return None
            
        await collection.delete_one({"_id": oid})
        return self.model(**doc)
