from sqlalchemy.orm import Session
from app.models.interaction import Interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate # Import InteractionUpdate
from app.crud import hcp as crud_hcp  # Add this import

def get_interaction(db: Session, interaction_id: int):
    return db.query(Interaction).filter(Interaction.id == interaction_id).first()

def get_interactions_by_hcp(db: Session, hcp_id: int, skip: int = 0, limit: int = 100):
    return db.query(Interaction).filter(Interaction.hcp_id == hcp_id).offset(skip).limit(limit).all()

def create_interaction(db: Session, interaction: InteractionCreate, summary: str = None, raw_text_input: str = None):
    db_interaction = Interaction(
        hcp_id=interaction.hcp_id,
        interaction_type=interaction.interaction_type,
        interaction_date=interaction.interaction_date,
        interaction_time=interaction.interaction_time,
        attendees=interaction.attendees,
        topics_discussed=interaction.topics_discussed,
        materials_shared=interaction.materials_shared,
        samples_distributed=interaction.samples_distributed,
        hcp_sentiment=interaction.hcp_sentiment,
        outcomes=interaction.outcomes,
        follow_up_actions=interaction.follow_up_actions,
        summary=summary, # Pass summary
        raw_text_input=raw_text_input # Pass raw_text_input
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

# Add to your CRUD operations
def get_most_recent_interaction_by_hcp_name(db: Session, hcp_name: str):
    hcp = crud_hcp.get_hcp_by_name(db, hcp_name)
    if not hcp:
        return None
    return db.query(Interaction)\
        .filter(Interaction.hcp_id == hcp.id)\
        .order_by(Interaction.interaction_date.desc())\
        .first()

def update_interaction(db: Session, interaction_id: int, interaction_in: InteractionUpdate): # Updated function
    db_interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not db_interaction:
        return None

    # Update only the provided fields
    # Use .dict(exclude_unset=True) for Pydantic v1, or .model_dump(exclude_unset=True) for Pydantic v2
    update_data = interaction_in.model_dump(exclude_unset=True) # Changed from .dict() for Pydantic v2 compatibility
    for field, value in update_data.items():
        setattr(db_interaction, field, value)

    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction