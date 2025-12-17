# Quick Start Guide

Get up and running with enricha-vision in 5 minutes!

## Prerequisites

- Windows 10/11, macOS, or Linux
- Internet connection
- Administrator/sudo access (for installations)

## Step 1: Install Tools (2 minutes)

### Windows
```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File install-tools.ps1
```

### macOS/Linux
```bash
./install-tools.sh
```

This installs:
- ✅ Git
- ✅ Node.js & npm
- ✅ Obsidian
- ✅ GitKraken

## Step 2: Configure Environment (2 minutes)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Use your favorite editor or:
code .env  # VS Code
notepad .env  # Windows Notepad
nano .env  # Linux/Mac terminal
```

**Required variables:**
```bash
DATABASE_URL="your-neon-postgres-url"
FIREBASE_API_KEY="your-firebase-key"
GEMINI_API_KEY="your-gemini-key"
```

See `ENV_SETUP.md` for detailed instructions on getting API keys.

## Step 3: Install Dependencies (1 minute)

```bash
npm install
```

## Step 4: Launch Applications

### Start Development Server
```bash
npm run dev
```

### Open Obsidian
1. Launch Obsidian
2. Open folder as vault → Select `enricha-vision`
3. Browse CTB documentation in `ctb/docs/`

### Open GitKraken
1. Launch GitKraken
2. File → Open → Select `enricha-vision`
3. Connect GitHub account in settings

## Step 5: Configure Git

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Step 6: Enable Auto-Sync (Optional but Recommended)

Keep your tools automatically updated:

**Start background service:**
```bash
# Windows
start-sync-service.bat

# macOS/Linux
./start-sync-service.sh
```

This will:
- ✅ Auto-pull changes every 5 minutes
- ✅ Sync Obsidian vault automatically
- ✅ Update GitKraken configurations
- ✅ Refresh Git hooks
- ✅ Update CTB registry

See [AUTO_SYNC_GUIDE.md](./AUTO_SYNC_GUIDE.md) for details.

## You're Ready! 🎉

### Next Steps

**Learn the CTB System:**
```bash
# Read the main guide
Read: CTB_README.md
```

**Explore Documentation:**
- Open Obsidian vault
- Browse `ctb/docs/`
- Check out templates in `ctb/docs/templates/`

**Start Developing:**
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Commit: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/your-feature`
5. Create PR on GitHub

**Use GitKraken:**
- Visual commit history
- Easy branch management
- Built-in GitFlow support

### Common Commands

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm run test         # Run tests
npm run lint         # Run linter

# Git
git status           # Check status
git add .            # Stage all changes
git commit -m "msg"  # Commit with message
git push             # Push to remote

# GitFlow (in GitKraken)
GitFlow → Start Feature     # New feature
GitFlow → Finish Feature    # Complete feature
```

## Troubleshooting

**Server won't start?**
- Check `.env` file exists
- Verify all required variables are set
- Run `npm install` again

**Git hooks not working?**
- Windows: `icacls .git\hooks\* /grant:r %USERNAME%:F`
- Mac/Linux: `chmod +x .git/hooks/*`

**Obsidian won't open vault?**
- Make sure you selected the `enricha-vision` folder
- Check `.obsidian` folder exists
- Try "Open another vault"

## Getting Help

1. Check `TOOLS_SETUP.md` for detailed tool configuration
2. Read `ENV_SETUP.md` for environment setup
3. Browse `ctb/docs/guides/` for specific guides
4. Open issue on GitHub

## Project Structure

```
enricha-vision/
├── ctb/                    # CTB system
│   ├── sys/               # System config
│   ├── ai/                # AI config
│   ├── data/              # Database
│   ├── docs/              # Documentation
│   ├── ui/                # UI components
│   └── meta/              # Metadata
├── src/                   # Source code
├── .obsidian/             # Obsidian vault
├── .gitkraken/            # GitKraken config
├── global-config.yaml     # CTB config
├── .env                   # Your environment
└── package.json           # Dependencies
```

## Important Files

- `CTB_README.md` - CTB system overview
- `TOOLS_SETUP.md` - Detailed tools guide
- `ENV_SETUP.md` - Environment configuration
- `SECURITY.md` - Security policies
- `QUICK_START.md` - This file

---

**You're all set! Start building amazing features! 🚀**

For detailed information, see the full documentation in `ctb/docs/`
