from openai import AsyncOpenAI, OpenAIError
from typing import Optional, Dict, List, Any
import os
from datetime import datetime
from templates.prompts import PROMPT_TEMPLATES
from dotenv import load_dotenv
import logging
from fastapi import HTTPException

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors"""
    pass

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIServiceError("OPENAI_API_KEY not found in environment variables")
        
        logger.debug("Initializing AsyncOpenAI client")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_section_content(
        self,
        section_type: str,
        context: Dict[str, str]
    ) -> str:
        """
        Generate content for a newsletter section using OpenAI.
        
        Args:
            section_type: Type of section to generate
            context: Dictionary containing context variables for the prompt
        
        Returns:
            Generated content as a string
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Validate section type first
        template = PROMPT_TEMPLATES.get(section_type)
        if not template:
            raise ValueError(f"No template found for section type: {section_type}")

        # Validate context
        try:
            prompt = template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing required context key: {str(e)}")

        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "You are a professional financial newsletter writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()

        except OpenAIError as e:
            raise OpenAIServiceError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise OpenAIServiceError(f"Unexpected error: {str(e)}")

    async def generate_response(self, messages, context=None):
        try:
            # This model may need to be updated if gpt-4o-mini isn't working
            model = "gpt-4o-mini" # Try this instead of gpt-4o-mini-2024-07-18
            
            system_prompt = """You are a helpful AI assistant that provides clear, step-by-step guidance for writing newsletters and other content. 
            For each response:
            1. First, acknowledge the user's request
            2. Break down the task into clear, numbered steps
            3. For each step, provide specific guidance and examples
            4. End with a question to check if they need clarification or are ready to proceed
            
            When writing newsletters:
            - Use engaging, professional language
            - Include data-driven insights
            - Maintain a clear narrative structure
            - End with actionable takeaways
            
            Format your response in Markdown, using:
            - Numbered lists for steps
            - Bold for important terms
            - Code blocks for specific examples
            - Bullet points for key details
            """

            # Convert message format
            formatted_messages = []
            formatted_messages.append({"role": "system", "content": system_prompt})
            
            # Debug log to see the structure
            logger.debug(f"Message structure: {messages[0] if messages else 'No messages'}")
            
            # Handle different possible message formats
            for msg in messages:
                if isinstance(msg, dict):
                    if "role" in msg and "content" in msg:
                        # Already in correct format
                        formatted_messages.append(msg)
                    elif "speaker" in msg and "content" in msg:
                        # Convert from speaker format to role format
                        role = msg["speaker"]
                        # Map custom speaker types to OpenAI role types if needed
                        if role == "assistant" or role == "user" or role == "system":
                            formatted_messages.append({"role": role, "content": msg["content"]})
                        else:
                            # Default unknown speakers to user
                            formatted_messages.append({"role": "user", "content": msg["content"]})
                elif hasattr(msg, 'speaker') and hasattr(msg, 'content'):
                    # Handle object with attributes
                    role = msg.speaker
                    if role == "assistant" or role == "user" or role == "system":
                        formatted_messages.append({"role": role, "content": msg.content})
                    else:
                        formatted_messages.append({"role": "user", "content": msg.content})

            if context:
                # Add context as a system message if provided
                formatted_messages.insert(1, {
                    "role": "system",
                    "content": f"Additional context: {context}"
                })

            # Log the final formatted messages
            logger.debug(f"Sending formatted messages to OpenAI: {formatted_messages}")

            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=formatted_messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                # Log the response for debugging
                response_text = response.choices[0].message.content
                logger.debug(f"Received response from OpenAI: {response_text[:100]}...")
                
                return response_text
                
            except Exception as api_err:
                logger.error(f"Error from OpenAI API: {str(api_err)}")
                # Try with a fallback model
                logger.info("Trying fallback model gpt-3.5-turbo")
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=formatted_messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                response_text = response.choices[0].message.content
                logger.debug(f"Received response from fallback model: {response_text[:100]}...")
                
                return response_text

        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate response: {str(e)}"
            ) 