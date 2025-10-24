# UI Specifications

This directory contains UI specifications, wireframes, and design documents for outreach pipeline interfaces.

## Purpose

Define user interfaces for:
- Campaign management dashboards
- Contact enrichment viewers
- Performance analytics displays
- Error monitoring consoles
- A/B testing configuration

## Structure

```
ui_specs/
├── README.md                    ← This file
├── dashboards/                  ← Dashboard wireframes
│   ├── campaign_overview.md
│   ├── enrichment_status.md
│   └── analytics_dashboard.md
├── components/                  ← Reusable UI components
│   ├── contact_card.md
│   ├── metric_widget.md
│   └── event_timeline.md
└── flows/                       ← User interaction flows
    ├── campaign_creation.md
    └── error_resolution.md
```

## Design Principles

1. **Data-Driven** - All UI elements backed by Neon queries
2. **Real-Time** - Live updates from n8n REST API + WebSocket
3. **Responsive** - Mobile-first design for on-the-go monitoring
4. **Accessible** - WCAG 2.1 AA compliance
5. **Performance** - <2s load time, optimistic updates

## Tools

- **Wireframing:** Figma, Excalidraw
- **Prototyping:** React + shadcn/ui
- **Data Viz:** Recharts, D3.js
- **State Management:** React Query (for API caching)

## Related

- **Data Source:** Neon PostgreSQL (`marketing.*` tables)
- **API Endpoints:** n8n REST API (https://dbarton.app.n8n.cloud/api/v1)
- **Event Stream:** PostgreSQL LISTEN/NOTIFY

---

**Status:** Planning Phase
**Last Updated:** 2025-10-24
