from pydantic import BaseModel, EmailStr, Field

# Pydantic models for user authentication and token management
class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    name : str
    tenant_name : str

# Token response model
class Token(BaseModel):
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)