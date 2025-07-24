# backend/app/services/ai_agent.py

import operator
import re
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END, START 
from langchain_core.tools import tool

from app.core.config import settings
from app.crud import hcp as crud_hcp, interaction as crud_interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate, Interaction
from app.schemas.hcp import HPCCreate, HCP
from sqlalchemy.orm import Session
import json
import asyncio
from datetime import datetime

# Add this function to parse the LLM response

def extract_interaction_details(text: str) -> dict:
    """Enhanced field extraction from chat text"""
    details = {
        'attendees': '',
        'topics_discussed': '',
        'materials_shared': '',
        'samples_distributed': '',
        'outcomes': '',
        'follow_up_actions': ''
    }

    # Extract attendees (look for "with X" or "met with X" patterns)
    attendee_match = re.search(r'(?:with|met with)\s([^.,;]+)', text, re.IGNORECASE)
    if attendee_match:
        details['attendees'] = attendee_match.group(1).strip()

    # Extract topics (after "discuss" or "about")
    topic_match = re.search(r'(?:discuss|discussed|about)\s([^.,;]+)', text, re.IGNORECASE)
    if topic_match:
        details['topics_discussed'] = topic_match.group(1).strip()

    # Extract materials (after "shared" or "provided")
    materials_match = re.search(r'(?:shared|provided)\s([^.,;]+)', text, re.IGNORECASE)
    if materials_match:
        details['materials_shared'] = materials_match.group(1).strip()

    # Extract samples (after "distributed" or "gave")
    samples_match = re.search(r'(?:distributed|gave)\s([^.,;]+)', text, re.IGNORECASE)
    if samples_match:
        details['samples_distributed'] = samples_match.group(1).strip()

    # Extract outcomes (after "agreed" or "decided")
    outcomes_match = re.search(r'(?:agreed|decided)\s([^.,;]+)', text, re.IGNORECASE)
    if outcomes_match:
        details['outcomes'] = outcomes_match.group(1).strip()

    # Extract follow-ups (after "follow up" or "next steps")
    followup_match = re.search(r'(?:follow up|next steps)\s([^.,;]+)', text, re.IGNORECASE)
    if followup_match:
        details['follow_up_actions'] = followup_match.group(1).strip()

    return details

# backend/app/services/ai_agent.py

# ... (imports and other functions remain the same) ...

# backend/app/services/ai_agent.py

# ... (imports and other functions remain the same) ...

def parse_interaction_from_response(response_text: str) -> Dict[str, Any]:
    """
    Parses the LLM response (which is now in a structured key-value/bullet point format)
    to extract interaction details.
    Returns a dictionary with all interaction fields.
    """
    parsed_data = {
        'hcp_name': '',
        'interaction_type': 'Meeting',
        'interaction_date': datetime.now().strftime("%Y-%m-%d"),
        'interaction_time': datetime.now().strftime("%H:%M"),
        'attendees': '',
        'topics_discussed': '',
        'materials_shared': '',
        'samples_distributed': '',
        'hcp_sentiment': 'Neutral',
        'outcomes': '',
        'follow_up_actions': ''
    }

    patterns = {
        'hcp_name': r"HCP Name:\s*(.+)",
        'topics_discussed': r"Topics discussed:\s*(.+)",
        'materials_shared': r"Materials shared:\s*(.+)",
        'samples_distributed': r"Samples distributed:\s*(.+)",
        'hcp_sentiment': r"HCP sentiment:\s*(.+)",
        'outcomes': r"Outcomes:\s*(.+)",
        'follow_up_actions': r"Follow-up actions:\s*(.+)"
    }

    for line in response_text.split('\n'):
        line = line.strip()
        if not line:
            continue

        sentiment_match = re.search(patterns['hcp_sentiment'], line, re.IGNORECASE)
        if sentiment_match:
            sentiment_value = sentiment_match.group(1).strip()
            sentiment_value = re.sub(r'^\*+\s*|\s*\*+$', '', sentiment_value).strip() 
            if 'positive' in sentiment_value.lower():
                parsed_data['hcp_sentiment'] = 'Positive'
            elif 'negative' in sentiment_value.lower():
                parsed_data['hcp_sentiment'] = 'Negative'
            elif 'neutral' in sentiment_value.lower():
                parsed_data['hcp_sentiment'] = 'Neutral'
            continue

        for key, pattern in patterns.items():
            if key == 'hcp_sentiment':
                continue

            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                value = re.sub(r'^\*+\s*|\s*\*+$', '', value).strip()

                if value.lower() in ["not mentioned", "n/a", "none", "unknown"]:
                    parsed_data[key] = ''
                else:
                    parsed_data[key] = value
                break 

    if parsed_data['materials_shared'].lower() in ["not mentioned", "n/a", "none", "unknown"]:
        parsed_data['materials_shared'] = ''
    if parsed_data['samples_distributed'].lower() in ["not mentioned", "n/a", "none", "unknown"]:
        parsed_data['samples_distributed'] = ''

    return parsed_data

