from typing import List, Optional
from bson import ObjectId
from app.core.database import get_database
from app.models.notificacion_model import NotificacionModel
from datetime import datetime


class CRUDNotificacion:
    """CRUD operations for notifications"""

    async def create(self, db, notificacion_data: dict) -> dict:
        """Create a new notification"""
        collection = db["notificaciones"]
        
        # Add timestamps
        notificacion_data["created_at"] = datetime.utcnow()
        notificacion_data["updated_at"] = datetime.utcnow()
        notificacion_data["is_read"] = False
        
        result = await collection.insert_one(notificacion_data)
        notificacion_data["_id"] = result.inserted_id
        
        return notificacion_data

    async def create_many(self, db, notificaciones_data: List[dict]) -> List[dict]:
        """Create multiple notifications at once"""
        collection = db["notificaciones"]
        
        # Add timestamps to all notifications
        for notif in notificaciones_data:
            notif["created_at"] = datetime.utcnow()
            notif["updated_at"] = datetime.utcnow()
            notif["is_read"] = False
        
        result = await collection.insert_many(notificaciones_data)
        
        # Add inserted IDs to the data
        for i, inserted_id in enumerate(result.inserted_ids):
            notificaciones_data[i]["_id"] = inserted_id
        
        return notificaciones_data

    async def get_by_user(
        self, 
        db, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 50,
        is_read: Optional[bool] = None
    ) -> List[dict]:
        """Get all notifications for a specific user"""
        collection = db["notificaciones"]
        
        query = {"user_id": ObjectId(user_id)}
        if is_read is not None:
            query["is_read"] = is_read
        
        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        
        notifications = []
        async for notif in cursor:
            notif["_id"] = str(notif["_id"])
            notif["user_id"] = str(notif["user_id"])
            if notif.get("related_id"):
                notif["related_id"] = str(notif["related_id"])
            notifications.append(notif)
        
        return notifications

    async def get_by_id(self, db, notificacion_id: str) -> Optional[dict]:
        """Get a specific notification by ID"""
        collection = db["notificaciones"]
        
        notif = await collection.find_one({"_id": ObjectId(notificacion_id)})
        
        if notif:
            notif["_id"] = str(notif["_id"])
            notif["user_id"] = str(notif["user_id"])
            if notif.get("related_id"):
                notif["related_id"] = str(notif["related_id"])
        
        return notif

    async def mark_as_read(self, db, notificacion_id: str) -> bool:
        """Mark a notification as read"""
        collection = db["notificaciones"]
        
        result = await collection.update_one(
            {"_id": ObjectId(notificacion_id)},
            {"$set": {"is_read": True, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0

    async def mark_all_as_read(self, db, user_id: str) -> int:
        """Mark all notifications for a user as read"""
        collection = db["notificaciones"]
        
        result = await collection.update_many(
            {"user_id": ObjectId(user_id), "is_read": False},
            {"$set": {"is_read": True, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count

    async def delete(self, db, notificacion_id: str) -> bool:
        """Delete a notification"""
        collection = db["notificaciones"]
        
        result = await collection.delete_one({"_id": ObjectId(notificacion_id)})
        
        return result.deleted_count > 0

    async def count_unread(self, db, user_id: str) -> int:
        """Count unread notifications for a user"""
        collection = db["notificaciones"]
        
        count = await collection.count_documents({
            "user_id": ObjectId(user_id),
            "is_read": False
        })
        
        return count


# Create a singleton instance
notificacion = CRUDNotificacion()
