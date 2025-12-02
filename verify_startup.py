from fastapi import FastAPI
from app.api.auth_router import router
import sys

try:
    print("Attempting to import FastAPI app...")
    app = FastAPI()
    app.include_router(router)
    print("SUCCESS: FastAPI app initialized and router included.")
except Exception as e:
    print(f"FAILURE: {e}")
    sys.exit(1)
