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

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="JobSasa Career Optimization Platform", version="3.0.0")

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

@app.on_event("startup")
async def startup_event():
    global mongodb_client, database
    mongodb_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    mongodb_client = AsyncIOMotorClient(mongodb_url)
    database = mongodb_client.jobsasa_platform

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

# Routes
@app.get("/")
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

# Placeholder endpoints for Phase 3 features
@app.post("/api/analyze/extended")
async def analyze_extended(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Extended analysis with all 8 agents - placeholder for Phase 3"""
    return {
        "status": "success",
        "message": "Phase 3 Extended analysis endpoint - coming soon!",
        "session_id": str(uuid.uuid4()),
        "analysis_type": "extended"
    }

@app.post("/api/agents/basic-resume")
async def optimize_resume_basic(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Basic resume optimization - placeholder"""
    return {
        "status": "success", 
        "message": "Phase 3 Basic resume optimization - coming soon!",
        "agent_type": "basic_resume"
    }

@app.get("/api/admin/dashboard")
async def get_admin_dashboard(
    period_days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Admin dashboard - placeholder"""
    if not current_user.email.endswith("@admin.jobsasa.com") and current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "message": "Phase 3 Admin dashboard - coming soon!",
        "period_days": period_days,
        "user_metrics": {"total_users": 0, "active_users": 0},
        "analysis_metrics": {"total_analyses": 0}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)