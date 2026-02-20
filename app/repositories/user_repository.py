from sqlalchemy.orm import Session
from app.models.user import Users

class UserRepository:
    def __init__(self, db: Session):
        '''
        Docstring for __init__
        
        :param self: Description
        :param db: Description
        :type db: Session
        ''' 
        self.db = db
    
    def find_by_email(self, email: str):
        return self.db.query(Users).filter(Users.email == email).first()
    
    def create(self, name , email: str, password_hash: str, tenant_id: int , role: str = "admin"):
        user = Users(name=name, email=email, hashed_password=password_hash, tenant_id=tenant_id, role=role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    