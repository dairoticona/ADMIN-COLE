from typing import Any, Dict, Optional, Union
from app.crud.base import CRUDBase
from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreate, UserUpdate

class CRUDUser(CRUDBase[UserModel, UserCreate, UserUpdate]):
    async def get_by_email(self, db: Any, *, email: str) -> Optional[UserModel]:
        collection = db[self.collection_name]
        doc = await collection.find_one({"email": email})
        if doc:
            return self.model(**doc)
        return None

    # Override create to handle password hashing if needed, or keep simple for now 
    # and handle hashing in service/route. 
    # For now, keeping generic, assuming hashing happens before calling create or inside simple create if we add logic here.
    # But usually better to keep CRUD simple dumb DB access.
    
user = CRUDUser(UserModel, "users")
