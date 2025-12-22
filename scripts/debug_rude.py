
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.estudiante_model import EstudianteModel

try:
    print("Testing EstudianteModel with rude=0...")
    model = EstudianteModel(
        rude=0,
        nombres="Test",
        apellidos="User",
        estado="ACTIVO"
    )
    print("Success! EstudianteModel accepted rude=0.")
    print(model)
except Exception as e:
    print(f"Caught expected error: {e}")
