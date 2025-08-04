#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Career Tools Platform
Tests all authentication, career tools, document management, and admin endpoints
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime

class CareerToolsAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.auth_token = None
        self.admin_token = None
        self.test_user_id = None
        self.admin_user_id = None
        self.test_document_id = None
        
        # Test data
        self.test_user_data = {
            "email": f"testuser_{int(time.time())}@example.com",
            "full_name": "Test User",
            "password": "SecurePass123!"
        }
        
        self.admin_credentials = {
            "email": "admin@example.com",
            "password": "admin123"
        }
        
        self.sample_resume_data = {
            "personal_info": {
                "name": "Sarah Johnson",
                "email": "sarah.johnson@example.com",
                "phone": "+1-555-0123",
                "location": "San Francisco, CA",
                "summary": "Experienced software engineer with 5+ years in full-stack development"
            },
            "work_experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "TechCorp Inc.",
                    "duration": "2021-2024",
                    "description": "Led development of microservices architecture",
                    "achievements": [
                        "Improved system performance by 40%",
                        "Mentored 3 junior developers"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "Stanford University",
                    "year": "2019",
                    "description": "Graduated Magna Cum Laude"
                }
            ],
            "skills": ["Python", "JavaScript", "React", "FastAPI", "MongoDB", "AWS"],
            "projects": [
                {
                    "name": "E-commerce Platform",
                    "description": "Built scalable e-commerce solution",
                    "technologies": ["React", "Node.js", "MongoDB"]
                }
            ]
        }
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_symbol} {test_name}: {status}")
        if details:
            print(f"    Details: {details}")
        print()
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    files: Dict = None, use_admin: bool = False) -> requests.Response:
        """Make HTTP request with proper authentication"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        # Add authentication if available
        token = self.admin_token if use_admin else self.auth_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop("Content-Type", None)
                    response = self.session.post(url, headers=headers, files=files, data=data)
                else:
                    response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            response = self.make_request("GET", "/api/health")
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_test("Health Check", "PASS", f"Status: {data['status']}")
                    return True
                else:
                    self.log_test("Health Check", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                self.log_test("Health Check", "FAIL", f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_user_registration(self) -> bool:
        """Test user registration"""
        try:
            response = self.make_request("POST", "/api/auth/register", self.test_user_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.auth_token = data["access_token"]
                    self.test_user_id = data["user"]["id"]
                    self.log_test("User Registration", "PASS", 
                                f"User ID: {self.test_user_id}")
                    return True
                else:
                    self.log_test("User Registration", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("User Registration", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("User Registration", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_user_login(self) -> bool:
        """Test user login"""
        try:
            login_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            response = self.make_request("POST", "/api/auth/login", login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    # Update token (should be same as registration)
                    self.auth_token = data["access_token"]
                    self.log_test("User Login", "PASS", 
                                f"Token received for user: {data['user']['email']}")
                    return True
                else:
                    self.log_test("User Login", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("User Login", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("User Login", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_admin_login(self) -> bool:
        """Test admin login"""
        try:
            response = self.make_request("POST", "/api/auth/login", self.admin_credentials)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    self.admin_user_id = data["user"]["id"]
                    if data["user"]["role"] == "admin":
                        self.log_test("Admin Login", "PASS", 
                                    f"Admin token received for: {data['user']['email']}")
                        return True
                    else:
                        self.log_test("Admin Login", "FAIL", 
                                    f"User is not admin: {data['user']['role']}")
                        return False
                else:
                    self.log_test("Admin Login", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Admin Login", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_get_current_user(self) -> bool:
        """Test get current user info"""
        try:
            response = self.make_request("GET", "/api/users/me")
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "email" in data:
                    self.log_test("Get Current User", "PASS", 
                                f"User: {data['email']}, Role: {data.get('role', 'N/A')}")
                    return True
                else:
                    self.log_test("Get Current User", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Get Current User", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Get Current User", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_update_user_profile(self) -> bool:
        """Test update user profile"""
        try:
            update_data = {
                "full_name": "Sarah Johnson Updated",
                "profile_data": {
                    "bio": "Updated bio for testing",
                    "location": "New York, NY"
                }
            }
            response = self.make_request("PUT", "/api/users/me", update_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("full_name") == update_data["full_name"]:
                    self.log_test("Update User Profile", "PASS", 
                                f"Updated name: {data['full_name']}")
                    return True
                else:
                    self.log_test("Update User Profile", "FAIL", f"Update not reflected: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Update User Profile", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Update User Profile", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_resume_optimization(self) -> bool:
        """Test resume optimization with AI"""
        try:
            request_data = {
                "resume_data": self.sample_resume_data,
                "job_description": "Looking for a senior software engineer with Python and React experience",
                "target_position": "Senior Software Engineer"
            }
            response = self.make_request("POST", "/api/resume/optimize", request_data)
            
            if response.status_code == 200:
                data = response.json()
                if "document_id" in data and "optimized_content" in data:
                    self.test_document_id = data["document_id"]
                    self.log_test("Resume Optimization", "PASS", 
                                f"Document ID: {data['document_id']}, Score: {data.get('score', 'N/A')}")
                    return True
                else:
                    self.log_test("Resume Optimization", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Resume Optimization", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Resume Optimization", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_cover_letter_generation(self) -> bool:
        """Test cover letter generation"""
        try:
            request_data = {
                "job_title": "Senior Software Engineer",
                "company_name": "Google",
                "job_description": "We are looking for a senior software engineer to join our team...",
                "resume_data": self.sample_resume_data,
                "additional_notes": "I am particularly interested in working on machine learning projects"
            }
            response = self.make_request("POST", "/api/cover-letter/generate", request_data)
            
            if response.status_code == 200:
                data = response.json()
                if "document_id" in data and "cover_letter" in data:
                    self.log_test("Cover Letter Generation", "PASS", 
                                f"Document ID: {data['document_id']}, Score: {data.get('personalization_score', 'N/A')}")
                    return True
                else:
                    self.log_test("Cover Letter Generation", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Cover Letter Generation", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Cover Letter Generation", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_linkedin_optimization(self) -> bool:
        """Test LinkedIn profile optimization"""
        try:
            request_data = {
                "current_profile": {
                    "headline": "Software Engineer",
                    "summary": "I am a software engineer with experience in web development",
                    "skills": ["Python", "JavaScript"],
                    "experience": "5 years"
                },
                "target_industry": "Technology",
                "career_goals": "Looking to advance to senior engineering roles"
            }
            response = self.make_request("POST", "/api/linkedin/optimize", request_data)
            
            if response.status_code == 200:
                data = response.json()
                if "document_id" in data and "optimized_headline" in data:
                    self.log_test("LinkedIn Optimization", "PASS", 
                                f"Document ID: {data['document_id']}")
                    return True
                else:
                    self.log_test("LinkedIn Optimization", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("LinkedIn Optimization", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("LinkedIn Optimization", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_interview_preparation(self) -> bool:
        """Test interview preparation"""
        try:
            request_data = {
                "job_title": "Senior Software Engineer",
                "company_name": "Microsoft",
                "job_description": "Senior role focusing on cloud architecture and distributed systems",
                "experience_level": "senior",
                "interview_type": "technical"
            }
            response = self.make_request("POST", "/api/interview/prepare", request_data)
            
            if response.status_code == 200:
                data = response.json()
                if "document_id" in data and "questions" in data:
                    self.log_test("Interview Preparation", "PASS", 
                                f"Document ID: {data['document_id']}, Questions: {len(data.get('questions', []))}")
                    return True
                else:
                    self.log_test("Interview Preparation", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Interview Preparation", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Interview Preparation", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_get_user_documents(self) -> bool:
        """Test get user documents"""
        try:
            response = self.make_request("GET", "/api/documents")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get User Documents", "PASS", 
                                f"Found {len(data)} documents")
                    return True
                else:
                    self.log_test("Get User Documents", "FAIL", f"Invalid response format: {type(data)}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Get User Documents", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Get User Documents", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_get_specific_document(self) -> bool:
        """Test get specific document"""
        if not self.test_document_id:
            self.log_test("Get Specific Document", "SKIP", "No document ID available")
            return True
            
        try:
            response = self.make_request("GET", f"/api/documents/{self.test_document_id}")
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and data["id"] == self.test_document_id:
                    self.log_test("Get Specific Document", "PASS", 
                                f"Document type: {data.get('document_type', 'N/A')}")
                    return True
                else:
                    self.log_test("Get Specific Document", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Get Specific Document", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Get Specific Document", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_document_download(self) -> bool:
        """Test document download functionality"""
        if not self.test_document_id:
            self.log_test("Document Download", "SKIP", "No document ID available")
            return True
            
        try:
            # Test PDF download
            response = self.make_request("GET", f"/api/documents/{self.test_document_id}/download/pdf")
            
            if response.status_code == 200:
                if response.headers.get('content-type') == 'application/pdf':
                    self.log_test("Document Download (PDF)", "PASS", 
                                f"PDF size: {len(response.content)} bytes")
                    
                    # Test DOCX download
                    response_docx = self.make_request("GET", f"/api/documents/{self.test_document_id}/download/docx")
                    if response_docx.status_code == 200:
                        self.log_test("Document Download (DOCX)", "PASS", 
                                    f"DOCX size: {len(response_docx.content)} bytes")
                        return True
                    else:
                        self.log_test("Document Download (DOCX)", "FAIL", 
                                    f"Status: {response_docx.status_code}")
                        return False
                else:
                    self.log_test("Document Download (PDF)", "FAIL", 
                                f"Wrong content type: {response.headers.get('content-type')}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Document Download", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Document Download", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_user_analytics(self) -> bool:
        """Test user analytics"""
        try:
            response = self.make_request("GET", "/api/analytics/user")
            
            if response.status_code == 200:
                data = response.json()
                if "user_id" in data and "total_documents" in data:
                    self.log_test("User Analytics", "PASS", 
                                f"Total docs: {data['total_documents']}, Tier: {data.get('subscription_tier', 'N/A')}")
                    return True
                else:
                    self.log_test("User Analytics", "FAIL", f"Invalid response: {data}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("User Analytics", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("User Analytics", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_admin_system_analytics(self) -> bool:
        """Test admin system analytics"""
        try:
            response = self.make_request("GET", "/api/admin/analytics", use_admin=True)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_users", "active_users_today", "active_users_this_month", 
                                 "documents_generated_today", "documents_generated_this_month", 
                                 "documents_by_type", "subscription_distribution"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Admin System Analytics", "PASS", 
                                f"Total users: {data['total_users']}, Total docs today: {data['documents_generated_today']}")
                    return True
                else:
                    missing_fields = [field for field in required_fields if field not in data]
                    self.log_test("Admin System Analytics", "FAIL", f"Missing fields: {missing_fields}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Admin System Analytics", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Admin System Analytics", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_admin_get_users(self) -> bool:
        """Test admin get all users"""
        try:
            response = self.make_request("GET", "/api/admin/users", use_admin=True)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Admin Get Users", "PASS", 
                                f"Found {len(data)} users")
                    return True
                else:
                    self.log_test("Admin Get Users", "FAIL", f"Invalid response format: {type(data)}")
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "No response"
                self.log_test("Admin Get Users", "FAIL", 
                            f"Status: {response.status_code}, Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Admin Get Users", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """Test that endpoints properly reject unauthorized access"""
        try:
            # Temporarily remove auth token
            original_token = self.auth_token
            self.auth_token = None
            
            response = self.make_request("GET", "/api/users/me")
            
            # Restore token
            self.auth_token = original_token
            
            if response.status_code == 401:
                self.log_test("Unauthorized Access Protection", "PASS", 
                            "Properly rejected unauthorized request")
                return True
            else:
                self.log_test("Unauthorized Access Protection", "FAIL", 
                            f"Should have returned 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Unauthorized Access Protection", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_admin_only_access(self) -> bool:
        """Test that admin endpoints reject non-admin users"""
        try:
            # Use regular user token for admin endpoint
            response = self.make_request("GET", "/api/admin/analytics", use_admin=False)
            
            if response.status_code == 403:
                self.log_test("Admin Only Access Protection", "PASS", 
                            "Properly rejected non-admin request")
                return True
            else:
                self.log_test("Admin Only Access Protection", "FAIL", 
                            f"Should have returned 403, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Only Access Protection", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("=" * 80)
        print("CAREER TOOLS PLATFORM - BACKEND API TESTING")
        print("=" * 80)
        print(f"Testing backend at: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        results = {}
        
        # Health and basic connectivity
        results["health_check"] = self.test_health_check()
        
        # Authentication flow
        results["user_registration"] = self.test_user_registration()
        results["user_login"] = self.test_user_login()
        results["admin_login"] = self.test_admin_login()
        
        # User management
        results["get_current_user"] = self.test_get_current_user()
        results["update_user_profile"] = self.test_update_user_profile()
        
        # Career tools APIs
        results["resume_optimization"] = self.test_resume_optimization()
        results["cover_letter_generation"] = self.test_cover_letter_generation()
        results["linkedin_optimization"] = self.test_linkedin_optimization()
        results["interview_preparation"] = self.test_interview_preparation()
        
        # Document management
        results["get_user_documents"] = self.test_get_user_documents()
        results["get_specific_document"] = self.test_get_specific_document()
        results["document_download"] = self.test_document_download()
        
        # Analytics
        results["user_analytics"] = self.test_user_analytics()
        results["admin_system_analytics"] = self.test_admin_system_analytics()
        results["admin_get_users"] = self.test_admin_get_users()
        
        # Security tests
        results["unauthorized_access"] = self.test_unauthorized_access()
        results["admin_only_access"] = self.test_admin_only_access()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print()
        print(f"OVERALL RESULT: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Backend is working correctly.")
        else:
            print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
        
        print("=" * 80)
        
        return results

def main():
    """Main function to run the tests"""
    # Get backend URL from environment or use default
    backend_url = "https://7d3d370a-4457-4647-999d-7934a4805891.preview.emergentagent.com"
    
    print(f"Starting comprehensive backend API testing...")
    print(f"Backend URL: {backend_url}")
    print()
    
    # Create tester instance and run tests
    tester = CareerToolsAPITester(backend_url)
    results = tester.run_all_tests()
    
    # Return exit code based on results
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())