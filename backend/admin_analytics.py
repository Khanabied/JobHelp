"""
Admin Analytics and KPI Tracking System
Comprehensive monitoring for JobSasa platform
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import asyncio


class AdminAnalytics:
    """Analytics service for admin dashboard KPI monitoring"""
    
    def __init__(self, database):
        self.db = database
    
    async def get_user_metrics(self, period_days: int = 30) -> Dict:
        """Get comprehensive user metrics"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Total users registered
        total_users = await self.db.users.count_documents({})
        
        # New users in period
        new_users = await self.db.users.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Active users (users who performed analysis in period)
        active_users = await self.db.analysis_results.distinct("user_id", {
            "created_at": {"$gte": start_date}
        })
        active_users_count = len(active_users)
        
        # User growth trend (daily registrations)
        user_growth_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        growth_cursor = self.db.users.aggregate(user_growth_pipeline)
        user_growth = []
        async for doc in growth_cursor:
            user_growth.append({
                "date": doc["_id"],
                "registrations": doc["count"]
            })
        
        return {
            "total_users": total_users,
            "new_users_period": new_users,
            "active_users_period": active_users_count,
            "user_growth_trend": user_growth,
            "period_days": period_days
        }
    
    async def get_analysis_metrics(self, period_days: int = 30) -> Dict:
        """Get analysis usage metrics"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Total analyses
        total_analyses = await self.db.analysis_results.count_documents({})
        
        # Analyses in period
        period_analyses = await self.db.analysis_results.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Analysis type breakdown
        analysis_types_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$analysis_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        types_cursor = self.db.analysis_results.aggregate(analysis_types_pipeline)
        analysis_types = {}
        async for doc in types_cursor:
            analysis_types[doc["_id"] or "basic"] = doc["count"]
        
        # Daily analysis trend
        daily_analysis_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        daily_cursor = self.db.analysis_results.aggregate(daily_analysis_pipeline)
        daily_trend = []
        async for doc in daily_cursor:
            daily_trend.append({
                "date": doc["_id"],
                "analyses": doc["count"]
            })
        
        return {
            "total_analyses": total_analyses,
            "period_analyses": period_analyses,
            "analysis_types": analysis_types,
            "daily_trend": daily_trend
        }
    
    async def get_document_metrics(self, period_days: int = 30) -> Dict:
        """Get document generation and download metrics"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Total documents generated
        total_documents = await self.db.generated_documents.count_documents({})
        
        # Documents in period
        period_documents = await self.db.generated_documents.count_documents({
            "created_at": {"$gte": start_date}
        })
        
        # Document type popularity (based on generated files)
        doc_types_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$project": {
                    "file_types": {"$objectToArray": "$generated_files"}
                }
            },
            {
                "$unwind": "$file_types"
            },
            {
                "$group": {
                    "_id": "$file_types.k",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        types_cursor = self.db.generated_documents.aggregate(doc_types_pipeline)
        document_types = {}
        async for doc in types_cursor:
            document_types[doc["_id"]] = doc["count"]
        
        return {
            "total_documents": total_documents,
            "period_documents": period_documents,
            "document_types": document_types
        }
    
    async def get_engagement_metrics(self, period_days: int = 30) -> Dict:
        """Get user engagement metrics"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Average analyses per user
        total_users = await self.db.users.count_documents({})
        total_analyses = await self.db.analysis_results.count_documents({})
        avg_analyses_per_user = total_analyses / max(total_users, 1)
        
        # Most active users
        active_users_pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "analysis_count": {"$sum": 1}
                }
            },
            {"$sort": {"analysis_count": -1}},
            {"$limit": 10}
        ]
        
        active_cursor = self.db.analysis_results.aggregate(active_users_pipeline)
        top_users = []
        async for doc in active_cursor:
            # Get user info
            user = await self.db.users.find_one({"_id": doc["_id"]})
            if user:
                top_users.append({
                    "user_email": user["email"],
                    "analysis_count": doc["analysis_count"]
                })
        
        # Feature usage (individual agents vs extended)
        feature_usage = {
            "basic_analysis": await self.db.analysis_results.count_documents({
                "analysis_type": {"$in": [None, "basic"]},
                "created_at": {"$gte": start_date}
            }),
            "extended_analysis": await self.db.analysis_results.count_documents({
                "analysis_type": "extended",
                "created_at": {"$gte": start_date}
            })
        }
        
        return {
            "avg_analyses_per_user": round(avg_analyses_per_user, 2),
            "top_active_users": top_users,
            "feature_usage": feature_usage
        }
    
    async def get_system_metrics(self, period_days: int = 30) -> Dict:
        """Get system performance metrics"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # File upload metrics
        total_uploads = await self.db.uploaded_files.count_documents({})
        period_uploads = await self.db.uploaded_files.count_documents({
            "upload_time": {"$gte": start_date}
        })
        
        # Processing success rate (processed files vs total uploads)
        processed_files = await self.db.uploaded_files.count_documents({
            "processed": True,
            "upload_time": {"$gte": start_date}
        })
        
        success_rate = (processed_files / max(period_uploads, 1)) * 100
        
        # Database statistics
        db_stats = {
            "users": await self.db.users.count_documents({}),
            "uploaded_files": await self.db.uploaded_files.count_documents({}),
            "analysis_results": await self.db.analysis_results.count_documents({}),
            "generated_documents": await self.db.generated_documents.count_documents({})
        }
        
        return {
            "total_uploads": total_uploads,
            "period_uploads": period_uploads,
            "processing_success_rate": round(success_rate, 2),
            "database_stats": db_stats
        }
    
    async def get_comprehensive_dashboard(self, period_days: int = 30) -> Dict:
        """Get all metrics for admin dashboard"""
        try:
            user_metrics = await self.get_user_metrics(period_days)
            analysis_metrics = await self.get_analysis_metrics(period_days)
            document_metrics = await self.get_document_metrics(period_days)
            engagement_metrics = await self.get_engagement_metrics(period_days)
            system_metrics = await self.get_system_metrics(period_days)
            
            return {
                "generated_at": datetime.utcnow().isoformat(),
                "period_days": period_days,
                "user_metrics": user_metrics,
                "analysis_metrics": analysis_metrics,
                "document_metrics": document_metrics,
                "engagement_metrics": engagement_metrics,
                "system_metrics": system_metrics
            }
        except Exception as e:
            print(f"Error generating dashboard metrics: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }

# Event tracking for detailed analytics
class EventTracker:
    """Track specific user events for detailed analytics"""
    
    def __init__(self, database):
        self.db = database
    
    async def track_event(self, user_id: str, event_type: str, event_data: Dict = None):
        """Track a user event"""
        event = {
            "_id": f"{user_id}_{event_type}_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "event_type": event_type,
            "event_data": event_data or {},
            "timestamp": datetime.utcnow()
        }
        
        try:
            await self.db.user_events.insert_one(event)
        except Exception as e:
            print(f"Error tracking event: {e}")
    
    async def get_events_by_type(self, event_type: str, period_days: int = 30) -> int:
        """Get count of events by type"""
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        count = await self.db.user_events.count_documents({
            "event_type": event_type,
            "timestamp": {"$gte": start_date}
        })
        
        return count


# Admin model for API responses
class AdminDashboardResponse(BaseModel):
    generated_at: str
    period_days: int
    user_metrics: Dict
    analysis_metrics: Dict
    document_metrics: Dict
    engagement_metrics: Dict
    system_metrics: Dict