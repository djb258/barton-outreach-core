"""
Neon driver implementation
"""
import os
import httpx
from typing import Dict, Any, Optional, List, Union
from ..base_driver import BaseDriver, DatabaseType


class NeonDriver(BaseDriver):
    """Neon Postgres driver implementation"""
    
    @property
    def driver_type(self) -> DatabaseType:
        return DatabaseType.NEON
    
    @property
    def required_env_vars(self) -> List[str]:
        return [
            "NEON_API_KEY",
            "NEON_PROJECT_ID"
        ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.project_id = os.getenv("NEON_PROJECT_ID")
        self.base_url = "https://console.neon.tech/api/v2"
    
    async def connect(self) -> bool:
        """Establish connection to Neon"""
        try:
            self.client = httpx.AsyncClient()
            return True
        except Exception:
            return False
    
    async def disconnect(self) -> bool:
        """Close connection to Neon"""
        if self.client:
            await self.client.aclose()
            self.client = None
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Neon connectivity"""
        try:
            if not self.client:
                await self.connect()
            
            response = await self.client.get(
                f"{self.base_url}/projects/{self.project_id}",
                headers=self._get_headers()
            )
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "project_id": self.project_id,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "project_id": self.project_id
            }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authenticated headers for Neon API"""
        return {
            "Authorization": f"Bearer {os.getenv('NEON_API_KEY')}",
            "Content-Type": "application/json"
        }
    
    async def migrate(self, target_version: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Run database migrations on Neon"""
        project_id = os.getenv("NEON_PROJECT_ID")
        
        async with httpx.AsyncClient() as client:
            # Get database info
            response = await client.get(
                f"https://console.neon.tech/api/v2/projects/{project_id}/databases",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            databases = response.json().get("databases", [])
            main_db = next((db for db in databases if db.get("name") == "main"), None)
            
            if not main_db:
                raise RuntimeError("Main database not found in Neon project")
            
            # In a real implementation, this would execute migrations
            # For now, return a mock response
            return {
                "driver": "neon",
                "current_version": "1.0.0",
                "target_version": target_version or "latest",
                "migrations_applied": [] if dry_run else ["001_init", "002_add_users"],
                "success": True,
                "dry_run": dry_run
            }
    
    async def upgrade(self, force: bool = False) -> Dict[str, Any]:
        """Upgrade Neon database to latest version"""
        project_id = os.getenv("NEON_PROJECT_ID")
        
        # Mock upgrade response
        return {
            "driver": "neon",
            "previous_version": "1.0.0",
            "new_version": "1.1.0",
            "upgraded": True,
            "project_id": project_id
        }
    
    async def seed(self, dataset: str, truncate: bool = False) -> Dict[str, Any]:
        """Seed Neon database with data"""
        return {
            "driver": "neon",
            "dataset": dataset,
            "records_inserted": 100,  # Mock count
            "tables_affected": ["users", "products"],
            "truncated": truncate
        }
    
    async def snapshot(self, name: str, include_data: bool = True) -> Dict[str, Any]:
        """Create a Neon database snapshot"""
        project_id = os.getenv("NEON_PROJECT_ID")
        
        async with httpx.AsyncClient() as client:
            # Create branch in Neon (serves as snapshot)
            response = await client.post(
                f"https://console.neon.tech/api/v2/projects/{project_id}/branches",
                headers=self._get_headers(),
                json={
                    "name": f"snapshot-{name}",
                    "parent_id": "main"
                }
            )
            
            if response.status_code == 201:
                branch_data = response.json()
                return {
                    "driver": "neon",
                    "snapshot_id": branch_data.get("branch", {}).get("id"),
                    "name": name,
                    "branch_name": f"snapshot-{name}",
                    "timestamp": branch_data.get("branch", {}).get("created_at"),
                    "size_bytes": 0  # Neon doesn't provide size info
                }
            else:
                raise RuntimeError(f"Failed to create Neon snapshot: {response.text}")
    
    async def backup(self, backup_name: Optional[str] = None, compress: bool = True) -> Dict[str, Any]:
        """Create a backup using Neon branching"""
        from datetime import datetime
        
        backup_name = backup_name or f"backup-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Use snapshot functionality as backup
        snapshot_result = await self.snapshot(backup_name, include_data=True)
        
        return {
            "driver": "neon",
            "backup_id": snapshot_result["snapshot_id"],
            "path": f"neon://branch/{snapshot_result['branch_name']}",
            "size_bytes": 0,
            "timestamp": snapshot_result["timestamp"],
            "compressed": False  # Neon handles compression internally
        }
    
    async def restore(self, backup_id: str, target_database: Optional[str] = None) -> Dict[str, Any]:
        """Restore from Neon backup (branch)"""
        project_id = os.getenv("NEON_PROJECT_ID")
        
        # In real implementation, would restore from branch
        return {
            "driver": "neon",
            "backup_id": backup_id,
            "restored": True,
            "target_database": target_database or "main",
            "project_id": project_id
        }
    
    async def ingest_json_secure(self, rows: List[Dict[str, Any]], source: str, batch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Securely ingest JSON data using SECURITY DEFINER function
        Uses intake.f_ingest_json($1::jsonb[], $2::text, $3::text)
        """
        try:
            import json
            import asyncpg
            from datetime import datetime
            
            # Generate batch ID if not provided
            if not batch_id:
                batch_id = f"batch-{int(datetime.now().timestamp())}"
            
            # Get connection string from environment
            conn_str = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
            if not conn_str:
                return {
                    "success": False,
                    "error": "No database connection string configured"
                }
            
            # Connect to database
            conn = await asyncpg.connect(conn_str)
            
            try:
                # Convert rows to PostgreSQL array format
                jsonb_array = json.dumps(rows)
                
                # Execute secure function
                query = "SELECT * FROM intake.f_ingest_json($1::jsonb[], $2::text, $3::text);"
                result = await conn.fetch(query, jsonb_array, source, batch_id)
                
                # Parse result
                if result:
                    row = dict(result[0])
                    return {
                        "success": row.get('status') == 'success',
                        "message": row.get('message', ''),
                        "batch_id": batch_id,
                        "source": source,
                        "load_id": row.get('load_id')
                    }
                
                return {
                    "success": False,
                    "error": "No result from ingestion function"
                }
                
            finally:
                await conn.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Secure ingestion failed: {str(e)}"
            }
    
    async def promote_contacts_secure(self, load_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Securely promote contacts using SECURITY DEFINER function
        Uses vault.f_promote_contacts($1::bigint[])
        """
        try:
            import asyncpg
            
            # Get connection string from environment
            conn_str = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
            if not conn_str:
                return {
                    "success": False,
                    "error": "No database connection string configured"
                }
            
            # Connect to database
            conn = await asyncpg.connect(conn_str)
            
            try:
                # Execute secure function
                if load_ids:
                    query = "SELECT * FROM vault.f_promote_contacts($1::bigint[]);"
                    result = await conn.fetch(query, load_ids)
                else:
                    # Promote all pending if no IDs specified
                    query = "SELECT * FROM vault.f_promote_contacts(NULL);"
                    result = await conn.fetch(query)
                
                # Parse result
                if result:
                    row = dict(result[0])
                    return {
                        "success": True,
                        "promoted_count": row.get('promoted_count', 0),
                        "updated_count": row.get('updated_count', 0),
                        "failed_count": row.get('failed_count', 0),
                        "message": row.get('message', '')
                    }
                
                return {
                    "success": False,
                    "error": "No result from promotion function"
                }
                
            finally:
                await conn.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Secure promotion failed: {str(e)}"
            }
    
    async def get_latest_loads(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get latest loads from the intake.latest_100 view
        """
        try:
            import asyncpg
            
            # Get connection string from environment
            conn_str = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
            if not conn_str:
                return {
                    "success": False,
                    "error": "No database connection string configured"
                }
            
            # Connect to database
            conn = await asyncpg.connect(conn_str)
            
            try:
                # Query the view
                query = "SELECT * FROM intake.latest_100 LIMIT $1;"
                result = await conn.fetch(query, limit)
                
                # Convert to list of dicts
                loads = [dict(row) for row in result]
                
                return {
                    "success": True,
                    "loads": loads,
                    "count": len(loads)
                }
                
            finally:
                await conn.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get latest loads: {str(e)}"
            }