async def process_chat_input(db: Session, user_message: str):
    try:
        async with asyncio.timeout(30):
            # MODIFIED PROMPT: Emphasize extracting HCP Name consistently
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an AI assistant for logging and editing HCP interactions. "
                           "Your primary goal is to extract specific details from the user's message "
                           "and output them in a structured, concise manner, ideally as key-value pairs. "
                           "**Always prioritize extracting the HCP name if it is mentioned or implied.** " # <-- ADDED EMPHASIS
                           "Extract the following: "
                           "1. HCP name (e.g., 'Dr. Jane Smith')"
                           "2. Topics discussed"
                           "3. Materials shared"
                           "4. Samples distributed"
                           "5. HCP sentiment (Positive, Neutral, Negative)"
                           "6. Outcomes"
                           "7. Follow-up actions"
                           "8. If the user is referring to a specific interaction ID (e.g., 'interaction 123'), extract that too." # <-- ADDED FOR EDITING
                           "If a detail is not present or implies 'none', indicate 'Not mentioned' or leave it blank. "
                           "Example: 'HCP Name: Dr. Emily White. Topics: Product X. Sentiment: Positive. Interaction ID: Not mentioned.'"), # <-- UPDATED EXAMPLE
                ("human", "{user_input}")
            ]).format_prompt(user_input=user_message)

            llm_extraction_response = await llm.ainvoke(extraction_prompt.to_messages())
            
            if not llm_extraction_response.content:
                return {"status": "error", "response": "AI agent could not extract information. Please try rephrasing."}
            
            print(f"DEBUG: LLM Extraction Response Content: {llm_extraction_response.content}")

            interaction_data = parse_interaction_from_response(llm_extraction_response.content)
            
            print(f"DEBUG: Parsed Interaction Data (from LLM output): {interaction_data}")

            # Added a fallback for HCP name from the selected HCP in ChatInterface
            # This is a good way to improve robustness if the LLM doesn't extract it
            # The frontend passes selected_hcp_name in chatData, but the backend doesn't receive it directly here
            # For now, we rely on LLM extraction or user explicitly mentioning it in the prompt.
            # If the HCP name is empty from LLM extraction, it will still error out.
            
            if not interaction_data.get('hcp_name'):
                # Attempt to extract HCP name from original user_message as a last resort
                hcp_from_message_match = re.search(r'(?:Dr\.?\s?\w+\s?\w+)', user_message, re.IGNORECASE)
                if hcp_from_message_match:
                    interaction_data['hcp_name'] = hcp_from_message_match.group(0).strip()
                    print(f"DEBUG: Fallback: Extracted HCP name '{interaction_data['hcp_name']}' from raw user message.")

            if not interaction_data.get('hcp_name'): # Re-check after fallback attempt
                return {"status": "error", "response": "Could not identify HCP name from your input. Please specify the HCP (e.g., 'Dr. John Doe')."}


            summary_prompt = ChatPromptTemplate.from_messages([
                ("system", "Create a concise 1-2 sentence summary of the following interaction:"),
                ("human", user_message)
            ])
            summary_response = await llm.ainvoke(summary_prompt.format_prompt())
            summary = summary_response.content if summary_response.content else user_message[:200]
            
            print(f"DEBUG: Generated Summary: {summary}")

            # Check if an interaction ID was extracted for editing purposes
            # We add a new field 'interaction_id' to `parsed_data` based on LLM output
            extracted_interaction_id = None
            id_match = re.search(r"Interaction ID:\s*(\d+)", llm_extraction_response.content, re.IGNORECASE)
            if id_match:
                try:
                    extracted_interaction_id = int(id_match.group(1))
                    print(f"DEBUG: Extracted Interaction ID for editing: {extracted_interaction_id}")
                except ValueError:
                    pass # Not a valid number

            if extracted_interaction_id:
                # This suggests an edit operation
                # Construct kwargs for edit_internal_interaction from interaction_data
                edit_kwargs = {k: v for k, v in interaction_data.items() if k not in ['hcp_name', 'interaction_type', 'interaction_date', 'interaction_time'] and v}
                
                # If HCP name changed in the prompt, find the new hcp_id
                hcp_to_edit_obj = crud_hcp.get_hcp_by_name(db, interaction_data['hcp_name'])
                if not hcp_to_edit_obj:
                    return {"status": "error", "response": f"HCP '{interaction_data['hcp_name']}' not found for editing interaction. Please create it first."}
                edit_kwargs['hcp_id'] = hcp_to_edit_obj.id

                # Include other potential edits like type, date, time if explicitly extracted
                if interaction_data['interaction_type'] != 'Meeting': # if changed from default
                    edit_kwargs['interaction_type'] = interaction_data['interaction_type']
                if interaction_data['interaction_date'] != datetime.now().strftime("%Y-%m-%d"):
                    edit_kwargs['interaction_date'] = interaction_data['interaction_date']
                if interaction_data['interaction_time'] != datetime.now().strftime("%H:%M"):
                    edit_kwargs['interaction_time'] = interaction_data['interaction_time']

                # Always update summary and raw_text_input for edits from chat
                edit_kwargs['summary'] = summary
                edit_kwargs['raw_text_input'] = user_message

                result = edit_internal_interaction(db, extracted_interaction_id, **edit_kwargs)
                print(f"DEBUG: Result from edit_internal_interaction: {result}") # Debug print
                return {
                    "status": "success",
                    "response": result.get("message", "Interaction updated successfully!"),
                    "interaction_object": result.get("interaction_object")
                }
            else:
                # This suggests a log operation (if no interaction ID for edit)
                result = log_internal_interaction(
                    db=db,
                    hcp_name=interaction_data['hcp_name'],
                    interaction_type=interaction_data['interaction_type'],
                    interaction_date=interaction_data['interaction_date'],
                    interaction_time=interaction_data['interaction_time'],
                    attendees=interaction_data['attendees'],
                    topics_discussed=interaction_data['topics_discussed'],
                    materials_shared=interaction_data['materials_shared'],
                    samples_distributed=interaction_data['samples_distributed'],
                    hcp_sentiment=interaction_data['hcp_sentiment'],
                    outcomes=interaction_data['outcomes'],
                    follow_up_actions=interaction_data['follow_up_actions'],
                    summary=summary,
                    raw_text_input=user_message
                )
                print(f"DEBUG: Result from log_internal_interaction: {result}")
                return {
                    "status": "success",
                    "response": result.get("message", "Interaction logged successfully!"),
                    "interaction_object": result.get("interaction_object")
                }

    except asyncio.TimeoutError:
        return {
            "status": "error",
            "response": "AI processing timed out. Please try again or simplify your request."
        }
    except Exception as e:
        print(f"ERROR: process_chat_input: {e}")
        return {
            "status": "error",
            "response": f"An unexpected error occurred: {str(e)}. Please check backend logs."
        }

