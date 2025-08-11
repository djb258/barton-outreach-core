# HEIR Architecture Compliance - Apollo Scraper Service

This document outlines how the Apollo Scraper Service adheres to the HEIR (Hierarchical, Event-driven, Intelligent, Resilient) architecture principles and serves as a template for future service integrations.

## 🏗️ HEIR Architecture Principles

### H - Hierarchical
The Apollo Scraper operates as a specialized agent within the Barton Outreach Core hierarchy:

```
Barton Outreach Core (Master Orchestrator)
├── Lead Generation Domain
│   ├── Apollo Scraper Service ⭐ (This Service)
│   ├── LinkedIn Scraper Service (Future)
│   └── Email Finder Service (Future)
├── Campaign Management Domain
│   ├── Email Campaign Service
│   └── Follow-up Automation Service
└── Analytics Domain
    ├── Performance Analytics Service
    └── ROI Tracking Service
```

#### Implementation:
- **Agent Registration**: Service registers with `heir/agent-registry.ts`
- **Capability Declaration**: Declares `apollo-scraping`, `contact-enrichment`, `lead-generation`
- **Hierarchical Communication**: Reports to orchestration engine, not direct peer-to-peer
- **Role Specialization**: Focused solely on Apollo.io data collection

### E - Event-driven
All operations are asynchronous and event-based:

#### Event Types:
```typescript
// Service Events
interface ApolloScraperEvents {
  'job.started': { jobId: string, companyName: string };
  'job.progress': { jobId: string, progress: number, status: string };
  'job.completed': { jobId: string, resultCount: number };
  'job.failed': { jobId: string, error: string };
  'data.processed': { companyId: string, contactCount: number };
  'health.status': { status: 'healthy' | 'degraded' | 'unhealthy' };
}
```

#### Implementation:
- **Async Processing**: All scraping operations are non-blocking
- **Status Updates**: Real-time job status via WebSocket or polling
- **Event Publishing**: Publishes events to core event bus
- **Webhook Support**: Can receive events from external systems (Apify callbacks)

### I - Intelligent
Service incorporates intelligent decision-making and adaptive behavior:

#### Intelligence Features:
1. **Smart Filtering**: Advanced contact filtering based on titles, roles, seniority
2. **Apollo URL Analysis**: Intelligent parsing and validation of search parameters  
3. **Adaptive Rate Limiting**: Adjusts scraping speed based on API response times
4. **Quality Assessment**: Evaluates contact data quality and completeness
5. **Learning Optimization**: Tracks successful patterns for better results

#### Implementation:
```typescript
// Intelligent filtering logic
class IntelligentContactFilter {
  private executiveTitles = ['CEO', 'CTO', 'VP', 'Director', 'Head of'];
  private excludeTerms = ['intern', 'assistant', 'junior'];
  
  assessContactQuality(contact: Contact): QualityScore {
    // Smart quality scoring algorithm
  }
  
  adaptFilterCriteria(pastResults: ScrapingResult[]): FilterCriteria {
    // Learn from successful patterns
  }
}
```

### R - Resilient
Comprehensive error handling, recovery, and fault tolerance:

#### Resilience Mechanisms:
1. **Circuit Breaker**: Prevents cascading failures
2. **Retry Logic**: Exponential backoff for transient failures  
3. **Graceful Degradation**: Partial functionality during outages
4. **Health Monitoring**: Continuous health checks and self-healing
5. **Data Backup**: Multiple storage options and failover

#### Implementation:
```typescript
// Resilient operation wrapper
class ResilientOperation {
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    return this.circuitBreaker.wrap(
      this.retryPolicy.wrap(
        this.timeoutPolicy.wrap(operation)
      )
    );
  }
}
```

## 🔄 Integration Patterns for Future Services

When adding new services to the Barton Outreach Core, ensure they follow these HEIR patterns:

### 1. Service Structure Template
```
services/[service-name]/
├── api/                    # REST API endpoints
│   ├── routes/            # Route handlers
│   ├── middleware/        # Custom middleware
│   └── server.js          # Express server
├── lib/                   # Core business logic
│   ├── intelligence/      # AI/ML components
│   ├── resilience/        # Error handling & recovery
│   └── events/            # Event handling
├── integration/           # HEIR integration points
│   ├── agent-config.ts    # Agent registry configuration
│   ├── events.ts          # Event definitions
│   └── orchestration.ts   # Task definitions
├── tests/                 # Comprehensive testing
├── docs/                  # Service documentation
└── HEIR_COMPLIANCE.md     # This document
```

