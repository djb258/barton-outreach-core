#!/usr/bin/env python3
"""Test Gemini API connection."""
import os
import google.generativeai as genai

api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GOOGLE_API_KEY not set")
    exit(1)

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Say 'Hello from Gemini!' in one sentence.")
    print("SUCCESS!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
