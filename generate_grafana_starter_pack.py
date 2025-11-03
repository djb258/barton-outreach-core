#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate complete Grafana starter pack for Neon Marketing Database visualization.
Creates Docker setup, datasource config, and pre-built dashboards.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.03.01
Unique ID: CTB-GRAFANA
Enforcement: ORBT
"""

import os
import json

def create_folder_structure():
    """Create necessary folders for Grafana provisioning."""
    print("\n[1/6] Creating folder structure...")
    
    os.makedirs("grafana/provisioning/datasources", exist_ok=True)
    os.makedirs("grafana/provisioning/dashboards", exist_ok=True)
    os.makedirs("grafana/dashboards", exist_ok=True)
    
    print("      Created: grafana/provisioning/datasources/")
    print("      Created: grafana/provisioning/dashboards/")
    print("      Created: grafana/dashboards/")
    print()

def create_docker_compose():
    """Create docker-compose.yml for Grafana."""
    print("[2/6] Creating docker-compose.yml...")
    
    docker_compose = """version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    container_name: barton-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - grafana-storage:/var/lib/grafana
    restart: unless-stopped
    networks:
      - barton-network

networks:
  barton-network:
    driver: bridge

volumes:
  grafana-storage:
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose.strip())
    
    print("      [OK] docker-compose.yml created")
    print()

def create_neon_datasource():
    """Create Neon PostgreSQL datasource configuration."""
    print("[3/6] Creating Neon datasource config...")
    
    neon_datasource = {
        "apiVersion": 1,
        "datasources": [
            {
                "name": "Neon Marketing DB",
                "type": "postgres",
                "access": "proxy",
                "url": "ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432",
                "database": "Marketing DB",
                "user": "Marketing DB_owner",
                "secureJsonData": {
                    "password": "npg_OsE4Z2oPCpiT"
                },
                "jsonData": {
                    "sslmode": "require",
                    "postgresVersion": 1700,
                    "timescaledb": False
                },
                "isDefault": True,
                "editable": True
            }
        ]
    }
    
    with open("grafana/provisioning/datasources/neon.yaml", "w") as f:
        f.write("# Neon PostgreSQL Datasource\n")
        f.write("apiVersion: 1\n\n")
        f.write("datasources:\n")
        f.write("  - name: Neon Marketing DB\n")
        f.write("    type: postgres\n")
        f.write("    access: proxy\n")
        f.write("    url: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432\n")
        f.write("    database: Marketing DB\n")
        f.write("    user: Marketing DB_owner\n")
        f.write("    secureJsonData:\n")
        f.write("      password: npg_OsE4Z2oPCpiT\n")
        f.write("    jsonData:\n")
        f.write("      sslmode: require\n")
        f.write("      postgresVersion: 1700\n")
        f.write("    isDefault: true\n")
        f.write("    editable: true\n")
    
    print("      [OK] Neon datasource configured")
    print("      Host: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech")
    print("      Database: Marketing DB")
    print()

def create_dashboard_provisioning():
    """Create dashboard provisioning config."""
    print("[4/6] Creating dashboard provisioning...")
    
    dashboard_config = """apiVersion: 1

providers:
  - name: 'Barton Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
"""
    
    with open("grafana/provisioning/dashboards/dashboard.yaml", "w") as f:
        f.write(dashboard_config)
    
    print("      [OK] Dashboard provisioning configured")
    print()

