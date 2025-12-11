#!/usr/bin/env node

/**
 * Talent Engine CLI Runner
 * ========================
 * Python calls this file to run TypeScript agents.
 *
 * Usage:
 *   node dist/scripts/run_talent_engine.js --mode pattern --input "<json>"
 *   node dist/scripts/run_talent_engine.js --mode generate_email --input "<json>"
 *   node dist/scripts/run_talent_engine.js --mode verify --input "<json>"
 *
 * Build first: npm run build (from talent_engine directory)
 */

import { NodeDispatcher } from "../src/dispatcher/NodeDispatcher.js";

// ----------------------------
// Types
// ----------------------------
interface InputRow {
  company_id?: string;
  person_id?: string;
  [key: string]: any;
}

interface ErrorRecord {
  row_id: string;
  error: string;
}

interface RunResult {
  success: boolean;
  results: Record<string, any>[];
  errors?: ErrorRecord[];
  processed: number;
  failed: number;
}

// ----------------------------
// Parse CLI args
// ----------------------------
const args = process.argv.slice(2);
let mode: string | null = null;
let inputData: InputRow[] | null = null;

for (let i = 0; i < args.length; i++) {
  const arg = args[i];

  // Handle --mode=value or --mode value
  if (arg === "--mode" && args[i + 1]) {
    mode = args[++i];
  } else if (arg.startsWith("--mode=")) {
    mode = arg.replace("--mode=", "");
  }

  // Handle --input=value or --input value
  if (arg === "--input" && args[i + 1]) {
    try {
      const parsed = JSON.parse(args[++i]);
      inputData = Array.isArray(parsed) ? parsed : [parsed];
    } catch (e: any) {
      console.error(JSON.stringify({ success: false, errors: [`Failed to parse input JSON: ${e.message}`] }));
      process.exit(1);
    }
  } else if (arg.startsWith("--input=")) {
    try {
      const parsed = JSON.parse(arg.replace("--input=", ""));
      inputData = Array.isArray(parsed) ? parsed : [parsed];
    } catch (e: any) {
      console.error(JSON.stringify({ success: false, errors: [`Failed to parse input JSON: ${e.message}`] }));
      process.exit(1);
    }
  }
}

if (!mode) {
  console.error(JSON.stringify({ success: false, errors: ["--mode is required"] }));
  process.exit(1);
}

if (!inputData) {
  console.error(JSON.stringify({ success: false, errors: ["--input=<json> is required"] }));
  process.exit(1);
}

// ----------------------------
// Run Dispatcher
// ----------------------------
const dispatcher = new NodeDispatcher({
  enforce_dependencies: true,
  mock_mode: true, // Use mock mode for development/testing
  verbose: false,
});

async function run(): Promise<void> {
  const results: Record<string, any>[] = [];
  const errors: ErrorRecord[] = [];

  for (const row of inputData!) {
    try {
      // dispatcher.run() automatically uses dependency graph, throttling, failure routing
      const enriched = await dispatcher.run(row, mode!);
      results.push(enriched);
    } catch (err: any) {
      errors.push({
        row_id: row.company_id || row.person_id || "unknown",
        error: err.message,
      });
      // Include partial result with error status
      results.push({
        ...row,
        status: "error",
        error: err.message,
      });
    }
  }

  // Python reads STDOUT as JSON
  const output: RunResult = {
    success: errors.length === 0,
    results,
    errors: errors.length > 0 ? errors : undefined,
    processed: results.length,
    failed: errors.length,
  };

  console.log(JSON.stringify(output));
}

run().catch((err: Error) => {
  console.error(JSON.stringify({
    success: false,
    errors: [`Talent Engine Error: ${err.message}`],
    stack: err.stack
  }));
  process.exit(1);
});
