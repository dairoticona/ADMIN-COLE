"""
Servicio de Cloudinary para subida de imágenes (Deshabilitado)
"""
from app.core.config import settings

# Cloudinary deshabilitado para evitar errores de importación
# import cloudinary
# import cloudinary.uploader

async def upload_image(file_bytes: bytes, folder: str = "licencias") -> dict:
    """
    Subir imagen a Cloudinary (Stub)
    """
    return {
        "success": False,
        "error": "Cloudinary service is disabled because the module is not installed."
    }

async def delete_image(public_id: str) -> bool:
    """
    Eliminar imagen de Cloudinary (Stub)
    """
    return False
