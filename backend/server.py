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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    try:
        # Find the user's most recent uploaded file
        file_record = await database.uploaded_files.find_one({
            "user_id": current_user.id,
            "processed": False
        }, sort=[("upload_time", -1)])
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
        # Import and run CrewAI analysis
        from web_crew import WebOptimizedResumeCrew
        
        # Determine job input type and content
        is_job_url = bool(request.job_url)
        job_input = request.job_url if is_job_url else request.job_description
        
        # Create and run the crew analysis
        crew_system = WebOptimizedResumeCrew(
            resume_file_path=file_record["file_path"],
            job_input=job_input,
            company_name=request.company_name,
            is_job_url=is_job_url
        )
        
        # Run the analysis (this will take some time)
        print(f"🔄 Starting CrewAI analysis for user {current_user.email}")
        result = crew_system.run_analysis()
        
        if result["status"] == "success":
            # Mark file as processed
            await database.uploaded_files.update_one(
                {"_id": file_record["_id"]},
                {"$set": {"processed": True, "processed_at": datetime.utcnow()}}
            )
            
            # Store analysis result in database
            analysis_record = {
                "_id": str(uuid.uuid4()),
                "user_id": current_user.id,
                "file_id": file_record["_id"],
                "job_input": job_input,
                "company_name": request.company_name,
                "is_job_url": is_job_url,
                "analysis_result": result,
                "created_at": datetime.utcnow()
            }
            
            await database.analysis_results.insert_one(analysis_record)
            
            print(f"✅ CrewAI analysis completed for user {current_user.email}")
            
            return {
                "status": "success",
                "message": "Resume analysis completed successfully",
                "analysis_id": analysis_record["_id"],
                "job_input": job_input,
                "company_name": request.company_name,
                "result": result
            }
        else:
            print(f"❌ CrewAI analysis failed for user {current_user.email}: {result['message']}")
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        print(f"❌ Analysis error for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/analysis/results/{analysis_id}")
async def get_analysis_results(
    analysis_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed analysis results"""
    try:
        # Find analysis record
        analysis = await database.analysis_results.find_one({
            "_id": analysis_id,
            "user_id": current_user.id
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Read output files
        results = {}
        output_files = {
            "job_analysis": "/app/output/job_analysis.json",
            "resume_optimization": "/app/output/resume_optimization.json", 
            "company_research": "/app/output/company_research.json",
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
            "created_at": analysis["created_at"],
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

@app.get("/api/analysis/download/{analysis_id}/{file_type}")
async def download_analysis_file(
    analysis_id: str,
    file_type: str,
    current_user: User = Depends(get_current_user)
):
    """Download analysis files (resume, report, etc.)"""
    try:
        # Verify user owns this analysis
        analysis = await database.analysis_results.find_one({
            "_id": analysis_id,
            "user_id": current_user.id
        })
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Map file types to paths including new agent outputs
        file_mapping = {
            "optimized_resume": "/app/output/optimized_resume.md",
            "final_report": "/app/output/final_report.md",
            "job_analysis": "/app/output/job_analysis.json",
            "resume_optimization": "/app/output/resume_optimization.json",
            "company_research": "/app/output/company_research.json",
            "cover_letter": "/app/output/cover_letter.json",
            "linkedin_optimization": "/app/output/linkedin_optimization.json",
            "interview_preparation": "/app/output/interview_preparation.json"
        }
        
        if file_type not in file_mapping:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        file_path = file_mapping[file_type]
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # For now, return file content as JSON
        # In Phase 4, we'll add proper document generation (DOCX/PDF)
        with open(file_path, 'r') as f:
            content = f.read()
        
        return {
            "file_type": file_type,
            "filename": f"{file_type}_{analysis_id}",
            "content": content,
            "message": "File content retrieved successfully. Professional DOCX/PDF generation coming in Phase 4."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

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

# Extended analysis endpoints for new AI agents
@app.post("/api/analyze/extended")
async def analyze_extended(
    request: JobAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Run complete analysis with all 8 agents including new ones"""
    # Validate input
    if not request.job_url and not request.job_description:
        raise HTTPException(status_code=400, detail="Either job_url or job_description must be provided")
    
    try:
        # Find the user's most recent uploaded file
        file_record = await database.uploaded_files.find_one({
            "user_id": current_user.id,
            "processed": False
        }, sort=[("upload_time", -1)])
        
        if not file_record:
            raise HTTPException(status_code=400, detail="No resume file found. Please upload a resume first.")
        
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
            
            print(f"✅ Extended CrewAI analysis completed for user {current_user.email}")
            
            return {
                "status": "success",
                "message": "Extended resume analysis completed successfully",
                "analysis_id": analysis_record["_id"],
                "job_input": job_input,
                "company_name": request.company_name,
                "analysis_type": "extended",
                "result": result
            }
        else:
            print(f"❌ Extended CrewAI analysis failed for user {current_user.email}: {result['message']}")
            raise HTTPException(status_code=500, detail=result["message"])
            
    except Exception as e:
        print(f"❌ Extended analysis error for user {current_user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extended analysis failed: {str(e)}")

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
            "user_id": current_user.id,
            "processed": False
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
            "user_id": current_user.id,
            "processed": False
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
            "user_id": current_user.id,
            "processed": False
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

@app.get("/api/test/gemini")
async def test_gemini_connection():
    """Test endpoint for Gemini API connection"""
    try:
        from gemini_config import test_gemini_connection
        result = await test_gemini_connection()
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
            "database": "connected" if database is not None else "disconnected",
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "not configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)