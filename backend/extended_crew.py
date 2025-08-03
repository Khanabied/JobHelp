"""
Extended CrewAI system with additional AI agents for cover letters, LinkedIn optimization, and interview preparation
Built on top of the existing WebOptimizedResumeCrew
"""
import os
import sys
from typing import Optional, Dict, List
from pathlib import Path
from crewai import Agent, Crew, Process, Task, LLM
from pydantic import BaseModel, Field

# Import available tools
try:
    from crewai_tools import SerperDevTool, ScrapeWebsiteTool
except ImportError:
    print("⚠️ CrewAI tools not available, using basic agents")
    SerperDevTool = None
    ScrapeWebsiteTool = None

from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

# Add the src directory to Python path
sys.path.append('/app/src')
from resume_crew.models import JobRequirements, ResumeOptimization, CompanyResearch

# Import the base crew system
from web_crew import WebOptimizedResumeCrew

# New Pydantic models for the extended agents
class CoverLetter(BaseModel):
    """Model for cover letter output"""
    cover_letter_content: str = Field(description="Complete cover letter in markdown format")
    key_highlights: List[str] = Field(description="Key points highlighted in the cover letter")
    personalization_notes: List[str] = Field(description="Company-specific personalizations included")
    call_to_action: str = Field(description="Closing call to action used")
    word_count: int = Field(description="Total word count of the cover letter")
    ats_keywords: List[str] = Field(description="ATS keywords incorporated")

class LinkedInOptimization(BaseModel):
    """Model for LinkedIn profile optimization"""
    optimized_headline: str = Field(description="Optimized LinkedIn headline")
    professional_summary: str = Field(description="Enhanced professional summary/about section")
    skills_to_add: List[str] = Field(description="Skills to add or emphasize on LinkedIn")
    experience_enhancements: List[Dict[str, str]] = Field(
        description="Enhancements to experience descriptions with before/after examples"
    )
    keyword_optimization: List[str] = Field(description="Keywords to incorporate throughout profile")
    networking_strategy: List[str] = Field(description="Networking and engagement strategies")
    content_suggestions: List[str] = Field(description="Content creation and posting suggestions")

class InterviewPreparation(BaseModel):
    """Model for interview preparation output"""
    behavioral_questions: List[Dict[str, str]] = Field(
        description="Behavioral interview questions with suggested answer frameworks"
    )
    technical_questions: List[Dict[str, str]] = Field(
        description="Technical/role-specific questions with guidance"
    )
    company_specific_questions: List[Dict[str, str]] = Field(
        description="Questions tailored to the specific company and role"
    )
    questions_to_ask: List[str] = Field(
        description="Thoughtful questions candidate should ask the interviewer"
    )
    preparation_tips: List[str] = Field(description="General interview preparation advice")
    potential_challenges: List[Dict[str, str]] = Field(
        description="Potential challenging questions and how to handle them"
    )
    success_metrics: List[str] = Field(description="How to measure interview success")


