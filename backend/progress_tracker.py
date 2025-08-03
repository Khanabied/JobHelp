"""
Progress Tracking System for AI Agent Processing
Provides real-time updates on analysis progress
"""
import json
import time
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import asyncio

@dataclass
class ProgressStep:
    """Individual progress step"""
    step_id: str
    name: str
    description: str
    status: str  # pending, running, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress_percent: int = 0
    message: str = ""
    error: Optional[str] = None


class ProgressTracker:
    """Track progress of multi-step AI analysis processes"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def create_session(self, session_id: str, steps: List[Dict]) -> None:
        """Create a new progress tracking session"""
        progress_steps = []
        for step in steps:
            progress_steps.append(ProgressStep(
                step_id=step['id'],
                name=step['name'],
                description=step['description'],
                status='pending'
            ))
        
        self.sessions[session_id] = {
            'steps': progress_steps,
            'current_step': 0,
            'overall_progress': 0,
            'status': 'initialized',
            'start_time': datetime.now(),
            'end_time': None,
            'total_steps': len(progress_steps)
        }
    
    def start_step(self, session_id: str, step_id: str, message: str = "") -> None:
        """Mark a step as started"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        for step in session['steps']:
            if step.step_id == step_id:
                step.status = 'running'
                step.start_time = datetime.now()
                step.message = message
                session['status'] = 'running'
                break
        
        self._update_overall_progress(session_id)
    
    def complete_step(self, session_id: str, step_id: str, message: str = "") -> None:
        """Mark a step as completed"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        for step in session['steps']:
            if step.step_id == step_id:
                step.status = 'completed'
                step.end_time = datetime.now()
                step.progress_percent = 100
                step.message = message or "Completed successfully"
                break
        
        self._update_overall_progress(session_id)
    
    def fail_step(self, session_id: str, step_id: str, error: str) -> None:
        """Mark a step as failed"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        for step in session['steps']:
            if step.step_id == step_id:
                step.status = 'failed'
                step.end_time = datetime.now()
                step.error = error
                step.message = f"Failed: {error}"
                break
        
        session['status'] = 'failed'
        session['end_time'] = datetime.now()
    
    def update_step_progress(self, session_id: str, step_id: str, progress_percent: int, message: str = "") -> None:
        """Update progress percentage for a step"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        for step in session['steps']:
            if step.step_id == step_id:
                step.progress_percent = min(100, max(0, progress_percent))
                if message:
                    step.message = message
                break
        
        self._update_overall_progress(session_id)
    
    def complete_session(self, session_id: str) -> None:
        """Mark entire session as completed"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session['status'] = 'completed'
        session['end_time'] = datetime.now()
        session['overall_progress'] = 100
        
        # Mark any pending steps as completed
        for step in session['steps']:
            if step.status == 'pending':
                step.status = 'completed'
                step.progress_percent = 100
                step.end_time = datetime.now()
    
    def get_progress(self, session_id: str) -> Optional[Dict]:
        """Get current progress for a session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            'session_id': session_id,
            'status': session['status'],
            'overall_progress': session['overall_progress'],
            'current_step': session['current_step'],
            'total_steps': session['total_steps'],
            'start_time': session['start_time'].isoformat() if session['start_time'] else None,
            'end_time': session['end_time'].isoformat() if session['end_time'] else None,
            'steps': [asdict(step) for step in session['steps']]
        }
    
    def _update_overall_progress(self, session_id: str) -> None:
        """Update overall progress based on individual steps"""
        session = self.sessions[session_id]
        total_progress = sum(step.progress_percent for step in session['steps'])
        session['overall_progress'] = int(total_progress / session['total_steps'])
        
        # Update current step index
        for i, step in enumerate(session['steps']):
            if step.status in ['running', 'pending']:
                session['current_step'] = i
                break
        else:
            session['current_step'] = session['total_steps']
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> None:
        """Clean up old progress sessions"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            if session['start_time']:
                age = current_time - session['start_time']
                if age.total_seconds() > max_age_hours * 3600:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]


# Global progress tracker instance
progress_tracker = ProgressTracker()


def get_analysis_steps(analysis_type: str = "extended") -> List[Dict]:
    """Get the steps for different types of analysis"""
    
    if analysis_type == "extended":
        return [
            {
                "id": "job_analysis",
                "name": "Job Analysis",
                "description": "Analyzing job requirements and extracting key information"
            },
            {
                "id": "resume_analysis", 
                "name": "Resume Analysis",
                "description": "Analyzing current resume and identifying optimization opportunities"
            },
            {
                "id": "company_research",
                "name": "Company Research",
                "description": "Researching company culture, values, and recent developments"
            },
            {
                "id": "resume_optimization",
                "name": "Resume Optimization",
                "description": "Generating optimized resume tailored to job requirements"
            },
            {
                "id": "cover_letter",
                "name": "Cover Letter Generation",
                "description": "Creating personalized cover letter for the position"
            },
            {
                "id": "linkedin_optimization",
                "name": "LinkedIn Optimization",
                "description": "Optimizing LinkedIn profile for better visibility"
            },
            {
                "id": "interview_preparation",
                "name": "Interview Preparation",
                "description": "Generating tailored interview questions and preparation guide"
            },
            {
                "id": "final_report",
                "name": "Final Report",
                "description": "Compiling comprehensive analysis report"
            }
        ]
    
    elif analysis_type == "basic":
        return [
            {
                "id": "job_analysis",
                "name": "Job Analysis",
                "description": "Analyzing job requirements and extracting key information"
            },
            {
                "id": "resume_analysis",
                "name": "Resume Analysis", 
                "description": "Analyzing current resume and identifying optimization opportunities"
            },
            {
                "id": "company_research",
                "name": "Company Research",
                "description": "Researching company culture, values, and recent developments"
            },
            {
                "id": "resume_optimization",
                "name": "Resume Optimization",
                "description": "Generating optimized resume tailored to job requirements"
            },
            {
                "id": "final_report",
                "name": "Final Report",
                "description": "Compiling analysis report"
            }
        ]
    
    else:
        # Single agent steps
        agent_steps = {
            "cover_letter": [
                {"id": "prerequisites", "name": "Loading Prerequisites", "description": "Loading job analysis and resume data"},
                {"id": "generation", "name": "Cover Letter Generation", "description": "Creating personalized cover letter"}
            ],
            "linkedin": [
                {"id": "prerequisites", "name": "Loading Prerequisites", "description": "Loading job analysis and resume data"},
                {"id": "optimization", "name": "LinkedIn Optimization", "description": "Optimizing LinkedIn profile"}
            ],
            "interview": [
                {"id": "prerequisites", "name": "Loading Prerequisites", "description": "Loading analysis data"},
                {"id": "preparation", "name": "Interview Preparation", "description": "Generating interview questions and guidance"}
            ]
        }
        
        return agent_steps.get(analysis_type, [])