/**
 * AgentEventLog
 * =============
 * Event logging system for tracking agent actions and validation outcomes.
 *
 * Purpose:
 * - Track EMAIL_SKIPPED events with full context
 * - Capture validation decisions and reasons
 * - Enable audit trail for Golden Rule enforcement
 * - Support metrics and reporting
 *
 * Event Types:
 * - EMAIL_SKIPPED: Email generation was skipped due to validation failure
 * - COMPANY_VALIDATED: Company validation result
 * - PERSON_VALIDATED: Person-company validation result
 * - PATTERN_DISCOVERED: Email pattern discovered for company
 * - MOVEMENT_DETECTED: Employment movement detected
 */

/**
 * Event type enumeration.
 */
export type AgentEventType =
  | "EMAIL_SKIPPED"
  | "COMPANY_VALIDATED"
  | "PERSON_VALIDATED"
  | "PATTERN_DISCOVERED"
  | "MOVEMENT_DETECTED"
  | "SLOT_FILLED"
  | "SLOT_MISSING"
  | "LINKEDIN_FOUND"
  | "LINKEDIN_NOT_FOUND"
  | "EMAIL_GENERATED"
  | "EMAIL_VERIFIED"
  | "VALIDATION_ERROR";

/**
 * Event severity levels.
 */
export type EventSeverity = "INFO" | "WARNING" | "ERROR";

/**
 * Skip reason categories for EMAIL_SKIPPED events.
 */
export type EmailSkipReason =
  | "COMPANY_INVALID"
  | "COMPANY_MANUAL_REVIEW"
  | "PERSON_COMPANY_MISMATCH"
  | "NO_EMAIL_PATTERN"
  | "NO_PERSON_NAME"
  | "NO_COMPANY_NAME"
  | "NO_LINKEDIN_URL"
  | "ALREADY_SKIPPED"
  | "VALIDATION_FAILED"
  | "OTHER";

/**
 * Base event structure.
 */
export interface AgentEvent {
  /** Unique event ID */
  event_id: string;
  /** Event type */
  event_type: AgentEventType;
  /** Event severity */
  severity: EventSeverity;
  /** Timestamp */
  timestamp: Date;
  /** Agent that generated the event */
  agent_type: string;
  /** Company context */
  company_id: string;
  company_name: string;
  /** Slot/row context (if applicable) */
  slot_row_id?: string;
  person_name?: string;
  slot_type?: string;
  /** Event-specific payload */
  payload: Record<string, unknown>;
  /** Human-readable message */
  message: string;
}

/**
 * EMAIL_SKIPPED event payload.
 */
export interface EmailSkippedPayload {
  skip_reason: EmailSkipReason;
  skip_reason_detail: string;
  company_valid: boolean;
  company_invalid_reason?: string;
  person_company_valid: boolean;
  person_company_match_score?: number;
  email_pattern_available: boolean;
}

/**
 * COMPANY_VALIDATED event payload.
 */
export interface CompanyValidatedPayload {
  valid: boolean;
  match_status: "MATCHED" | "MANUAL_REVIEW" | "UNMATCHED";
  match_score: number;
  matched_company?: string;
  reason?: string;
}

/**
 * PERSON_VALIDATED event payload.
 */
export interface PersonValidatedPayload {
  valid: boolean;
  scraped_employer?: string;
  canonical_company: string;
  match_score: number;
  reason?: string;
}

/**
 * AgentEventLog - Centralized event logging system.
 *
 * Usage:
 * ```typescript
 * const log = new AgentEventLog();
 *
 * // Log an email skip event
 * log.logEmailSkipped(
 *   "EmailGeneratorAgent",
 *   companyId,
 *   companyName,
 *   slotRowId,
 *   personName,
 *   slotType,
 *   {
 *     skip_reason: "COMPANY_INVALID",
 *     skip_reason_detail: "Company not found in master list",
 *     company_valid: false,
 *     person_company_valid: true,
 *     email_pattern_available: false,
 *   }
 * );
 *
 * // Get skip statistics
 * const stats = log.getSkipStatistics();
 * ```
 */
export class AgentEventLog {
  private events: AgentEvent[] = [];
  private maxEvents: number;

  constructor(maxEvents: number = 10000) {
    this.maxEvents = maxEvents;
  }

  /**
   * Generate unique event ID.
   */
  private generateEventId(): string {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Add an event to the log.
   */
  addEvent(event: Omit<AgentEvent, "event_id" | "timestamp">): AgentEvent {
    const fullEvent: AgentEvent = {
      ...event,
      event_id: this.generateEventId(),
      timestamp: new Date(),
    };

    this.events.push(fullEvent);

    // Trim if exceeding max
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }

    return fullEvent;
  }

  /**
   * Log an EMAIL_SKIPPED event.
   */
  logEmailSkipped(
    agentType: string,
    companyId: string,
    companyName: string,
    slotRowId: string,
    personName: string | null,
    slotType: string,
    payload: EmailSkippedPayload
  ): AgentEvent {
    return this.addEvent({
      event_type: "EMAIL_SKIPPED",
      severity: "WARNING",
      agent_type: agentType,
      company_id: companyId,
      company_name: companyName,
      slot_row_id: slotRowId,
      person_name: personName ?? undefined,
      slot_type: slotType,
      payload: payload as unknown as Record<string, unknown>,
      message: `Email generation skipped for ${personName || "unknown"} at ${companyName}: ${payload.skip_reason_detail}`,
    });
  }

  /**
   * Log a COMPANY_VALIDATED event.
   */
  logCompanyValidated(
    agentType: string,
    companyId: string,
    companyName: string,
    payload: CompanyValidatedPayload
  ): AgentEvent {
    return this.addEvent({
      event_type: "COMPANY_VALIDATED",
      severity: payload.valid ? "INFO" : "WARNING",
      agent_type: agentType,
      company_id: companyId,
      company_name: companyName,
      payload: payload as unknown as Record<string, unknown>,
      message: payload.valid
        ? `Company validated: ${companyName} matched to ${payload.matched_company} (score: ${payload.match_score})`
        : `Company validation failed: ${companyName} - ${payload.reason}`,
    });
  }

  /**
   * Log a PERSON_VALIDATED event.
   */
  logPersonValidated(
    agentType: string,
    companyId: string,
    companyName: string,
    slotRowId: string,
    personName: string,
    payload: PersonValidatedPayload
  ): AgentEvent {
    return this.addEvent({
      event_type: "PERSON_VALIDATED",
      severity: payload.valid ? "INFO" : "WARNING",
      agent_type: agentType,
      company_id: companyId,
      company_name: companyName,
      slot_row_id: slotRowId,
      person_name: personName,
      payload: payload as unknown as Record<string, unknown>,
      message: payload.valid
        ? `Person-company validated: ${personName} at ${payload.canonical_company} (score: ${payload.match_score})`
        : `Person-company validation failed: ${personName} - ${payload.reason}`,
    });
  }

  /**
   * Log an EMAIL_GENERATED event.
   */
  logEmailGenerated(
    agentType: string,
    companyId: string,
    companyName: string,
    slotRowId: string,
    personName: string,
    email: string,
    verified: boolean
  ): AgentEvent {
    return this.addEvent({
      event_type: "EMAIL_GENERATED",
      severity: "INFO",
      agent_type: agentType,
      company_id: companyId,
      company_name: companyName,
      slot_row_id: slotRowId,
      person_name: personName,
      payload: { email, verified },
      message: `Email generated for ${personName}: ${email} (verified: ${verified})`,
    });
  }

  /**
   * Get all events.
   */
  getEvents(): AgentEvent[] {
    return [...this.events];
  }

  /**
   * Get events by type.
   */
  getEventsByType(eventType: AgentEventType): AgentEvent[] {
    return this.events.filter((e) => e.event_type === eventType);
  }

  /**
   * Get events by company.
   */
  getEventsByCompany(companyId: string): AgentEvent[] {
    return this.events.filter((e) => e.company_id === companyId);
  }

  /**
   * Get EMAIL_SKIPPED events.
   */
  getSkippedEmails(): AgentEvent[] {
    return this.getEventsByType("EMAIL_SKIPPED");
  }

  /**
   * Get skip statistics.
   */
  getSkipStatistics(): {
    total_skipped: number;
    by_reason: Record<EmailSkipReason, number>;
    by_company: Record<string, number>;
    by_agent: Record<string, number>;
  } {
    const skippedEvents = this.getSkippedEmails();

    const byReason: Record<string, number> = {};
    const byCompany: Record<string, number> = {};
    const byAgent: Record<string, number> = {};

    for (const event of skippedEvents) {
      const payload = event.payload as unknown as EmailSkippedPayload;
      const reason = payload.skip_reason || "OTHER";

      byReason[reason] = (byReason[reason] || 0) + 1;
      byCompany[event.company_id] = (byCompany[event.company_id] || 0) + 1;
      byAgent[event.agent_type] = (byAgent[event.agent_type] || 0) + 1;
    }

    return {
      total_skipped: skippedEvents.length,
      by_reason: byReason as Record<EmailSkipReason, number>,
      by_company: byCompany,
      by_agent: byAgent,
    };
  }

  /**
   * Get validation summary.
   */
  getValidationSummary(): {
    companies_validated: number;
    companies_valid: number;
    companies_invalid: number;
    people_validated: number;
    people_valid: number;
    people_invalid: number;
    emails_generated: number;
    emails_skipped: number;
  } {
    const companyEvents = this.getEventsByType("COMPANY_VALIDATED");
    const personEvents = this.getEventsByType("PERSON_VALIDATED");
    const emailEvents = this.getEventsByType("EMAIL_GENERATED");
    const skippedEvents = this.getEventsByType("EMAIL_SKIPPED");

    return {
      companies_validated: companyEvents.length,
      companies_valid: companyEvents.filter(
        (e) => (e.payload as unknown as CompanyValidatedPayload).valid
      ).length,
      companies_invalid: companyEvents.filter(
        (e) => !(e.payload as unknown as CompanyValidatedPayload).valid
      ).length,
      people_validated: personEvents.length,
      people_valid: personEvents.filter(
        (e) => (e.payload as unknown as PersonValidatedPayload).valid
      ).length,
      people_invalid: personEvents.filter(
        (e) => !(e.payload as unknown as PersonValidatedPayload).valid
      ).length,
      emails_generated: emailEvents.length,
      emails_skipped: skippedEvents.length,
    };
  }

  /**
   * Generate report string.
   */
  generateReport(): string {
    const stats = this.getSkipStatistics();
    const summary = this.getValidationSummary();
    const lines: string[] = [];

    lines.push("=".repeat(60));
    lines.push("AGENT EVENT LOG REPORT");
    lines.push("=".repeat(60));
    lines.push("");

    lines.push("VALIDATION SUMMARY");
    lines.push("-".repeat(40));
    lines.push(`  Companies validated: ${summary.companies_validated}`);
    lines.push(`  Companies valid:     ${summary.companies_valid}`);
    lines.push(`  Companies invalid:   ${summary.companies_invalid}`);
    lines.push(`  People validated:    ${summary.people_validated}`);
    lines.push(`  People valid:        ${summary.people_valid}`);
    lines.push(`  People invalid:      ${summary.people_invalid}`);
    lines.push("");

    lines.push("EMAIL GENERATION");
    lines.push("-".repeat(40));
    lines.push(`  Emails generated: ${summary.emails_generated}`);
    lines.push(`  Emails skipped:   ${summary.emails_skipped}`);
    lines.push("");

    lines.push("SKIP REASONS BREAKDOWN");
    lines.push("-".repeat(40));
    for (const [reason, count] of Object.entries(stats.by_reason)) {
      lines.push(`  ${reason}: ${count}`);
    }
    lines.push("");

    lines.push("SKIPS BY COMPANY");
    lines.push("-".repeat(40));
    const sortedCompanies = Object.entries(stats.by_company)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
    for (const [company, count] of sortedCompanies) {
      lines.push(`  ${company}: ${count}`);
    }
    lines.push("");

    lines.push("=".repeat(60));

    return lines.join("\n");
  }

  /**
   * Export events to JSON.
   */
  exportToJSON(): string {
    return JSON.stringify(this.events, null, 2);
  }

  /**
   * Export skipped emails to CSV format.
   */
  exportSkippedToCSV(): string {
    const skipped = this.getSkippedEmails();
    const headers = [
      "event_id",
      "timestamp",
      "company_id",
      "company_name",
      "person_name",
      "slot_type",
      "skip_reason",
      "skip_reason_detail",
      "company_valid",
      "person_company_valid",
    ];

    const rows = skipped.map((e) => {
      const payload = e.payload as unknown as EmailSkippedPayload;
      return [
        e.event_id,
        e.timestamp.toISOString(),
        e.company_id,
        e.company_name,
        e.person_name || "",
        e.slot_type || "",
        payload.skip_reason,
        payload.skip_reason_detail,
        String(payload.company_valid),
        String(payload.person_company_valid),
      ];
    });

    return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  }

  /**
   * Clear all events.
   */
  clear(): void {
    this.events = [];
  }

  /**
   * Get event count.
   */
  get count(): number {
    return this.events.length;
  }
}

/**
 * Global event log instance.
 */
export const globalEventLog = new AgentEventLog();
