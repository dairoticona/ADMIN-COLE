"""
Servicio de Cloudinary para subida de imágenes
"""
import cloudinary
import cloudinary.uploader
from app.core.config import settings

# Configurar Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

async def upload_image(file_bytes: bytes, folder: str = "licencias") -> dict:
    """
    Subir imagen a Cloudinary
    
    Args:
        file_bytes: Bytes de la imagen
        folder: Carpeta en Cloudinary donde guardar
        
    Returns:
        dict con url, public_id y otros datos
    """
    if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
         return {
            "success": False,
            "error": "Cloudinary credentials are not configured. Please check your .env file."
        }

    # DEBUG: Imprimir el Cloud Name para verificar qué está leyendo el sistema
    print(f"DEBUG: Intentando subir a Cloudinary con Cloud Name: '{settings.CLOUDINARY_CLOUD_NAME}'")
        
    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            resource_type="image",
            allowed_formats=["jpg", "jpeg", "png", "pdf"],
            transformation=[
                {"width": 1200, "height": 1200, "crop": "limit"},
                {"quality": "auto:good"}
            ]
        )
        return {
            "success": True,
            "url": result.get("secure_url"),
            "public_id": result.get("public_id"),
            "format": result.get("format"),
            "width": result.get("width"),
            "height": result.get("height")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def delete_image(public_id: str) -> bool:
    """
    Eliminar imagen de Cloudinary
    
    Args:
        public_id: ID público de la imagen
        
    Returns:
        True si se eliminó correctamente
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception:
        return False
