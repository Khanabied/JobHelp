from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import jwt
import bcrypt
import uuid
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Import our new modules
from document_generator import DocumentGenerator, generate_all_documents
from progress_tracker import progress_tracker, get_analysis_steps
from admin_analytics import AdminAnalytics, EventTracker, AdminDashboardResponse

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Resume Optimization Platform", version="1.0.0")

# CORS configuration - using newer syntax
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# MongoDB connection
mongodb_client = None
database = None
admin_analytics = None
event_tracker = None

@app.on_event("startup")
async def startup_event():
    global mongodb_client, database, admin_analytics, event_tracker
    mongodb_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    mongodb_client = AsyncIOMotorClient(mongodb_url)
    database = mongodb_client.jobsasa_platform
    
    # Initialize analytics services
    admin_analytics = AdminAnalytics(database)
    event_tracker = EventTracker(database)

@app.on_event("shutdown")
async def shutdown_event():
    if mongodb_client:
        mongodb_client.close()

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime

class JobAnalysisRequest(BaseModel):
    job_url: Optional[str] = None
    job_description: Optional[str] = None
    company_name: str

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_data: dict) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = user_data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await database.users.find_one({"_id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(
            id=user["_id"],
            email=user["email"],
            full_name=user["full_name"],
            created_at=user["created_at"]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def run_extended_analysis_with_progress(session_id: str, file_record: dict, request: JobAnalysisRequest, current_user: User):
    """Run extended analysis with progress tracking"""
    try:
        # Import and run extended CrewAI analysis
        from extended_crew import ExtendedCareerOptimizationCrew
        
        # Determine job input type and content
        is_job_url = bool(request.job_url)
        job_input = request.job_url if is_job_url else request.job_description
        
        # Create and run the extended crew analysis
        extended_crew = ExtendedCareerOptimizationCrew(
            resume_file_path=file_record["file_path"],
            job_input=job_input,
            company_name=request.company_name,
            is_job_url=is_job_url
        )
        
        # Run the extended analysis (this will take some time)
        print(f"🔄 Starting extended CrewAI analysis for user {current_user.email}")
        result = extended_crew.run_extended_analysis()
        
        if result["status"] == "success":
            # Mark file as processed
            await database.uploaded_files.update_one(
                {"_id": file_record["_id"]},
                {"$set": {"processed": True, "processed_at": datetime.utcnow()}}
            )
            
            # Store extended analysis result in database
            analysis_record = {
                "_id": str(uuid.uuid4()),
                "user_id": current_user.id,
                "file_id": file_record["_id"],
                "job_input": job_input,
                "company_name": request.company_name,
                "is_job_url": is_job_url,
                "analysis_type": "extended",
                "analysis_result": result,
                "created_at": datetime.utcnow()
            }
            
            await database.analysis_results.insert_one(analysis_record)
            
            # Update progress to completed
            progress_tracker.complete_session(session_id, {
                "status": "success",
                "message": "Extended resume analysis completed successfully",
                "analysis_id": analysis_record["_id"],
                "job_input": job_input,
                "company_name": request.company_name,
                "analysis_type": "extended",
                "result": result
            })
            
            print(f"✅ Extended CrewAI analysis completed for user {current_user.email}")
        else:
            # Update progress to failed
            progress_tracker.fail_session(session_id, result["message"])
            print(f"❌ Extended CrewAI analysis failed for user {current_user.email}: {result['message']}")
            
    except Exception as e:
        # Update progress to failed
        progress_tracker.fail_session(session_id, f"Extended analysis failed: {str(e)}")
        print(f"❌ Extended analysis error for user {current_user.email}: {str(e)}")

# Routes
@app.get("/")
async def root():
    return {"message": "Resume Optimization Platform API", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Resume Optimization Platform API is running",
        "services": {
            "database": "connected" if database is not None else "disconnected",
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "not configured"
        }
    }

@app.get("/api/test/gemini")
async def test_gemini_connection():
    """Test endpoint for Gemini API connection"""
    try:
        from gemini_config import test_gemini_connection
        result = await test_gemini_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini test failed: {str(e)}")

@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await database.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    new_user = {
        "_id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    await database.users.insert_one(new_user)
    
    # Track registration event
    if event_tracker:
        await event_tracker.track_event(user_id, "user_registered", {
            "email": user_data.email,
            "full_name": user_data.full_name
        })
    
    # Create JWT token
    token = create_jwt_token({"user_id": user_id, "email": user_data.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name
        }
    }

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    # Find user
    user = await database.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    token = create_jwt_token({"user_id": user["_id"], "email": user["email"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    }

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/upload/resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create temporary file
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    try:
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Store file info in database
        file_id = str(uuid.uuid4())
        file_record = {
            "_id": file_id,
            "user_id": current_user.id,
            "filename": file.filename,
            "file_path": temp_file_path,
            "upload_time": datetime.utcnow(),
            "processed": False
        }
        
        await database.uploaded_files.insert_one(file_record)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Extended analysis endpoints for new AI agents
@app.post("/api/analyze/extended")
async def analyze_extended(
    request: JobAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Run complete analysis with all 8 agents including new ones"""
    # Validate input
    if not request.job_url and not request.job_description:
        raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
    
    try:
        # Find the user's most recent uploaded file
        file_record = await database.uploaded_files.find_one({
            "user_id": current_user.id
        }, sort=[("upload_time", -1)])
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
        # Create progress tracking session
        session_id = str(uuid.uuid4())
        steps = get_analysis_steps("extended")
        progress_tracker.create_session(session_id, steps)
        
        # Start background analysis
        background_tasks.add_task(
            run_extended_analysis_with_progress,
            session_id,
            file_record,
            request,
            current_user
        )
        
        return {
            "status": "started",
            "message": "Extended resume analysis started",
            "session_id": session_id,
            "progress_url": f"/api/progress/{session_id}"
        }
            
    except Exception as e:
        print(f"❌ Extended analysis error for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extended analysis failed: {str(e)}")

@app.get("/api/progress/{session_id}")
async def get_progress(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get progress of an analysis session"""
    progress = progress_tracker.get_progress(session_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Progress session not found")
    
    return progress

@app.post("/api/documents/generate")
async def generate_documents(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate professional documents from analysis results"""
    try:
        # Get analysis results
        analysis = await database.analysis_results.find_one({
            "_id": analysis_id,
            "user_id": current_user.id
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Read all output files
        results = {}
        output_files = {
            "job_analysis": "/app/output/job_analysis.json",
            "resume_optimization": "/app/output/resume_optimization.json", 
            "company_research": "/app/output/company_research.json",
            "cover_letter": "/app/output/cover_letter.json",
            "linkedin_optimization": "/app/output/linkedin_optimization.json",
            "interview_preparation": "/app/output/interview_preparation.json",
            "optimized_resume": "/app/output/optimized_resume.md",
            "final_report": "/app/output/final_report.md"
        }
        
        for key, file_path in output_files.items():
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if file_path.endswith('.json'):
                            import json
                            results[key] = json.loads(content)
                        else:
                            results[key] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    results[key] = None
        
        # Generate professional documents
        generated_files = generate_all_documents(results, current_user.id)
        
        # Store document info in database
        doc_record = {
            "_id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "analysis_id": analysis_id,
            "generated_files": generated_files,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=48)  # 48 hour expiry
        }
        
        await database.generated_documents.insert_one(doc_record)
        
        return {
            "status": "success",
            "message": "Professional documents generated",
            "document_id": doc_record["_id"],
            "available_documents": list(generated_files.keys()),
            "expires_at": doc_record["expires_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")

@app.get("/api/documents/download/{document_id}/{file_type}")
async def download_document(
    document_id: str,
    file_type: str,
    current_user: User = Depends(get_current_user)
):
    """Download a generated document"""
    try:
        # Find document record
        doc_record = await database.generated_documents.find_one({
            "_id": document_id,
            "user_id": current_user.id
        })
        
        if not doc_record:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check expiry
        if doc_record["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=410, detail="Document has expired")
        
        # Get file path
        file_path = doc_record["generated_files"].get(file_type)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Return file
        filename = Path(file_path).name
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/documents/list")
async def list_user_documents(
    current_user: User = Depends(get_current_user)
):
    """List all generated documents for a user"""
    try:
        # Find all non-expired documents for user
        cursor = database.generated_documents.find({
            "user_id": current_user.id,
            "expires_at": {"$gt": datetime.utcnow()}
        }).sort("created_at", -1)
        
        documents = []
        async for doc in cursor:
            documents.append({
                "document_id": doc["_id"],
                "analysis_id": doc["analysis_id"],
                "available_files": list(doc["generated_files"].keys()),
                "created_at": doc["created_at"],
                "expires_at": doc["expires_at"]
            })
        
        return {
            "documents": documents,
            "total_count": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.post("/api/agents/cover-letter")
async def generate_cover_letter(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate cover letter independently"""
    if not request.job_url and not request.job_description:
        raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
    
    try:
        file_record = await database.uploaded_files.find_one({
            "user_id": current_user.id
        }, sort=[("upload_time", -1)])
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
        from extended_crew import ExtendedCareerOptimizationCrew
        
        is_job_url = bool(request.job_url)
        job_input = request.job_url if is_job_url else request.job_description
        
        extended_crew = ExtendedCareerOptimizationCrew(
            resume_file_path=file_record["file_path"],
            job_input=job_input,
            company_name=request.company_name,
            is_job_url=is_job_url
        )
        
        print(f"🔄 Starting cover letter generation for user {current_user.email}")
        result = extended_crew.run_individual_agent("cover_letter")
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": "Cover letter generated successfully",
                "agent_type": "cover_letter",
                "result": result
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        print(f"❌ Cover letter generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {str(e)}")

@app.post("/api/agents/linkedin")
async def optimize_linkedin(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Optimize LinkedIn profile independently"""
    if not request.job_url and not request.job_description:
        raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
    
    try:
        file_record = await database.uploaded_files.find_one({
            "user_id": current_user.id
        }, sort=[("upload_time", -1)])
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
        from extended_crew import ExtendedCareerOptimizationCrew
        
        is_job_url = bool(request.job_url)
        job_input = request.job_url if is_job_url else request.job_description
        
        extended_crew = ExtendedCareerOptimizationCrew(
            resume_file_path=file_record["file_path"],
            job_input=job_input,
            company_name=request.company_name,
            is_job_url=is_job_url
        )
        
        print(f"🔄 Starting LinkedIn optimization for user {current_user.email}")
        result = extended_crew.run_individual_agent("linkedin")
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": "LinkedIn optimization completed successfully",
                "agent_type": "linkedin",
                "result": result
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        print(f"❌ LinkedIn optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LinkedIn optimization failed: {str(e)}")

@app.post("/api/agents/interview")
async def prepare_interview(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate interview preparation materials independently"""
    if not request.job_url and not request.job_description:
        raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
    
    try:
        file_record = await database.uploaded_files.find_one({
            "user_id": current_user.id
        }, sort=[("upload_time", -1)])
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
        from extended_crew import ExtendedCareerOptimizationCrew
        
        is_job_url = bool(request.job_url)
        job_input = request.job_url if is_job_url else request.job_description
        
        extended_crew = ExtendedCareerOptimizationCrew(
            resume_file_path=file_record["file_path"],
            job_input=job_input,
            company_name=request.company_name,
            is_job_url=is_job_url
        )
        
        print(f"🔄 Starting interview preparation for user {current_user.email}")
        result = extended_crew.run_individual_agent("interview")
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": "Interview preparation completed successfully",
                "agent_type": "interview",
                "result": result
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        print(f"❌ Interview preparation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Interview preparation failed: {str(e)}")

@app.post("/api/agents/basic-resume")
async def optimize_resume_basic(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate basic optimized resume only"""
    if not request.job_url and not request.job_description:
        raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
    
    try:
        file_record = await database.uploaded_files.find_one({
            "user_id": current_user.id
        }, sort=[("upload_time", -1)])
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
        # Track event
        if event_tracker:
            await event_tracker.track_event(current_user.id, "basic_resume_generation", {
                "company_name": request.company_name,
                "has_job_url": bool(request.job_url)
            })
        
        from web_crew import WebOptimizedResumeCrew
        
        is_job_url = bool(request.job_url)
        job_input = request.job_url if is_job_url else request.job_description
        
        resume_crew = WebOptimizedResumeCrew(
            resume_file_path=file_record["file_path"],
            job_input=job_input,
            company_name=request.company_name,
            is_job_url=is_job_url
        )
        
        print(f"🔄 Starting basic resume optimization for user {current_user.email}")
        result = resume_crew.run_analysis()
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": "Basic resume optimization completed successfully",
                "agent_type": "basic_resume",
                "result": result
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        print(f"❌ Basic resume optimization error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Basic resume optimization failed: {str(e)}")

# Admin Dashboard Endpoints
@app.get("/api/admin/dashboard")
async def get_admin_dashboard(
    period_days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive admin dashboard metrics"""
    # For now, simple admin check - in production, implement proper admin role
    if not current_user.email.endswith("@admin.jobsasa.com") and current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        if admin_analytics:
            dashboard_data = await admin_analytics.get_comprehensive_dashboard(period_days)
            return dashboard_data
        else:
            raise HTTPException(status_code=500, detail="Analytics service not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get admin dashboard: {str(e)}")

@app.get("/api/admin/users")
async def get_admin_users(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get user list for admin"""
    # Simple admin check
    if not current_user.email.endswith("@admin.jobsasa.com") and current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        skip = (page - 1) * limit
        
        # Get users with pagination
        cursor = database.users.find(
            {},
            {"password": 0}  # Exclude password field
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        users = []
        async for user in cursor:
            # Get user's analysis count
            analysis_count = await database.analysis_results.count_documents({
                "user_id": user["_id"]
            })
            
            users.append({
                "id": user["_id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "created_at": user["created_at"],
                "analysis_count": analysis_count
            })
        
        # Get total count for pagination
        total_count = await database.users.count_documents({})
        
        return {
            "users": users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@app.get("/api/admin/analytics/events")
async def get_admin_events(
    event_type: Optional[str] = None,
    period_days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """Get user events for admin analytics"""
    # Simple admin check
    if not current_user.email.endswith("@admin.jobsasa.com") and current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Build query
        query = {"timestamp": {"$gte": start_date}}
        if event_type:
            query["event_type"] = event_type
        
        # Get events
        cursor = database.user_events.find(query).sort("timestamp", -1).limit(1000)
        
        events = []
        async for event in cursor:
            events.append({
                "user_id": event["user_id"],
                "event_type": event["event_type"],
                "event_data": event.get("event_data", {}),
                "timestamp": event["timestamp"]
            })
        
        return {
            "events": events,
            "period_days": period_days,
            "event_type_filter": event_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")

# Enhanced progress tracking with session completion
@app.post("/api/analyze/extended")
async def analyze_extended(
    request: JobAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Run complete analysis with all 8 agents including new ones"""
    # Validate input
    if not request.job_url and not request.job_description:
        raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
    
    try:
        # Find the user's most recent uploaded file
        file_record = await database.uploaded_files.find_one({
            "user_id": current_user.id
        }, sort=[("upload_time", -1)])
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
        # Track event
        if event_tracker:
            await event_tracker.track_event(current_user.id, "extended_analysis_started", {
                "company_name": request.company_name,
                "has_job_url": bool(request.job_url)
            })
        
        # Create progress tracking session
        session_id = str(uuid.uuid4())
        steps = get_analysis_steps("extended")
        progress_tracker.create_session(session_id, steps)
        
        # Start background analysis
        background_tasks.add_task(
            run_extended_analysis_with_progress,
            session_id,
            file_record,
            request,
            current_user
        )
        
        return {
            "status": "started",
            "message": "Extended resume analysis started",
            "session_id": session_id,
            "progress_url": f"/api/progress/{session_id}"
        }
            
    except Exception as e:
        print(f"❌ Extended analysis error for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extended analysis failed: {str(e)}")

@app.get("/api/analysis/extended-results/{analysis_id}")
async def get_extended_analysis_results(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed extended analysis results including new agent outputs"""
    try:
        # Find analysis record
        analysis = await database.analysis_results.find_one({
            "_id": analysis_id,
            "user_id": current_user.id
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Track event
        if event_tracker:
            await event_tracker.track_event(current_user.id, "results_viewed", {
                "analysis_id": analysis_id,
                "analysis_type": analysis.get("analysis_type", "basic")
            })
        
        # Read all output files including new ones
        results = {}
        output_files = {
            "job_analysis": "/app/output/job_analysis.json",
            "resume_optimization": "/app/output/resume_optimization.json", 
            "company_research": "/app/output/company_research.json",
            "cover_letter": "/app/output/cover_letter.json",
            "linkedin_optimization": "/app/output/linkedin_optimization.json",
            "interview_preparation": "/app/output/interview_preparation.json",
            "optimized_resume": "/app/output/optimized_resume.md",
            "final_report": "/app/output/final_report.md"
        }
        
        for key, file_path in output_files.items():
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if file_path.endswith('.json'):
                            import json
                            results[key] = json.loads(content)
                        else:
                            results[key] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    results[key] = None
            else:
                results[key] = None
        
        return {
            "analysis_id": analysis_id,
            "job_input": analysis["job_input"],
            "company_name": analysis["company_name"],
            "is_job_url": analysis["is_job_url"],
            "analysis_type": analysis.get("analysis_type", "basic"),
            "created_at": analysis["created_at"],
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get extended results: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)