def create_outreach_dashboard():
    """Create main outreach metrics dashboard."""
    print("[5/6] Creating Barton Outreach Dashboard...")
    
    dashboard_obj = {
        "annotations": {
            "list": []
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": [
            {
                "datasource": {"type": "postgres", "uid": "neon"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None}
                            ]
                        },
                        "unit": "short"
                    }
                },
                "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                "id": 1,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {
                        "calcs": ["lastNotNull"],
                        "fields": "",
                        "values": False
                    },
                    "textMode": "auto"
                },
                "targets": [{
                    "format": "table",
                    "rawSql": "SELECT COUNT(*) as \"Companies\" FROM marketing.company_master",
                    "refId": "A"
                }],
                "title": "🏢 Total Companies",
                "type": "stat"
            },
            {
                "datasource": {"type": "postgres", "uid": "neon"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None}
                            ]
                        }
                    }
                },
                "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                "id": 2,
                "options": {"colorMode": "value", "textMode": "auto"},
                "targets": [{
                    "format": "table",
                    "rawSql": "SELECT COUNT(*) as \"Contacts\" FROM marketing.people_master",
                    "refId": "A"
                }],
                "title": "👥 Total Contacts",
                "type": "stat"
            },
            {
                "datasource": {"type": "postgres", "uid": "neon"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "red", "value": None},
                                {"color": "yellow", "value": 100},
                                {"color": "green", "value": 500}
                            ]
                        }
                    }
                },
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "id": 3,
                "options": {"colorMode": "value", "textMode": "auto"},
                "targets": [{
                    "format": "table",
                    "rawSql": "SELECT COUNT(*) as \"Tasks\" FROM marketing.people_resolution_queue WHERE status = 'pending'",
                    "refId": "A"
                }],
                "title": "🔥 Pending Resolution Tasks",
                "type": "stat"
            },
            {
                "datasource": {"type": "postgres", "uid": "neon"},
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "fillOpacity": 80,
                            "gradientMode": "none",
                            "hideFrom": {"tooltip": False, "viz": False, "legend": False},
                            "lineWidth": 1
                        }
                    }
                },
                "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                "id": 4,
                "options": {"legend": {"displayMode": "list", "placement": "bottom"}},
                "targets": [{
                    "format": "table",
                    "rawSql": """SELECT 
                        slot_type as \"Role\",
                        COUNT(*) as \"Count\"
                    FROM marketing.company_slots cs
                    LEFT JOIN marketing.people_master pm ON cs.company_slot_unique_id = pm.company_slot_unique_id
                    WHERE pm.unique_id IS NOT NULL
                    GROUP BY slot_type
                    ORDER BY slot_type""",
                    "refId": "A"
                }],
                "title": "Filled Slots by Role",
                "type": "barchart"
            },
            {
                "datasource": {"type": "postgres", "uid": "neon"},
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "displayMode": "auto",
                            "inspect": False
                        }
                    }
                },
                "gridPos": {"h": 10, "w": 12, "x": 0, "y": 8},
                "id": 5,
                "options": {"showHeader": True},
                "targets": [{
                    "format": "table",
                    "rawSql": """SELECT 
                        cm.company_name as \"Company\",
                        COUNT(pm.unique_id) as \"Contacts\",
                        cm.industry as \"Industry\",
                        cm.address_city as \"City\"
                    FROM marketing.company_master cm
                    LEFT JOIN marketing.people_master pm ON cm.company_unique_id = pm.company_unique_id
                    GROUP BY cm.company_unique_id, cm.company_name, cm.industry, cm.address_city
                    HAVING COUNT(pm.unique_id) > 0
                    ORDER BY COUNT(pm.unique_id) DESC
                    LIMIT 20""",
                    "refId": "A"
                }],
                "title": "Top 20 Companies by Contact Count",
                "type": "table"
            },
            {
                "datasource": {"type": "postgres", "uid": "neon"},
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "displayMode": "auto"
                        }
                    }
                },
                "gridPos": {"h": 10, "w": 12, "x": 12, "y": 8},
                "id": 6,
                "options": {"showHeader": True},
                "targets": [{
                    "format": "table",
                    "rawSql": """SELECT 
                        issue_type as \"Issue\",
                        assigned_to as \"Agent\",
                        COUNT(*) as \"Count\",
                        MIN(priority) as \"Priority\"
                    FROM marketing.people_resolution_queue
                    WHERE status = 'pending'
                    GROUP BY issue_type, assigned_to
                    ORDER BY MIN(priority), COUNT(*) DESC""",
                    "refId": "A"
                }],
                "title": "Resolution Queue Breakdown",
                "type": "table"
            }
        ],
        "refresh": "30s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["barton", "outreach", "neon"],
        "templating": {"list": []},
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": "Barton Outreach Dashboard",
        "uid": "barton_outreach",
        "version": 0,
        "weekStart": ""
    }
    
    with open("grafana/dashboards/barton_outreach_dashboard.json", "w") as f:
        json.dump(dashboard_obj, f, indent=2)
    
    print("      [OK] Barton Outreach Dashboard created")
    print()

