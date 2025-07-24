# backend/app/api/v1/endpoints/interactions.py
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.crud import interaction as crud_interaction, hcp as crud_hcp
from app.schemas.interaction import Interaction, InteractionCreate, InteractionUpdate, InteractionCreateFromChat # Import InteractionUpdate
from app.api.deps import get_db_session
from app.services.ai_agent import process_chat_input
import asyncio

router = APIRouter()

@router.post("/", response_model=Interaction)
def create_interaction(interaction: InteractionCreate, db: Session = Depends(get_db_session)):
    db_hcp = crud_hcp.get_hcp(db, interaction.hcp_id)
    if not db_hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return crud_interaction.create_interaction(db=db, interaction=interaction)

@router.put("/{interaction_id}", response_model=Interaction) # New PUT endpoint
def update_interaction(
    interaction_id: int,
    interaction_in: InteractionUpdate,
    db: Session = Depends(get_db_session)
):
    db_interaction = crud_interaction.update_interaction(db, interaction_id, interaction_in)
    if not db_interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return db_interaction

@router.post("/chat", response_model=Dict[str, Any])
async def create_interaction_from_chat(
    chat_input: InteractionCreateFromChat,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    try:
        response = await process_chat_input(db, chat_input.raw_text_input)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI agent error: {str(e)}")


@router.get("/", response_model=List[Interaction])
def read_interactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    interactions = db.query(Interaction).offset(skip).limit(limit).all()
    return interactions

@router.get("/{interaction_id}", response_model=Interaction)
def read_interaction(interaction_id: int, db: Session = Depends(get_db_session)):
    db_interaction = crud_interaction.get_interaction(db, interaction_id=interaction_id)
    if db_interaction is None:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return db_interaction