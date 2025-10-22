#!/usr/bin/env python3
"""
Apify Actor Discovery Script
Discovers all Apify actors, analyzes their schemas, and generates comprehensive inventory report
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Configuration
APIFY_API_KEY = os.getenv('APIFY_API_KEY', '')
COMPOSIO_MCP_URL = os.getenv('COMPOSIO_MCP_URL', 'http://localhost:3001')
UNIQUE_ID = '04.01.99.11.05000.001'
PROCESS_ID = 'Apify Actor Discovery and Schema Analysis'

# Known actors to check
KNOWN_ACTORS = [
    'apify/email-phone-scraper',
    'apify/linkedin-profile-scraper',
    'apify/website-content-crawler',
    'apify/linkedin-company-scraper',
    'apify/google-search-scraper',
    'apify/contact-finder',
    'apify/people-data-scraper',
    'apify/web-scraper',
    'compass/apollo-scraper',
    'compass/linkedin-people-scraper',
]

# Executive enrichment keywords
EXECUTIVE_KEYWORDS = [
    'ceo', 'cfo', 'hr', 'executive', 'officer', 'director', 'manager',
    'leadership', 'title', 'role', 'position', 'linkedin', 'contact',
    'email', 'name', 'company', 'organization', 'people', 'profile'
]

def fetch_actor_details(actor_id: str) -> Dict[str, Any]:
    """Fetch detailed information about an Apify actor"""
    url = f'https://api.apify.com/v2/acts/{actor_id}'
    params = {'token': APIFY_API_KEY}

    print(f'  [FETCH] Fetching: {actor_id}')

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f'     [OK] Success')
            return data.get('data', {})
        else:
            print(f'     [WARN] HTTP {response.status_code}')
            return None
    except Exception as e:
        print(f'     [ERROR] Error: {str(e)}')
        return None

def analyze_for_executive_enrichment(actor: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze an actor's relevance for executive enrichment"""

    title = (actor.get('title', '') or '').lower()
    description = (actor.get('description', '') or '').lower()
    input_schema = actor.get('inputSchema', {})

    score = 0
    relevant_fields = []

    # Analyze input schema properties
    properties = input_schema.get('properties', {})
    for field, field_data in properties.items():
        field_lower = field.lower()
        field_desc = (field_data.get('description', '') or '').lower()

        for keyword in EXECUTIVE_KEYWORDS:
            if keyword in field_lower or keyword in field_desc:
                score += 10
                relevant_fields.append({
                    'field': field,
                    'type': field_data.get('type', 'unknown'),
                    'description': field_data.get('description', ''),
                    'keyword': keyword
                })
                break  # Count each field only once

    # Analyze title and description
    for keyword in EXECUTIVE_KEYWORDS:
        if keyword in title:
            score += 5
        if keyword in description:
            score += 3

    # Categorize actor
    is_people = any(kw in title or kw in description for kw in ['people', 'contact', 'profile', 'person'])
    is_company = any(kw in title or kw in description for kw in ['company', 'organization', 'business'])
    is_linkedin = 'linkedin' in title or 'linkedin' in description
    is_email = 'email' in title or 'email' in description

    return {
        'relevanceScore': score,
        'relevantFields': relevant_fields,
        'isPeopleEnrichment': is_people,
        'isCompanyEnrichment': is_company,
        'isLinkedInSpecific': is_linkedin,
        'isEmailFocused': is_email,
        'categories': {
            'people': is_people,
            'company': is_company,
            'linkedin': is_linkedin,
            'email': is_email
        }
    }