# def parse_interaction_from_response(response_text: str) -> Dict[str, Any]:
#     """
#     Parses the LLM response (which is now in a structured key-value/bullet point format)
#     to extract interaction details.
#     Returns a dictionary with all interaction fields.
#     """
#     # Default values - these will be overridden if found in the LLM response
#     parsed_data = {
#         'hcp_name': '',
#         'interaction_type': 'Meeting', # Default interaction type
#         'interaction_date': datetime.now().strftime("%Y-%m-%d"),
#         'interaction_time': datetime.now().strftime("%H:%M"),
#         'attendees': '',
#         'topics_discussed': '',
#         'materials_shared': '',
#         'samples_distributed': '',
#         'hcp_sentiment': 'Neutral', # Default sentiment
#         'outcomes': '',
#         'follow_up_actions': ''
#     }

#     # Regex patterns to extract values from "Key: Value" lines
#     patterns = {
#         'hcp_name': r"HCP Name:\s*(.+)",
#         'topics_discussed': r"Topics discussed:\s*(.+)",
#         'materials_shared': r"Materials shared:\s*(.+)",
#         'samples_distributed': r"Samples distributed:\s*(.+)",
#         'hcp_sentiment': r"HCP sentiment:\s*(.+)",
#         'outcomes': r"Outcomes:\s*(.+)",
#         'follow_up_actions': r"Follow-up actions:\s*(.+)"
#     }

#     # Iterate over each line of the LLM response
#     for line in response_text.split('\n'):
#         line = line.strip()
#         if not line:
#             continue

#         # Check for sentiment first as it has a specific set of values
#         sentiment_match = re.search(patterns['hcp_sentiment'], line, re.IGNORECASE)
#         if sentiment_match:
#             sentiment_value = sentiment_match.group(1).strip()
#             # Normalize sentiment to expected values and clean
#             sentiment_value = re.sub(r'^\*+\s*|\s*\*+$', '', sentiment_value).strip() # Remove leading/trailing **
#             if 'positive' in sentiment_value.lower():
#                 parsed_data['hcp_sentiment'] = 'Positive'
#             elif 'negative' in sentiment_value.lower():
#                 parsed_data['hcp_sentiment'] = 'Negative'
#             elif 'neutral' in sentiment_value.lower():
#                 parsed_data['hcp_sentiment'] = 'Neutral'
#             continue # Move to next line

#         # Extract other fields
#         for key, pattern in patterns.items():
#             if key == 'hcp_sentiment': # Already handled above
#                 continue

#             match = re.search(pattern, line, re.IGNORECASE)
#             if match:
#                 value = match.group(1).strip()
#                 # --- NEW CLEANING STEP ---
#                 # Remove leading/trailing asterisks and extra spaces
#                 value = re.sub(r'^\*+\s*|\s*\*+$', '', value).strip()
#                 # --- END NEW CLEANING STEP ---

#                 # If the LLM explicitly said "Not mentioned", treat as empty
#                 if value.lower() in ["not mentioned", "n/a", "none", "unknown"]:
#                     parsed_data[key] = ''
#                 else:
#                     parsed_data[key] = value
#                 break # Found a match for this line, move to next line in response

