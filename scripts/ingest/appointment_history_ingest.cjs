#!/usr/bin/env node
/**
 * Appointment History Ingest Script
 *
 * Lane A: Appointment Reactivation
 * Target: sales.appointment_history
 *
 * Usage:
 *   doppler run -- node scripts/ingest/appointment_history_ingest.cjs <excel_file.xlsx>
 *   doppler run -- node scripts/ingest/appointment_history_ingest.cjs <excel_file.xlsx> --source=crm
 *   doppler run -- node scripts/ingest/appointment_history_ingest.cjs <excel_file.xlsx> --dry-run
 */

const { Pool } = require('pg');
const xlsx = require('xlsx');
const path = require('path');

// Valid enum values
const VALID_MEETING_TYPES = ['discovery', 'systems', 'numbers', 'other'];
const VALID_MEETING_OUTCOMES = ['progressed', 'stalled', 'ghosted', 'lost'];
const VALID_SOURCES = ['calendar', 'crm', 'manual'];

// Parse command line arguments
const args = process.argv.slice(2);
const filePath = args.find(arg => !arg.startsWith('--'));
const sourceOverride = args.find(arg => arg.startsWith('--source='))?.split('=')[1];
const dryRun = args.includes('--dry-run');

if (!filePath) {
    console.error('Usage: node appointment_history_ingest.cjs <excel_file.xlsx> [--source=crm] [--dry-run]');
    process.exit(1);
}

// Database connection
const pool = new Pool({
    host: process.env.NEON_HOST,
    database: process.env.NEON_DATABASE,
    user: process.env.NEON_USER,
    password: process.env.NEON_PASSWORD,
    port: 5432,
    ssl: { rejectUnauthorized: false }
});

/**
 * Generate deterministic appointment_uid
 */
function generateAppointmentUid(companyId, peopleId, meetingDate) {
    const company = companyId || 'UNKNOWN';
    const people = peopleId || 'UNKNOWN';
    const date = meetingDate instanceof Date
        ? meetingDate.toISOString().split('T')[0]
        : meetingDate;
    return `${company}|${people}|${date}`;
}

/**
 * Validate UUID format
 */
function isValidUuid(str) {
    if (!str) return true; // Nullable
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
}

/**
 * Parse date from various formats
 */
function parseDate(value) {
    if (!value) return null;
    if (value instanceof Date) return value;

    // Excel serial date number
    if (typeof value === 'number') {
        const date = new Date((value - 25569) * 86400 * 1000);
        return date;
    }

    // String date
    const parsed = new Date(value);
    if (isNaN(parsed.getTime())) return null;
    return parsed;
}

/**
 * Validate and transform row
 */
function validateRow(row, rowIndex) {
    const errors = [];

    // Required fields
    if (!row.meeting_date) {
        errors.push(`Row ${rowIndex}: meeting_date is required`);
    }

    if (!row.meeting_type) {
        errors.push(`Row ${rowIndex}: meeting_type is required`);
    } else if (!VALID_MEETING_TYPES.includes(row.meeting_type.toLowerCase())) {
        errors.push(`Row ${rowIndex}: invalid meeting_type '${row.meeting_type}'. Must be one of: ${VALID_MEETING_TYPES.join(', ')}`);
    }

    if (!row.meeting_outcome) {
        errors.push(`Row ${rowIndex}: meeting_outcome is required`);
    } else if (!VALID_MEETING_OUTCOMES.includes(row.meeting_outcome.toLowerCase())) {
        errors.push(`Row ${rowIndex}: invalid meeting_outcome '${row.meeting_outcome}'. Must be one of: ${VALID_MEETING_OUTCOMES.join(', ')}`);
    }

    // Conditional: stalled_reason required if outcome is stalled
    if (row.meeting_outcome?.toLowerCase() === 'stalled' && !row.stalled_reason) {
        errors.push(`Row ${rowIndex}: stalled_reason is required when meeting_outcome is 'stalled'`);
    }

    // UUID validation
    if (row.company_id && !isValidUuid(row.company_id)) {
        errors.push(`Row ${rowIndex}: invalid company_id UUID format`);
    }
    if (row.people_id && !isValidUuid(row.people_id)) {
        errors.push(`Row ${rowIndex}: invalid people_id UUID format`);
    }
    if (row.outreach_id && !isValidUuid(row.outreach_id)) {
        errors.push(`Row ${rowIndex}: invalid outreach_id UUID format`);
    }

    // Source validation
    const source = sourceOverride || row.source || 'manual';
    if (!VALID_SOURCES.includes(source.toLowerCase())) {
        errors.push(`Row ${rowIndex}: invalid source '${source}'. Must be one of: ${VALID_SOURCES.join(', ')}`);
    }

    // Date validation
    const meetingDate = parseDate(row.meeting_date);
    if (row.meeting_date && !meetingDate) {
        errors.push(`Row ${rowIndex}: invalid meeting_date format`);
    }

    return {
        errors,
        transformed: errors.length === 0 ? {
            appointment_uid: generateAppointmentUid(row.company_id, row.people_id, meetingDate),
            company_id: row.company_id || null,
            people_id: row.people_id || null,
            outreach_id: row.outreach_id || null,
            meeting_date: meetingDate,
            meeting_type: row.meeting_type.toLowerCase(),
            meeting_outcome: row.meeting_outcome.toLowerCase(),
            stalled_reason: row.stalled_reason || null,
            source: (sourceOverride || row.source || 'manual').toLowerCase(),
            source_record_id: row.source_record_id || null
        } : null
    };
}

/**
 * Main ingest function
 */
async function ingest() {
    console.log(`\n=== Appointment History Ingest ===`);
    console.log(`File: ${filePath}`);
    console.log(`Source Override: ${sourceOverride || 'none'}`);
    console.log(`Dry Run: ${dryRun}`);
    console.log();

    // Read Excel file
    const absolutePath = path.resolve(filePath);
    const workbook = xlsx.readFile(absolutePath);
    const sheetName = workbook.SheetNames[0];
    const sheet = workbook.Sheets[sheetName];
    const rows = xlsx.utils.sheet_to_json(sheet);

    console.log(`Found ${rows.length} rows in sheet '${sheetName}'`);

    // Validate all rows
    const validRows = [];
    const allErrors = [];

    for (let i = 0; i < rows.length; i++) {
        const { errors, transformed } = validateRow(rows[i], i + 2); // +2 for 1-indexed + header row
        if (errors.length > 0) {
            allErrors.push(...errors);
        } else {
            validRows.push(transformed);
        }
    }

    // Report validation results
    console.log(`\nValidation Results:`);
    console.log(`  Valid rows: ${validRows.length}`);
    console.log(`  Invalid rows: ${rows.length - validRows.length}`);

    if (allErrors.length > 0) {
        console.log(`\nValidation Errors:`);
        allErrors.forEach(err => console.log(`  - ${err}`));
    }

    if (validRows.length === 0) {
        console.log('\nNo valid rows to insert. Exiting.');
        process.exit(1);
    }

    if (dryRun) {
        console.log('\n=== DRY RUN - No changes made ===');
        console.log('\nSample transformed rows:');
        validRows.slice(0, 3).forEach((row, i) => {
            console.log(`\nRow ${i + 1}:`);
            console.log(JSON.stringify(row, null, 2));
        });
        process.exit(0);
    }

    // Insert into database
    const client = await pool.connect();
    let inserted = 0;
    let duplicates = 0;
    let errors = 0;

    try {
        console.log('\nInserting rows...');

        for (const row of validRows) {
            try {
                await client.query(`
                    INSERT INTO sales.appointment_history (
                        appointment_uid, company_id, people_id, outreach_id,
                        meeting_date, meeting_type, meeting_outcome, stalled_reason,
                        source, source_record_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                `, [
                    row.appointment_uid,
                    row.company_id,
                    row.people_id,
                    row.outreach_id,
                    row.meeting_date,
                    row.meeting_type,
                    row.meeting_outcome,
                    row.stalled_reason,
                    row.source,
                    row.source_record_id
                ]);
                inserted++;
            } catch (err) {
                if (err.code === '23505') { // Unique violation
                    duplicates++;
                } else {
                    errors++;
                    console.error(`  Error inserting ${row.appointment_uid}: ${err.message}`);
                }
            }
        }

        console.log('\n=== Ingest Complete ===');
        console.log(`  Inserted: ${inserted}`);
        console.log(`  Duplicates (skipped): ${duplicates}`);
        console.log(`  Errors: ${errors}`);

    } finally {
        client.release();
        await pool.end();
    }
}

// Run
ingest().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
