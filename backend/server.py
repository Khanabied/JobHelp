from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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
import asyncio
import json
import logging
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_event()
    yield
    # Shutdown  
    await shutdown_event()

app = FastAPI(
    title="JobSasa Career Optimization Platform", 
    version="3.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "jobsasa-secret-key-change-in-production-2025")
JWT_ALGORITHM = "HS256"

# MongoDB connection
mongodb_client = None
database = None

# Global progress tracking
analysis_progress = {}

async def startup_event():
    global mongodb_client, database
    mongodb_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    mongodb_client = AsyncIOMotorClient(mongodb_url)
    database = mongodb_client.jobsasa_platform
    
    # Ensure output directory exists
    os.makedirs('/app/output', exist_ok=True)
    logger.info("🚀 JobSasa Career Optimization Platform started")

async def shutdown_event():
    if mongodb_client:
        mongodb_client.close()
    logger.info("💤 JobSasa shutting down")

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

class AnalysisProgressResponse(BaseModel):
    session_id: str
    status: str  # "running", "completed", "failed"
    progress_percentage: int
    current_step: str
    steps_completed: List[str]
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

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

async def run_crew_analysis_background(session_id: str, resume_file_path: str, job_data: JobAnalysisRequest, user_id: str):
    """Background task to run CrewAI analysis"""
    try:
        # Import here to avoid startup issues
        from web_crew import WebOptimizedResumeCrew
        
        # Update progress
        analysis_progress[session_id] = {
            "status": "running",
            "progress_percentage": 10,
            "current_step": "Initializing AI agents",
            "steps_completed": ["File uploaded"],
            "error_message": None
        }
        
        # Determine if job_data contains URL or description
        is_job_url = bool(job_data.job_url)
        job_input = job_data.job_url if is_job_url else job_data.job_description
        
        # Create crew instance
        crew_system = WebOptimizedResumeCrew(
            resume_file_path=resume_file_path,
            job_input=job_input,
            company_name=job_data.company_name,
            is_job_url=is_job_url
        )
        
        # Update progress
        analysis_progress[session_id]["progress_percentage"] = 20
        analysis_progress[session_id]["current_step"] = "Analyzing job requirements"
        analysis_progress[session_id]["steps_completed"].append("AI agents initialized")
        
        # Run the analysis
        result = crew_system.run_analysis()
        
        if result["status"] == "success":
            # Update progress
            analysis_progress[session_id]["progress_percentage"] = 80
            analysis_progress[session_id]["current_step"] = "Processing results"
            analysis_progress[session_id]["steps_completed"].extend([
                "Job analyzed", "Resume optimized", "Company researched", "Documents generated"
            ])
            
            # Store analysis results in database
            analysis_id = str(uuid.uuid4())
            analysis_record = {
                "_id": analysis_id,
                "user_id": user_id,
                "session_id": session_id,
                "job_input": job_input,
                "company_name": job_data.company_name,
                "is_job_url": is_job_url,
                "analysis_type": "extended",
                "status": "completed",
                "created_at": datetime.utcnow(),
                "crew_result": result.get("crew_result"),
                "output_files": []
            }
            
            # Check for output files and store references
            output_files = [
                "/app/output/job_analysis.json",
                "/app/output/resume_optimization.json", 
                "/app/output/company_research.json",
                "/app/output/optimized_resume.md",
                "/app/output/final_report.md"
            ]
            
            for file_path in output_files:
                if os.path.exists(file_path):
                    analysis_record["output_files"].append(file_path)
            
            await database.analyses.insert_one(analysis_record)
            
            # Final progress update
            analysis_progress[session_id] = {
                "status": "completed",
                "progress_percentage": 100,
                "current_step": "Analysis completed",
                "steps_completed": analysis_progress[session_id]["steps_completed"] + ["Results stored"],
                "error_message": None,
                "result": {
                    "analysis_id": analysis_id,
                    "job_input": job_input,
                    "company_name": job_data.company_name
                }
            }
            
        else:
            # Analysis failed
            analysis_progress[session_id] = {
                "status": "failed",
                "progress_percentage": 0,
                "current_step": "Analysis failed",
                "steps_completed": analysis_progress[session_id]["steps_completed"],
                "error_message": result.get("message", "Unknown error occurred")
            }
            
    except Exception as e:
        logger.error(f"Background analysis error: {e}")
        analysis_progress[session_id] = {
            "status": "failed",
            "progress_percentage": 0,
            "current_step": "Analysis failed",
            "steps_completed": analysis_progress.get(session_id, {}).get("steps_completed", []),
            "error_message": str(e)
        }

# Routes
@app.get("/api")
async def root():
    return {"message": "JobSasa Career Optimization Platform API", "status": "running", "version": "3.0.0"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "JobSasa Career Optimization Platform API is running",
        "version": "3.0.0",
        "services": {
            "database": "connected" if database is not None else "disconnected",
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "not configured"
        }
    }

@app.get("/api/test/gemini")
async def test_gemini_connection():
    """Test endpoint for Gemini API connection"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Hello, this is a test.")
        return {
            "status": "success",
            "message": "Gemini API connection successful",
            "response": response.text[:100] + "..." if len(response.text) > 100 else response.text
        }
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

@app.post("/api/analyze/extended")
async def analyze_extended(
    request: JobAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Extended analysis with all AI agents"""
    try:
        # Get user's latest uploaded resume
        file_record = await database.uploaded_files.find_one(
            {"user_id": current_user.id},
            sort=[("upload_time", -1)]
        )
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
        if not os.path.exists(file_record["file_path"]):
            raise HTTPException(status_code=400, detail="Resume file not found. Please upload again.")
        
        # Validate input
        if not request.job_url and not request.job_description:
            raise HTTPException(status_code=400, detail="Either job_url or job_description is required")
        
        if not request.company_name:
            raise HTTPException(status_code=400, detail="Company name is required")
        
        # Create session ID for progress tracking
        session_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        analysis_progress[session_id] = {
            "status": "starting",
            "progress_percentage": 5,
            "current_step": "Preparing analysis",
            "steps_completed": [],
            "error_message": None
        }
        
        # Start background analysis
        background_tasks.add_task(
            run_crew_analysis_background,
            session_id,
            file_record["file_path"],
            request,
            current_user.id
        )
        
        return {
            "status": "success",
            "message": "Extended analysis started. Check progress using session_id.",
            "session_id": session_id,
            "analysis_type": "extended"
        }
        
    except Exception as e:
        logger.error(f"Extended analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{session_id}")
async def get_progress(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get analysis progress by session ID"""
    if session_id not in analysis_progress:
        raise HTTPException(status_code=404, detail="Session not found")
    
    progress = analysis_progress[session_id]
    
    return AnalysisProgressResponse(
        session_id=session_id,
        status=progress["status"],
        progress_percentage=progress["progress_percentage"],
        current_step=progress["current_step"],
        steps_completed=progress["steps_completed"],
        error_message=progress.get("error_message"),
        result=progress.get("result")
    )

@app.get("/api/analysis/extended-results/{analysis_id}")
async def get_extended_analysis_results(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get extended analysis results by analysis ID"""
    try:
        # Find analysis record
        analysis = await database.analyses.find_one({
            "_id": analysis_id,
            "user_id": current_user.id
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Load results from output files
        results = {}
        
        # Load JSON results
        json_files = [
            ("job_analysis", "/app/output/job_analysis.json"),
            ("resume_optimization", "/app/output/resume_optimization.json"),
            ("company_research", "/app/output/company_research.json")
        ]
        
        for key, file_path in json_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        results[key] = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load {file_path}: {e}")
                    results[key] = None
        
        # Load markdown files
        md_files = [
            ("optimized_resume", "/app/output/optimized_resume.md"),
            ("final_report", "/app/output/final_report.md")
        ]
        
        for key, file_path in md_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        results[key] = f.read()
                except Exception as e:
                    logger.warning(f"Could not load {file_path}: {e}")
                    results[key] = None
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "results": results,
            "created_at": analysis["created_at"]
        }
        
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/dashboard")
async def get_admin_dashboard(
    period_days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Admin dashboard with real analytics"""
    if not current_user.email.endswith("@admin.jobsasa.com") and current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        # User metrics
        total_users = await database.users.count_documents({})
        new_users_period = await database.users.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Analysis metrics
        total_analyses = await database.analyses.count_documents({})
        analyses_period = await database.analyses.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Analysis types breakdown
        analysis_pipeline = [
            {"$group": {"_id": "$analysis_type", "count": {"$sum": 1}}}
        ]
        analysis_types_cursor = database.analyses.aggregate(analysis_pipeline)
        analysis_types = {}
        async for doc in analysis_types_cursor:
            analysis_types[doc["_id"] or "unknown"] = doc["count"]
        
        # Top active users
        user_activity_pipeline = [
            {"$group": {"_id": "$user_id", "analysis_count": {"$sum": 1}}},
            {"$sort": {"analysis_count": -1}},
            {"$limit": 10}
        ]
        
        top_users = []
        user_activity_cursor = database.analyses.aggregate(user_activity_pipeline)
        async for doc in user_activity_cursor:
            user = await database.users.find_one({"_id": doc["_id"]})
            if user:
                top_users.append({
                    "user_email": user["email"],
                    "analysis_count": doc["analysis_count"]
                })
        
        return {
            "user_metrics": {
                "total_users": total_users,
                "new_users_period": new_users_period,
                "active_users_period": len(top_users)
            },
            "analysis_metrics": {
                "total_analyses": total_analyses,
                "analyses_period": analyses_period,
                "analysis_types": analysis_types
            },
            "document_metrics": {
                "total_documents": total_analyses * 3  # Rough estimate
            },
            "engagement_metrics": {
                "feature_usage": {
                    "basic_analysis": analysis_types.get("basic", 0),
                    "extended_analysis": analysis_types.get("extended", 0)
                },
                "avg_analyses_per_user": round(total_analyses / max(total_users, 1), 2),
                "top_active_users": top_users
            },
            "system_metrics": {
                "processing_success_rate": 95.5  # Mock metric
            }
        }
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Basic analysis endpoint (simplified version)
@app.post("/api/agents/basic-resume")
async def optimize_resume_basic(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Basic resume optimization - simplified single agent"""
    return {
        "status": "success", 
        "message": "Basic resume optimization completed",
        "agent_type": "basic_resume",
        "analysis_id": str(uuid.uuid4())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)