# CC System Diagram

**Doctrine Version**: v1.1.0
**Last Updated**: 2026-01-05

---

## Full System Diagram

```mermaid
flowchart TB
    %% CC-01 SOVEREIGN (External)
    subgraph CC01["CC-01 SOVEREIGN (External)"]
        CL["Company Lifecycle (CL)<br/>MINTS: company_unique_id"]
    end

    %% CC-02 HUB (Ownership + Routing)
    subgraph CC02["CC-02 HUB (Ownership + Routing)"]
        CT["Company Target<br/>04.04.01"]
        DOL["DOL Filings<br/>04.04.03"]
        PI["People Intelligence<br/>04.04.02"]
        BLOG["Blog Content<br/>04.04.05"]
        OE["Outreach Execution<br/>04.04.04"]
    end

    %% CC-03 CONTEXT
    subgraph CC03["CC-03 CONTEXT"]
        CTX["contexts/"]
        CON["contracts/"]
    end

    %% CC-04 PROCESS
    subgraph CC04["CC-04 PROCESS"]
        PHASES["phases/"]
        OPS["ops/"]
    end

    %% Identity Flow
    CL -->|"company_unique_id"| CT

    %% Waterfall
    CT --> DOL
    CT --> PI
    DOL --> PI
    CT --> BLOG
    PI --> OE
    CT --> OE

    %% Context Binding
    CTX -.-> CC02
    CON -.-> CC02

    %% Process Execution
    PHASES -.-> CC02
    OPS -.-> CC02
```

---

## ERD-Style Layer Diagram

```mermaid
erDiagram
    CC01_SOVEREIGN ||--o{ CC02_HUB : "provides identity"
    CC02_HUB ||--o{ CC03_CONTEXT : "creates"
    CC03_CONTEXT ||--o{ CC04_PROCESS : "bounds"

    CC01_SOVEREIGN {
        uuid company_unique_id PK "SOVEREIGN - IMMUTABLE"
        string company_name
        string company_domain
        timestamp created_at
    }

    CC02_HUB {
        uuid outreach_context_id PK "program-scoped"
        uuid company_unique_id FK "from CC-01"
        string hub_name
        string status
    }

    CC03_CONTEXT {
        uuid context_id PK
        uuid outreach_context_id FK
        jsonb configuration
        string scope
    }

    CC04_PROCESS {
        uuid pid PK "process ID"
        uuid context_id FK
        string phase_name
        string status
        timestamp executed_at
    }
```

---

## Hub Waterfall Diagram

```mermaid
flowchart LR
    subgraph WATERFALL["Outreach Waterfall (Sequential)"]
        direction LR
        CT["1. Company Target<br/>04.04.01<br/>━━━━━━━━━━━━<br/>Domain<br/>Pattern<br/>BIT"]
        DOL["2. DOL Filings<br/>04.04.03<br/>━━━━━━━━━━━━<br/>EIN<br/>Form 5500"]
        PI["3. People Intel<br/>04.04.02<br/>━━━━━━━━━━━━<br/>People<br/>Slots"]
        BLOG["4. Blog Content<br/>04.04.05<br/>━━━━━━━━━━━━<br/>Signals<br/>News"]
        OE["5. Outreach Exec<br/>04.04.04<br/>━━━━━━━━━━━━<br/>Campaigns<br/>Contacts"]
    end

    CT -->|"PASS"| DOL
    DOL -->|"PASS"| PI
    CT -->|"PASS"| PI
    CT -->|"PASS"| BLOG
    PI -->|"PASS"| OE

    style CT fill:#e3f2fd
    style DOL fill:#e3f2fd
    style PI fill:#e3f2fd
    style BLOG fill:#e3f2fd
    style OE fill:#e3f2fd
```

---

## Authorization Matrix Diagram

```mermaid
flowchart TB
    subgraph MATRIX["CC Authorization Matrix"]
        direction TB

        CC01["CC-01<br/>SOVEREIGN"]
        CC02["CC-02<br/>HUB"]
        CC03["CC-03<br/>CONTEXT"]
        CC04["CC-04<br/>PROCESS"]

        CC01 -->|"WRITE ✓"| CC02
        CC01 -->|"WRITE ✓"| CC03
        CC01 -->|"WRITE ✓"| CC04

        CC02 -->|"DENIED ✗"| CC01
        CC02 -->|"WRITE ✓<br/>(within boundary)"| CC02
        CC02 -->|"WRITE ✓"| CC03
        CC02 -->|"WRITE ✓"| CC04

        CC03 -->|"DENIED ✗"| CC01
        CC03 -->|"DENIED ✗"| CC02
        CC03 -->|"WRITE ✓<br/>(same context)"| CC03
        CC03 -->|"WRITE ✓"| CC04

        CC04 -->|"DENIED ✗"| CC01
        CC04 -->|"DENIED ✗"| CC02
        CC04 -->|"READ ONLY"| CC03
        CC04 -->|"WRITE ✓<br/>(same PID)"| CC04
    end

    style CC01 fill:#ffcdd2,stroke:#c62828
    style CC02 fill:#bbdefb,stroke:#1565c0
    style CC03 fill:#fff9c4,stroke:#f9a825
    style CC04 fill:#c8e6c9,stroke:#2e7d32
```

---

## Spoke Interface Diagram

```mermaid
flowchart LR
    subgraph SPOKE_NET["Spoke Network (I/O Only)"]
        CT((Company<br/>Target))
        DOL((DOL<br/>Filings))
        PI((People<br/>Intel))
        OE((Outreach<br/>Exec))

        CT <-->|"company-dol"| DOL
        CT <-->|"company-people"| PI
        CT <-->|"company-outreach"| OE
        PI <-->|"people-outreach"| OE

        EXT[/"External<br/>Signals"/]
        EXT -->|"signal-company<br/>(ingress only)"| CT
    end

    style CT fill:#e3f2fd
    style DOL fill:#e3f2fd
    style PI fill:#e3f2fd
    style OE fill:#e3f2fd
    style EXT fill:#f3e5f5
```

---

## Legend

| Color | CC Layer | Description |
|-------|----------|-------------|
| Red | CC-01 | Sovereign (External) |
| Blue | CC-02 | Hub (Ownership) |
| Yellow | CC-03 | Context (Configuration) |
| Green | CC-04 | Process (Runtime) |
| Purple | Spoke | Interface (No CC Layer) |

---

## Files

- `cc_system_diagram.mmd` - Full Mermaid source
- `CC_SYSTEM_DIAGRAM.md` - This file (rendered diagrams)
