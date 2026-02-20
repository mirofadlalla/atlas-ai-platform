from .base import Base
from sqlalchemy import Column ,DateTime, String , ForeignKey
from .uuid import uuid_pk
from sqlalchemy.orm import relationship
from datetime import datetime

class Users(Base):
    __tablename__ = 'users'
    id  = uuid_pk()
    name  = Column(String , nullable=False)
    tenant_id = Column(String , ForeignKey('tenants.id'))
    email = Column(String , nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")

    tenant = relationship("Tenants", back_populates="users")    