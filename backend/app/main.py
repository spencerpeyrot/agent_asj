from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from enum import Enum, auto
from services.openai_service import OpenAIService, OpenAIServiceError

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

# In-memory session storage
sessions = {}

# Add this function to get the OpenAI service
def get_openai_service():
    if not hasattr(get_openai_service, "_instance"):
        get_openai_service._instance = OpenAIService()
    return get_openai_service._instance

class SpeakerType(str, Enum):
    USER = "user"
    SYSTEM = "system"

class Message(BaseModel):
    speaker: SpeakerType
    timestamp: str
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict] = None

    @field_validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError('Invalid timestamp format. Must be ISO format.')
        return v

    @field_validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty or just whitespace')
        return v.strip()

class Session(BaseModel):
    session_id: str
    created_at: str
    chat_history: List[Message] = []
    newsletter_sections: Dict[str, str] = {}

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

@app.post("/session/start")
def start_session():
    session_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    sessions[session_id] = Session(
        session_id=session_id,
        created_at=created_at
    )
    return {"session_id": session_id}

@app.get("/session/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.post("/message")
def create_message(message: dict):
    session_id = message.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        new_message = Message(
            speaker=message.get("speaker", "user"),
            timestamp=datetime.now().isoformat(),
            content=message.get("content", ""),
            metadata=message.get("metadata")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    session = sessions[session_id]
    session.chat_history.append(new_message)
    
    # For now, just echo back the message
    system_response = Message(
        speaker=SpeakerType.SYSTEM,
        timestamp=datetime.now().isoformat(),
        content=f"Received: {new_message.content}",
        metadata=None
    )
    
    session.chat_history.append(system_response)
    
    return system_response

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)