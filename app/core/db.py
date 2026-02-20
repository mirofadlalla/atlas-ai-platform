from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

data_base = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)


Sessions = sessionmaker(
    autoflush=False,
    autocommit=False,

    bind=data_base
)

def get_db():
    db = Sessions()
    try :
        yield db
    finally:
        db.close()