"""
Script de prueba para verificar el sistema de autenticación y CRUD de Usuarios Admin
"""
import requests

BASE_URL = "http://localhost:8000/api/auth"

def test_register_user():
    """Probar registro de usuario"""
    print("\n=== Probando registro de usuario ===")
    data = {
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Administrador Principal",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_login_user(email, password):
    """Probar login de usuario"""
    print(f"\n=== Probando login de usuario: {email} ===")
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_get_current_user(token):
    """Probar obtener información del usuario actual"""
    print("\n=== Probando obtener usuario actual ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_get_all_users():
    """Probar obtener todos los usuarios"""
    print("\n=== Probando obtener todos los usuarios ===")
    response = requests.get(BASE_URL)
    print(f"Status: {response.status_code}")
    print(f"Usuarios encontrados: {len(response.json())}")
    return response.json()

def test_get_user(user_id):
    """Probar obtener un usuario específico"""
    print(f"\n=== Probando obtener usuario {user_id} ===")
    response = requests.get(f"{BASE_URL}/{user_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_update_user(user_id):
    """Probar actualización de usuario"""
    print(f"\n=== Probando actualización de usuario {user_id} ===")
    data = {
        "email": "admin@example.com",
        "username": "admin_updated",
        "full_name": "Administrador Principal - ACTUALIZADO",
        "password": "admin123"
    }
    
    response = requests.put(f"{BASE_URL}/{user_id}", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_delete_user(user_id):
    """Probar eliminación de usuario"""
    print(f"\n=== Probando eliminación de usuario {user_id} ===")
    response = requests.delete(f"{BASE_URL}/{user_id}")
    print(f"Status: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("Iniciando pruebas del sistema de Usuarios Admin...")
    print("Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    print("=" * 60)
    
    try:
        # 1. Registrar un usuario
        user = test_register_user()
        test_user_id = user["_id"]
        
        # 2. Login del usuario
        token_response = test_login_user("admin@example.com", "admin123")
        test_token = token_response["access_token"]
        
        # 3. Obtener información del usuario actual (usando token)
        test_get_current_user(test_token)
        
        # 4. Obtener todos los usuarios
        test_get_all_users()
        
        # 5. Obtener un usuario específico
        test_get_user(test_user_id)
        
        # 6. Actualizar el usuario
        test_update_user(test_user_id)
        
        # 7. Verificar la actualización
        test_get_user(test_user_id)
        
        # 8. Eliminar el usuario
        test_delete_user(test_user_id)
        
        # 9. Verificar que fue eliminado
        print("\n=== Verificando eliminación ===")
        test_get_all_users()
        
        print("\n" + "=" * 60)
        print("✅ Todas las pruebas completadas exitosamente!")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Error durante las pruebas: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
