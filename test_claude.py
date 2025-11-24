#!/usr/bin/env python3
"""Test Anthropic Claude API connection."""
import os
from anthropic import Anthropic

api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set")
    exit(1)

try:
    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=50,
        messages=[
            {"role": "user", "content": "Say 'Hello from Claude!' in one sentence."}
        ]
    )
    print("SUCCESS!")
    print(f"Response: {message.content[0].text}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
