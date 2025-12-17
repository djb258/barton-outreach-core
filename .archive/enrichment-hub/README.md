# Enricha Vision

AI-powered enrichment and vision tracking system with CTB (Component-Task-Blueprint) architecture.

## 🚀 Quick Start

**New to the project?** Start here: [QUICK_START.md](./QUICK_START.md)

**Setting up tools?** See: [TOOLS_SETUP.md](./TOOLS_SETUP.md)

**Need environment config?** Check: [ENV_SETUP.md](./ENV_SETUP.md)

## Project Info

**Lovable URL**: https://lovable.dev/projects/9c3b8311-2229-4bff-a6bc-4033931c5bc9

**Repository**: https://github.com/djb258/enricha-vision.git

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/9c3b8311-2229-4bff-a6bc-4033931c5bc9) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Copy the environment variables file and configure your settings.
cp .env.example .env
# Edit .env and add your Supabase credentials and n8n webhook URLs

# Step 5: Start the development server with auto-reloading and an instant preview.
npm run dev
```

### Running in VS Code

This project works seamlessly with VS Code or Cursor:

1. **Install dependencies**: `npm install`
2. **Configure environment**: 
   - Copy `.env.example` to `.env`
   - The Supabase credentials are automatically configured via Lovable Cloud
   - Add your n8n webhook URLs for the enrichment tools
3. **Start dev server**: `npm run dev`
4. **Test Supabase connection**: The app will automatically connect to Lovable Cloud backend

**VS Code Extensions Recommended:**
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- TypeScript Vue Plugin (Volar)

**Development Tips:**
- Use the provided n8n webhook integration in `/lib/n8nClient.ts`
- All Supabase operations use the client from `/src/integrations/supabase/client.ts`
- Add new enrichment tools by extending the webhook configuration

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

### Core Stack
- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS + shadcn-ui
- **State**: Zustand / React Context
- **Database**: Firebase Firestore + Neon PostgreSQL
- **AI**: Google Gemini Pro + OpenAI
- **Integration**: Composio MCP + n8n webhooks

### Development Tools
- **Git**: Version control
- **GitKraken**: Visual Git client with GitFlow
- **Obsidian**: Documentation and knowledge management
- **Node.js**: Runtime environment

### CTB Architecture

This project implements the **CTB (Component-Task-Blueprint)** system:

```
ctb/
├── sys/      # System integrations (Firebase, Neon, Composio, GitHub)
├── ai/       # AI models and prompts (Gemini, OpenAI)
├── data/     # Database schemas and migrations
├── docs/     # Complete documentation
├── ui/       # UI components and pages
└── meta/     # HEIR/ORBT system and registry
```

**Learn more**: [CTB_README.md](./CTB_README.md)

## 📚 Documentation

- **[QUICK_START.md](./QUICK_START.md)** - Get started in 5 minutes
- **[CTB_README.md](./CTB_README.md)** - CTB system overview
- **[TOOLS_SETUP.md](./TOOLS_SETUP.md)** - Obsidian, GitKraken, Git setup
- **[ENV_SETUP.md](./ENV_SETUP.md)** - Environment configuration
- **[SECURITY.md](./SECURITY.md)** - Security policies
- **[ctb/docs/](./ctb/docs/)** - Complete project documentation

## 🔧 Development Setup

### Automated Installation

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File install-tools.ps1
```

**macOS/Linux:**
```bash
./install-tools.sh
```

This installs: Git, Node.js, Obsidian, GitKraken, and all dependencies.

### Manual Setup

```sh
# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start development
npm run dev
```

## 🎯 Features

- ✅ CTB Architecture with doctrine enforcement
- ✅ Firebase Authentication & Firestore
- ✅ Neon PostgreSQL integration
- ✅ AI-powered features (Gemini Pro)
- ✅ n8n webhook integrations
- ✅ Automated compliance checking
- ✅ Git hooks for quality assurance
- ✅ Obsidian documentation vault
- ✅ GitKraken visual Git workflow
- ✅ **Auto-sync system** - Keeps tools updated automatically

## 🔄 Auto-Sync System

The project includes an automated synchronization system that keeps Obsidian, GitKraken, and Git configurations up-to-date:

**Features:**
- 🔁 Auto-sync on Git pull/merge/checkout
- 📦 Background service for continuous monitoring
- 🎯 Smart pull management with auto-stash
- 📋 Updates CTB registry automatically
- 🔧 Refreshes tool configurations

**Quick Usage:**

```bash
# Windows
powershell -File auto-sync.ps1 -Watch

# macOS/Linux
./auto-sync.sh --watch

# Or run as background service
./start-sync-service.sh
```

**Learn more:** [AUTO_SYNC_GUIDE.md](./AUTO_SYNC_GUIDE.md)

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/9c3b8311-2229-4bff-a6bc-4033931c5bc9) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
