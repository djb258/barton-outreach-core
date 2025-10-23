# ─────────────────────────────────────────────
# 📁 CTB Classification Metadata
# ─────────────────────────────────────────────
# CTB Branch: sys/github-factory
# Barton ID: 04.04.06
# Unique ID: CTB-A69C7A5F
# Blueprint Hash:
# Last Updated: 2025-10-23
# Enforcement: ORBT
# ─────────────────────────────────────────────

@echo off
REM Auto-deploy script for Barton Outreach Core orchestration system (Windows)

echo 🚀 Deploying Barton Outreach Core orchestration system...

REM Check if we're in a git repo
if not exist ".git" (
    echo 📁 Initializing git repository...
    git init
)

REM Add all files
echo 📦 Adding files to git...
git add .

REM Commit with detailed message
echo 💾 Committing changes...
git commit -m "Add complete orchestration system

✨ Features:
- HEIR agent orchestration with master/branch coordination
- Lead processing: CSV → canonicalization → validation  
- Message composition: persona resolution → drafting → personalization
- Delivery management: channel mapping → rate limiting → tracking
- Express webhook server for external service integration
- CLI tools for workflow execution and system monitoring

🏗️ Architecture:
- Master orchestrator coordinates cross-branch workflows
- Branch orchestrators handle specialized processing pipelines
- Database integration with Neon PostgreSQL
- External API integration (Apify, Instantly, HeyReach, MillionVerifier)
- Comprehensive error handling and retry mechanisms

🛠️ Operations:
- Webhook endpoints for external service callbacks
- Manual workflow triggers via CLI and API
- Real-time status monitoring and health checks
- Environment-based configuration management
- Production-ready deployment setup

📚 Documentation:
- Complete usage guide with examples
- Environment configuration reference
- API endpoint documentation
- Development and production setup instructions

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

REM Check if remote exists
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo ❌ No git remote 'origin' found!
    echo Please create a GitHub repository and run:
    echo git remote add origin https://github.com/yourusername/barton-outreach-core.git
    echo Then run this script again.
    pause
    exit /b 1
)

REM Push to GitHub
echo 🌐 Pushing to GitHub...
git push -u origin main

echo ✅ Successfully deployed to GitHub!
echo.
echo 🔗 Next steps:
echo 1. Install dependencies: npm install
echo 2. Configure environment: cp .env.example .env
echo 3. Start worker: npm run dev:worker
echo 4. Test workflows: npm run test:lead
echo.
echo 📖 See docs/orchestration-usage.md for complete usage guide
pause