def extract_input_fields(input_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and summarize input fields from schema"""
    properties = input_schema.get('properties', {})
    required = input_schema.get('required', [])

    fields = []
    for field_name, field_data in properties.items():
        fields.append({
            'name': field_name,
            'type': field_data.get('type', 'unknown'),
            'description': field_data.get('description', ''),
            'required': field_name in required,
            'default': field_data.get('default'),
            'enum': field_data.get('enum')
        })

    return fields

def extract_output_fields(output_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract and summarize output fields from schema"""
    properties = output_schema.get('properties', {})

    fields = []
    for field_name, field_data in properties.items():
        fields.append({
            'name': field_name,
            'type': field_data.get('type', 'unknown'),
            'description': field_data.get('description', '')
        })

    return fields

def discover_actors() -> Dict[str, Any]:
    """Main discovery function"""

    print('\n>> Starting Apify Actor Discovery')
    print('=' * 70)
    print(f'[KEY] API Key: {APIFY_API_KEY[:10]}...' if APIFY_API_KEY else '[ERROR] No API Key')
    print(f'[PROC] Process ID: {PROCESS_ID}')
    print(f'[ID] Unique ID: {UNIQUE_ID}')
    print('=' * 70)
    print()

    if not APIFY_API_KEY:
        print('[ERROR] APIFY_API_KEY not set in environment')
        print('   Please set it in .env file')
        return None

    results = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'unique_id': UNIQUE_ID,
        'process_id': PROCESS_ID,
        'discoveredActors': [],
        'currentlyUsedActors': [
            {
                'actorId': 'apify/email-phone-scraper',
                'usage': 'Primary contact scraper in apifyRunner.js',
                'location': 'agents/specialists/apifyRunner.js:18'
            },
            {
                'actorId': 'apify~linkedin-profile-scraper',
                'usage': 'LinkedIn profile scraping',
                'location': 'packages/mcp-clients/src/clients/apify-mcp-client.ts:57'
            },
            {
                'actorId': 'apify~website-content-crawler',
                'usage': 'Website contact extraction',
                'location': 'packages/mcp-clients/src/clients/apify-mcp-client.ts:118'
            }
        ],
        'mockActors': [
            'linkedin-company-scraper',
            'website-content-crawler',
            'company-data-scraper',
            'business-permit-scraper',
            'financial-data-scraper'
        ],
        'errors': []
    }

    print('[LIST] Discovering Apify actors...\n')

    for actor_id in KNOWN_ACTORS:
        try:
            actor_data = fetch_actor_details(actor_id)

            if actor_data:
                # Analyze for executive enrichment
                analysis = analyze_for_executive_enrichment(actor_data)

                # Extract input/output schemas
                input_fields = extract_input_fields(actor_data.get('inputSchema', {}))
                output_fields = extract_output_fields(actor_data.get('outputSchema', {}))

                # Build actor record
                actor_record = {
                    'actorId': actor_id,
                    'title': actor_data.get('title', ''),
                    'description': actor_data.get('description', '')[:500],
                    'username': actor_data.get('username', actor_id.split('/')[0]),
                    'isPublic': actor_data.get('isPublic', False),
                    'stats': {
                        'totalRuns': actor_data.get('stats', {}).get('totalRuns', 0),
                        'totalUsers': actor_data.get('stats', {}).get('totalUsers', 0)
                    },
                    'inputFields': input_fields,
                    'outputFields': output_fields,
                    'analysis': analysis,
                    'versions': actor_data.get('versions', [])
                }

                results['discoveredActors'].append(actor_record)

                print(f'     [SCORE] Relevance Score: {analysis["relevanceScore"]}')
                print(f'     [PEOPLE] People: {analysis["isPeopleEnrichment"]}')
                print(f'     [COMPANY] Company: {analysis["isCompanyEnrichment"]}')
                print(f'     [LINKEDIN] LinkedIn: {analysis["isLinkedInSpecific"]}')
                print(f'     [EMAIL] Email: {analysis["isEmailFocused"]}')
                print(f'     [INPUT] Input Fields: {len(input_fields)}')
                print(f'     [OUTPUT] Output Fields: {len(output_fields)}')
                print()

        except Exception as e:
            results['errors'].append({
                'actorId': actor_id,
                'error': str(e)
            })
            print()

    # Rank actors by relevance
    ranked = sorted(
        [a for a in results['discoveredActors'] if a['analysis']['relevanceScore'] > 0],
        key=lambda x: x['analysis']['relevanceScore'],
        reverse=True
    )

    results['topExecutiveEnrichmentActors'] = [
        {
            'rank': i + 1,
            'actorId': actor['actorId'],
            'title': actor['title'],
            'relevanceScore': actor['analysis']['relevanceScore'],
            'categories': actor['analysis']['categories'],
            'keyInputFields': [f['name'] for f in actor['input Fields'][:5]],
            'keyOutputFields': [f['name'] for f in actor['outputFields'][:5]]
        }
        for i, actor in enumerate(ranked[:10])
    ]

    return results

def save_results(results: Dict[str, Any]):
    """Save discovery results to file"""
    output_dir = Path(__file__).parent
    output_file = output_dir / 'apify_discovery_raw.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f'[SAVE] Saved raw results to: {output_file}')
    return output_file

def print_summary(results: Dict[str, Any]):
    """Print discovery summary"""
    print('\n[SUMMARY] DISCOVERY SUMMARY')
    print('=' * 70)
    print(f"Total Actors Discovered: {len(results['discoveredActors'])}")
    print(f"Currently Used in Codebase: {len(results['currentlyUsedActors'])}")
    print(f"Errors Encountered: {len(results['errors'])}")

    print('\n[TOP] Top 3 Actors for Executive Enrichment:\n')

    for actor in results['topExecutiveEnrichmentActors'][:3]:
        print(f"{actor['rank']}. {actor['actorId']}")
        print(f"   [SCORE] Score: {actor['relevanceScore']}")
        print(f"   [TITLE] Title: {actor['title']}")
        print(f"   [PEOPLE] People: {actor['categories']['people']}")
        print(f"   [COMPANY] Company: {actor['categories']['company']}")
        print(f"   [LINKEDIN] LinkedIn: {actor['categories']['linkedin']}")
        print(f"   [EMAIL] Email: {actor['categories']['email']}")
        if actor.get('keyInputFields'):
            print(f"   [INPUTS] Key Inputs: {', '.join(actor['keyInputFields'])}")
        print()

    print('=' * 70)

if __name__ == '__main__':
    results = discover_actors()

    if results:
        output_file = save_results(results)
        print_summary(results)
        print(f'\n[OK] Discovery completed successfully!')
        print(f'[FILE] Results saved to: {output_file}')
    else:
        print('\n[ERROR] Discovery failed')
        exit(1)
