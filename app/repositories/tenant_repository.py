from sqlalchemy.orm import Session
from app.models.tenant import Tenants

class TenantRepository:
    '''
    Docstring for TenantRepository
    
    ''' 
    def __init__(self, db: Session):
        self.db = db
    
    def find_by_name(self, name: str):
        return self.db.query(Tenants).filter(Tenants.name == name).first()
    
    def create(self, name: str):
        tenant = Tenants(name=name ,plan="basic")
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant
    