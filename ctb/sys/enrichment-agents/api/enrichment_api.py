"""
Enrichment API Server for n8n Integration
Barton Doctrine ID: 04.04.02.04.50000.300

FastAPI server that exposes enrichment functionality as HTTP endpoints
for n8n workflows to call.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator.enrichment_orchestrator import EnrichmentOrchestrator
import asyncpg

app = FastAPI(
    title="Enrichment API",
    description="API for enriching invalid company and people records",
    version="1.0.0"
)

# CORS - allow n8n to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to n8n URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
orchestrator = None
db_pool = None


class EnrichmentRequest(BaseModel):
    """Request model for enrichment"""
    table: str  # 'company_invalid' or 'people_invalid'
    limit: Optional[int] = 10
    record_ids: Optional[List[int]] = None  # Specific record IDs to enrich


class EnrichmentResponse(BaseModel):
    """Response model for enrichment"""
    success: bool
    message: str
    stats: Dict[str, Any]
    timestamp: str


class SimpleDBConnection:
    """Database connection wrapper"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None

    async def connect(self):
        """Create connection pool"""
        self._pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=1,
            max_size=10
        )

    async def close(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()

    async def fetch(self, query: str):
        """Fetch multiple rows"""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str):
        """Fetch single row"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query)
            return dict(row) if row else None

    async def execute(self, query: str):
        """Execute query"""
        async with self._pool.acquire() as conn:
            await conn.execute(query)


@app.on_event("startup")
async def startup():
    """Initialize on startup"""
    global orchestrator, db_pool

    # Load config
    config_path = Path(__file__).parent.parent / 'config' / 'agent_config.json'
    with open(config_path) as f:
        config = json.load(f)

    # Get database URL
    database_url = os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING')
    if not database_url:
        raise RuntimeError("DATABASE_URL not found in environment")

    # Create database connection
    db_pool = SimpleDBConnection(database_url)
    await db_pool.connect()

    # Create orchestrator
    orchestrator = EnrichmentOrchestrator(config, db_pool)

    print("✅ Enrichment API started")
    print(f"   Agents: {list(orchestrator.agents.keys())}")
    print(f"   Batch size: {orchestrator.batch_size}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Enrichment API",
        "version": "1.0.0",
        "agents": list(orchestrator.agents.keys()) if orchestrator else [],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    global orchestrator, db_pool

    # Check database
    try:
        await db_pool.fetchrow("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check agents
    agent_status = {}
    if orchestrator:
        for name, agent in orchestrator.agents.items():
            stats = agent.get_stats()
            agent_status[name] = {
                "enabled": True,
                "total_calls": stats['total_calls'],
                "rate_limit_status": stats['rate_limit_status']
            }

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "agents": agent_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/enrich", response_model=EnrichmentResponse)
async def enrich_records(
    request: EnrichmentRequest,
    background_tasks: BackgroundTasks
):
    """
    Enrich invalid records

    Called by n8n workflow to trigger enrichment batch
    """
    global orchestrator

    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    # Validate table name
    if request.table not in ['company_invalid', 'people_invalid']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table: {request.table}. Must be 'company_invalid' or 'people_invalid'"
        )

    try:
        # Run enrichment
        stats = await orchestrator.enrich_batch(
            request.table,
            limit=request.limit
        )

        return EnrichmentResponse(
            success=True,
            message=f"Enriched {stats['enriched']} records, promoted {stats['promoted']}",
            stats=stats,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/enrich/company", response_model=EnrichmentResponse)
async def enrich_companies(limit: int = 10):
    """
    Enrich invalid companies

    Convenience endpoint for n8n
    """
    return await enrich_records(
        EnrichmentRequest(table='company_invalid', limit=limit),
        BackgroundTasks()
    )


@app.post("/enrich/people", response_model=EnrichmentResponse)
async def enrich_people(limit: int = 10):
    """
    Enrich invalid people

    Convenience endpoint for n8n
    """
    return await enrich_records(
        EnrichmentRequest(table='people_invalid', limit=limit),
        BackgroundTasks()
    )


@app.get("/stats")
async def get_stats():
    """
    Get enrichment statistics

    Returns global stats and per-agent stats
    """
    global orchestrator

    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    return {
        "global": orchestrator.get_stats(),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/invalid/count")
async def get_invalid_count():
    """
    Get count of invalid records

    Useful for n8n conditionals (if > 0, trigger enrichment)
    """
    global db_pool

    try:
        company_count = await db_pool.fetchrow(
            "SELECT COUNT(*) as count FROM marketing.company_invalid WHERE reviewed = FALSE"
        )
        people_count = await db_pool.fetchrow(
            "SELECT COUNT(*) as count FROM marketing.people_invalid WHERE reviewed = FALSE"
        )

        return {
            "company_invalid": company_count['count'],
            "people_invalid": people_count['count'],
            "total": company_count['count'] + people_count['count'],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/invalid/recent")
async def get_recent_invalid(limit: int = 10):
    """
    Get recently failed records

    For n8n to review/alert on new failures
    """
    global db_pool

    try:
        companies = await db_pool.fetch(f"""
            SELECT id, company_name, failed_at, reason_code
            FROM marketing.company_invalid
            WHERE reviewed = FALSE
            ORDER BY failed_at DESC
            LIMIT {limit}
        """)

        people = await db_pool.fetch(f"""
            SELECT id, full_name, failed_at, reason_code
            FROM marketing.people_invalid
            WHERE reviewed = FALSE
            ORDER BY failed_at DESC
            LIMIT {limit}
        """)

        return {
            "companies": companies,
            "people": people,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/enrichment-complete")
async def enrichment_complete_webhook(data: Dict[str, Any]):
    """
    Webhook endpoint for enrichment completion

    n8n can call this when enrichment is done to trigger next steps
    """
    return {
        "status": "received",
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("ENRICHMENT_API_PORT", "8001"))

    print(f"\n🚀 Starting Enrichment API on port {port}")
    print(f"   Documentation: http://localhost:{port}/docs")
    print(f"   Health check: http://localhost:{port}/health\n")

    uvicorn.run(
        "enrichment_api:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
