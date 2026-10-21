import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

# di Vercel setiap instance function punya pool sendiri, koneksi ke Neon dibuat seminimal mungkin
POOL = {"pool_size": 1, "max_overflow": 2} if os.getenv("VERCEL") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, **POOL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
