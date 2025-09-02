"""
MCP Orchestrator - Unified orchestration for multiple MCP servers
Including RefTools and Composio integrations
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import toml
import httpx

# Import drivers
from ..drivers.reference.reftools import RefToolsDriver
from ..drivers.reference.composio import ComposioDriver

class MCPOrchestrator:
    """
    Orchestrates multiple MCP servers including new RefTools and Composio integrations
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or Path(__file__).parent.parent.parent / "config" / "mcp-servers.toml"
        self.config = self._load_config()
        self.servers = {}
        self.drivers = {}
        self._initialize_servers()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP servers configuration"""
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                return toml.load(f)
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Provide default configuration if file not found"""
        return {
            'servers': {
                'reftools': {
                    'name': 'RefTools API',
                    'type': 'external',
                    'driver': 'reference.reftools.RefToolsDriver',
                    'enabled': True
                },
                'composio': {
                    'name': 'Composio Platform',
                    'type': 'external',
                    'driver': 'reference.composio.ComposioDriver',
                    'enabled': True
                }
            }
        }
    
    def _initialize_servers(self):
        """Initialize configured MCP servers"""
        for server_id, server_config in self.config.get('servers', {}).items():
            if not server_config.get('enabled', True):
                continue
            
            driver_path = server_config.get('driver')
            if driver_path:
                driver = self._create_driver(driver_path, server_config.get('config', {}))
                if driver:
                    self.drivers[server_id] = driver
                    self.servers[server_id] = server_config
    
    def _create_driver(self, driver_path: str, config: Dict[str, Any]):
        """Create driver instance from path"""
        if driver_path == 'reference.reftools.RefToolsDriver':
            return RefToolsDriver(config)
        elif driver_path == 'reference.composio.ComposioDriver':
            return ComposioDriver(config)
        # Add other drivers as needed
        return None
    
    async def search_api_references(self, query: str, language: str = None) -> Dict[str, Any]:
        """
        Search API references using RefTools
        
        Args:
            query: Search query
            language: Programming language filter
            
        Returns:
            Search results from RefTools
        """
        if 'reftools' in self.drivers:
            return await self.drivers['reftools'].search_references(query, language)
        return {'error': 'RefTools not configured', 'results': []}
    
    async def list_ai_tools(self, category: str = None) -> Dict[str, Any]:
        """
        List available AI agent tools from Composio
        
        Args:
            category: Tool category filter
            
        Returns:
            List of available tools
        """
        if 'composio' in self.drivers:
            tools = await self.drivers['composio'].list_tools(category)
            return {'tools': tools, 'source': 'composio'}
        return {'error': 'Composio not configured', 'tools': []}
    
    async def execute_composio_action(self, action_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Composio action
        
        Args:
            action_id: Action to execute
            params: Action parameters
            
        Returns:
            Execution results
        """
        if 'composio' in self.drivers:
            return await self.drivers['composio'].execute_action(action_id, params)
        return {'error': 'Composio not configured', 'executed': False}
    
    async def get_api_documentation(self, api_id: str, version: str = 'latest') -> Dict[str, Any]:
        """
        Get API documentation from RefTools
        
        Args:
            api_id: API identifier
            version: API version
            
        Returns:
            API documentation
        """
        if 'reftools' in self.drivers:
            return await self.drivers['reftools'].get_documentation(api_id, version)
        return {'error': 'RefTools not configured', 'documentation': None}
    
    async def create_ai_workflow(self, name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create an AI workflow using Composio
        
        Args:
            name: Workflow name
            steps: Workflow steps
            
        Returns:
            Created workflow details
        """
        if 'composio' in self.drivers:
            return await self.drivers['composio'].create_workflow(name, steps)
        return {'error': 'Composio not configured', 'created': False}
    
    async def get_code_examples(self, api_id: str, method: str = None) -> List[Dict[str, Any]]:
        """
        Get code examples from RefTools
        
        Args:
            api_id: API identifier
            method: Specific method
            
        Returns:
            Code examples
        """
        if 'reftools' in self.drivers:
            return await self.drivers['reftools'].get_code_examples(api_id, method)
        return []
    
    async def get_agent_optimized_tools(self, agent_type: str = 'claude') -> Dict[str, Any]:
        """
        Get tools optimized for specific AI agents
        
        Args:
            agent_type: Type of AI agent
            
        Returns:
            Optimized tools for the agent
        """
        results = {
            'agent_type': agent_type,
            'tools': [],
            'sources': []
        }
        
        # Get tools from Composio
        if 'composio' in self.drivers:
            composio_tools = await self.drivers['composio'].get_agent_tools(agent_type)
            results['tools'].extend(composio_tools)
            results['sources'].append('composio')
        
        # Add RefTools capabilities if available
        if 'reftools' in self.drivers:
            reftools_info = {
                'id': 'api_reference_search',
                'name': 'API Reference Search',
                'description': 'Search and retrieve API documentation',
                'source': 'reftools'
            }
            results['tools'].append(reftools_info)
            results['sources'].append('reftools')
        
        return results
    
    async def validate_api_specification(self, spec_content: str, spec_type: str = 'openapi') -> Dict[str, Any]:
        """
        Validate API specification using RefTools
        
        Args:
            spec_content: API specification content
            spec_type: Type of specification
            
        Returns:
            Validation results
        """
        if 'reftools' in self.drivers:
            return await self.drivers['reftools'].validate_api_spec(spec_content, spec_type)
        return {'valid': False, 'errors': ['RefTools not configured']}
    
    async def health_check_all_servers(self) -> Dict[str, Any]:
        """
        Check health of all configured MCP servers
        
        Returns:
            Health status of all servers
        """
        health_status = {}
        
        for server_id, server_config in self.servers.items():
            status = {
                'name': server_config.get('name'),
                'type': server_config.get('type'),
                'healthy': False,
                'details': {}
            }
            
            # Check driver-based servers
            if server_id in self.drivers:
                driver = self.drivers[server_id]
                if hasattr(driver, 'get_info'):
                    status['details'] = driver.get_info()
                    status['healthy'] = status['details'].get('configured', False)
            
            # Check internal servers
            elif server_config.get('type') == 'internal':
                port = server_config.get('port')
                if port:
                    try:
                        async with httpx.AsyncClient(timeout=5) as client:
                            endpoint = self.config.get('health_checks', {}).get('endpoints', {}).get(server_id, '/health')
                            response = await client.get(f'http://localhost:{port}{endpoint}')
                            status['healthy'] = response.status_code == 200
                            status['details'] = {'port': port, 'endpoint': endpoint}
                    except:
                        status['healthy'] = False
            
            health_status[server_id] = status
        
        return health_status
    
    async def orchestrate_complex_task(self, task_description: str) -> Dict[str, Any]:
        """
        Orchestrate a complex task using multiple MCP servers
        
        Args:
            task_description: Description of the task to perform
            
        Returns:
            Orchestration results
        """
        results = {
            'task': task_description,
            'steps_completed': [],
            'errors': []
        }
        
        # Example orchestration flow
        try:
            # Step 1: Search for relevant API documentation
            if 'reftools' in self.drivers:
                api_search = await self.search_api_references(task_description)
                results['steps_completed'].append({
                    'step': 'api_search',
                    'result_count': len(api_search.get('results', []))
                })
            
            # Step 2: Get AI tools for the task
            if 'composio' in self.drivers:
                tools = await self.list_ai_tools()
                results['steps_completed'].append({
                    'step': 'tool_discovery',
                    'tools_found': len(tools.get('tools', []))
                })
            
            # Step 3: Create workflow if multiple steps identified
            if len(results['steps_completed']) > 1:
                workflow_steps = [
                    {'action': 'search_api', 'params': {'query': task_description}},
                    {'action': 'generate_code', 'params': {'language': 'python'}}
                ]
                
                if 'composio' in self.drivers:
                    workflow = await self.create_ai_workflow(
                        name=f"Task: {task_description[:50]}",
                        steps=workflow_steps
                    )
                    results['steps_completed'].append({
                        'step': 'workflow_creation',
                        'workflow_id': workflow.get('id')
                    })
            
        except Exception as e:
            results['errors'].append(str(e))
        
        return results
    
    def get_server_info(self, server_id: str) -> Dict[str, Any]:
        """
        Get information about a specific server
        
        Args:
            server_id: Server identifier
            
        Returns:
            Server information
        """
        if server_id in self.servers:
            info = self.servers[server_id].copy()
            if server_id in self.drivers:
                driver = self.drivers[server_id]
                if hasattr(driver, 'get_info'):
                    info['driver_info'] = driver.get_info()
            return info
        return {'error': f'Server {server_id} not found'}
    
    def list_all_servers(self) -> List[Dict[str, Any]]:
        """
        List all configured MCP servers
        
        Returns:
            List of server configurations
        """
        servers_list = []
        for server_id, server_config in self.servers.items():
            info = {
                'id': server_id,
                'name': server_config.get('name'),
                'type': server_config.get('type'),
                'enabled': server_config.get('enabled', True),
                'has_driver': server_id in self.drivers
            }
            servers_list.append(info)
        return servers_list


# Singleton instance
_orchestrator_instance = None

def get_orchestrator(config_path: str = None) -> MCPOrchestrator:
    """Get or create the MCP Orchestrator singleton"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MCPOrchestrator(config_path)
    return _orchestrator_instance