### 2. Service Configuration Pattern
```typescript
// integration/agent-config.ts
export const serviceAgentConfig = {
  id: 'service-name',
  type: 'domain-category',
  version: '1.0.0',
  capabilities: [
    'capability-1',
    'capability-2'
  ],
  dependencies: [
    'required-service-1',
    'optional-service-2'
  ],
  endpoints: {
    health: '/api/v1/health',
    primary: '/api/v1/primary-action'
  },
  events: {
    publishes: ['event.completed', 'event.failed'],
    subscribes: ['system.shutdown', 'config.updated']
  },
  resilience: {
    timeout: 30000,
    retries: 3,
    circuitBreaker: true
  }
};
```

### 3. Event Handling Pattern
```typescript
// lib/events/event-handler.ts
export class ServiceEventHandler {
  constructor(private eventBus: EventBus) {
    this.setupEventListeners();
  }
  
  private setupEventListeners() {
    // Subscribe to system events
    this.eventBus.on('system.shutdown', this.handleGracefulShutdown);
    this.eventBus.on('config.updated', this.handleConfigUpdate);
  }
  
  async publishEvent(eventType: string, payload: any) {
    // Intelligent event publishing with retry
    await this.resilientPublish(eventType, payload);
  }
}
```

### 4. Health Check Pattern
```typescript
// api/routes/health.ts
export const healthCheckEndpoint = {
  endpoint: '/api/v1/health',
  checks: [
    'database-connectivity',
    'external-api-status', 
    'memory-usage',
    'cpu-usage',
    'disk-space'
  ],
  response: {
    status: 'healthy' | 'degraded' | 'unhealthy',
    checks: Record<string, HealthStatus>,
    timestamp: string,
    uptime: number
  }
};
```

## 📋 HEIR Compliance Checklist

Before integrating any new service, verify it meets these HEIR requirements:

### Hierarchical ✅
- [ ] Service is registered in agent registry
- [ ] Clear capability definitions
- [ ] Proper role within domain hierarchy
- [ ] Communication through orchestration layer

### Event-driven ✅
- [ ] All operations are asynchronous
- [ ] Event publishing for major state changes
- [ ] Event subscription for system notifications
- [ ] Webhook support where applicable

### Intelligent ✅
- [ ] Smart decision-making algorithms
- [ ] Adaptive behavior based on feedback
- [ ] Learning from historical data
- [ ] Quality assessment mechanisms

### Resilient ✅
- [ ] Circuit breaker implementation
- [ ] Retry logic with exponential backoff
- [ ] Graceful degradation capabilities
- [ ] Comprehensive error handling
- [ ] Health monitoring and self-healing

## 🚨 Anti-Patterns to Avoid

### ❌ Non-HEIR Compliant Patterns:
1. **Direct Service-to-Service Communication**: Always go through orchestration layer
2. **Synchronous Operations**: Use async/await and event-driven patterns
3. **Hardcoded Dependencies**: Use dependency injection and configuration
4. **No Error Recovery**: Always implement resilience mechanisms
5. **Monolithic Design**: Keep services focused and specialized

### ❌ Architecture Violations:
- Bypassing the agent registry
- Blocking operations without timeout
- Direct database access from multiple services
- Tightly coupled service dependencies
- Missing health check endpoints

## 📈 Monitoring and Observability

All HEIR-compliant services must provide:

### Metrics
- Request/response times
- Success/failure rates
- Resource utilization
- Business-specific KPIs

### Logging
- Structured logging (JSON format)
- Correlation IDs for request tracing
- Appropriate log levels
- No sensitive data in logs

### Tracing
- Distributed tracing support
- Performance bottleneck identification
- Cross-service request flow tracking

### Alerting
- Health check failures
- Performance degradation
- Resource exhaustion
- Business metric anomalies

## 🔮 Future Evolution Guidelines

As the Barton Outreach Core system grows, maintain HEIR compliance by:

1. **Regular Architecture Reviews**: Quarterly assessments of service alignment
2. **Evolution Planning**: Consider HEIR impact when adding features
3. **Documentation Updates**: Keep HEIR compliance docs current
4. **Training**: Ensure all developers understand HEIR principles
5. **Tooling**: Develop tools to enforce HEIR compliance automatically

## 📞 HEIR Compliance Support

For questions about HEIR compliance:
- **Architecture Review**: Submit PR for review
- **Documentation**: Update this document for new patterns
- **Training**: Regular HEIR architecture workshops
- **Tools**: Automated compliance checking in CI/CD

---

**Remember**: Every new process, service, or component should be evaluated against HEIR principles to maintain system coherence, scalability, and reliability.