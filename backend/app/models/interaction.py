from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"))
    hcp = relationship("HCP") # Relationship to HCP model

    interaction_type = Column(String(100)) # e.g., Meeting, Call, Email
    interaction_date = Column(DateTime, default=datetime.datetime.now)
    interaction_time = Column(String(50)) # e.g., "19:36"
    attendees = Column(Text, nullable=True) # Comma-separated names or JSON string
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(Text, nullable=True)
    samples_distributed = Column(Text, nullable=True)
    hcp_sentiment = Column(String(50), nullable=True) # Positive, Neutral, Negative
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    summary = Column(String, nullable=True) # AI-generated summary
    raw_text_input = Column(String, nullable=True) # Original text from chat