"""
Outreach Command Center - FastAPI Backend
===========================================
Provides REST API endpoints for:
- Neon Database views (phase stats, errors)
- n8n workflow monitoring
- Apify actor execution

Environment Variables Required:
- NEON_DATABASE_URL
- N8N_API_URL (or N8N_BASE_URL)
- N8N_API_KEY
- APIFY_TOKEN (or APIFY_API_KEY)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Outreach Command Center API",
    description="Backend API for Barton Outreach Core dashboard",
    version="1.0.0"
)

# CORS Configuration - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================
# Environment Variables
# ===========================================
NEON_DATABASE_URL = os.getenv('NEON_DATABASE_URL') or os.getenv('DATABASE_URL')
N8N_BASE_URL = os.getenv('N8N_API_URL') or os.getenv('N8N_BASE_URL', 'https://dbarton.app.n8n.cloud')
N8N_API_KEY = os.getenv('N8N_API_KEY')
APIFY_API_TOKEN = os.getenv('APIFY_TOKEN') or os.getenv('APIFY_API_KEY')

# Validate environment variables
ENV_WARNINGS = []
if not NEON_DATABASE_URL:
    ENV_WARNINGS.append("[WARN] NEON_DATABASE_URL not set")
if not N8N_API_KEY:
    ENV_WARNINGS.append("[WARN] N8N_API_KEY not set")
if not APIFY_API_TOKEN:
    ENV_WARNINGS.append("[WARN] APIFY_TOKEN not set")

if ENV_WARNINGS:
    for warning in ENV_WARNINGS:
        logger.warning(warning)

# ===========================================
# Database Helper Functions
# ===========================================
def get_db_connection():
    """Create a connection to Neon PostgreSQL database"""
    if not NEON_DATABASE_URL:
        raise HTTPException(
            status_code=500,
            detail="NEON_DATABASE_URL environment variable not configured"
        )

    try:
        conn = psycopg2.connect(NEON_DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results as list of dicts"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )
    finally:
        if conn:
            conn.close()

# ===========================================
# Pydantic Models
# ===========================================
class ApifyRunRequest(BaseModel):
    actor_id: str
    input_data: Optional[Dict[str, Any]] = {}
    timeout: Optional[int] = 300  # 5 minutes default

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    environment: Dict[str, bool]
    warnings: List[str]

# ===========================================
# Root & Health Endpoints
# ===========================================
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Outreach Command Center API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "neon_phase_stats": "/api/neon/v_phase_stats",
            "neon_errors": "/api/neon/v_error_recent",
            "n8n_errors": "/api/n8n/errors",
            "apify_run": "/api/apify/run"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with environment validation"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": {
            "neon_configured": bool(NEON_DATABASE_URL),
            "n8n_configured": bool(N8N_API_KEY),
            "apify_configured": bool(APIFY_API_TOKEN)
        },
        "warnings": ENV_WARNINGS
    }

# ===========================================
# Neon Database Endpoints
# ===========================================
@app.get("/api/neon/v_phase_stats")
async def get_phase_stats():
    """
    Get pipeline phase statistics from Neon view
    Returns: Phase-wise company counts and status
    """
    query = """
        SELECT
            phase,
            status,
            count,
            last_updated
        FROM marketing.v_phase_stats
        ORDER BY phase, status
    """

    try:
        results = execute_query(query)
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching phase stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/neon/v_error_recent")
async def get_recent_errors():
    """
    Get recent errors from Neon pipeline_errors table
    Returns: Recent error logs with details
    """
    query = """
        SELECT
            id as error_id,
            event_type as phase,
            severity as error_type,
            error_message,
            record_id as company_id,
            created_at
        FROM marketing.pipeline_errors
        ORDER BY created_at DESC
        LIMIT 50
    """

    try:
        results = execute_query(query)
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recent errors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/neon/company_master")
async def get_company_master(limit: int = 100):
    """
    Get companies from company_master table
    Returns: List of companies with their details
    """
    query = """
        SELECT
            company_unique_id as barton_id,
            company_name,
            website_url as website,
            industry,
            employee_count,
            linkedin_url,
            created_at,
            updated_at
        FROM marketing.company_master
        ORDER BY updated_at DESC
        LIMIT %s
    """

    try:
        results = execute_query(query, (limit,))
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company master: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# n8n Workflow Endpoints
# ===========================================
@app.get("/api/n8n/errors")
async def get_n8n_errors():
    """
    Get failed workflow executions from n8n
    Returns: List of failed n8n workflow executions
    """
    if not N8N_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="N8N_API_KEY not configured"
        )

    try:
        url = f"{N8N_BASE_URL}/api/v1/executions"
        headers = {
            "X-N8N-API-KEY": N8N_API_KEY,
            "Accept": "application/json"
        }
        params = {
            "status": "error",
            "limit": 50
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return {
            "success": True,
            "data": data.get("data", []),
            "count": len(data.get("data", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"n8n API request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"n8n API request failed: {str(e)}"
        )

@app.get("/api/n8n/executions")
async def get_n8n_executions(limit: int = 20):
    """
    Get recent workflow executions from n8n
    Returns: List of recent n8n workflow executions
    """
    if not N8N_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="N8N_API_KEY not configured"
        )

    try:
        url = f"{N8N_BASE_URL}/api/v1/executions"
        headers = {
            "X-N8N-API-KEY": N8N_API_KEY,
            "Accept": "application/json"
        }
        params = {"limit": limit}

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return {
            "success": True,
            "data": data.get("data", []),
            "count": len(data.get("data", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"n8n API request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"n8n API request failed: {str(e)}"
        )

# ===========================================
# Apify Integration Endpoints
# ===========================================
@app.post("/api/apify/run")
async def run_apify_actor(request: ApifyRunRequest):
    """
    Run an Apify actor
    Request body: {actor_id, input_data, timeout}
    Returns: Apify actor run result
    """
    if not APIFY_API_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="APIFY_TOKEN not configured"
        )

    try:
        url = f"https://api.apify.com/v2/acts/{request.actor_id}/runs"
        headers = {
            "Authorization": f"Bearer {APIFY_API_TOKEN}",
            "Content-Type": "application/json"
        }
        params = {
            "timeout": request.timeout,
            "waitForFinish": 60  # Wait up to 60 seconds for result
        }

        response = requests.post(
            url,
            headers=headers,
            json=request.input_data,
            params=params,
            timeout=request.timeout
        )
        response.raise_for_status()

        data = response.json()
        return {
            "success": True,
            "data": data,
            "actor_id": request.actor_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Apify API request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Apify API request failed: {str(e)}"
        )

@app.get("/api/apify/actors")
async def list_apify_actors():
    """
    List available Apify actors in your account
    Returns: List of Apify actors
    """
    if not APIFY_API_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="APIFY_TOKEN not configured"
        )

    try:
        url = "https://api.apify.com/v2/acts"
        headers = {
            "Authorization": f"Bearer {APIFY_API_TOKEN}",
            "Accept": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        return {
            "success": True,
            "data": data.get("data", {}).get("items", []),
            "count": data.get("data", {}).get("count", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Apify API request failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Apify API request failed: {str(e)}"
        )

# ===========================================
# Error Handler
# ===========================================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return {
        "success": False,
        "error": str(exc),
        "timestamp": datetime.utcnow().isoformat()
    }

# ===========================================
# Startup Event
# ===========================================
@app.on_event("startup")
async def startup_event():
    logger.info("==> Outreach Command Center API starting up...")
    logger.info(f" NEON configured: {bool(NEON_DATABASE_URL)}")
    logger.info(f" n8n configured: {bool(N8N_API_KEY)}")
    logger.info(f" Apify configured: {bool(APIFY_API_TOKEN)}")

    if ENV_WARNINGS:
        logger.warning("[WARN] Environment warnings:")
        for warning in ENV_WARNINGS:
            logger.warning(f"   {warning}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
