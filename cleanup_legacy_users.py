"""
Script para limpiar usuarios de prueba antiguos sin datos completos
Este script elimina usuarios que no tienen los campos nombre, apellido o role
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def cleanup_legacy_users():
    """Eliminar usuarios antiguos sin datos completos"""
    # Conectar a la base de datos
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    collection = db["users"]
    
    # Buscar usuarios sin nombre, apellido o role
    legacy_users = await collection.find({
        "$or": [
            {"nombre": {"$exists": False}},
            {"apellido": {"$exists": False}},
            {"role": {"$exists": False}},
            {"nombre": ""},
            {"apellido": ""},
            {"role": None}
        ]
    }).to_list(length=None)
    
    print(f"\n{'='*60}")
    print(f"USUARIOS ANTIGUOS ENCONTRADOS: {len(legacy_users)}")
    print(f"{'='*60}\n")
    
    if not legacy_users:
        print("✅ No se encontraron usuarios antiguos para eliminar.")
        return
    
    # Mostrar usuarios encontrados
    for i, user in enumerate(legacy_users, 1):
        print(f"{i}. Username: {user.get('username', 'N/A')}")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   Nombre: {user.get('nombre', 'VACÍO')}")
        print(f"   Apellido: {user.get('apellido', 'VACÍO')}")
        print(f"   Role: {user.get('role', 'VACÍO')}")
        print(f"   ID: {user['_id']}")
        print()
    
    # Confirmar eliminación
    print(f"\n{'='*60}")
    confirm = input(f"¿Deseas eliminar estos {len(legacy_users)} usuarios? (si/no): ").strip().lower()
    
    if confirm in ['si', 's', 'yes', 'y']:
        # Eliminar usuarios
        user_ids = [user['_id'] for user in legacy_users]
        result = await collection.delete_many({"_id": {"$in": user_ids}})
        
        print(f"\n✅ Se eliminaron {result.deleted_count} usuarios antiguos.")
        print(f"{'='*60}\n")
    else:
        print("\n❌ Operación cancelada. No se eliminó ningún usuario.")
    
    client.close()

if __name__ == "__main__":
    print("\n🧹 LIMPIEZA DE USUARIOS ANTIGUOS")
    print("Este script eliminará usuarios sin datos completos (nombre, apellido, role)\n")
    asyncio.run(cleanup_legacy_users())
