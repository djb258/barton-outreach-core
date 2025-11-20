#!/usr/bin/env python3
"""
Test Enrichment Agent Setup
Verify everything is configured correctly without making API calls
"""

import os
import json
import sys
from pathlib import Path

def check_api_keys():
    """Check if API keys are set in environment"""
    print("\n🔑 Checking API Keys...")

    keys = {
        'APIFY_API_KEY': os.getenv('APIFY_API_KEY'),
        'ABACUS_API_KEY': os.getenv('ABACUS_API_KEY'),
        'FIRECRAWL_API_KEY': os.getenv('FIRECRAWL_API_KEY'),
    }

    all_set = True
    for key_name, key_value in keys.items():
        if not key_value or key_value == f'your_{key_name.lower()}_here':
            print(f"   ❌ {key_name}: NOT SET")
            all_set = False
        else:
            masked = key_value[:8] + '...' + key_value[-4:] if len(key_value) > 12 else key_value[:4] + '...'
            print(f"   ✅ {key_name}: {masked}")

    return all_set

def check_database_url():
    """Check if database URL is set"""
    print("\n💾 Checking Database URL...")

    db_url = os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING')

    if not db_url:
        print("   ❌ DATABASE_URL: NOT SET")
        return False

    # Check if it's the new role (without spaces)
    if 'marketing_db_owner' in db_url:
        print("   ✅ DATABASE_URL: Set (new role without spaces)")
    elif 'Marketing%20DB_owner' in db_url:
        print("   ⚠️  DATABASE_URL: Set (old role with spaces - may cause issues)")
    else:
        print("   ✅ DATABASE_URL: Set")

    return True

def check_config_file():
    """Check if config file exists and is valid JSON"""
    print("\n⚙️  Checking Configuration...")

    config_path = Path(__file__).parent / 'config' / 'agent_config.json'

    if not config_path.exists():
        print("   ❌ agent_config.json: NOT FOUND")
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)

        print("   ✅ agent_config.json: Valid JSON")

        # Check agents
        agents = config.get('agents', {})
        enabled_agents = [name for name, cfg in agents.items() if cfg.get('enabled')]

        print(f"   ✅ Enabled agents: {', '.join(enabled_agents)}")

        # Check config values
        enrichment_config = config.get('enrichment_config', {})
        batch_size = enrichment_config.get('batch_size', 'not set')
        max_concurrent = enrichment_config.get('max_concurrent_agents', 'not set')

        print(f"   ✅ Batch size: {batch_size}")
        print(f"   ✅ Max concurrent: {max_concurrent}")

        # Check throttle rules
        throttle = config.get('throttle_rules', {})
        max_time = throttle.get('max_time_per_record_seconds', 'not set')

        print(f"   ✅ Max time per record: {max_time}s")

        return True

    except json.JSONDecodeError as e:
        print(f"   ❌ agent_config.json: Invalid JSON - {e}")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n📦 Checking Dependencies...")

    required = {
        'asyncpg': 'Async PostgreSQL driver',
        'aiohttp': 'Async HTTP client',
        'dotenv': 'Environment variables'
    }

    all_installed = True
    for package, description in required.items():
        try:
            __import__(package)
            print(f"   ✅ {package}: Installed")
        except ImportError:
            print(f"   ❌ {package}: NOT INSTALLED ({description})")
            all_installed = False

    if not all_installed:
        print("\n   To install: pip install -r requirements.txt")

    return all_installed

def check_database_connection():
    """Test database connection (requires asyncpg)"""
    print("\n🔌 Testing Database Connection...")

    try:
        import asyncpg
        import asyncio

        db_url = os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING')

        if not db_url:
            print("   ⚠️  Skipped (DATABASE_URL not set)")
            return False

        async def test_connection():
            try:
                conn = await asyncpg.connect(db_url)
                result = await conn.fetchval('SELECT 1')
                await conn.close()
                return result == 1
            except Exception as e:
                print(f"   ❌ Connection failed: {e}")
                return False

        success = asyncio.run(test_connection())

        if success:
            print("   ✅ Database connection: SUCCESS")
        else:
            print("   ❌ Database connection: FAILED")

        return success

    except ImportError:
        print("   ⚠️  Skipped (asyncpg not installed)")
        return False

def check_agent_modules():
    """Check if agent modules can be imported"""
    print("\n🤖 Checking Agent Modules...")

    modules = {
        'agents.base_agent': 'Base agent class',
        'agents.apify_agent': 'Apify agent',
        'agents.abacus_agent': 'Abacus agent',
        'agents.firecrawl_agent': 'Firecrawl agent',
        'orchestrator.enrichment_orchestrator': 'Enrichment orchestrator'
    }

    all_imported = True
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"   ✅ {module}: Importable")
        except Exception as e:
            print(f"   ❌ {module}: Error - {e}")
            all_imported = False

    return all_imported

def main():
    """Run all checks"""
    print("\n" + "="*80)
    print("🧪 ENRICHMENT AGENTS SETUP TEST")
    print("="*80)

    # Load .env file
    try:
        from dotenv import load_dotenv
        # Try to load from multiple possible locations
        env_paths = [
            Path(__file__).parent / '.env',
            Path(__file__).parent.parent.parent.parent / '.env',
        ]

        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ Loaded .env from: {env_path}")
                break
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment only")

    # Run checks
    checks = {
        'API Keys': check_api_keys(),
        'Database URL': check_database_url(),
        'Configuration File': check_config_file(),
        'Dependencies': check_dependencies(),
        'Database Connection': check_database_connection(),
        'Agent Modules': check_agent_modules()
    }

    # Summary
    print("\n" + "="*80)
    print("📊 SETUP TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    for check_name, check_result in checks.items():
        status = "✅ PASS" if check_result else "❌ FAIL"
        print(f"{status}: {check_name}")

    print("\n" + "="*80)
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("✅ ALL CHECKS PASSED - Ready to run enrichment!")
        print("\nNext step: python run_enrichment.py --limit 3")
    else:
        print("❌ SOME CHECKS FAILED - Fix issues before running enrichment")
        print("\nRefer to SETUP.md for troubleshooting")

    print("="*80 + "\n")

    sys.exit(0 if passed == total else 1)

if __name__ == '__main__':
    main()
