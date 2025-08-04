from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class DocumentType(str, Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    LINKEDIN_PROFILE = "linkedin_profile"
    INTERVIEW_PREP = "interview_prep"

class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    subscription_tier: str = "free"  # free, premium, enterprise
    documents_generated: int = 0
    profile_data: Optional[Dict[str, Any]] = {}

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

# Document Models
class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    document_type: DocumentType
    content: Dict[str, Any]
    generated_content: Optional[str] = None
    optimization_suggestions: Optional[List[str]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_favorite: bool = False
    template_used: Optional[str] = None

class DocumentCreate(BaseModel):
    title: str
    document_type: DocumentType
    content: Dict[str, Any]
    template_used: Optional[str] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    is_favorite: Optional[bool] = None

# Resume Models
class ResumeData(BaseModel):
    personal_info: Dict[str, str]
    work_experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[str]
    certifications: Optional[List[Dict[str, str]]] = []
    projects: Optional[List[Dict[str, Any]]] = []

class ResumeOptimizeRequest(BaseModel):
    resume_data: ResumeData
    job_description: Optional[str] = None
    target_position: Optional[str] = None

# Cover Letter Models
class CoverLetterRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: str
    resume_data: ResumeData
    additional_notes: Optional[str] = None

# LinkedIn Models
class LinkedInOptimizeRequest(BaseModel):
    current_profile: Dict[str, Any]
    target_industry: Optional[str] = None
    career_goals: Optional[str] = None

# Interview Prep Models
class InterviewPrepRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: str
    experience_level: str  # junior, mid, senior
    interview_type: str  # behavioral, technical, case_study

# Analytics Models
class UserAnalytics(BaseModel):
    user_id: str
    total_documents: int
    documents_by_type: Dict[str, int]
    last_activity: datetime
    subscription_tier: str

class SystemAnalytics(BaseModel):
    total_users: int
    active_users_today: int
    active_users_this_month: int
    documents_generated_today: int
    documents_generated_this_month: int
    documents_by_type: Dict[str, int]
    subscription_distribution: Dict[str, int]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# Admin Models
class AdminUserView(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    subscription_tier: str
    documents_generated: int

class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    subscription_tier: Optional[str] = None

# Template Models
class Template(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    document_type: DocumentType
    template_content: str
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # admin user id

class TemplateCreate(BaseModel):
    name: str
    document_type: DocumentType
    template_content: str
    is_default: bool = False