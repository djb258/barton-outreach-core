"""
Composio MCP Driver - Integration with composio.dev for AI agent tools and integrations
"""

import os
import json
import httpx
from typing import Dict, Any, List, Optional
from pathlib import Path
from ..base_driver import BaseDriver

class ComposioDriver(BaseDriver):
    """
    MCP Driver for composio.dev - AI agent tools and integrations platform
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.base_url = self.config.get('base_url', 'https://api.composio.dev/v1')
        self.api_key = self.config.get('api_key') or os.getenv('COMPOSIO_API_KEY')
        self.workspace_id = self.config.get('workspace_id') or os.getenv('COMPOSIO_WORKSPACE_ID')
        self.timeout = self.config.get('timeout', 30)
        
    def validate_config(self) -> bool:
        """Validate Composio configuration"""
        if not self.api_key:
            print("[Composio] Warning: No API key configured. Using limited mode.")
            return False
        return True
    
    async def list_tools(self, category: str = None) -> List[Dict[str, Any]]:
        """
        List available AI agent tools
        
        Args:
            category: Tool category filter (optional)
            
        Returns:
            List of available tools
        """
        headers = self._get_headers()
        params = {}
        if category:
            params['category'] = category
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f'{self.base_url}/tools',
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return response.json().get('tools', [])
            except httpx.HTTPError:
                return self._get_fallback_tools()
    
    async def get_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific tool
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Tool details including configuration and usage
        """
        headers = self._get_headers()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f'{self.base_url}/tools/{tool_id}',
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    'error': str(e),
                    'tool_id': tool_id,
                    'fallback': self._get_fallback_tool_info(tool_id)
                }
    
    async def create_integration(self, integration_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new integration
        
        Args:
            integration_type: Type of integration (github, slack, discord, etc.)
            config: Integration configuration
            
        Returns:
            Created integration details
        """
        headers = self._get_headers()
        
        payload = {
            'type': integration_type,
            'config': config,
            'workspace_id': self.workspace_id
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f'{self.base_url}/integrations',
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    'error': str(e),
                    'created': False,
                    'integration_type': integration_type
                }
    
    async def execute_action(self, action_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Composio action
        
        Args:
            action_id: Action identifier
            params: Action parameters
            
        Returns:
            Action execution results
        """
        headers = self._get_headers()
        
        payload = {
            'action_id': action_id,
            'params': params,
            'workspace_id': self.workspace_id
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    f'{self.base_url}/actions/execute',
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    'error': str(e),
                    'executed': False,
                    'action_id': action_id
                }
    
    async def create_workflow(self, name: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a multi-step workflow
        
        Args:
            name: Workflow name
            steps: List of workflow steps
            
        Returns:
            Created workflow details
        """
        headers = self._get_headers()
        
        payload = {
            'name': name,
            'steps': steps,
            'workspace_id': self.workspace_id,
            'enabled': True
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f'{self.base_url}/workflows',
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    'error': str(e),
                    'created': False,
                    'workflow_name': name
                }
    
    async def list_integrations(self) -> List[Dict[str, Any]]:
        """
        List all configured integrations
        
        Returns:
            List of integrations
        """
        headers = self._get_headers()
        params = {}
        if self.workspace_id:
            params['workspace_id'] = self.workspace_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f'{self.base_url}/integrations',
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return response.json().get('integrations', [])
            except httpx.HTTPError:
                return []
    
    async def get_agent_tools(self, agent_type: str = 'claude') -> List[Dict[str, Any]]:
        """
        Get tools optimized for specific AI agents
        
        Args:
            agent_type: Type of AI agent (claude, gpt4, etc.)
            
        Returns:
            List of optimized tools for the agent
        """
        headers = self._get_headers()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f'{self.base_url}/agents/{agent_type}/tools',
                    headers=headers
                )
                response.raise_for_status()
                return response.json().get('tools', [])
            except httpx.HTTPError:
                return self._get_fallback_agent_tools(agent_type)
    
    async def create_connection(self, app: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a connection to an external app
        
        Args:
            app: App name (github, slack, notion, etc.)
            credentials: App credentials
            
        Returns:
            Connection details
        """
        headers = self._get_headers()
        
        payload = {
            'app': app,
            'credentials': credentials,
            'workspace_id': self.workspace_id
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f'{self.base_url}/connections',
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    'error': str(e),
                    'connected': False,
                    'app': app
                }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        if self.workspace_id:
            headers['X-Workspace-Id'] = self.workspace_id
        return headers
    
    def _get_fallback_tools(self) -> List[Dict[str, Any]]:
        """Provide fallback tool list when API is unavailable"""
        return [
            {
                'id': 'github_create_issue',
                'name': 'Create GitHub Issue',
                'category': 'development',
                'description': 'Create a new issue in a GitHub repository'
            },
            {
                'id': 'slack_send_message',
                'name': 'Send Slack Message',
                'category': 'communication',
                'description': 'Send a message to a Slack channel'
            },
            {
                'id': 'notion_create_page',
                'name': 'Create Notion Page',
                'category': 'documentation',
                'description': 'Create a new page in Notion'
            },
            {
                'id': 'web_scraper',
                'name': 'Web Scraper',
                'category': 'data',
                'description': 'Extract data from web pages'
            },
            {
                'id': 'code_interpreter',
                'name': 'Code Interpreter',
                'category': 'development',
                'description': 'Execute Python code safely'
            }
        ]
    
    def _get_fallback_tool_info(self, tool_id: str) -> Dict[str, Any]:
        """Provide fallback tool information"""
        tools = {
            'github_create_issue': {
                'parameters': ['repo', 'title', 'body', 'labels'],
                'required': ['repo', 'title'],
                'example': {
                    'repo': 'owner/repo',
                    'title': 'Bug: Issue title',
                    'body': 'Issue description'
                }
            },
            'slack_send_message': {
                'parameters': ['channel', 'text', 'thread_ts'],
                'required': ['channel', 'text'],
                'example': {
                    'channel': '#general',
                    'text': 'Hello from Composio!'
                }
            }
        }
        return tools.get(tool_id, {'error': 'Tool not found in fallback data'})
    
    def _get_fallback_agent_tools(self, agent_type: str) -> List[Dict[str, Any]]:
        """Provide fallback agent-specific tools"""
        base_tools = [
            {
                'id': 'web_search',
                'name': 'Web Search',
                'description': 'Search the web for information',
                'agent_optimized': True
            },
            {
                'id': 'code_execution',
                'name': 'Code Execution',
                'description': 'Execute code in various languages',
                'agent_optimized': True
            },
            {
                'id': 'file_operations',
                'name': 'File Operations',
                'description': 'Read, write, and manipulate files',
                'agent_optimized': True
            }
        ]
        
        # Add agent-specific tools
        if agent_type == 'claude':
            base_tools.append({
                'id': 'claude_artifacts',
                'name': 'Claude Artifacts',
                'description': 'Create and manage Claude artifacts',
                'agent_optimized': True
            })
        
        return base_tools
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for the workspace
        
        Returns:
            Usage statistics
        """
        headers = self._get_headers()
        params = {}
        if self.workspace_id:
            params['workspace_id'] = self.workspace_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f'{self.base_url}/usage',
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return {
                    'actions_executed': 0,
                    'tools_used': 0,
                    'integrations_active': 0
                }
    
    def get_info(self) -> Dict[str, Any]:
        """Get driver information"""
        return {
            'driver': 'ComposioDriver',
            'version': '1.0.0',
            'service': 'composio.dev',
            'capabilities': [
                'list_tools',
                'get_tool',
                'create_integration',
                'execute_action',
                'create_workflow',
                'list_integrations',
                'get_agent_tools',
                'create_connection',
                'get_usage_stats'
            ],
            'configured': bool(self.api_key),
            'workspace_id': self.workspace_id,
            'base_url': self.base_url
        }