#     # Special handling for "materials_shared" and "samples_distributed"
#     # If LLM put 'medicines' under outcomes, ensure it's not misparsed as materials
#     # This is a bit of a heuristic. If 'materials_shared' or 'samples_distributed'
#     # were set to 'Not mentioned', ensure they are truly empty.
#     if parsed_data['materials_shared'].lower() in ["not mentioned", "n/a", "none", "unknown"]:
#         parsed_data['materials_shared'] = ''
#     if parsed_data['samples_distributed'].lower() in ["not mentioned", "n/a", "none", "unknown"]:
#         parsed_data['samples_distributed'] = ''

#     return parsed_data

# # ... (rest of the ai_agent.py file remains the same) ...

# # ... (rest of the ai_agent.py file, including process_chat_input and tool definitions, remains the same) ...

# async def process_chat_input(db: Session, user_message: str):
#     # Initial state for the agent (though for direct LLM call here, agent state might be simplified)
#     # The LangGraph agent structure is more for multi-turn conversations and tool chaining.
#     # For a single request to log interaction, we directly call LLM for extraction and then log.
    
#     try:
#         async with asyncio.timeout(30): # Timeout for the LLM call
#             # Prompt the LLM to extract structured data
#             extraction_prompt = ChatPromptTemplate.from_messages([
#                 ("system", "You are an AI assistant for logging HCP interactions. "
#                            "Your task is to extract specific details from the user's message "
#                            "and output them in a structured, concise manner, ideally as key-value pairs "
#                            "or clear sentences that indicate the values for each field. "
#                            "Extract the following: "
#                            "1. HCP name (e.g., 'Dr. Jane Smith')"
#                            "2. Topics discussed"
#                            "3. Materials shared"
#                            "4. Samples distributed"
#                            "5. HCP sentiment (Positive, Neutral, Negative)"
#                            "6. Outcomes"
#                            "7. Follow-up actions"
#                            "If a detail is not present, indicate it or leave it blank. "
#                            "Example: 'HCP Name: Dr. Emily White. Topics: Product X. Sentiment: Positive.'"),
#                 ("human", "{user_input}")
#             ]).format_prompt(user_input=user_message)

#             llm_extraction_response = await llm.ainvoke(extraction_prompt.to_messages())
            
#             if not llm_extraction_response.content:
#                 # If LLM returns no content, it's an error from the LLM itself
#                 return {"status": "error", "response": "AI agent could not extract information. Please try rephrasing."}
            
#             print(f"DEBUG: LLM Extraction Response Content: {llm_extraction_response.content}") # Debug print

#             # Parse the LLM's raw response into a structured dictionary
#             interaction_data = parse_interaction_from_response(llm_extraction_response.content)
            
#             print(f"DEBUG: Parsed Interaction Data (from LLM output): {interaction_data}") # Debug print

#             # Generate a concise summary from the original user message
#             summary_prompt = ChatPromptTemplate.from_messages([
#                 ("system", "Create a concise 1-2 sentence summary of the following interaction:"),
#                 ("human", user_message)
#             ])
#             summary_response = await llm.ainvoke(summary_prompt.format_prompt())
#             summary = summary_response.content if summary_response.content else user_message[:200]
            
#             print(f"DEBUG: Generated Summary: {summary}") # Debug print

#             # Check if HCP name was extracted (critical for logging)
#             if not interaction_data.get('hcp_name'):
#                 return {"status": "error", "response": "Could not identify HCP name from your input. Please specify the HCP (e.g., 'Dr. John Doe')."}

#             # Log the interaction using the extracted data
#             result = log_internal_interaction(
#                 db=db,
#                 hcp_name=interaction_data['hcp_name'],
#                 interaction_type=interaction_data['interaction_type'],
#                 interaction_date=interaction_data['interaction_date'],
#                 interaction_time=interaction_data['interaction_time'],
#                 attendees=interaction_data['attendees'],
#                 topics_discussed=interaction_data['topics_discussed'],
#                 materials_shared=interaction_data['materials_shared'],
#                 samples_distributed=interaction_data['samples_distributed'],
#                 hcp_sentiment=interaction_data['hcp_sentiment'],
#                 outcomes=interaction_data['outcomes'],
#                 follow_up_actions=interaction_data['follow_up_actions'],
#                 summary=summary,
#                 raw_text_input=user_message # Always store original user input
#             )
            
#             print(f"DEBUG: Result from log_internal_interaction: {result}") # Debug print

#             # Return the success response including the interaction_object
#             if result.get("status") == "success":
#                 return {
#                     "status": "success",
#                     "response": "Interaction logged successfully!",
#                     "interaction_object": result.get("interaction_object")
#                 }
#             else:
#                 # Propagate error from log_internal_interaction
#                 return {"status": "error", "response": result.get("message", "Failed to log interaction.")}

#     except asyncio.TimeoutError:
#         return {
#             "status": "error",
#             "response": "AI processing timed out. Please try again or simplify your request."
#         }
#     except Exception as e:
#         # Catch any other unexpected errors during the process
#         print(f"ERROR: process_chat_input: {e}") # Log the specific error
#         return {
#             "status": "error",
#             "response": f"An unexpected error occurred: {str(e)}. Please check backend logs."
#         }

# --- 1. Define Tools for the LangGraph Agent using @tool decorator ---
# (Rest of the file remains the same)
# ... [No changes from here onwards in the provided original file]

