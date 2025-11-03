"""
Quick server startup script with .env loading
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from the .env file
env_path = Path(__file__).parent / "ctb" / "sys" / "security-audit" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded environment from: {env_path}")
else:
    print(f"[WARN] .env file not found at: {env_path}")

# Verify critical env vars
required_vars = ["NEON_DATABASE_URL", "N8N_API_KEY", "N8N_BASE_URL", "APIFY_TOKEN"]
missing = []
for var in required_vars:
    if os.getenv(var):
        print(f"[OK] {var} loaded")
    else:
        print(f"[FAIL] {var} missing")
        missing.append(var)

if missing:
    print(f"\n[WARN] Missing variables: {', '.join(missing)}")
    print("Server may not function correctly!")

print("\n[START] Starting FastAPI server...")
print("=" * 60)

# Start uvicorn
import uvicorn
uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)
