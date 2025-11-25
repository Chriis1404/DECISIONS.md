from fastapi import Depends, Security
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from datetime import datetime, timedelta
import os
import jwt 
from passlib.context import CryptContext 

# --- CONFIGURACIÓN DE SEGURIDAD (JWT) ---
SECRET_KEY = os.getenv("JWT_SECRET", "mi_super_clave_secreta_ecomarket_2025") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Contexto para encriptar contraseñas (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticación (apunta al endpoint /login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
