import asyncio
import httpx
from app.core.config import settings

# URL base de la API (asumiendo que corre en el puerto 8000)
BASE_URL = "http://localhost:8000"

async def verify_padre_access():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Registrar/Login como padre
        username = "test_padre"
        password = "password123"
        
        print(f"1. Intentando login con usuario: {username}...")
        
        # Intentamos login primero
        login_response = await client.post("/api/auth/login", data={
            "username": username,
            "password": password
        })
        
        # Si falla, intentamos registrarlo
        if login_response.status_code != 200:
            print("   Usuario no existe, registrando...")
            reg_response = await client.post("/api/auth/register", json={
                "email": "test_padre@example.com",
                "username": username,
                "nombre": "Test",
                "apellido": "Padre",
                "password": password
            })
            if reg_response.status_code != 201:
                print(f"   Error registrando: {reg_response.text}")
                return
            
            # Login de nuevo
            login_response = await client.post("/api/auth/login", data={
                "username": username,
                "password": password
            })
            
        if login_response.status_code != 200:
            print(f"   Error en login: {login_response.text}")
            return
            
        token = login_response.json()["access_token"]
        print("   Login exitoso! Token obtenido.")
        
        # 2. Intentar acceder a reuniones
        print("\n2. Intentando acceder a /api/reuniones/ con el token del padre...")
        headers = {"Authorization": f"Bearer {token}"}
        
        reuniones_response = await client.get("/api/reuniones/", headers=headers)
        
        if reuniones_response.status_code == 200:
            print("   ✅ ÉXITO: El padre puede ver las reuniones.")
            print(f"   Reuniones encontradas: {len(reuniones_response.json())}")
        else:
            print(f"   ❌ ERROR: Código de estado {reuniones_response.status_code}")
            print(f"   Detalle: {reuniones_response.text}")

if __name__ == "__main__":
    asyncio.run(verify_padre_access())
