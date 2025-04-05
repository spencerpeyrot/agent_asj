from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from enum import Enum, auto
from services.openai_service import OpenAIService, OpenAIServiceError
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session
from . import models, schemas, database
from .database import get_db
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the FastAPI app instance
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Now we can define the sessions dictionary
sessions: Dict[str, Session] = {}

# Add this function to get the OpenAI service
def get_openai_service():
    if not hasattr(get_openai_service, "_instance"):
        get_openai_service._instance = OpenAIService()
    return get_openai_service._instance

class SpeakerType(str, Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"

class SectionType(str, Enum):
    THESIS = "thesis"
    INTRODUCTION = "introduction"
    ACTIONABLE_TRADES = "actionable_trades"
    CONCLUSION = "conclusion"

class NewsletterSection(BaseModel):
    section_type: SectionType
    content: str = Field(..., min_length=1)
    generated_at: str
    metadata: Optional[Dict] = None

    @field_validator('generated_at')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError('Invalid timestamp format. Must be ISO format.')
        return v

# Add new model for section generation request
class SectionGenerationRequest(BaseModel):
    session_id: str
    section_type: SectionType
    context: Dict[str, str]

    @field_validator('context')
    def validate_context(cls, v):
        required_fields = ['topic']
        missing = [field for field in required_fields if field not in v]
        if missing:
            raise ValueError(f"Missing required context fields: {', '.join(missing)}")
        return v

@app.get("/")
def read_root():
    return {"message": "Newsletter Builder API"}

@app.post("/session")
async def create_session(db: Session = Depends(get_db)):
    db_session = models.DBSession()
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return {"session_id": db_session.id}

@app.get("/sessions")
async def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(models.DBSession).order_by(models.DBSession.created_at.desc()).all()
    return {
        "sessions": [
            {
                "id": session.id,
                "created_at": session.created_at,
                "message_count": len(session.messages)
            }
            for session in sessions
        ]
    }

@app.get("/session/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(models.DBSession).filter(models.DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Format messages to be properly returned to frontend
    messages = db.query(models.DBMessage).filter(models.DBMessage.session_id == session_id).all()
    formatted_messages = [
        {
            "id": msg.id,
            "session_id": msg.session_id,
            "speaker": msg.speaker,
            "timestamp": msg.timestamp.isoformat(),
            "content": msg.content,
            "message_metadata": msg.message_metadata
        }
        for msg in messages
    ]
    
    # Return formatted session data
    return {
        "id": session.id,
        "session_id": session.id,
        "created_at": session.created_at.isoformat(),
        "messages": formatted_messages
    }

@app.post("/message")
async def create_message(message: schemas.Message, db: Session = Depends(get_db)):
    try:
        logger.debug(f"Received message request: {message.dict()}")
        
        session = db.query(models.DBSession).filter(models.DBSession.id == message.session_id).first()
        if not session:
            logger.error(f"Session not found: {message.session_id}")
            raise HTTPException(status_code=404, detail="Session not found")

        # Create user message
        logger.debug("Creating user message in database")
        db_message = models.DBMessage(
            session_id=message.session_id,
            speaker=message.speaker,
            content=message.content,
            message_metadata=message.metadata
        )
        db.add(db_message)
        db.commit()
        
        # Get previous messages for context
        previous_messages = [
            {"role": msg.speaker, "content": msg.content}
            for msg in session.messages
        ]
        logger.debug(f"Previous messages context: {previous_messages}")
        
        # Generate AI response
        logger.debug("Calling OpenAI service for response")
        try:
            ai_response = await get_openai_service().generate_response(
                messages=previous_messages,
                context={
                    "session_id": message.session_id,
                    "current_time": datetime.now().isoformat()
                }
            )
            logger.debug(f"Received AI response: {ai_response}")
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error generating AI response: {str(e)}")

        # Create AI message
        logger.debug("Creating AI message in database")
        ai_db_message = models.DBMessage(
            session_id=message.session_id,
            speaker="assistant",
            content=ai_response,
            message_metadata={}
        )
        db.add(ai_db_message)
        db.commit()
        
        # Return a properly serialized response
        return {
            "id": ai_db_message.id,
            "session_id": ai_db_message.session_id,
            "speaker": ai_db_message.speaker,
            "timestamp": ai_db_message.timestamp.isoformat(),
            "content": ai_db_message.content,
            "message_metadata": ai_db_message.message_metadata
        }
    except Exception as e:
        logger.error(f"Unexpected error in create_message: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/section")
async def generate_section(request: SectionGenerationRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[request.session_id]
    
    try:
        # Get OpenAI service instance
        openai_service = get_openai_service()
        
        # Generate content using OpenAI
        content = await openai_service.generate_section_content(
            request.section_type.value,
            request.context
        )
        
        # Create and validate section
        section = NewsletterSection(
            section_type=request.section_type,
            content=content,
            generated_at=datetime.now().isoformat()
        )
        
        # Store in session
        session.newsletter_sections[request.section_type.value] = section.content
        
        return section
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OpenAIServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/openai")
async def check_openai():
    """Check OpenAI API connection"""
    try:
        openai_service = get_openai_service()
        if not openai_service.api_key:
            return {
                "status": "error",
                "message": "OPENAI_API_KEY not set",
                "timestamp": datetime.now().isoformat()
            }
        
        # Test a simple completion
        response = await openai_service.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        # Check if we got a valid response
        if response and response.choices:
            return {
                "status": "healthy",
                "message": "OpenAI API connection successful",
                "response": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "No response from OpenAI API",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)