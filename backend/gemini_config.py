import os
import google.generativeai as genai
from crewai import LLM

# Configure Gemini API
def configure_gemini():
    """Configure Gemini API with the provided key"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    genai.configure(api_key=api_key)
    return api_key

# Create Gemini LLM instance for CrewAI
def get_gemini_llm():
    """Get configured Gemini LLM for CrewAI agents"""
    configure_gemini()
    
    # Create LLM instance pointing to Gemini
    return LLM(
        model="gemini-2.0-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=None  # Use default Gemini endpoint
    )

# Test Gemini connection
async def test_gemini_connection():
    """Test if Gemini API is working properly"""
    try:
        configure_gemini()
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_content("Hello, this is a test. Please respond briefly.")
        return {
            "status": "success",
            "message": "Gemini API connection successful",
            "test_response": response.text
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Gemini API connection failed: {str(e)}"
        }

# Model configuration for different use cases
GEMINI_MODELS = {
    "default": "gemini-2.0-flash",
    "analysis": "gemini-2.0-flash",  # For job and resume analysis
    "creative": "gemini-2.0-flash-exp",  # For cover letter and content generation
    "fast": "gemini-2.0-flash"  # For quick operations
}