# --- 1. Define Tools for the LangGraph Agent using @tool decorator ---

class CreateHCPInput(BaseModel):
    """Input for creating a new Healthcare Professional (HCP) in the system."""
    name: str = Field(description="The full name of the Healthcare Professional.")
    specialty: Optional[str] = Field(None, description="The medical specialty of the HCP (e.g., 'Cardiology', 'Oncology').")
    contact_info: Optional[str] = Field(None, description="Contact details for the HCP (e.g., email, phone number).")

@tool("create_hcp", args_schema=CreateHCPInput)
def create_hcp_tool_wrapper(name: str, specialty: Optional[str] = None, contact_info: Optional[str] = None):
    """Creates a new Healthcare Professional in the database. (Internal wrapper for agent)"""
    pass


class LogInteractionInput(BaseModel):
    """Input for logging a new interaction with an HCP."""
    hcp_name: str = Field(description="The name of the Healthcare Professional the interaction was with.")
    interaction_type: str = Field(default="Meeting", description="Type of interaction (e.g., 'Meeting', 'Call', 'Email', 'Presentation').")
    interaction_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"), description="Date of the interaction in YYYY-MM-DD format.")
    interaction_time: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M"), description="Time of the interaction in HH:MM format (24-hour).")
    attendees: Optional[str] = Field(None, description="Comma-separated names of other attendees if any (e.g., 'Dr. Smith, Nurse Jane').")
    topics_discussed: str = Field(description="Key topics discussed during the interaction.")
    materials_shared: Optional[str] = Field(None, description="Materials or documents shared with the HCP (e.g., 'Product X brochure', 'Clinical study data').")
    samples_distributed: Optional[str] = Field(None, description="Samples of products distributed (e.g., 'Sample A', 'Sample B').")
    hcp_sentiment: Optional[str] = Field("Neutral", description="Observed or inferred sentiment of the HCP (e.g., 'Positive', 'Neutral', 'Negative').")
    outcomes: Optional[str] = Field(None, description="Key outcomes, agreements, or decisions.")
    follow_up_actions: Optional[str] = Field(None, description="Required follow-up actions (e.g., 'Schedule next meeting', 'Send research paper').")
    summary: Optional[str] = Field(None, description="A concise summary of the interaction, ideally generated by the LLM.")


@tool("log_interaction", args_schema=LogInteractionInput)
def log_interaction_tool_wrapper(hcp_name: str, interaction_type: str = "Meeting", interaction_date: str = None,
                         interaction_time: str = None, attendees: Optional[str] = None,
                         topics_discussed: str = None, materials_shared: Optional[str] = None,
                         samples_distributed: Optional[str] = None, hcp_sentiment: Optional[str] = "Neutral",
                         outcomes: Optional[str] = None, follow_up_actions: Optional[str] = None,
                         summary: Optional[str] = None, raw_text_input: Optional[str] = None):
    """Logs an interaction with an existing Healthcare Professional. (Internal wrapper for agent)"""
    pass


# --- New Tool for Editing Interaction ---
class EditInteractionInput(BaseModel):
    """Input for editing an existing interaction with an HCP."""
    interaction_id: int = Field(description="The ID of the interaction to be edited.")
    hcp_id: Optional[int] = Field(None, description="The ID of the new HCP to link this interaction to, if changing HCP name.")
    interaction_type: Optional[str] = Field(None, description="New type of interaction (e.g., 'Meeting', 'Call').")
    interaction_date: Optional[str] = Field(None, description="New date of the interaction in YYYY-MM-DD format.")
    interaction_time: Optional[str] = Field(None, description="New time of the interaction in HH:MM format (24-hour).")
    attendees: Optional[str] = Field(None, description="Updated comma-separated names of other attendees.")
    topics_discussed: Optional[str] = Field(None, description="Updated key topics discussed during the interaction.")
    materials_shared: Optional[str] = Field(None, description="Updated materials or documents distributed.")
    samples_distributed: Optional[str] = Field(None, description="Updated samples of products distributed.")
    hcp_sentiment: Optional[str] = Field(None, description="Updated observed or inferred sentiment of the HCP ('Positive', 'Neutral', 'Negative').")
    outcomes: Optional[str] = Field(None, description="Key outcomes, agreements, or decisions.")
    follow_up_actions: Optional[str] = Field(None, description="Updated required follow-up actions.")
    summary: Optional[str] = Field(None, description="Updated concise summary of the interaction.")

@tool("edit_interaction", args_schema=EditInteractionInput)
def edit_interaction_tool_wrapper(interaction_id: int, **kwargs):
    """Edits an existing interaction with an HCP. Requires interaction_id and fields to update."""
    pass


# --- NEW TOOL FOR LOOKUP ---
class GetRecentInteractionInput(BaseModel):
    """Input for getting the most recent interaction for a given HCP name."""
    hcp_name: str = Field(description="The name of the Healthcare Professional to look up the most recent interaction for.")

