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

# Updated detailed system prompt for newsletter creation
NEWSLETTER_SYSTEM_PROMPT = """
You are a professional financial newsletter writer. The newsletter creation process occurs in multiple, interactive steps. For each step, output the content following the exact format provided and then end with the question: "Are there any edits you'd like or can we continue to the next section?" This ensures a step-by-step, interactive process.

1. **Thesis & Overview**:
   - Write a thesis statement and a high-level overview for a financial newsletter about a given topic.
   - The overview should include only the headers for each section (no bullet points).
   - At the end, ask: "Are there any edits you'd like or can we continue to the next section (Intro)?"

2. **Intro Section**:
   - Use the format:
     ***Intro Section***
     <Header text>
     - 3-4 bullet points opening the story (integrate agent outputs if available).
   - End with: "Are there any edits you'd like or can we continue to the next section?"

3. **Body Sections (Non-Intro/Conclusion)**:
   - Use the format:
     ***Section Title***
     <Header text>
     <Intro sentence>
     - 3-4 bullet points building the case (integrate agent outputs).
     <Conclusion/transition sentence>
   - End with: "Are there any edits you'd like or can we continue to the next section?"

4. **Actionable Trades Section**:
   - Use the format:
     ***Section Title***
     <Header text>
     <Intro sentence>
     - Provide three separate creative segments (one for each trade) without numbering or a header for each; just leave a creative space for each trade.
     <Conclusion sentence>
   - End with: "Are there any edits you'd like or can we continue to the next section?"

5. **Conclusion Section**:
   - Use the format:
     ***Conclusion Section***
     <Header text>
     - 4-5 bullet points that encapsulate the thesis and wrap up the newsletter (avoid simple repetition).
     <CTA that ties into the newsletter topic and intelligently encourages readers to try the platform>
   - End with: "Are there any edits you'd like or can we continue to the next section?"

When integrating additional agent outputs provided by the user, seamlessly incorporate them into the draft and clearly indicate which parts should be used as screenshots. Always adhere strictly to the specified formatting.
"""

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
            section_type: Type of section to generate (e.g. "thesis_overview", "introduction", "body_section", "actionable_trades", "conclusion")
            context: Dictionary containing context variables for the prompt
        
        Returns:
            Generated content as a string
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        # Retrieve the appropriate template
        template = PROMPT_TEMPLATES.get(section_type)
        if not template:
            raise ValueError(f"No template found for section type: {section_type}")

        # Format the prompt with the provided context
        try:
            prompt = template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing required context key: {str(e)}")

        try:
            # Call OpenAI API with the detailed newsletter system prompt
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": NEWSLETTER_SYSTEM_PROMPT},
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
            model = "gpt-4o-mini"  # Primary model
            system_prompt = NEWSLETTER_SYSTEM_PROMPT

            # Prepare message history
            formatted_messages = []
            formatted_messages.append({"role": "system", "content": system_prompt})
            
            logger.debug(f"Message structure: {messages[0] if messages else 'No messages'}")
            
            for msg in messages:
                if isinstance(msg, dict):
                    if "role" in msg and "content" in msg:
                        formatted_messages.append(msg)
                    elif "speaker" in msg and "content" in msg:
                        role = msg["speaker"]
                        if role in ["assistant", "user", "system"]:
                            formatted_messages.append({"role": role, "content": msg["content"]})
                        else:
                            formatted_messages.append({"role": "user", "content": msg["content"]})
                elif hasattr(msg, 'speaker') and hasattr(msg, 'content'):
                    role = msg.speaker
                    if role in ["assistant", "user", "system"]:
                        formatted_messages.append({"role": role, "content": msg.content})
                    else:
                        formatted_messages.append({"role": "user", "content": msg.content})

            if context:
                formatted_messages.insert(1, {
                    "role": "system",
                    "content": f"Additional context: {context}"
                })

            logger.debug(f"Sending formatted messages to OpenAI: {formatted_messages}")

            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=formatted_messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                response_text = response.choices[0].message.content
                logger.debug(f"Received response from OpenAI: {response_text[:100]}...")
                return response_text
                
            except Exception as api_err:
                logger.error(f"Error from OpenAI API: {str(api_err)}")
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