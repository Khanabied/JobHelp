import google.generativeai as genai
from typing import List, Dict, Any, Optional
import os
import json
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class GeminiAIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables - AI features will be disabled")
            self.model = None
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {str(e)}")
            self.model = None
    
    async def optimize_resume(self, resume_data: Dict[str, Any], job_description: Optional[str] = None) -> Dict[str, Any]:
        """Optimize resume based on job description and best practices."""
        try:
            prompt = self._create_resume_optimization_prompt(resume_data, job_description)
            
            response = self.model.generate_content(prompt)
            result = self._parse_ai_response(response.text)
            
            return {
                "optimized_content": result.get("optimized_content", ""),
                "suggestions": result.get("suggestions", []),
                "score": result.get("score", 0),
                "keywords_added": result.get("keywords_added", [])
            }
        except Exception as e:
            logger.error(f"Error optimizing resume: {str(e)}")
            return {
                "optimized_content": "",
                "suggestions": ["Error occurred during optimization"],
                "score": 0,
                "keywords_added": []
            }
    
    async def generate_cover_letter(self, job_title: str, company_name: str, 
                                  job_description: str, resume_data: Dict[str, Any], 
                                  additional_notes: Optional[str] = None) -> Dict[str, Any]:
        """Generate personalized cover letter."""
        try:
            prompt = self._create_cover_letter_prompt(
                job_title, company_name, job_description, resume_data, additional_notes
            )
            
            response = self.model.generate_content(prompt)
            result = self._parse_ai_response(response.text)
            
            return {
                "cover_letter": result.get("cover_letter", ""),
                "key_points": result.get("key_points", []),
                "personalization_score": result.get("personalization_score", 0)
            }
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}")
            return {
                "cover_letter": "Error occurred during generation",
                "key_points": [],
                "personalization_score": 0
            }
    
    async def optimize_linkedin_profile(self, current_profile: Dict[str, Any], 
                                      target_industry: Optional[str] = None) -> Dict[str, Any]:
        """Optimize LinkedIn profile for better visibility."""
        try:
            prompt = self._create_linkedin_optimization_prompt(current_profile, target_industry)
            
            response = self.model.generate_content(prompt)
            result = self._parse_ai_response(response.text)
            
            return {
                "optimized_headline": result.get("optimized_headline", ""),
                "optimized_summary": result.get("optimized_summary", ""),
                "suggested_skills": result.get("suggested_skills", []),
                "optimization_tips": result.get("optimization_tips", [])
            }
        except Exception as e:
            logger.error(f"Error optimizing LinkedIn profile: {str(e)}")
            return {
                "optimized_headline": "",
                "optimized_summary": "",
                "suggested_skills": [],
                "optimization_tips": ["Error occurred during optimization"]
            }
    
    async def generate_interview_questions(self, job_title: str, company_name: str, 
                                         job_description: str, experience_level: str,
                                         interview_type: str) -> Dict[str, Any]:
        """Generate interview questions and preparation materials."""
        try:
            prompt = self._create_interview_prep_prompt(
                job_title, company_name, job_description, experience_level, interview_type
            )
            
            response = self.model.generate_content(prompt)
            result = self._parse_ai_response(response.text)
            
            return {
                "questions": result.get("questions", []),
                "sample_answers": result.get("sample_answers", []),
                "preparation_tips": result.get("preparation_tips", []),
                "company_research_points": result.get("company_research_points", [])
            }
        except Exception as e:
            logger.error(f"Error generating interview questions: {str(e)}")
            return {
                "questions": [],
                "sample_answers": [],
                "preparation_tips": ["Error occurred during generation"],
                "company_research_points": []
            }
    
    def _create_resume_optimization_prompt(self, resume_data: Dict[str, Any], job_description: Optional[str]) -> str:
        """Create prompt for resume optimization."""
        base_prompt = f"""
        As an expert career counselor and ATS specialist, optimize this resume for maximum impact.
        
        Current Resume Data:
        {json.dumps(resume_data, indent=2)}
        
        Job Description (if provided):
        {job_description or "No specific job description provided"}
        
        Please provide optimization suggestions in this JSON format:
        {{
            "optimized_content": "Improved resume content with better formatting and keywords",
            "suggestions": ["List of specific improvement suggestions"],
            "score": 85,
            "keywords_added": ["keyword1", "keyword2"]
        }}
        
        Focus on:
        1. ATS optimization with relevant keywords
        2. Impact-driven bullet points with quantifiable achievements
        3. Professional formatting and structure
        4. Skills alignment with job requirements
        5. Action verbs and power words
        """
        return base_prompt
    
    def _create_cover_letter_prompt(self, job_title: str, company_name: str, 
                                  job_description: str, resume_data: Dict[str, Any],
                                  additional_notes: Optional[str]) -> str:
        """Create prompt for cover letter generation."""
        prompt = f"""
        As an expert career writer, create a compelling cover letter for this job application.
        
        Job Details:
        - Position: {job_title}
        - Company: {company_name}
        - Job Description: {job_description}
        
        Candidate Resume Data:
        {json.dumps(resume_data, indent=2)}
        
        Additional Notes:
        {additional_notes or "None provided"}
        
        Please provide the response in this JSON format:
        {{
            "cover_letter": "Complete cover letter text",
            "key_points": ["List of key selling points highlighted"],
            "personalization_score": 90
        }}
        
        Requirements:
        1. Professional tone and structure
        2. Personalize for the specific company and role
        3. Highlight relevant experience and achievements
        4. Show enthusiasm and cultural fit
        5. Strong opening and closing
        6. Keep to 300-400 words
        """
        return prompt
    
    def _create_linkedin_optimization_prompt(self, current_profile: Dict[str, Any], 
                                           target_industry: Optional[str]) -> str:
        """Create prompt for LinkedIn optimization."""
        prompt = f"""
        As a LinkedIn optimization expert, improve this profile for better visibility and engagement.
        
        Current Profile:
        {json.dumps(current_profile, indent=2)}
        
        Target Industry: {target_industry or "General optimization"}
        
        Please provide optimization suggestions in this JSON format:
        {{
            "optimized_headline": "Improved headline with keywords",
            "optimized_summary": "Enhanced summary section",
            "suggested_skills": ["skill1", "skill2", "skill3"],
            "optimization_tips": ["List of actionable tips"]
        }}
        
        Focus on:
        1. Keyword optimization for searchability
        2. Compelling headline that stands out
        3. Professional summary that tells a story
        4. Skills alignment with industry standards
        5. Content that encourages engagement
        """
        return prompt
    
    def _create_interview_prep_prompt(self, job_title: str, company_name: str, 
                                    job_description: str, experience_level: str,
                                    interview_type: str) -> str:
        """Create prompt for interview preparation."""
        prompt = f"""
        As an expert interview coach, create comprehensive interview preparation materials.
        
        Interview Details:
        - Position: {job_title}
        - Company: {company_name}
        - Experience Level: {experience_level}
        - Interview Type: {interview_type}
        - Job Description: {job_description}
        
        Please provide preparation materials in this JSON format:
        {{
            "questions": ["List of likely interview questions"],
            "sample_answers": ["Sample answers with STAR method where applicable"],
            "preparation_tips": ["Specific preparation advice"],
            "company_research_points": ["Key points to research about the company"]
        }}
        
        Include:
        1. Role-specific questions based on job description
        2. Behavioral questions with STAR method guidance
        3. Technical questions if applicable
        4. Company culture and values alignment questions
        5. Questions the candidate should ask the interviewer
        """
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and extract JSON data."""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, return the raw response
                return {"content": response_text}
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON")
            return {"content": response_text}

# Create global instance
ai_service = GeminiAIService()