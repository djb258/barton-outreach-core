#!/usr/bin/env python3
"""
MCP Server Demo - Demonstrates RefTools and Composio integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent and garage-mcp directories to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / "garage-mcp"))

# Import from the correct path
from services.mcp.modules.mcp_orchestrator import get_orchestrator

async def demo_reftools():
    """Demonstrate RefTools API reference capabilities"""
    print("\n=== RefTools API Reference Demo ===\n")
    
    orchestrator = get_orchestrator()
    
    # Search for API references
    print("1. Searching for FastAPI documentation...")
    results = await orchestrator.search_api_references("FastAPI", language="python")
    
    if 'error' not in results:
        print(f"   Found {len(results.get('results', []))} results")
        for result in results.get('results', [])[:3]:
            print(f"   - {result.get('title')}: {result.get('url')}")
    else:
        print(f"   Using fallback references: {len(results.get('fallback', []))} available")
    
    # Get code examples
    print("\n2. Getting code examples for REST API...")
    examples = await orchestrator.get_code_examples("rest-api", method="POST")
    
    print(f"   Found {len(examples)} code examples")
    for example in examples[:2]:
        print(f"   - {example.get('language')}: {example.get('description')}")
    
    # Validate API specification
    print("\n3. Validating OpenAPI specification...")
    sample_spec = """
    openapi: 3.0.0
    info:
      title: Sample API
      version: 1.0.0
    paths:
      /health:
        get:
          summary: Health check
          responses:
            '200':
              description: Healthy
    """
    
    validation = await orchestrator.validate_api_specification(sample_spec, spec_type='openapi')
    print(f"   Valid: {validation.get('valid')}")
    if validation.get('errors'):
        print(f"   Errors: {validation.get('errors')}")

async def demo_composio():
    """Demonstrate Composio AI agent tools"""
    print("\n=== Composio AI Agent Tools Demo ===\n")
    
    orchestrator = get_orchestrator()
    
    # List available tools
    print("1. Listing available AI tools...")
    tools_response = await orchestrator.list_ai_tools(category="development")
    
    tools = tools_response.get('tools', [])
    print(f"   Found {len(tools)} development tools")
    for tool in tools[:5]:
        print(f"   - {tool.get('name')}: {tool.get('description')}")
    
    # Get agent-optimized tools
    print("\n2. Getting Claude-optimized tools...")
    agent_tools = await orchestrator.get_agent_optimized_tools(agent_type='claude')
    
    print(f"   Found {len(agent_tools.get('tools', []))} optimized tools")
    print(f"   Sources: {', '.join(agent_tools.get('sources', []))}")
    
    for tool in agent_tools.get('tools', [])[:3]:
        print(f"   - {tool.get('name')}: {tool.get('description')}")
    
    # Create a workflow
    print("\n3. Creating an AI workflow...")
    workflow_steps = [
        {
            'action': 'web_search',
            'params': {'query': 'latest Python features'}
        },
        {
            'action': 'code_generation',
            'params': {'language': 'python', 'task': 'example using new features'}
        }
    ]
    
    workflow = await orchestrator.create_ai_workflow(
        name="Python Feature Explorer",
        steps=workflow_steps
    )
    
    if workflow.get('created'):
        print(f"   Workflow created: {workflow.get('workflow_name')}")
    else:
        print(f"   Workflow creation status: {workflow}")

async def demo_orchestration():
    """Demonstrate multi-server orchestration"""
    print("\n=== Multi-Server Orchestration Demo ===\n")
    
    orchestrator = get_orchestrator()
    
    # Check health of all servers
    print("1. Checking health of all MCP servers...")
    health_status = await orchestrator.health_check_all_servers()
    
    for server_id, status in health_status.items():
        health_icon = "[OK]" if status['healthy'] else "[FAIL]"
        print(f"   {health_icon} {status['name']}: {status['type']} server")
    
    # List all configured servers
    print("\n2. Listing all configured servers...")
    all_servers = orchestrator.list_all_servers()
    
    for server in all_servers:
        driver_status = "with driver" if server['has_driver'] else "no driver"
        enabled_status = "enabled" if server['enabled'] else "disabled"
        print(f"   - {server['name']} ({server['type']}, {driver_status}, {enabled_status})")
    
    # Orchestrate a complex task
    print("\n3. Orchestrating a complex task...")
    task_result = await orchestrator.orchestrate_complex_task(
        "Create a REST API client for GitHub with error handling"
    )
    
    print(f"   Task: {task_result['task']}")
    print(f"   Steps completed: {len(task_result['steps_completed'])}")
    for step in task_result['steps_completed']:
        print(f"   - {step['step']}: {step}")
    
    if task_result['errors']:
        print(f"   Errors: {task_result['errors']}")

async def main():
    """Run all demos"""
    print("=" * 60)
    print("MCP Server Integration Demo")
    print("Featuring RefTools and Composio")
    print("=" * 60)
    
    # Check for API keys
    if not os.getenv('REFTOOLS_API_KEY'):
        print("\nWARNING: REFTOOLS_API_KEY not set - using fallback mode")
    
    if not os.getenv('COMPOSIO_API_KEY'):
        print("WARNING: COMPOSIO_API_KEY not set - using fallback mode")
    
    try:
        # Run RefTools demo
        await demo_reftools()
        
        # Run Composio demo
        await demo_composio()
        
        # Run orchestration demo
        await demo_orchestration()
        
    except Exception as e:
        print(f"\nERROR during demo: {e}")
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())