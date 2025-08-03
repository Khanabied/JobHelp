from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# Initialize FastAPI app
app = FastAPI(title="Resume Optimization Platform", version="1.0.0")

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
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# MongoDB connection
mongodb_client = None
database = None

@app.on_event("startup")
async def startup_event():
    global mongodb_client, database
    mongodb_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    mongodb_client = AsyncIOMotorClient(mongodb_url)
    database = mongodb_client.resume_platform

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
    return {"message": "Resume Optimization Platform API", "status": "running"}

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

@app.post("/api/analyze/job")
async def analyze_job(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    # Validate input
    if not request.job_url and not request.job_description:
        raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
    
    # For now, return a placeholder response
    # This will be implemented in Phase 2 with CrewAI integration
    return {
        "message": "Job analysis endpoint ready",
        "job_url": request.job_url,
        "company_name": request.company_name,
        "has_description": bool(request.job_description),
        "status": "pending_implementation"
    }

@app.delete("/api/cleanup/{file_id}")
async def cleanup_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    # Find file record
    file_record = await database.uploaded_files.find_one({
        "_id": file_id,
        "user_id": current_user.id
    })
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Remove physical file
    file_path = file_record.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
        # Also remove temp directory if empty
        temp_dir = os.path.dirname(file_path)
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass  # Directory not empty or doesn't exist
    
    # Remove database record
    await database.uploaded_files.delete_one({"_id": file_id})
    
    return {"message": "File cleaned up successfully"}

@app.get("/api/test/gemini")
async def test_gemini_connection():
    """Test endpoint for Gemini API connection"""
    try:
        from crew_integration import crew_integration
        result = await crew_integration.test_gemini()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini test failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Resume Optimization Platform API is running",
        "services": {
            "database": "connected" if database else "disconnected",
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "not configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)