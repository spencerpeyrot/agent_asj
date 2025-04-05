from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from enum import Enum, auto
from services.openai_service import OpenAIService, OpenAIServiceError
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

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

# Define the Message model first
class Message(BaseModel):
    session_id: str
    speaker: str
    timestamp: str
    content: str
    metadata: Optional[dict] = {}

# Then define the Session model that uses Message
class Session(BaseModel):
    session_id: str
    created_at: datetime
    messages: List[Message] = []

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
async def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = Session(
        session_id=session_id,
        created_at=datetime.now(),
        messages=[]
    )
    return {"session_id": session_id}

@app.get("/sessions")
async def get_sessions():
    return {
        "sessions": [
            {
                "id": session_id,
                "created_at": session.created_at,
                "message_count": len(session.messages)
            }
            for session_id, session in sessions.items()
        ]
    }

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.post("/message")
async def create_message(message: Message):
    try:
        if message.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add user message to session
        sessions[message.session_id].messages.append(message)
        
        # Generate AI response
        openai_service = get_openai_service()
        previous_messages = [
            {"role": "user" if msg.speaker == "user" else "assistant", "content": msg.content}
            for msg in sessions[message.session_id].messages
        ]
        
        print(f"Sending messages to OpenAI: {previous_messages}")  # Debug log
        
        # Create a context dictionary from the message content
        context = {
            "messages": previous_messages,
            "session_id": message.session_id,
            # Add any other context needed by your OpenAI service
        }
        
        ai_response = await openai_service.generate_response(previous_messages, context)
        
        # Create AI message
        ai_message = Message(
            session_id=message.session_id,
            speaker="assistant",
            timestamp=datetime.now().isoformat(),
            content=ai_response,
            metadata={}
        )
        
        # Add AI message to session
        sessions[message.session_id].messages.append(ai_message)
        
        return ai_message
    
    except HTTPException as he:
        raise he
    except OpenAIServiceError as oe:
        print(f"OpenAI Service Error: {str(oe)}")  # Debug log
        raise HTTPException(status_code=503, detail=str(oe))
    except Exception as e:
        import traceback
        print(f"Unexpected error: {str(e)}")  # Debug log
        print(traceback.format_exc())  # Print full traceback
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

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