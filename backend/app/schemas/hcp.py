from pydantic import BaseModel
from typing import Optional

class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    contact_info: Optional[str] = None

class HPCCreate(HCPBase):
    pass

class HCP(HCPBase):
    id: int

    class Config:
        from_attributes = True