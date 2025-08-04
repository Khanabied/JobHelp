from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import io

# Import custom modules
from models import *
from auth import *
from ai_service import ai_service
from document_service import document_generator
from database import get_database, connect_to_mongo, close_mongo_connection, get_user_analytics, get_system_analytics

# Load environment variables
from dotenv import load_dotenv
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app without a prefix
app = FastAPI(title="Career Tools Platform", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        # Insert user into database
        await db.users.insert_one(user.dict())
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Authenticate user and return token."""
    try:
        user = await authenticate_user(db, user_credentials.email, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        await db.users.update_one(
            {"id": user.id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

# User management endpoints
@api_router.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@api_router.put("/users/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update current user information."""
    try:
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            await db.users.update_one(
                {"id": current_user.id},
                {"$set": update_data}
            )
        
        # Return updated user
        updated_user_doc = await db.users.find_one({"id": current_user.id})
        return User(**updated_user_doc)
    
    except Exception as e:
        logger.error(f"User update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )

# Resume optimization endpoints
@api_router.post("/resume/optimize")
async def optimize_resume(
    request: ResumeOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Optimize resume using AI."""
    try:
        # Use AI service to optimize resume
        optimization_result = await ai_service.optimize_resume(
            request.resume_data.dict(),
            request.job_description
        )
        
        # Save optimization to database
        document = Document(
            user_id=current_user.id,
            title=f"Resume Optimization - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            document_type=DocumentType.RESUME,
            content=request.resume_data.dict(),
            generated_content=optimization_result.get("optimized_content", ""),
            optimization_suggestions=optimization_result.get("suggestions", [])
        )
        
        await db.documents.insert_one(document.dict())
        
        # Update user's document count
        await db.users.update_one(
            {"id": current_user.id},
            {"$inc": {"documents_generated": 1}}
        )
        
        return {
            "document_id": document.id,
            "optimized_content": optimization_result.get("optimized_content", ""),
            "suggestions": optimization_result.get("suggestions", []),
            "score": optimization_result.get("score", 0),
            "keywords_added": optimization_result.get("keywords_added", [])
        }
    
    except Exception as e:
        logger.error(f"Resume optimization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume optimization failed"
        )

# Cover letter generation endpoints
@api_router.post("/cover-letter/generate")
async def generate_cover_letter(
    request: CoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate cover letter using AI."""
    try:
        # Use AI service to generate cover letter
        generation_result = await ai_service.generate_cover_letter(
            request.job_title,
            request.company_name,
            request.job_description,
            request.resume_data.dict(),
            request.additional_notes
        )
        
        # Save cover letter to database
        document = Document(
            user_id=current_user.id,
            title=f"Cover Letter - {request.company_name} ({datetime.utcnow().strftime('%Y-%m-%d')})",
            document_type=DocumentType.COVER_LETTER,
            content={
                "job_title": request.job_title,
                "company_name": request.company_name,
                "job_description": request.job_description,
                "additional_notes": request.additional_notes
            },
            generated_content=generation_result.get("cover_letter", "")
        )
        
        await db.documents.insert_one(document.dict())
        
        # Update user's document count
        await db.users.update_one(
            {"id": current_user.id},
            {"$inc": {"documents_generated": 1}}
        )
        
        return {
            "document_id": document.id,
            "cover_letter": generation_result.get("cover_letter", ""),
            "key_points": generation_result.get("key_points", []),
            "personalization_score": generation_result.get("personalization_score", 0)
        }
    
    except Exception as e:
        logger.error(f"Cover letter generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cover letter generation failed"
        )

# LinkedIn optimization endpoints
@api_router.post("/linkedin/optimize")
async def optimize_linkedin(
    request: LinkedInOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Optimize LinkedIn profile using AI."""
    try:
        # Use AI service to optimize LinkedIn profile
        optimization_result = await ai_service.optimize_linkedin_profile(
            request.current_profile,
            request.target_industry
        )
        
        # Save optimization to database
        document = Document(
            user_id=current_user.id,
            title=f"LinkedIn Optimization - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            document_type=DocumentType.LINKEDIN_PROFILE,
            content=request.current_profile,
            generated_content=str(optimization_result)
        )
        
        await db.documents.insert_one(document.dict())
        
        return {
            "document_id": document.id,
            "optimized_headline": optimization_result.get("optimized_headline", ""),
            "optimized_summary": optimization_result.get("optimized_summary", ""),
            "suggested_skills": optimization_result.get("suggested_skills", []),
            "optimization_tips": optimization_result.get("optimization_tips", [])
        }
    
    except Exception as e:
        logger.error(f"LinkedIn optimization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LinkedIn optimization failed"
        )

# Interview preparation endpoints
@api_router.post("/interview/prepare")
async def prepare_interview(
    request: InterviewPrepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate interview preparation materials using AI."""
    try:
        # Use AI service to generate interview materials
        prep_result = await ai_service.generate_interview_questions(
            request.job_title,
            request.company_name,
            request.job_description,
            request.experience_level,
            request.interview_type
        )
        
        # Save preparation materials to database
        document = Document(
            user_id=current_user.id,
            title=f"Interview Prep - {request.company_name} ({datetime.utcnow().strftime('%Y-%m-%d')})",
            document_type=DocumentType.INTERVIEW_PREP,
            content={
                "job_title": request.job_title,
                "company_name": request.company_name,
                "job_description": request.job_description,
                "experience_level": request.experience_level,
                "interview_type": request.interview_type
            },
            generated_content=str(prep_result)
        )
        
        await db.documents.insert_one(document.dict())
        
        return {
            "document_id": document.id,
            "questions": prep_result.get("questions", []),
            "sample_answers": prep_result.get("sample_answers", []),
            "preparation_tips": prep_result.get("preparation_tips", []),
            "company_research_points": prep_result.get("company_research_points", [])
        }
    
    except Exception as e:
        logger.error(f"Interview preparation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interview preparation failed"
        )

# Document management endpoints
@api_router.get("/documents", response_model=List[Document])
async def get_user_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    document_type: Optional[DocumentType] = None,
    limit: int = 50
):
    """Get user's documents."""
    try:
        query = {"user_id": current_user.id}
        if document_type:
            query["document_type"] = document_type
        
        documents = await db.documents.find(query).sort("created_at", -1).limit(limit).to_list(limit)
        return [Document(**doc) for doc in documents]
    
    except Exception as e:
        logger.error(f"Get documents error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )

@api_router.get("/documents/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get specific document."""
    try:
        document = await db.documents.find_one({
            "id": document_id,
            "user_id": current_user.id
        })
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return Document(**document)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )

# Document download endpoints
@api_router.get("/documents/{document_id}/download/{format}")
async def download_document(
    document_id: str,
    format: DocumentFormat,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Download document in specified format."""
    try:
        # Get document
        document = await db.documents.find_one({
            "id": document_id,
            "user_id": current_user.id
        })
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc_obj = Document(**document)
        
        # Generate document based on type and format
        if doc_obj.document_type == DocumentType.RESUME:
            if format == DocumentFormat.DOCX:
                buffer = document_generator.generate_resume_docx(doc_obj.content, doc_obj.generated_content)
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                filename = f"resume_{document_id}.docx"
            else:  # PDF
                buffer = document_generator.generate_resume_pdf(doc_obj.content, doc_obj.generated_content)
                media_type = "application/pdf"
                filename = f"resume_{document_id}.pdf"
        
        elif doc_obj.document_type == DocumentType.COVER_LETTER:
            cover_letter_data = {
                "content": doc_obj.generated_content,
                "company_name": doc_obj.content.get("company_name", ""),
                "signature": current_user.full_name
            }
            
            if format == DocumentFormat.DOCX:
                buffer = document_generator.generate_cover_letter_docx(cover_letter_data)
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                filename = f"cover_letter_{document_id}.docx"
            else:  # PDF
                buffer = document_generator.generate_cover_letter_pdf(cover_letter_data)
                media_type = "application/pdf"
                filename = f"cover_letter_{document_id}.pdf"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document type not supported for download"
            )
        
        return StreamingResponse(
            io.BytesIO(buffer.read()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document download error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document download failed"
        )

# Analytics endpoints
@api_router.get("/analytics/user")
async def get_user_analytics_data(
    current_user: User = Depends(get_current_user)
):
    """Get user analytics."""
    try:
        analytics = await get_user_analytics(current_user.id)
        return analytics
    except Exception as e:
        logger.error(f"User analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )

# Admin endpoints
@api_router.get("/admin/analytics", response_model=SystemAnalytics)
async def get_system_analytics_data(
    current_user: User = Depends(get_admin_user)
):
    """Get system analytics (Admin only)."""
    try:
        analytics = await get_system_analytics()
        return SystemAnalytics(**analytics)
    except Exception as e:
        logger.error(f"System analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system analytics"
        )

@api_router.get("/admin/users", response_model=List[AdminUserView])
async def get_all_users(
    current_user: User = Depends(get_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
    limit: int = 100,
    skip: int = 0
):
    """Get all users (Admin only)."""
    try:
        users = await db.users.find().skip(skip).limit(limit).to_list(limit)
        return [AdminUserView(**user) for user in users]
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@api_router.put("/admin/users/{user_id}")
async def update_user_admin(
    user_id: str,
    user_update: AdminUserUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update user (Admin only)."""
    try:
        update_data = user_update.dict(exclude_unset=True)
        if update_data:
            result = await db.users.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        return {"message": "User updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

# Include the router in the main app
app.include_router(api_router)
