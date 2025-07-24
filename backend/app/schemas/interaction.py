from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: str = "Meeting"
    interaction_date: datetime = Field(default_factory=datetime.now)
    interaction_time: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M"))
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    hcp_sentiment: Optional[str] = "Neutral" # Positive, Neutral, Negative
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel): # Schema for updating interactions
    interaction_type: Optional[str] = None
    interaction_date: Optional[datetime] = None
    interaction_time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    hcp_sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    summary: Optional[str] = None
    raw_text_input: Optional[str] = None
    hcp_id: Optional[int] = None # Added for HCP name correction flow

class InteractionCreateFromChat(BaseModel):
    raw_text_input: str
    hcp_name: str
    hcp_sentiment: Optional[str] = "Neutral"
    
class Interaction(InteractionBase): # Full Interaction schema for responses
    id: int
    summary: Optional[str] = None
    raw_text_input: Optional[str] = None

    class Config:
        from_attributes = True