@tool("get_most_recent_interaction_by_hcp_name", args_schema=GetRecentInteractionInput)
def get_most_recent_interaction_by_hcp_name_wrapper(hcp_name: str):
    """Gets the most recent interaction for a given HCP name. Useful for finding interaction IDs when the user provides an HCP name for editing an unverified interaction."""
    pass

# --- NEW TOOL FOR HCP LOOKUP BY NAME (to get new HCP's ID) ---
class GetHcpByNameInput(BaseModel):
    """Input for getting an HCP by their name."""
    name: str = Field(description="The full name of the HCP.")

@tool("get_hcp_by_name", args_schema=GetHcpByNameInput)
def get_hcp_by_name_wrapper(name: str):
    """Gets an HCP's details by their name. Useful for finding an HCP's ID."""
    pass


# --- Helper functions that interact with DB via CRUD ops ---
def create_internal_hcp(db: Session, name: str, specialty: Optional[str] = None, contact_info: Optional[str] = None):
    """Internal function to handle creating HCP with db session and proper return."""
    hcp_data = HPCCreate(name=name, specialty=specialty, contact_info=contact_info)
    try:
        db_hcp = crud_hcp.create_hcp(db, hcp_data)
        return {"status": "success", "message": f"HCP '{db_hcp.name}' created with ID {db_hcp.id}.", "hcp": HCP.from_orm(db_hcp).model_dump()}
    except Exception as e:
        return {"status": "error", "message": f"Failed to create HCP: {str(e)}"}


