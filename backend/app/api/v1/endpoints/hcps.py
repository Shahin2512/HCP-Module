from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.crud import hcp as crud_hcp
from app.schemas.hcp import HCP, HPCCreate
from app.api.deps import get_db_session

router = APIRouter()

@router.post("/", response_model=HCP)
def create_hcp(hcp: HPCCreate, db: Session = Depends(get_db_session)):
    db_hcp = crud_hcp.get_hcp_by_name(db, name=hcp.name)
    if db_hcp:
        raise HTTPException(status_code=400, detail="HCP with this name already registered")
    return crud_hcp.create_hcp(db=db, hcp=hcp)

@router.get("/", response_model=List[HCP])
def read_hcps(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    hcps = crud_hcp.get_hcps(db, skip=skip, limit=limit)
    return hcps

@router.get("/{hcp_id}", response_model=HCP)
def read_hcp(hcp_id: int, db: Session = Depends(get_db_session)):
    db_hcp = crud_hcp.get_hcp(db, hcp_id=hcp_id)
    if db_hcp is None:
        raise HTTPException(status_code=404, detail="HCP not found")
    return db_hcp