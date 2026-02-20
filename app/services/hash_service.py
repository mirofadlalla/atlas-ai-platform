from passlib.context import CryptContext
import os


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Utility functions for password hashing and token creation/verification
def password_hash(password : str) -> str :
    return pwd_context.hash(password)

# Verify the password against the hashed password
def verify_password(plain_password : str, hashed_password : str) -> bool :
    return pwd_context.verify(plain_password, hashed_password)