def create_readme():
    """Create README with instructions."""
    print("[6/6] Creating Grafana setup guide...")
    
    readme = """# Grafana Dashboard for Barton Outreach Engine

Complete Grafana setup for visualizing your Neon Marketing Database.

## 🚀 Quick Start

### 1. Start Grafana

```bash
docker-compose up -d
```

### 2. Access Grafana

- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`

### 3. View Dashboard

The "Barton Outreach Dashboard" is automatically loaded with:
- Total companies, contacts, and tasks
- Slot fill rates by role (CEO/CFO/HR)
- Top companies by contact count
- Resolution queue breakdown

## 📊 Dashboard Panels

| Panel | Query | Purpose |
|-------|-------|---------|
| Total Companies | `SELECT COUNT(*) FROM marketing.company_master` | Company count |
| Total Contacts | `SELECT COUNT(*) FROM marketing.people_master` | Contact count |
| Pending Tasks | `SELECT COUNT(*) FROM people_resolution_queue WHERE status='pending'` | AI agent queue |
| Filled Slots | Group by role with JOIN | Slot fill visualization |
| Top Companies | Companies ranked by contact count | Enrichment status |
| Queue Breakdown | Issue types and assignments | Agent workload |

## 🔗 Embed in Lovable.dev

### Get Panel URL

1. Open a panel in Grafana
2. Click "Share" → "Link"
3. Toggle "Direct link rendered image"
4. Copy the URL

### Embed in Lovable

```jsx
// In your Lovable.dev component:
<iframe 
  src="http://localhost:3000/d-solo/barton_outreach/barton-outreach-dashboard?orgId=1&panelId=3"
  width="100%"
  height="400"
  frameBorder="0"
></iframe>
```

### Panel IDs

- Panel 1: Total Companies
- Panel 2: Total Contacts  
- Panel 3: Pending Resolution Tasks
- Panel 4: Filled Slots by Role
- Panel 5: Top 20 Companies
- Panel 6: Resolution Queue Breakdown

## 🔧 Customization

### Edit Dashboards

Dashboards are in `grafana/dashboards/` as JSON files. Edit directly or:
1. Edit in Grafana UI
2. Export JSON
3. Save to `grafana/dashboards/`

### Add New Panels

Example SQL queries you can use:

```sql
-- CEO fill rate
SELECT 
  COUNT(CASE WHEN pm.unique_id IS NOT NULL THEN 1 END) as filled,
  COUNT(*) as total
FROM marketing.company_slots cs
LEFT JOIN marketing.people_master pm ON cs.company_slot_unique_id = pm.company_slot_unique_id
WHERE cs.slot_type = 'CEO';

-- Recent pipeline events
SELECT 
  event_type,
  COUNT(*) as count,
  MAX(created_at) as last_event
FROM marketing.pipeline_events
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY event_type;

-- Hot companies (when BIT is active)
SELECT 
  cm.company_name,
  bcs.score,
  bcs.signal_count
FROM marketing.company_master cm
JOIN bit.bit_company_score bcs ON cm.company_unique_id = bcs.company_unique_id
WHERE bcs.score_tier IN ('hot', 'warm')
ORDER BY bcs.score DESC;
```

## 🛠️ Troubleshooting

### Connection Issues

If Grafana can't connect to Neon:
1. Check `grafana/provisioning/datasources/neon.yaml`
2. Verify Neon connection string is correct
3. Ensure SSL mode is set to `require`
4. Check Neon project is not paused

### Dashboard Not Loading

```bash
# Restart Grafana to reload dashboards
docker-compose restart grafana
```

### View Logs

```bash
docker-compose logs -f grafana
```

## 📱 Mobile/Responsive

Grafana dashboards are responsive by default. Use:
- `&kiosk` in URL for fullscreen mode
- `&theme=light` for light theme
- `&refresh=30s` for auto-refresh

## 🎯 Production Deployment

For production (not localhost):

1. Update `docker-compose.yml` environment:
   ```yaml
   - GF_SERVER_ROOT_URL=https://your-domain.com
   - GF_SECURITY_ADMIN_PASSWORD=<strong-password>
   ```

2. Add SSL/TLS proxy (nginx, Caddy, etc.)

3. Restrict anonymous access:
   ```yaml
   - GF_AUTH_ANONYMOUS_ENABLED=false
   ```

---

**Created:** 2025-11-03  
**Neon Database:** Marketing DB (PostgreSQL 17)  
**Auto-refresh:** 30 seconds  
**Dashboard Count:** 1 (expandable)
"""
    
    with open("GRAFANA_SETUP.md", "w", encoding='utf-8') as f:
        f.write(readme)
    
    print("      [OK] GRAFANA_SETUP.md created")
    print()

def main():
    """Generate complete Grafana starter pack."""
    
    print("\n" + "="*100)
    print("GRAFANA STARTER PACK GENERATOR")
    print("="*100)
    print("\nGenerating complete Grafana setup for Neon Marketing Database...")
    print()
    
    create_folder_structure()
    create_docker_compose()
    create_neon_datasource()
    create_dashboard_provisioning()
    create_outreach_dashboard()
    create_readme()
    
    print("="*100)
    print("GRAFANA STARTER PACK GENERATED!")
    print("="*100)
    print()
    print("Files created:")
    print("  - docker-compose.yml")
    print("  - grafana/provisioning/datasources/neon.yaml")
    print("  - grafana/provisioning/dashboards/dashboard.yaml")
    print("  - grafana/dashboards/barton_outreach_dashboard.json")
    print("  - GRAFANA_SETUP.md")
    print()
    print("Next steps:")
    print("  1. Run: docker-compose up -d")
    print("  2. Open: http://localhost:3000")
    print("  3. Login: admin / admin")
    print("  4. View: Barton Outreach Dashboard")
    print()
    print("To embed in Lovable.dev:")
    print("  - Copy panel URLs from Grafana Share menu")
    print("  - Use iframe with panel-specific URLs")
    print("  - See GRAFANA_SETUP.md for examples")
    print()
    print("="*100 + "\n")

if __name__ == "__main__":
    main()

