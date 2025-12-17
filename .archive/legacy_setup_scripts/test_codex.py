#!/usr/bin/env python3
"""Test OpenAI Codex API connection."""
import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("ERROR: OPENAI_API_KEY not set")
    exit(1)

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Say 'Hello from Codex!' in one sentence."}
        ],
        max_tokens=50
    )
    print("SUCCESS!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
