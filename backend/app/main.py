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
    ASSISTANT = "assistant"

class Message(BaseModel):
    speaker: SpeakerType
    timestamp: str
    content: str = Field(..., min_length=1)
    metadata: Optional[Dict] = None
    session_id: str

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
    messages: List[Message] = []

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
async def create_message(message: Message):
    try:
        if message.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[message.session_id]
        
        # Add user message to session
        session.messages.append(message)
        
        # Generate AI response
        try:
            # Format previous messages for context
            previous_messages = [
                {
                    "role": "user" if msg.speaker == SpeakerType.USER else "assistant",
                    "content": msg.content
                }
                for msg in session.messages[-5:]  # Get last 5 messages for context
            ]

            # Call OpenAI service
            openai_service = get_openai_service()
            ai_response = await openai_service.generate_response(
                system_prompt="You are a helpful AI assistant specializing in newsletter creation. Help the user create their newsletter.",
                context={
                    "previous_messages": previous_messages,
                    "current_message": message.content
                }
            )

            # Create AI message
            ai_message = Message(
                session_id=message.session_id,
                speaker=SpeakerType.ASSISTANT,
                content=ai_response,
                timestamp=datetime.now().isoformat(),
                metadata={}
            )

            # Add AI message to session
            session.messages.append(ai_message)
            
            return ai_message

        except OpenAIServiceError as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    except Exception as e:
        print(f"Error in create_message: {str(e)}")  # Add logging
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