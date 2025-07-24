from sqlalchemy import Column, Integer, String
from app.core.database import Base

class HCP(Base):
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    specialty = Column(String(255), nullable=True)
    contact_info = Column(String(255), nullable=True)