def log_internal_interaction(
    db: Session,
    hcp_name: str,
    interaction_type: str = "Meeting",
    interaction_date: str = None,
    interaction_time: str = None,
    attendees: str = None,
    topics_discussed: str = None,  # Fixed parameter name
    materials_shared: str = None,
    samples_distributed: str = None,
    hcp_sentiment: str = "Neutral",
    outcomes: str = None,
    follow_up_actions: str = None,
    summary: str = None,
    raw_text_input: str = None
):
    """Fixed function with all expected parameters"""

    hcp = crud_hcp.get_hcp_by_name(db, hcp_name)
    if not hcp:
        return {"status": "error", "message": f"HCP '{hcp_name}' not found"}

    # Handle date/time defaults
    interaction_date = interaction_date or datetime.now().strftime("%Y-%m-%d")
    interaction_time = interaction_time or datetime.now().strftime("%H:%M")

    # Create interaction data with consistent field names
    interaction_data = InteractionCreate( # Use InteractionCreate Pydantic model
        hcp_id=hcp.id,
        interaction_type=interaction_type,
        interaction_date=interaction_date,
        interaction_time=interaction_time,
        attendees=attendees,
        topics_discussed=topics_discussed,
        materials_shared=materials_shared,
        samples_distributed=samples_distributed,
        hcp_sentiment=hcp_sentiment,
        outcomes=outcomes,
        follow_up_actions=follow_up_actions,
        summary=summary,
        raw_text_input=raw_text_input
    )

    try:
        db_interaction = crud_interaction.create_interaction(db, interaction_data)
        return {
            "status": "success",
            "message": f"Interaction logged for {hcp_name}",
            "interaction_object": {
                "id": db_interaction.id,
                "hcp_id": db_interaction.hcp_id,
                "interaction_type": db_interaction.interaction_type,
                "interaction_date": db_interaction.interaction_date.isoformat(),
                "interaction_time": db_interaction.interaction_time,
                "attendees": db_interaction.attendees,
                "topics_discussed": db_interaction.topics_discussed,
                "materials_shared": db_interaction.materials_shared,
                "samples_distributed": db_interaction.samples_distributed,
                "hcp_sentiment": db_interaction.hcp_sentiment,
                "outcomes": db_interaction.outcomes,
                "follow_up_actions": db_interaction.follow_up_actions
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def edit_internal_interaction(db: Session, interaction_id: int, hcp_id: Optional[int] = None, **kwargs): # Added hcp_id as explicit param
    """Internal function to handle editing interaction with db session."""
    if 'hcp_name' in kwargs: # This hcp_name is for context/lookup
        kwargs.pop('hcp_name') 

    if hcp_id is not None:
        kwargs['hcp_id'] = hcp_id # Use the provided hcp_id for the update

    if 'interaction_date' in kwargs and isinstance(kwargs['interaction_date'], str):
        try:
            kwargs['interaction_date'] = datetime.strptime(kwargs['interaction_date'], "%Y-%m-%d")
        except ValueError:
            return {"status": "error", "message": f"Invalid date format for interaction_date: {kwargs['interaction_date']}"}

    interaction_update_data = InteractionUpdate(**kwargs)

    try:
        db_interaction = crud_interaction.update_interaction(db, interaction_id, interaction_update_data)
        if not db_interaction:
            return {"status": "error", "message": f"Interaction with ID {interaction_id} not found."}
        # --- IMPORTANT CHANGE: Return the full interaction_object here ---
        # Ensure datetimes are serialized to strings
        interaction_dict = Interaction.from_orm(db_interaction).model_dump()
        if 'interaction_date' in interaction_dict and isinstance(interaction_dict['interaction_date'], datetime):
            interaction_dict['interaction_date'] = interaction_dict['interaction_date'].isoformat()
        # Add other datetime fields if needed
        return {"status": "success", "message": f"Interaction {db_interaction.id} updated successfully! HCP: {db_interaction.hcp.name if db_interaction.hcp else 'Unknown'}", "interaction_object": interaction_dict}
    except Exception as e:
        return {"status": "error", "message": f"Failed to update interaction {interaction_id}: {str(e)}"}

# --- NEW HELPER FOR LOOKUP TOOL ---
def get_internal_most_recent_interaction_by_hcp_name(db: Session, hcp_name: str):
    """Internal function to handle getting most recent interaction with db session."""
    db_interaction = crud_interaction.get_most_recent_interaction_by_hcp_name(db, hcp_name)
    if not db_interaction:
        return {"status": "error", "message": f"No recent interaction found for HCP '{hcp_name}'."}

    # Convert SQLAlchemy model to Pydantic model for JSON serialization
    interaction_dict = Interaction.from_orm(db_interaction).model_dump()
    if 'interaction_date' in interaction_dict and isinstance(interaction_dict['interaction_date'], datetime):
        interaction_dict['interaction_date'] = interaction_dict['interaction_date'].isoformat()
    return {"status": "success", "message": f"Found interaction {db_interaction.id} for {hcp_name}.", "interaction_object": interaction_dict} # Changed 'interaction' to 'interaction_object' for consistency


# --- NEW HELPER FOR HCP LOOKUP BY NAME ---
def get_internal_hcp_by_name(db: Session, name: str):
    """Internal function to handle getting HCP by name with db session."""
    db_hcp = crud_hcp.get_hcp_by_name(db, name)
    if not db_hcp:
        return {"status": "error", "message": f"HCP '{name}' not found. Please create HCP first."}
    return {"status": "success", "message": f"Found HCP '{db_hcp.name}' with ID {db_hcp.id}.", "hcp_id": db_hcp.id}


# --- This is the dictionary mapping tool names to the actual functions that perform the database ops ---
internal_tool_implementations = {
    "create_hcp": lambda db, **kwargs: create_internal_hcp(db, **kwargs),
    "log_interaction": lambda db, **kwargs: log_internal_interaction(db, **kwargs),
    "edit_interaction": lambda db, **kwargs: edit_internal_interaction(db, **kwargs),
    "get_most_recent_interaction_by_hcp_name": lambda db, **kwargs: get_internal_most_recent_interaction_by_hcp_name(db, **kwargs),
    "get_hcp_by_name": lambda db, **kwargs: get_internal_hcp_by_name(db, **kwargs),
}


# --- 2. Define the Agent State ---

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    db_session: Session
    user_input: str
    found_interaction_id: Optional[int]
    hcp_id_for_edit: Optional[int]
    old_hcp_name_for_correction: Optional[str]
    new_hcp_name_for_correction: Optional[str]


# --- 3. Initialize the LLM and Bind Tools ---

llm = ChatGroq(temperature=0, model_name="gemma2-9b-it", groq_api_key=settings.GROQ_API_KEY)

llm_with_tools = llm.bind_tools([
    create_hcp_tool_wrapper,
    log_interaction_tool_wrapper,
    edit_interaction_tool_wrapper,
    get_most_recent_interaction_by_hcp_name_wrapper,
    get_hcp_by_name_wrapper
])


# --- 4. Define Nodes and Edges for the LangGraph ---

def call_model(state: AgentState):
    messages = state["messages"]
    system_message_content = """You are an AI assistant for a life science field representative.
    Your primary goal is to help log and manage interactions with Healthcare Professionals (HCPs).
    You can perform the following actions:
    1. Log a new interaction: Use the `log_interaction` tool.
    2. Create a new HCP: Use the `create_hcp` tool.
    3. Edit an existing interaction: Use the `edit_interaction` tool.
       - If the user provides an `interaction_id` (e.g., "Edit interaction 123..."), use that directly with `edit_interaction`.
       - **If the user wants to correct an HCP's name in a recent interaction** (e.g., "It should be Dr. Vernika not Dr. Vaniya", "Correct Dr. Smith's last meeting to Dr. Jones"):
          - **Step 1: Get Old Interaction ID**: Call `get_most_recent_interaction_by_hcp_name` using the *incorrect/old* HCP name.
          - **Step 2: Get New HCP ID**: Call `get_hcp_by_name` using the *new/correct* HCP name.
          - **Step 3: Edit Interaction**: Call `edit_interaction` using the `interaction_id` found in Step 1, and the `hcp_id` found in Step 2.

    Always try to extract all necessary information from the user's request. If you need more information (e.g., "Which interaction for Dr. Smith?", "What is the new name?"), askгих specific questions.
    If you log or edit successfully, confirm it to the user.
    """

    updated_messages = []
    # Add state context to messages for the LLM
    if state.get("found_interaction_id") is not None:
        updated_messages.append(AIMessage(content=f"Tool Context: Previous step found interaction ID: {state['found_interaction_id']}"))
    if state.get("hcp_id_for_edit") is not None:
        updated_messages.append(AIMessage(content=f"Tool Context: Previous step found new HCP ID: {state['hcp_id_for_edit']}"))
    if state.get("old_hcp_name_for_correction"):
        updated_messages.append(AIMessage(content=f"Tool Context: Old HCP Name: {state['old_hcp_name_for_correction']}"))
    if state.get("new_hcp_name_for_correction"):
        updated_messages.append(AIMessage(content=f"Tool Context: New HCP Name: {state['new_hcp_name_for_correction']}"))

    # Prepend the system message if not already present or if new system message
    if messages and not (isinstance(messages[0], AIMessage) and messages[0].content == system_message_content):
        updated_messages.append(AIMessage(content=system_message_content))
    updated_messages.extend(messages) # Add original messages last

    response = llm_with_tools.invoke(updated_messages)
    return {"messages": [response]}


def call_tool(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    db_session = state["db_session"]
    user_input = state["user_input"]

    # Initialize state updates that might be passed back
    state_updates = {}

    if last_message.tool_calls:
        tool_outputs = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_name in internal_tool_implementations:
                tool_function_to_call = internal_tool_implementations[tool_name]

                # Special handling for log_interaction summary/raw_text_input
                current_summary = tool_args.get("summary")
                if tool_name == "log_interaction" and not current_summary and user_input:
                    summary_prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are an expert summarizer. Summarize the following interaction details concisely, focusing on key points, discussions, and outcomes. The summary should be suitable for a CRM interaction log."),
                        ("human", user_input)
                    ])
                    summary_response = llm.invoke(summary_prompt)
                    tool_args["summary"] = summary_response.content

                if tool_name == "log_interaction" and "raw_text_input" not in tool_args:
                    tool_args["raw_text_input"] = user_input

                output = tool_function_to_call(db=db_session, **tool_args)
                tool_outputs.append(ToolMessage(content=json.dumps(output), name=tool_call["name"], tool_call_id=tool_call["id"]))

                # --- Handle state updates based on tool outputs for multi-step ops ---
                if tool_name == "get_most_recent_interaction_by_hcp_name" and output.get("status") == "success":
                    found_interaction_data = output.get("interaction_object") # Changed to interaction_object
                    if found_interaction_data and "id" in found_interaction_data:
                        state_updates["found_interaction_id"] = found_interaction_data["id"]
                        state_updates["old_hcp_name_for_correction"] = tool_args.get("hcp_name") # Store the name that was looked up
                        # We also need the new HCP name from the original user input to store for the next step
                        match = re.search(r'should be (Dr\.?\s?\w+)', state["user_input"], re.IGNORECASE)
                        if match:
                            state_updates["new_hcp_name_for_correction"] = match.group(1)

                elif tool_name == "get_hcp_by_name" and output.get("status") == "success":
                    if "hcp_id" in output:
                        state_updates["hcp_id_for_edit"] = output["hcp_id"]

            else:
                tool_outputs.append(ToolMessage(content=f"Tool '{tool_name}' not found or implemented.", name=tool_name, tool_call_id=tool_call["id"]))

        return {"messages": tool_outputs, **state_updates} # Return messages and any state updates
    return {"messages": []}

# Define a custom router after call_tool for multi-step operations
def route_after_tool_call(state: AgentState) -> str:
    messages = state["messages"]
    last_message = messages[-1]

    # Check if the last message is a tool output
    if isinstance(last_message, (FunctionMessage, ToolMessage)):
        try:
            content_dict = json.loads(last_message.content)
            tool_name_from_output = last_message.name # The name of the tool that produced this output

            # --- Multi-step Routing Logic for HCP Name Correction ---
            if tool_name_from_output == "get_most_recent_interaction_by_hcp_name" and content_dict.get("status") == "success":
                # After finding interaction ID, route back to model so it can get new HCP ID or perform the edit
                return "call_model"

            elif tool_name_from_output == "get_hcp_by_name" and content_dict.get("status") == "success":
                # After finding new HCP ID, route back to model to perform edit_interaction
                return "call_model"

            # If any other tool (log, edit) returned a definitive status, or if previous steps are done, end.
            elif content_dict.get("status") in ["success", "error"]:
                return END # End the graph
        except json.JSONDecodeError:
            pass # Malformed JSON, continue to default end

    # Default to ending if tool output doesn't require further action or is malformed
    return END


# Build the graph
workflow = StateGraph(AgentState)

workflow.add_node("call_model", call_model)
workflow.add_node("call_tool", call_tool)

workflow.add_edge(START, "call_model")
workflow.add_conditional_edges(
    "call_model",
    # If model returns tool_calls, go to call_tool. Otherwise, it's a final text response and END.
    # Note: If this directly goes to END without a message, process_chat_input will handle.
    lambda state: "call_tool" if state["messages"][-1].tool_calls else END,
    {"call_tool": "call_tool"},
)
workflow.add_conditional_edges( # New conditional edge after call_tool
    "call_tool",
    route_after_tool_call, # Use the new routing function
    {"call_model": "call_model", END: END} # Define the target nodes
)

# IMPORTANT: Set checkpointer=None for development if not using state persistence
app_agent = workflow.compile(checkpointer=None)