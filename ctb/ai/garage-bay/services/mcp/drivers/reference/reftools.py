"""
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: ai/garage-bay
Barton ID: 03.01.02
Unique ID: CTB-AEF9BE4A
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
"""

"""
RefTools MCP Driver - Integration with ref.tools API reference service
"""

import os
import json
import httpx
from typing import Dict, Any, List, Optional
from pathlib import Path
from ..base_driver import BaseDriver

class RefToolsDriver(BaseDriver):
    """
    MCP Driver for ref.tools - API documentation and reference management
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.base_url = self.config.get('base_url', 'https://api.ref.tools/v1')
        self.api_key = self.config.get('api_key') or os.getenv('REFTOOLS_API_KEY')
        self.timeout = self.config.get('timeout', 30)
        
    def validate_config(self) -> bool:
        """Validate RefTools configuration"""
        if not self.api_key:
            print("[RefTools] Warning: No API key configured. Some features may be limited.")
            return False
        return True
        
    async def search_references(self, query: str, language: str = None, framework: str = None) -> Dict[str, Any]:
        """
        Search API references and documentation
        
        Args:
            query: Search query
            language: Programming language filter (optional)
            framework: Framework filter (optional)
            
        Returns:
            Search results with reference documentation
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json'
        }
        
        params = {
            'q': query,
            'language': language,
            'framework': framework
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f'{self.base_url}/search',
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    'error': str(e),
                    'results': [],
                    'fallback': self._get_fallback_references(query, language, framework)
                }
    
    async def get_documentation(self, api_id: str, version: str = 'latest') -> Dict[str, Any]:
        """
        Get detailed API documentation
        
        Args:
            api_id: API identifier
            version: API version (default: latest)
            
        Returns:
            Detailed API documentation
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f'{self.base_url}/docs/{api_id}/{version}',
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    'error': str(e),
                    'api_id': api_id,
                    'version': version,
                    'documentation': None
                }
    
    async def get_code_examples(self, api_id: str, method: str = None) -> List[Dict[str, Any]]:
        """
        Get code examples for an API
        
        Args:
            api_id: API identifier
            method: Specific method/endpoint (optional)
            
        Returns:
            List of code examples
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json'
        }
        
        endpoint = f'{self.base_url}/examples/{api_id}'
        if method:
            endpoint += f'/{method}'
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(endpoint, headers=headers)
                response.raise_for_status()
                return response.json().get('examples', [])
            except httpx.HTTPError:
                return self._get_fallback_examples(api_id, method)
    
    async def validate_api_spec(self, spec_content: str, spec_type: str = 'openapi') -> Dict[str, Any]:
        """
        Validate API specification
        
        Args:
            spec_content: API specification content
            spec_type: Type of specification (openapi, graphql, etc.)
            
        Returns:
            Validation results
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'spec': spec_content,
            'type': spec_type
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f'{self.base_url}/validate',
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    'valid': False,
                    'errors': [str(e)],
                    'warnings': []
                }
    
    def _get_fallback_references(self, query: str, language: str = None, framework: str = None) -> List[Dict[str, Any]]:
        """Provide fallback references when API is unavailable"""
        fallback_refs = [
            {
                'title': 'Python Standard Library',
                'language': 'python',
                'url': 'https://docs.python.org/3/library/',
                'description': 'Official Python standard library documentation'
            },
            {
                'title': 'JavaScript MDN Web Docs',
                'language': 'javascript',
                'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
                'description': 'Comprehensive JavaScript documentation'
            },
            {
                'title': 'React Documentation',
                'framework': 'react',
                'language': 'javascript',
                'url': 'https://react.dev/',
                'description': 'Official React documentation'
            },
            {
                'title': 'FastAPI Documentation',
                'framework': 'fastapi',
                'language': 'python',
                'url': 'https://fastapi.tiangolo.com/',
                'description': 'FastAPI framework documentation'
            }
        ]
        
        # Filter based on language/framework if provided
        results = []
        for ref in fallback_refs:
            if language and ref.get('language') != language:
                continue
            if framework and ref.get('framework') != framework:
                continue
            if query.lower() in ref['title'].lower() or query.lower() in ref.get('description', '').lower():
                results.append(ref)
        
        return results
    
    def _get_fallback_examples(self, api_id: str, method: str = None) -> List[Dict[str, Any]]:
        """Provide fallback code examples"""
        return [
            {
                'language': 'python',
                'code': f'''# Example for {api_id}
import requests

response = requests.{method or 'get'}('https://api.example.com/{api_id}')
data = response.json()
print(data)''',
                'description': 'Basic Python example'
            },
            {
                'language': 'javascript',
                'code': f'''// Example for {api_id}
fetch('https://api.example.com/{api_id}')
  .then(response => response.json())
  .then(data => console.log(data));''',
                'description': 'Basic JavaScript example'
            }
        ]
    
    async def generate_client(self, api_spec: str, language: str, output_dir: str = None) -> Dict[str, Any]:
        """
        Generate API client from specification
        
        Args:
            api_spec: API specification (OpenAPI, etc.)
            language: Target programming language
            output_dir: Output directory for generated client
            
        Returns:
            Generated client information
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'spec': api_spec,
            'language': language,
            'options': {
                'package_name': 'generated_client',
                'with_tests': True
            }
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(
                    f'{self.base_url}/generate',
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Save generated files if output_dir provided
                if output_dir and 'files' in result:
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)
                    
                    for file_info in result['files']:
                        file_path = output_path / file_info['name']
                        file_path.write_text(file_info['content'])
                    
                    result['output_directory'] = str(output_path)
                
                return result
                
            except httpx.HTTPError as e:
                return {
                    'error': str(e),
                    'generated': False
                }
    
    def get_info(self) -> Dict[str, Any]:
        """Get driver information"""
        return {
            'driver': 'RefToolsDriver',
            'version': '1.0.0',
            'service': 'ref.tools',
            'capabilities': [
                'search_references',
                'get_documentation',
                'get_code_examples',
                'validate_api_spec',
                'generate_client'
            ],
            'configured': bool(self.api_key),
            'base_url': self.base_url
        }