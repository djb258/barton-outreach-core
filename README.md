# Welcome to your Lovable project

---

## Doctrine Certifications

| Certification | System | Status | Date |
|---------------|--------|--------|------|
| **TF-001** | Talent Flow | 🚀 PRODUCTION-READY | 2026-01-08 |

> **Note:** Scope expansion for any certified system requires new certification.

---

## Project info

**URL**: https://lovable.dev/projects/a8e59576-8676-4e68-b0fc-322fc78b5a7c

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/a8e59576-8676-4e68-b0fc-322fc78b5a7c) and start prompting.

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

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

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

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## Deployment Platform

✅ **Active**: **Vercel Serverless** (primary and only deployment platform)

❌ **Deprecated**: Render (legacy files archived in `archive/render-legacy/`)

### Deployment Architecture

All external service integrations flow through **Composio MCP** server (port 3001), which runs independently of the deployment platform. This enables:
- Serverless-first architecture (Vercel edge functions)
- 100+ service integrations via single MCP interface
- No direct API credentials in deployment environment
- Simplified deployment and scaling

See: [VERCEL_DEPLOYMENT_GUIDE.md](./VERCEL_DEPLOYMENT_GUIDE.md) for deployment instructions

See: [COMPOSIO_INTEGRATION.md](./COMPOSIO_INTEGRATION.md) for MCP integration details

**Note**: Legacy Render files have been archived as part of doctrinal compliance audit (October 2025). See [docs/audit_report.md](./docs/audit_report.md) for details.

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/a8e59576-8676-4e68-b0fc-322fc78b5a7c) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/features/custom-domain#custom-domain)
