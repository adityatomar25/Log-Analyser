from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///logs.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Float, index=True)
    level = Column(String(20), index=True)
    message = Column(Text)
    user_id = Column(String(50), index=True, nullable=True)
    service_id = Column(String(50), index=True, nullable=True)
    request_id = Column(String(50), index=True, nullable=True)
    source = Column(String(100), index=True, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)
