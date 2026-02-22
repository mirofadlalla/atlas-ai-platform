from sqlalchemy.orm import Session
from app.models import User, tenant
from app.schema.auth_admin import UserCreate
from app.core.auth import password_hash, create_access_token
from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.repositories.tenant_repository import TenantRepository


class TenantService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.tenant_repo = TenantRepository(db)

    def register_tenant(self, tenant_name: str):
        tenant_obj = self.tenant_repo.find_by_name(tenant_name)
        
        if tenant_obj:
            raise HTTPException(
                status_code=400,
                detail="Tenant already exists"
            )
        
        new_tenant = self.tenant_repo.create(tenant_name)
        
        return new_tenant