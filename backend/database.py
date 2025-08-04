from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging
from models import User, UserRole
from auth import get_password_hash

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

# Database dependency
db_instance = Database()

async def get_database() -> AsyncIOMotorDatabase:
    return db_instance.database

async def connect_to_mongo():
    """Create database connection."""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    logger.info(f"Connecting to MongoDB at {mongo_url}")
    db_instance.client = AsyncIOMotorClient(mongo_url)
    db_instance.database = db_instance.client[db_name]
    
    # Create indexes
    await create_indexes()
    
    # Create admin user if it doesn't exist
    await create_admin_user()
    
    logger.info("Connected to MongoDB successfully")

async def close_mongo_connection():
    """Close database connection."""
    if db_instance.client:
        db_instance.client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for better performance."""
    try:
        # User indexes
        await db_instance.database.users.create_index("email", unique=True)
        await db_instance.database.users.create_index("id", unique=True)
        
        # Document indexes
        await db_instance.database.documents.create_index("id", unique=True)
        await db_instance.database.documents.create_index("user_id")
        await db_instance.database.documents.create_index("document_type")
        await db_instance.database.documents.create_index("created_at")
        
        # Template indexes
        await db_instance.database.templates.create_index("id", unique=True)
        await db_instance.database.templates.create_index("document_type")
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")

async def create_admin_user():
    """Create default admin user if it doesn't exist."""
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        
        # Check if admin user already exists
        existing_admin = await db_instance.database.users.find_one({"email": admin_email})
        if existing_admin:
            logger.info("Admin user already exists")
            return
        
        # Create admin user
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_user = User(
            email=admin_email,
            full_name="System Administrator",
            hashed_password=get_password_hash(admin_password),
            role=UserRole.ADMIN,
            subscription_tier="enterprise"
        )
        
        await db_instance.database.users.insert_one(admin_user.dict())
        logger.info(f"Admin user created with email: {admin_email}")
        
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")

async def get_user_analytics(user_id: str) -> dict:
    """Get analytics data for a specific user."""
    try:
        # Get user document count by type
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$document_type",
                "count": {"$sum": 1}
            }}
        ]
        
        type_counts = {}
        async for result in db_instance.database.documents.aggregate(pipeline):
            type_counts[result["_id"]] = result["count"]
        
        # Get total documents
        total_docs = await db_instance.database.documents.count_documents({"user_id": user_id})
        
        # Get user info
        user = await db_instance.database.users.find_one({"id": user_id})
        
        return {
            "user_id": user_id,
            "total_documents": total_docs,
            "documents_by_type": type_counts,
            "subscription_tier": user.get("subscription_tier", "free") if user else "free",
            "member_since": user.get("created_at") if user else None
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        return {}

async def get_system_analytics() -> dict:
    """Get system-wide analytics."""
    try:
        # Total users
        total_users = await db_instance.database.users.count_documents({})
        
        # Active users (logged in within last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = await db_instance.database.users.count_documents({
            "last_login": {"$gte": thirty_days_ago}
        })
        
        # Document statistics
        total_docs = await db_instance.database.documents.count_documents({})
        
        # Documents by type
        pipeline = [
            {"$group": {
                "_id": "$document_type",
                "count": {"$sum": 1}
            }}
        ]
        
        docs_by_type = {}
        async for result in db_instance.database.documents.aggregate(pipeline):
            docs_by_type[result["_id"]] = result["count"]
        
        # Subscription distribution
        subscription_pipeline = [
            {"$group": {
                "_id": "$subscription_tier",
                "count": {"$sum": 1}
            }}
        ]
        
        subscription_dist = {}
        async for result in db_instance.database.users.aggregate(subscription_pipeline):
            subscription_dist[result["_id"]] = result["count"]
        
        return {
            "total_users": total_users,
            "active_users_this_month": active_users,
            "total_documents": total_docs,
            "documents_by_type": docs_by_type,
            "subscription_distribution": subscription_dist,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting system analytics: {str(e)}")
        return {}