class ExtendedCareerOptimizationCrew(WebOptimizedResumeCrew):
    """Extended CrewAI system with additional career optimization agents"""
    
    def __init__(self, resume_file_path: str, job_input: str, company_name: str, is_job_url: bool = True):
        """Initialize extended crew with all agents"""
        super().__init__(resume_file_path, job_input, company_name, is_job_url)
        
        # Add extended agent configurations
        self.agents_config.update(self._get_extended_agents_config())
        self.tasks_config.update(self._get_extended_tasks_config())
    
    def _get_extended_agents_config(self):
        """Get configuration for the three new agents"""
        return {
            'cover_letter_writer': {
                'role': 'Professional Cover Letter Writer',
                'goal': 'Create compelling, personalized cover letters that highlight candidate strengths and match job requirements',
                'backstory': '''You are an expert cover letter writer with years of experience in crafting 
                compelling narratives that connect candidate qualifications to job requirements. You excel at 
                personalizing letters for specific companies and roles, incorporating relevant achievements, 
                and creating strong opening hooks and closing calls to action. Your letters are ATS-friendly 
                while maintaining a human, engaging tone that resonates with hiring managers.'''
            },
            'linkedin_optimizer': {
                'role': 'LinkedIn Profile Optimization Specialist',
                'goal': 'Optimize LinkedIn profiles to increase visibility, showcase professional brand, and attract relevant opportunities',
                'backstory': '''You are a LinkedIn optimization expert who understands the platform's algorithm, 
                best practices for professional networking, and how to craft profiles that stand out to recruiters 
                and hiring managers. You know how to leverage keywords for searchability, create compelling headlines 
                and summaries, and provide actionable strategies for building professional networks and engaging 
                with industry content.'''
            },
            'interview_coach': {
                'role': 'Senior Interview Preparation Coach',
                'goal': 'Provide comprehensive interview preparation including questions, strategies, and coaching advice',
                'backstory': '''You are a seasoned interview coach with extensive experience preparing candidates 
                for interviews at top companies. You excel at anticipating interview questions based on job 
                requirements and company culture, providing frameworks for answering behavioral questions, 
                and coaching candidates on how to effectively communicate their value proposition. You understand 
                different interview formats and can provide tailored preparation strategies.'''
            }
        }
    
    def _get_extended_tasks_config(self):
        """Get task configurations for the three new agents"""
        return {
            'write_cover_letter_task': {
                'description': f'''Using the optimized resume and job analysis, create a compelling cover letter for 
                the {self.company_name} position. The cover letter should be professional, ATS-friendly, and 
                tailored to the specific job requirements.

                Requirements:
                1. Opening Hook:
                   - Compelling opening that mentions the specific role
                   - Brief introduction highlighting top 2-3 relevant qualifications
                   - Show enthusiasm for the company and role

                2. Body Content:
                   - Connect resume achievements to job requirements
                   - Use specific examples and quantifiable results
                   - Incorporate company research findings
                   - Address any potential concerns or gaps

                3. Company Personalization:
                   - Reference specific company values, projects, or initiatives
                   - Show knowledge of company culture and mission
                   - Explain why you want to work specifically for this company

                4. Technical Requirements:
                   - 300-400 words total
                   - Include relevant ATS keywords
                   - Professional tone while showing personality
                   - Strong call to action in closing

                5. Format:
                   - Proper business letter format
                   - Use markdown for structure
                   - Include contact information
                   - Professional salutation and closing''',
                'expected_output': '''A complete, professionally formatted cover letter in markdown format according to 
                the CoverLetter model schema, including key highlights and personalization notes.'''
            },
            'optimize_linkedin_task': {
                'description': '''Create comprehensive LinkedIn profile optimization recommendations based on the 
                resume analysis and job requirements. Focus on increasing visibility, professional brand, and 
                attracting relevant opportunities.

                Optimization Areas:
                1. Profile Headline:
                   - Create compelling, keyword-rich headline
                   - Show value proposition clearly
                   - Include target role keywords

                2. Professional Summary:
                   - Engaging "About" section narrative
                   - Incorporate top achievements
                   - Include relevant keywords naturally
                   - Add personal touch and career goals

                3. Experience Section:
                   - Enhance job descriptions with achievements
                   - Use action verbs and quantifiable results
                   - Optimize for target role keywords
                   - Show career progression clearly

                4. Skills & Endorsements:
                   - Prioritize skills relevant to target role
                   - Add missing skills based on job analysis
                   - Strategic skill ordering for visibility

                5. Networking Strategy:
                   - Connection building recommendations
                   - Industry engagement tactics
                   - Content creation suggestions
                   - Professional activity guidance

                6. Keyword Strategy:
                   - Industry-specific keywords to incorporate
                   - Target role terminology
                   - ATS-friendly language
                   - Search optimization techniques''',
                'expected_output': '''Comprehensive LinkedIn optimization recommendations according to the 
                LinkedInOptimization model schema, with specific before/after examples and actionable strategies.'''
            },
            'prepare_interview_task': {
                'description': f'''Create comprehensive interview preparation materials for the {self.company_name} 
                position based on job analysis, resume optimization, and company research. Provide 10-15 tailored 
                questions with guidance and coaching advice.

                Interview Preparation Components:
                1. Behavioral Questions (5-6 questions):
                   - Use STAR method framework
                   - Connect to resume achievements
                   - Address key job requirements
                   - Include sample answer guidance

                2. Technical/Role-Specific Questions (4-5 questions):
                   - Based on job requirements
                   - Industry-relevant scenarios
                   - Skills assessment questions
                   - Problem-solving challenges

                3. Company-Specific Questions (3-4 questions):
                   - Based on company research
                   - Culture and values alignment
                   - Recent company developments
                   - Role-specific challenges

                4. Questions to Ask Interviewer:
                   - Strategic questions about role
                   - Company culture inquiries
                   - Growth and development opportunities
                   - Team dynamics questions

                5. Preparation Strategies:
                   - Research recommendations
                   - Practice techniques
                   - Confidence building tips
                   - Day-of interview guidance

                6. Challenge Areas:
                   - Address potential weaknesses
                   - Handle difficult questions
                   - Salary negotiation prep
                   - Follow-up strategies

                Format each question with:
                - The actual question
                - Why it might be asked
                - Framework for answering
                - Key points to include
                - What NOT to say''',
                'expected_output': '''Comprehensive interview preparation guide according to the InterviewPreparation 
                model schema, with 10-15 tailored questions, answer frameworks, and coaching advice.'''
            }
        }
    
    # New agent creation methods
    def create_cover_letter_writer(self) -> Agent:
        """Create cover letter writer agent with Gemini LLM"""
        return Agent(
            role=self.agents_config['cover_letter_writer']['role'],
            goal=self.agents_config['cover_letter_writer']['goal'],
            backstory=self.agents_config['cover_letter_writer']['backstory'],
            verbose=True,
            llm=self.gemini_llm,
            knowledge_sources=[self.resume_pdf]
        )
    
    def create_linkedin_optimizer(self) -> Agent:
        """Create LinkedIn optimization agent with Gemini LLM"""
        return Agent(
            role=self.agents_config['linkedin_optimizer']['role'],
            goal=self.agents_config['linkedin_optimizer']['goal'],
            backstory=self.agents_config['linkedin_optimizer']['backstory'],
            verbose=True,
            llm=self.gemini_llm,
            knowledge_sources=[self.resume_pdf]
        )
    
    def create_interview_coach(self) -> Agent:
        """Create interview preparation agent with Gemini LLM"""
        tools = []
        if SerperDevTool:
            tools = [SerperDevTool()]
            
        return Agent(
            role=self.agents_config['interview_coach']['role'],
            goal=self.agents_config['interview_coach']['goal'],
            backstory=self.agents_config['interview_coach']['backstory'],
            verbose=True,
            tools=tools,
            llm=self.gemini_llm,
            knowledge_sources=[self.resume_pdf]
        )
    
    # New task creation methods
    def create_cover_letter_task(self, agent: Agent, context: list) -> Task:
        """Create cover letter writing task"""
        return Task(
            description=self.tasks_config['write_cover_letter_task']['description'],
            expected_output=self.tasks_config['write_cover_letter_task']['expected_output'],
            agent=agent,
            context=context,
            output_file='/app/output/cover_letter.json',
            output_pydantic=CoverLetter
        )
    
    def create_linkedin_optimization_task(self, agent: Agent, context: list) -> Task:
        """Create LinkedIn optimization task"""
        return Task(
            description=self.tasks_config['optimize_linkedin_task']['description'],
            expected_output=self.tasks_config['optimize_linkedin_task']['expected_output'],
            agent=agent,
            context=context,
            output_file='/app/output/linkedin_optimization.json',
            output_pydantic=LinkedInOptimization
        )
    
    def create_interview_preparation_task(self, agent: Agent, context: list) -> Task:
        """Create interview preparation task"""
        return Task(
            description=self.tasks_config['prepare_interview_task']['description'],
            expected_output=self.tasks_config['prepare_interview_task']['expected_output'],
            agent=agent,
            context=context,
            output_file='/app/output/interview_preparation.json',
            output_pydantic=InterviewPreparation
        )
    
    def create_extended_crew(self) -> Crew:
        """Create crew with all agents including the three new ones"""
        try:
            # Create all agents (original + extended)
            resume_analyzer = self.create_resume_analyzer()
            job_analyzer = self.create_job_analyzer()
            company_researcher = self.create_company_researcher()
            resume_writer = self.create_resume_writer()
            report_generator = self.create_report_generator()
            
            # New agents
            cover_letter_writer = self.create_cover_letter_writer()
            linkedin_optimizer = self.create_linkedin_optimizer()
            interview_coach = self.create_interview_coach()
            
            # Create original tasks
            analyze_job_task = self.create_analyze_job_task(job_analyzer)
            optimize_resume_task = self.create_optimize_resume_task(resume_analyzer, [analyze_job_task])
            research_company_task = self.create_research_company_task(company_researcher, [analyze_job_task, optimize_resume_task])
            generate_resume_task = self.create_generate_resume_task(resume_writer, [optimize_resume_task, analyze_job_task, research_company_task])
            
            # Create new tasks
            cover_letter_task = self.create_cover_letter_task(cover_letter_writer, [analyze_job_task, optimize_resume_task, research_company_task])
            linkedin_optimization_task = self.create_linkedin_optimization_task(linkedin_optimizer, [analyze_job_task, optimize_resume_task])
            interview_preparation_task = self.create_interview_preparation_task(interview_coach, [analyze_job_task, research_company_task, optimize_resume_task])
            
            # Final report task (depends on all previous tasks)
            generate_report_task = self.create_generate_report_task(report_generator, [
                analyze_job_task, optimize_resume_task, research_company_task, 
                cover_letter_task, linkedin_optimization_task, interview_preparation_task
            ])
            
            # Create and return extended crew
            crew = Crew(
                agents=[
                    resume_analyzer, job_analyzer, company_researcher, resume_writer,
                    cover_letter_writer, linkedin_optimizer, interview_coach, report_generator
                ],
                tasks=[
                    analyze_job_task, optimize_resume_task, research_company_task, generate_resume_task,
                    cover_letter_task, linkedin_optimization_task, interview_preparation_task, generate_report_task
                ],
                verbose=True,
                process=Process.sequential,
                knowledge_sources=[self.resume_pdf]
            )
            
            return crew
            
        except Exception as e:
            print(f"Error creating extended crew: {e}")
            raise e
    
    def run_individual_agent(self, agent_type: str) -> Dict:
        """Run a single agent independently"""
        try:
            os.makedirs('/app/output', exist_ok=True)
            
            # First run base analysis if not already done
            base_outputs = [
                '/app/output/job_analysis.json',
                '/app/output/resume_optimization.json',
                '/app/output/company_research.json'
            ]
            
            # Check if base analysis exists, if not run it first
            if not all(os.path.exists(f) for f in base_outputs):
                print("🔄 Running base analysis first...")
                base_result = super().run_analysis()
                if base_result["status"] != "success":
                    return base_result
            
            # Create agents based on type
            if agent_type == "cover_letter":
                agent = self.create_cover_letter_writer()
                # Create minimal context tasks
                job_task = self.create_analyze_job_task(self.create_job_analyzer())
                resume_task = self.create_optimize_resume_task(self.create_resume_analyzer(), [])
                company_task = self.create_research_company_task(self.create_company_researcher(), [])
                task = self.create_cover_letter_task(agent, [job_task, resume_task, company_task])
                
            elif agent_type == "linkedin":
                agent = self.create_linkedin_optimizer()
                job_task = self.create_analyze_job_task(self.create_job_analyzer())
                resume_task = self.create_optimize_resume_task(self.create_resume_analyzer(), [])
                task = self.create_linkedin_optimization_task(agent, [job_task, resume_task])
                
            elif agent_type == "interview":
                agent = self.create_interview_coach()
                job_task = self.create_analyze_job_task(self.create_job_analyzer())
                resume_task = self.create_optimize_resume_task(self.create_resume_analyzer(), [])
                company_task = self.create_research_company_task(self.create_company_researcher(), [])
                task = self.create_interview_preparation_task(agent, [job_task, resume_task, company_task])
                
            else:
                return {"status": "error", "message": f"Unknown agent type: {agent_type}"}
            
            # Create minimal crew for single task
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True,
                process=Process.sequential,
                knowledge_sources=[self.resume_pdf]
            )
            
            print(f"🚀 Running {agent_type} agent independently...")
            result = crew.kickoff(inputs={})
            print(f"✅ {agent_type} agent completed!")
            
            return {
                "status": "success",
                "message": f"{agent_type.title()} agent completed successfully",
                "agent_type": agent_type,
                "crew_result": str(result)
            }
            
        except Exception as e:
            print(f"❌ Error running {agent_type} agent: {e}")
            return {
                "status": "error",
                "message": f"{agent_type.title()} agent failed: {str(e)}"
            }
    
    def run_extended_analysis(self) -> Dict:
        """Run complete analysis with all agents"""
        try:
            os.makedirs('/app/output', exist_ok=True)
            
            # Create and run the extended crew
            crew = self.create_extended_crew()
            
            print("🚀 Starting complete career optimization analysis with all 8 agents...")
            result = crew.kickoff(inputs={})
            print("✅ Complete career optimization analysis completed!")
            
            return {
                "status": "success",
                "message": "Complete career optimization analysis completed successfully",
                "crew_result": str(result)
            }
            
        except Exception as e:
            print(f"❌ Error in extended analysis: {e}")
            return {
                "status": "error", 
                "message": f"Extended analysis failed: {str(e)}"
            }