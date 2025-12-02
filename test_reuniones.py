"""
Script de prueba para verificar el CRUD de Reuniones
"""
import requests
from datetime import datetime, time

BASE_URL = "http://localhost:8000/api/reuniones"

def test_create_reunion():
    """Probar creación de reunión"""
    print("\n=== Probando creación de reunión ===")
    data = {
        "nombre_reunion": "Reunión de Planificación Q1",
        "tema": "Planificación del primer trimestre 2026",
        "fecha": "2026-01-15T00:00:00",
        "hora_inicio": "09:00:00",
        "hora_conclusion": "11:00:00"
    }
    
    response = requests.post(BASE_URL, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_get_all_reuniones():
    """Probar obtener todas las reuniones"""
    print("\n=== Probando obtener todas las reuniones ===")
    response = requests.get(BASE_URL)
    print(f"Status: {response.status_code}")
    print(f"Reuniones encontradas: {len(response.json())}")
    return response.json()

def test_get_reunion(reunion_id):
    """Probar obtener una reunión específica"""
    print(f"\n=== Probando obtener reunión {reunion_id} ===")
    response = requests.get(f"{BASE_URL}/{reunion_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_update_reunion(reunion_id):
    """Probar actualización de reunión"""
    print(f"\n=== Probando actualización de reunión {reunion_id} ===")
    data = {
        "tema": "Planificación del primer trimestre 2026 - ACTUALIZADO",
        "hora_conclusion": "12:00:00"
    }
    
    response = requests.put(f"{BASE_URL}/{reunion_id}", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()

def test_delete_reunion(reunion_id):
    """Probar eliminación de reunión"""
    print(f"\n=== Probando eliminación de reunión {reunion_id} ===")
    response = requests.delete(f"{BASE_URL}/{reunion_id}")
    print(f"Status: {response.status_code}")

if __name__ == "__main__":
    print("Iniciando pruebas del CRUD de Reuniones...")
    print("Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    
    try:
        # Crear una reunión
        reunion = test_create_reunion()
        reunion_id = reunion["_id"]
        
        # Obtener todas las reuniones
        test_get_all_reuniones()
        
        # Obtener una reunión específica
        test_get_reunion(reunion_id)
        
        # Actualizar la reunión
        test_update_reunion(reunion_id)
        
        # Verificar la actualización
        test_get_reunion(reunion_id)
        
        # Eliminar la reunión
        test_delete_reunion(reunion_id)
        
        # Verificar que fue eliminada
        print("\n=== Verificando eliminación ===")
        test_get_all_reuniones()
        
        print("\n✅ Todas las pruebas completadas exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
