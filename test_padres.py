"""
Script de prueba para verificar el sistema de autenticación y CRUD de Padres
"""
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000/api/padres"

# Variables globales para almacenar datos de prueba
test_padre_id = None
test_token = None

def test_register_padre():
    """Probar registro de padre"""
    print("\n=== Probando registro de padre ===")
    data = {
        "email": "juan.perez@example.com",
        "username": "juanperez",
        "full_name": "Juan Pérez García",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_login_padre(email, password):
    """Probar login de padre"""
    print(f"\n=== Probando login de padre: {email} ===")
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_get_current_padre(token):
    """Probar obtener información del padre actual"""
    print("\n=== Probando obtener padre actual ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_get_all_padres():
    """Probar obtener todos los padres"""
    print("\n=== Probando obtener todos los padres ===")
    response = requests.get(BASE_URL)
    print(f"Status: {response.status_code}")
    print(f"Padres encontrados: {len(response.json())}")
    return response.json()

def test_get_padre(padre_id):
    """Probar obtener un padre específico"""
    print(f"\n=== Probando obtener padre {padre_id} ===")
    response = requests.get(f"{BASE_URL}/{padre_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_update_padre(padre_id):
    """Probar actualización de padre"""
    print(f"\n=== Probando actualización de padre {padre_id} ===")
    data = {
        "full_name": "Juan Pérez García - ACTUALIZADO",
        "username": "juanperez_updated"
    }
    
    response = requests.put(f"{BASE_URL}/{padre_id}", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_delete_padre(padre_id):
    """Probar eliminación de padre"""
    print(f"\n=== Probando eliminación de padre {padre_id} ===")
    response = requests.delete(f"{BASE_URL}/{padre_id}")
    print(f"Status: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("Iniciando pruebas del sistema de Padres...")
    print("Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    print("=" * 60)
    
    try:
        # 1. Registrar un padre
        padre = test_register_padre()
        test_padre_id = padre["_id"]
        
        # 2. Login del padre
        token_response = test_login_padre("juan.perez@example.com", "password123")
        test_token = token_response["access_token"]
        
        # 3. Obtener información del padre actual (usando token)
        test_get_current_padre(test_token)
        
        # 4. Obtener todos los padres
        test_get_all_padres()
        
        # 5. Obtener un padre específico
        test_get_padre(test_padre_id)
        
        # 6. Actualizar el padre
        test_update_padre(test_padre_id)
        
        # 7. Verificar la actualización
        test_get_padre(test_padre_id)
        
        # 8. Eliminar el padre
        test_delete_padre(test_padre_id)
        
        # 9. Verificar que fue eliminado
        print("\n=== Verificando eliminación ===")
        test_get_all_padres()
        
        print("\n" + "=" * 60)
        print("✅ Todas las pruebas completadas exitosamente!")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Error durante las pruebas: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
