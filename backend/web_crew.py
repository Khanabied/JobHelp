"""
Web-integrated CrewAI system for resume optimization
Modified to work with uploaded files and Gemini LLM
"""
import os
import sys
from pathlib import Path
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

# Import available tools - let's check what's available
try:
    from crewai_tools import SerperDevTool, ScrapeWebsiteTool
except ImportError:
    # Fallback if tools are not available
    print("⚠️ CrewAI tools not available, using basic agents")
    SerperDevTool = None
    ScrapeWebsiteTool = None

from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

# Add the src directory to Python path
sys.path.append('/app/src')
from resume_crew.models import JobRequirements, ResumeOptimization, CompanyResearch

class WebOptimizedResumeCrew:
    """Web-optimized CrewAI system with Gemini LLM integration"""
    
    def __init__(self, resume_file_path: str, job_input: str, company_name: str, is_job_url: bool = True):
        """
        Initialize the crew with dynamic inputs
        
        Args:
            resume_file_path: Path to uploaded PDF resume
            job_input: Either job URL or job description text
            company_name: Name of the company
            is_job_url: Whether job_input is a URL or text description
        """
        self.resume_file_path = resume_file_path
        self.job_input = job_input
        self.company_name = company_name
        self.is_job_url = is_job_url
        
        # Initialize Gemini LLM
        self.gemini_llm = self._create_gemini_llm()
        
        # Create PDF knowledge source from uploaded file
        self.resume_pdf = PDFKnowledgeSource(file_paths=[resume_file_path])
        
        # Load agent and task configurations
        self.agents_config = self._load_agents_config()
        self.tasks_config = self._load_tasks_config()
    
    def _create_gemini_llm(self):
        """Create Gemini LLM instance for CrewAI agents"""
        try:
            return LLM(
                model="gemini/gemini-2.0-flash-exp", 
                api_key=os.getenv("GEMINI_API_KEY")
            )
        except Exception as e:
            print(f"Error creating Gemini LLM: {e}")
            # Fallback to a basic configuration
            return LLM(
                model="gemini-2.0-flash-exp",
                api_key=os.getenv("GEMINI_API_KEY")
            )
    
    def _load_agents_config(self):
        """Load agents configuration"""
        return {
            'resume_analyzer': {
                'role': 'Resume Optimization Expert',
                'goal': 'Analyze resumes and provide structured optimization suggestions',
                'backstory': '''You are a resume optimization specialist with deep knowledge of ATS systems
                and modern resume best practices. You excel at analyzing PDF resumes and
                providing actionable suggestions for improvement. Your recommendations always
                focus on both human readability and ATS compatibility.'''
            },
            'job_analyzer': {
                'role': 'Job Requirements Analyst', 
                'goal': 'Analyze job descriptions and score candidate fit',
                'backstory': '''You are an expert in job market analysis and candidate evaluation. Your strength
                lies in breaking down job requirements into clear categories and providing
                detailed scoring based on candidate qualifications. You understand both technical
                and soft skills requirements, and can evaluate experience levels accurately.'''
            },
            'company_researcher': {
                'role': 'Company Intelligence Specialist',
                'goal': 'Research companies and prepare interview insights', 
                'backstory': '''You are a corporate research expert who excels at gathering and analyzing
                the latest company information. You know how to find and synthesize data 
                from various sources to create comprehensive company profiles and prepare
                candidates for interviews.'''
            },
            'resume_writer': {
                'role': 'Resume Markdown Specialist',
                'goal': 'Create beautifully formatted, ATS-optimized resumes in markdown',
                'backstory': '''You are a resume writing expert who specializes in creating markdown-formatted
                resumes. You know how to transform structured optimization suggestions into
                beautifully formatted, ATS-friendly documents that maintain professionalism
                while showcasing candidate strengths effectively.'''
            },
            'report_generator': {
                'role': 'Career Report Generator and Markdown Specialist',
                'goal': 'Create comprehensive, visually appealing, and actionable reports from job application analysis',
                'backstory': '''You are an expert in data visualization, technical writing, and Markdown formatting.
                You excel at combining data from multiple JSON sources to create cohesive,
                visually appealing reports. Your specialty is transforming structured analysis
                into clear, actionable insights with proper markdown formatting, emojis, and
                visual elements that make information both appealing and easily digestible.'''
            }
        }
    
    def _load_tasks_config(self):
        """Load tasks configuration with dynamic job input handling"""
        job_analysis_desc = self._get_job_analysis_description()
        
        return {
            'analyze_job_task': {
                'description': job_analysis_desc,
                'expected_output': '''Structured JSON data containing job analysis and scoring details according to
                the JobRequirements model schema.'''
            },
            'optimize_resume_task': {
                'description': '''Review the provided resume against the job analysis and create structured optimization suggestions.
                Output will be saved as structured JSON data.

                1. Content Analysis:
                   - Compare resume content with job requirements
                   - Identify missing keywords and skills
                   - Analyze achievement descriptions
                   - Check for ATS compatibility

                2. Structure Review:
                   - Evaluate section organization
                   - Check formatting consistency
                   - Assess information hierarchy
                   - Verify contact details

                3. Generate Suggestions:
                   - Content improvements with before/after examples
                   - Skills to highlight based on job match
                   - Achievements to add or modify
                   - ATS optimization recommendations''',
                'expected_output': '''Structured JSON data containing detailed optimization suggestions according to
                the ResumeOptimization model schema.'''
            },
            'research_company_task': {
                'description': f'''Research {self.company_name} and prepare the latest (year 2025) and comprehensive analysis.
                Output will be saved as structured JSON data.

                1. Company Overview:
                   - Recent developments and news
                   - Culture and values
                   - Market position
                   - Growth trajectory

                2. Interview Preparation:
                   - Common interview questions
                   - Company-specific topics
                   - Recent projects or initiatives
                   - Key challenges and opportunities''',
                'expected_output': '''Structured JSON data containing company research results according to
                the CompanyResearch model schema.'''
            },
            'generate_resume_task': {
                'description': '''Using the optimization suggestions and job analysis from previous steps, 
                create a polished resume in markdown format.
                Do not add markdown code blocks like '```'.

                1. Content Integration:
                   - Incorporate optimization suggestions
                   - Add missing keywords and skills
                   - Enhance achievement descriptions
                   - Ensure ATS compatibility

                2. Formatting:
                   - Use proper markdown headers (#, ##, ###)
                   - Apply consistent styling
                   - Create clear section hierarchy
                   - Use bullet points effectively

                3. Documentation:
                   - Track changes made
                   - Note preserved elements
                   - Explain optimization choices''',
                'expected_output': '''A beautifully formatted markdown resume document that:
                - Incorporates all optimization suggestions
                - Uses proper markdown formatting
                - Is ATS-friendly
                - Documents all changes made'''
            },
            'generate_report_task': {
                'description': '''Create an executive summary report using data from previous steps. 
                Format in markdown without code blocks '```'.

                1. Data Integration:
                   - Job analysis and scores
                   - Resume optimization details
                   - Company research insights
                   - Final resume changes

                2. Report Sections:
                   ## Executive Summary
                   - Overall match score and quick wins
                   - Key strengths and improvement areas
                   - Action items priority list

                   ## Job Fit Analysis
                   - Detailed score breakdown
                   - Skills match assessment
                   - Experience alignment

                   ## Optimization Overview
                   - Key resume improvements
                   - ATS optimization results
                   - Impact metrics

                   ## Company Insights
                   - Culture fit analysis
                   - Interview preparation tips
                   - Key talking points

                   ## Next Steps
                   - Prioritized action items
                   - Skill development plan
                   - Application strategy

                3. Formatting:
                   - Use proper markdown headers
                   - Include relevant emojis
                   - Create tables where appropriate
                   - Use bullet points for scannability''',
                'expected_output': '''A comprehensive markdown report that combines all analyses into an
                actionable, clear document with concrete next steps.'''
            }
        }
    
    def _get_job_analysis_description(self):
        """Get job analysis task description based on input type"""
        if self.is_job_url:
            job_source = f"Analyze the job description from URL: {self.job_input}"
        else:
            job_source = f"Analyze the following job description text:\n\n{self.job_input}"
        
        return f'''{job_source} and score the candidate's fit based on their resume.
        Output will be saved as structured JSON data.

        1. Extract Requirements:
           - Technical skills (required vs nice-to-have)
           - Soft skills
           - Experience levels
           - Education requirements
           - Industry knowledge

        2. Score Technical Skills (35% of total):
           - For each required skill:
             * Match Level (0-1): How well does candidate's experience match?
             * Years Experience: Compare to required years
             * Context Score: How relevant is their usage of the skill?
           - Calculate weighted average based on skill importance

        3. Score Soft Skills (20% of total):
           - Identify soft skills from resume
           - Compare against job requirements
           - Consider context and demonstration of skills

        4. Score Experience (25% of total):
           - Years of relevant experience
           - Role similarity
           - Industry relevance
           - Project scope and complexity

        5. Score Education (10% of total):
           - Degree level match
           - Field of study relevance
           - Additional certifications

        6. Score Industry Knowledge (10% of total):
           - Years in similar industry
           - Domain expertise
           - Industry-specific achievements

        7. Calculate Overall Score:
           - Weighted average of all components
           - Identify key strengths and gaps
           - Provide detailed scoring explanation'''

    # Agent creation methods
    def create_resume_analyzer(self) -> Agent:
        """Create resume analyzer agent with Gemini LLM"""
        return Agent(
            role=self.agents_config['resume_analyzer']['role'],
            goal=self.agents_config['resume_analyzer']['goal'],
            backstory=self.agents_config['resume_analyzer']['backstory'],
            verbose=True,
            llm=self.gemini_llm,
            knowledge_sources=[self.resume_pdf]
        )
    
    def create_job_analyzer(self) -> Agent:
        """Create job analyzer agent with Gemini LLM"""
        tools = []
        if self.is_job_url and ScrapeWebsiteTool:
            tools = [ScrapeWebsiteTool()]
        
        return Agent(
            role=self.agents_config['job_analyzer']['role'],
            goal=self.agents_config['job_analyzer']['goal'], 
            backstory=self.agents_config['job_analyzer']['backstory'],
            verbose=True,
            tools=tools,
            llm=self.gemini_llm
        )
    
    def create_company_researcher(self) -> Agent:
        """Create company researcher agent with Gemini LLM"""
        return Agent(
            role=self.agents_config['company_researcher']['role'],
            goal=self.agents_config['company_researcher']['goal'],
            backstory=self.agents_config['company_researcher']['backstory'],
            verbose=True,
            tools=[SerperDevTool()],
            llm=self.gemini_llm,
            knowledge_sources=[self.resume_pdf]
        )
    
    def create_resume_writer(self) -> Agent:
        """Create resume writer agent with Gemini LLM"""
        return Agent(
            role=self.agents_config['resume_writer']['role'],
            goal=self.agents_config['resume_writer']['goal'],
            backstory=self.agents_config['resume_writer']['backstory'],
            verbose=True,
            llm=self.gemini_llm
        )
    
    def create_report_generator(self) -> Agent:
        """Create report generator agent with Gemini LLM"""
        return Agent(
            role=self.agents_config['report_generator']['role'],
            goal=self.agents_config['report_generator']['goal'],
            backstory=self.agents_config['report_generator']['backstory'],
            verbose=True,
            llm=self.gemini_llm
        )
    
    # Task creation methods
    def create_analyze_job_task(self, agent: Agent) -> Task:
        """Create job analysis task"""
        return Task(
            description=self.tasks_config['analyze_job_task']['description'],
            expected_output=self.tasks_config['analyze_job_task']['expected_output'],
            agent=agent,
            output_file='/app/output/job_analysis.json',
            output_pydantic=JobRequirements
        )
    
    def create_optimize_resume_task(self, agent: Agent, context: list) -> Task:
        """Create resume optimization task"""
        return Task(
            description=self.tasks_config['optimize_resume_task']['description'],
            expected_output=self.tasks_config['optimize_resume_task']['expected_output'],
            agent=agent,
            context=context,
            output_file='/app/output/resume_optimization.json',
            output_pydantic=ResumeOptimization
        )
    
    def create_research_company_task(self, agent: Agent, context: list) -> Task:
        """Create company research task"""
        return Task(
            description=self.tasks_config['research_company_task']['description'],
            expected_output=self.tasks_config['research_company_task']['expected_output'],
            agent=agent,
            context=context,
            output_file='/app/output/company_research.json',
            output_pydantic=CompanyResearch
        )
    
    def create_generate_resume_task(self, agent: Agent, context: list) -> Task:
        """Create resume generation task"""
        return Task(
            description=self.tasks_config['generate_resume_task']['description'],
            expected_output=self.tasks_config['generate_resume_task']['expected_output'],
            agent=agent,
            context=context,
            output_file='/app/output/optimized_resume.md'
        )
    
    def create_generate_report_task(self, agent: Agent, context: list) -> Task:
        """Create report generation task"""
        return Task(
            description=self.tasks_config['generate_report_task']['description'],
            expected_output=self.tasks_config['generate_report_task']['expected_output'],
            agent=agent,
            context=context,
            output_file='/app/output/final_report.md'
        )
    
    def create_crew(self) -> Crew:
        """Create and return the complete CrewAI crew"""
        try:
            # Create agents
            resume_analyzer = self.create_resume_analyzer()
            job_analyzer = self.create_job_analyzer()
            company_researcher = self.create_company_researcher()
            resume_writer = self.create_resume_writer()
            report_generator = self.create_report_generator()
            
            # Create tasks
            analyze_job_task = self.create_analyze_job_task(job_analyzer)
            optimize_resume_task = self.create_optimize_resume_task(resume_analyzer, [analyze_job_task])
            research_company_task = self.create_research_company_task(company_researcher, [analyze_job_task, optimize_resume_task])
            generate_resume_task = self.create_generate_resume_task(resume_writer, [optimize_resume_task, analyze_job_task, research_company_task])
            generate_report_task = self.create_generate_report_task(report_generator, [analyze_job_task, optimize_resume_task, research_company_task])
            
            # Create and return crew
            crew = Crew(
                agents=[resume_analyzer, job_analyzer, company_researcher, resume_writer, report_generator],
                tasks=[analyze_job_task, optimize_resume_task, research_company_task, generate_resume_task, generate_report_task],
                verbose=True,
                process=Process.sequential,
                knowledge_sources=[self.resume_pdf]
            )
            
            return crew
            
        except Exception as e:
            print(f"Error creating crew: {e}")
            raise e
    
    def run_analysis(self):
        """Run the complete resume analysis"""
        try:
            # Ensure output directory exists
            os.makedirs('/app/output', exist_ok=True)
            
            # Create and run the crew
            crew = self.create_crew()
            
            # Prepare inputs (empty dict since all info is in task descriptions)
            inputs = {}
            
            print("🚀 Starting resume analysis with CrewAI + Gemini...")
            result = crew.kickoff(inputs=inputs)
            print("✅ Resume analysis completed!")
            
            return {
                "status": "success",
                "message": "Resume analysis completed successfully",
                "crew_result": str(result)
            }
            
        except Exception as e:
            print(f"❌ Error in resume analysis: {e}")
            return {
                "status": "error", 
                "message": f"Resume analysis failed: {str(e)}"
            }