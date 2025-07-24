from sqlalchemy.orm import Session
from app.models.hcp import HCP
from app.schemas.hcp import HPCCreate

def get_hcp(db: Session, hcp_id: int):
    return db.query(HCP).filter(HCP.id == hcp_id).first()

def get_hcp_by_name(db: Session, name: str):
    return db.query(HCP).filter(HCP.name == name).first()

def get_hcps(db: Session, skip: int = 0, limit: int = 100):
    return db.query(HCP).offset(skip).limit(limit).all()

def create_hcp(db: Session, hcp: HPCCreate):
    db_hcp = HCP(name=hcp.name, specialty=hcp.specialty, contact_info=hcp.contact_info)
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp