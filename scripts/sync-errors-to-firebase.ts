#!/usr/bin/env node

/**
 * Firebase Error Sync Script
 *
 * Syncs error records from Neon PostgreSQL (shq_error_log) to Firebase Firestore (error_log collection)
 * via Composio MCP server integration.
 *
 * Usage:
 *   npm run sync:errors
 *   npm run sync:errors -- --limit 50
 *   npm run sync:errors -- --dry-run
 *
 * Part of Barton Outreach Core - Error Monitoring & Visualization Doctrine
 */

import { Pool } from 'pg';
import axios from 'axios';

// ============================================================================
// CONFIGURATION
// ============================================================================

const NEON_CONNECTION_STRING = process.env.NEON_DATABASE_URL || '';
const COMPOSIO_MCP_URL = process.env.COMPOSIO_MCP_URL || 'http://localhost:3001';
const FIREBASE_PROJECT_ID = process.env.FIREBASE_PROJECT_ID || 'barton-outreach';
const BATCH_SIZE = parseInt(process.env.SYNC_BATCH_SIZE || '100', 10);

// CLI argument parsing
const args = process.argv.slice(2);
const DRY_RUN = args.includes('--dry-run');
const CUSTOM_LIMIT = args.find(arg => arg.startsWith('--limit'))?.split('=')[1];
const LIMIT = CUSTOM_LIMIT ? parseInt(CUSTOM_LIMIT, 10) : BATCH_SIZE;

// ============================================================================
// COLOR CODING - Barton Doctrine Severity Colors
// ============================================================================

const SEVERITY_COLORS: Record<string, string> = {
  info: '#28A745',     // Green - Normal / success messages
  warning: '#FFC107',  // Yellow - Caution / potential issue
  error: '#FD7E14',    // Orange - Standard error
  critical: '#DC3545', // Red - Critical system failure
};

const DEFAULT_COLOR = '#6C757D'; // Gray - Unknown severity

// ============================================================================
// TYPES
// ============================================================================

interface NeonErrorRow {
  id: number;
  error_id: string;
  timestamp: Date;
  agent_name: string | null;
  process_id: string | null;
  unique_id: string | null;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  stack_trace: string | null;
  resolved: boolean;
  resolution_notes: string | null;
  last_touched: Date;
  firebase_synced: boolean;
}

interface FirebaseErrorDoc {
  error_id: string;
  timestamp: string; // ISO 8601
  agent_name: string | null;
  process_id: string | null;
  unique_id: string | null;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  stack_trace: string | null;
  resolved: boolean;
  resolution_notes: string | null;
  last_touched: string; // ISO 8601
  color: string; // Hex color for visualization (#28A745, #FFC107, #FD7E14, #DC3545)
  neon_id: number; // Reference back to source
  synced_at: string; // ISO 8601
}

interface ComposioPayload {
  tool: string;
  data: {
    collection: string;
    document_id: string;
    document_data: FirebaseErrorDoc;
  };
  unique_id: string;
  process_id: string;
  orbt_layer: number;
  blueprint_version: string;
}

interface SyncStats {
  total_fetched: number;
  successfully_synced: number;
  failed: number;
  errors: Array<{ error_id: string; reason: string }>;
}

// ============================================================================
// DATABASE CLIENT
// ============================================================================

class NeonClient {
  private pool: Pool;

  constructor(connectionString: string) {
    if (!connectionString) {
      throw new Error('NEON_DATABASE_URL environment variable is required');
    }

    this.pool = new Pool({
      connectionString,
      ssl: { rejectUnauthorized: false },
    });
  }

  async query<T = any>(sql: string, params: any[] = []): Promise<{ rows: T[]; rowCount: number }> {
    const result = await this.pool.query(sql, params);
    return {
      rows: result.rows,
      rowCount: result.rowCount || 0,
    };
  }

  async close(): Promise<void> {
    await this.pool.end();
  }
}

// ============================================================================
// FIREBASE CLIENT (via Composio MCP)
// ============================================================================

class FirebaseClient {
  private composioUrl: string;
  private projectId: string;

  constructor(composioUrl: string, projectId: string) {
    this.composioUrl = composioUrl;
    this.projectId = projectId;
  }

  async writeDocument(
    collection: string,
    documentId: string,
    data: FirebaseErrorDoc,
    uniqueId: string,
    processId: string
  ): Promise<void> {
    const payload: ComposioPayload = {
      tool: 'firebase_set_document',
      data: {
        collection,
        document_id: documentId,
        document_data: data,
      },
      unique_id: uniqueId,
      process_id: processId,
      orbt_layer: 1, // Visualization layer (1k altitude)
      blueprint_version: '1.0',
    };

    try {
      const response = await axios.post(`${this.composioUrl}/tool`, payload, {
        headers: { 'Content-Type': 'application/json' },
        timeout: 10000,
      });

      if (response.status !== 200) {
        throw new Error(`Firebase write failed: ${response.statusText}`);
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          `Composio MCP error: ${error.message} - ${error.response?.data || 'No details'}`
        );
      }
      throw error;
    }
  }
}

// ============================================================================
// SYNC ORCHESTRATOR
// ============================================================================

class ErrorSyncOrchestrator {
  private neonClient: NeonClient;
  private firebaseClient: FirebaseClient;
  private stats: SyncStats;

  constructor(neonClient: NeonClient, firebaseClient: FirebaseClient) {
    this.neonClient = neonClient;
    this.firebaseClient = firebaseClient;
    this.stats = {
      total_fetched: 0,
      successfully_synced: 0,
      failed: 0,
      errors: [],
    };
  }

  async fetchUnsyncedErrors(limit: number): Promise<NeonErrorRow[]> {
    console.log(`📥 Fetching up to ${limit} unsynced errors from Neon...`);

    const { rows } = await this.neonClient.query<NeonErrorRow>(
      `
      SELECT
        id, error_id, timestamp, agent_name, process_id, unique_id,
        severity, message, stack_trace, resolved, resolution_notes,
        last_touched, firebase_synced
      FROM shq_error_log
      WHERE firebase_synced IS FALSE OR firebase_synced IS NULL
      ORDER BY timestamp DESC
      LIMIT $1;
      `,
      [limit]
    );

    this.stats.total_fetched = rows.length;
    console.log(`✅ Fetched ${rows.length} unsynced error(s)\n`);

    return rows;
  }

  transformToFirebaseDoc(row: NeonErrorRow): FirebaseErrorDoc {
    // Map severity to color using Barton Doctrine color coding
    const color = SEVERITY_COLORS[row.severity] || DEFAULT_COLOR;

    return {
      error_id: row.error_id,
      timestamp: row.timestamp.toISOString(),
      agent_name: row.agent_name,
      process_id: row.process_id,
      unique_id: row.unique_id,
      severity: row.severity,
      message: row.message,
      stack_trace: row.stack_trace,
      resolved: row.resolved,
      resolution_notes: row.resolution_notes,
      last_touched: row.last_touched.toISOString(),
      color, // Hex color for dashboard visualization
      neon_id: row.id,
      synced_at: new Date().toISOString(),
    };
  }

  async syncSingleError(row: NeonErrorRow, index: number): Promise<boolean> {
    const errorIdShort = row.error_id.substring(0, 12);
    const color = SEVERITY_COLORS[row.severity] || DEFAULT_COLOR;
    console.log(
      `[${index + 1}/${this.stats.total_fetched}] Syncing ${errorIdShort}... (${row.severity} → ${color})`
    );

    try {
      // Transform to Firebase format
      const firebaseDoc = this.transformToFirebaseDoc(row);

      // Send to Firebase via Composio MCP
      await this.firebaseClient.writeDocument(
        'error_log',
        row.error_id,
        firebaseDoc,
        row.unique_id || `04.01.99.10.01000.${String(row.id).padStart(3, '0')}`,
        row.process_id || 'Sync Errors to Firebase'
      );

      // Mark as synced in Neon
      if (!DRY_RUN) {
        await this.neonClient.query(
          `UPDATE shq_error_log SET firebase_synced = TRUE WHERE id = $1;`,
          [row.id]
        );
      }

      console.log(`  ✅ Successfully synced ${errorIdShort}\n`);
      this.stats.successfully_synced++;
      return true;
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      console.error(`  ❌ Failed to sync ${errorIdShort}: ${reason}\n`);

      this.stats.failed++;
      this.stats.errors.push({
        error_id: row.error_id,
        reason,
      });

      return false;
    }
  }

  async syncAll(limit: number): Promise<SyncStats> {
    console.log('🚀 Starting Firebase Error Sync...\n');

    if (DRY_RUN) {
      console.log('⚠️  DRY RUN MODE - No data will be written\n');
    }

    try {
      // Fetch unsynced errors
      const unsyncedErrors = await this.fetchUnsyncedErrors(limit);

      if (unsyncedErrors.length === 0) {
        console.log('✨ No unsynced errors found. All up to date!\n');
        return this.stats;
      }

      // Sync each error
      console.log('📤 Syncing to Firebase via Composio MCP...\n');
      for (let i = 0; i < unsyncedErrors.length; i++) {
        await this.syncSingleError(unsyncedErrors[i], i);
      }

      // Print summary
      this.printSummary();

      return this.stats;
    } catch (error) {
      console.error('💥 Fatal error during sync:', error);
      throw error;
    }
  }

  printSummary(): void {
    console.log('═══════════════════════════════════════════════════════════');
    console.log('📊 SYNC SUMMARY');
    console.log('═══════════════════════════════════════════════════════════');
    console.log(`Total Fetched:        ${this.stats.total_fetched}`);
    console.log(`Successfully Synced:  ${this.stats.successfully_synced} ✅`);
    console.log(`Failed:               ${this.stats.failed} ❌`);
    console.log('═══════════════════════════════════════════════════════════\n');

    if (this.stats.errors.length > 0) {
      console.log('❌ Failed Error IDs:');
      this.stats.errors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err.error_id.substring(0, 12)}... - ${err.reason}`);
      });
      console.log('');
    }

    if (DRY_RUN) {
      console.log('⚠️  DRY RUN - No changes were persisted to Neon\n');
    }
  }
}

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================

async function main() {
  console.log('');
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  Barton Outreach - Firebase Error Sync                    ║');
  console.log('║  Syncs shq_error_log → Firebase error_log collection      ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('');

  // Validate environment
  if (!NEON_CONNECTION_STRING) {
    console.error('❌ ERROR: NEON_DATABASE_URL environment variable is not set');
    console.error('   Set it in your .env file or environment\n');
    process.exit(1);
  }

  // Initialize clients
  const neonClient = new NeonClient(NEON_CONNECTION_STRING);
  const firebaseClient = new FirebaseClient(COMPOSIO_MCP_URL, FIREBASE_PROJECT_ID);
  const orchestrator = new ErrorSyncOrchestrator(neonClient, firebaseClient);

  try {
    // Run sync
    const stats = await orchestrator.syncAll(LIMIT);

    // Exit with appropriate code
    if (stats.failed > 0) {
      console.log('⚠️  Sync completed with errors');
      process.exit(1);
    } else {
      console.log('✅ Sync completed successfully\n');
      process.exit(0);
    }
  } catch (error) {
    console.error('💥 Fatal error:', error);
    process.exit(1);
  } finally {
    await neonClient.close();
  }
}

// Run if executed directly
main().catch((error) => {
  console.error('💥 Unhandled error:', error);
  process.exit(1);
});
