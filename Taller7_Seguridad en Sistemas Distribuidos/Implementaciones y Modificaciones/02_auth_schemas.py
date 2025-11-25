from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Base de datos de usuarios simulada
users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"), # Pass: admin123
        "role": "admin"
    }
}
