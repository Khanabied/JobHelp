import asyncio
import os
import tempfile
import shutil
from pathlib import Path
import sys
import json

# Add the src directory to Python path to import CrewAI modules
sys.path.append('/app/src')

from resume_crew.crew import ResumeCrew
from gemini_config import get_gemini_llm, test_gemini_connection
from crewai import LLM

class WebCrewIntegration:
    """Integration service for connecting web API to CrewAI system"""
    
    def __init__(self):
        self.gemini_llm = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini LLM for CrewAI"""
        try:
            self.gemini_llm = get_gemini_llm()
            print("✅ Gemini LLM initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini LLM: {e}")
            self.gemini_llm = None
    
    async def test_gemini(self):
        """Test Gemini API connection"""
        return await test_gemini_connection()
    
    def create_modified_crew(self, resume_file_path: str):
        """Create a modified CrewAI crew with Gemini LLM and custom resume path"""
        try:
            # Create a modified version of ResumeCrew
            class WebResumeCrew(ResumeCrew):
                def __init__(self, resume_path: str):
                    # Override the parent __init__ to use custom resume path
                    from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
                    self.resume_pdf = PDFKnowledgeSource(file_paths=[resume_path])
                
                # Override all agent methods to use Gemini LLM
                def resume_analyzer(self):
                    agent = super().resume_analyzer()
                    if self.gemini_llm:
                        agent.llm = self.gemini_llm
                    return agent
                
                def job_analyzer(self):
                    agent = super().job_analyzer()
                    if self.gemini_llm:
                        agent.llm = self.gemini_llm
                    return agent
                
                def company_researcher(self):
                    agent = super().company_researcher()
                    if self.gemini_llm:
                        agent.llm = self.gemini_llm
                    return agent
                
                def resume_writer(self):
                    agent = super().resume_writer()
                    if self.gemini_llm:
                        agent.llm = self.gemini_llm
                    return agent
                
                def report_generator(self):
                    agent = super().report_generator()
                    if self.gemini_llm:
                        agent.llm = self.gemini_llm
                    return agent
            
            # Set the gemini_llm for the nested class
            WebResumeCrew.gemini_llm = self.gemini_llm
            
            return WebResumeCrew(resume_path=resume_file_path)
            
        except Exception as e:
            print(f"❌ Error creating modified crew: {e}")
            return None
    
    async def process_resume_analysis(
        self, 
        resume_file_path: str,
        job_url: str = None,
        job_description: str = None,
        company_name: str = "Unknown Company"
    ):
        """Process resume analysis with CrewAI using web inputs"""
        try:
            print(f"🚀 Starting resume analysis...")
            print(f"   Resume: {resume_file_path}")
            print(f"   Job URL: {job_url}")
            print(f"   Company: {company_name}")
            
            # Create modified crew with custom resume path
            crew_instance = self.create_modified_crew(resume_file_path)
            if not crew_instance:
                raise Exception("Failed to create CrewAI instance")
            
            # Prepare inputs for CrewAI
            inputs = {
                'company_name': company_name
            }
            
            # Add job URL or description based on what's provided
            if job_url:
                inputs['job_url'] = job_url
            else:
                # For now, we'll handle job description in Phase 2
                # CrewAI currently expects a URL, so we'll need to modify this
                inputs['job_url'] = 'https://example.com/job-posting'  # Placeholder
            
            print(f"🔄 Running CrewAI with inputs: {inputs}")
            
            # Run the crew analysis
            crew = crew_instance.crew()
            result = crew.kickoff(inputs=inputs)
            
            print(f"✅ CrewAI analysis completed successfully")
            
            return {
                "status": "success",
                "message": "Resume analysis completed successfully",
                "crew_result": str(result),
                "output_files": {
                    "job_analysis": "/app/output/job_analysis.json",
                    "resume_optimization": "/app/output/resume_optimization.json", 
                    "company_research": "/app/output/company_research.json",
                    "optimized_resume": "/app/output/optimized_resume.md",
                    "final_report": "/app/output/final_report.md"
                }
            }
            
        except Exception as e:
            print(f"❌ Error in resume analysis: {e}")
            return {
                "status": "error",
                "message": f"Resume analysis failed: {str(e)}"
            }
    
    async def get_analysis_results(self):
        """Retrieve the results from CrewAI output files"""
        try:
            import json
            results = {}
            
            # Read JSON output files
            json_files = [
                ("job_analysis", "/app/output/job_analysis.json"),
                ("resume_optimization", "/app/output/resume_optimization.json"),
                ("company_research", "/app/output/company_research.json")
            ]
            
            for key, file_path in json_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        results[key] = json.load(f)
            
            # Read markdown output files
            md_files = [
                ("optimized_resume", "/app/output/optimized_resume.md"),
                ("final_report", "/app/output/final_report.md")
            ]
            
            for key, file_path in md_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        results[key] = f.read()
            
            return results
            
        except Exception as e:
            print(f"❌ Error reading analysis results: {e}")
            return {}

# Global instance
crew_integration = WebCrewIntegration()