#!/usr/bin/env node
/**
 * Fractional CFO Partner Ingest Script
 *
 * Lane B: Fractional CFO Partner Outreach
 * Targets:
 *   - partners.fractional_cfo_master (updateable master)
 *   - partners.partner_appointments (write-once facts)
 *
 * Usage:
 *   doppler run -- node scripts/ingest/fractional_cfo_ingest.cjs partners <excel_file.xlsx>
 *   doppler run -- node scripts/ingest/fractional_cfo_ingest.cjs appointments <excel_file.xlsx>
 *   doppler run -- node scripts/ingest/fractional_cfo_ingest.cjs partners <excel_file.xlsx> --dry-run
 */

const { Pool } = require('pg');
const xlsx = require('xlsx');
const path = require('path');
const crypto = require('crypto');

// Valid enum values
const VALID_PARTNER_STATUSES = ['prospect', 'contacted', 'engaged', 'partner'];
const VALID_MEETING_TYPES = ['intro', 'followup'];
const VALID_MEETING_OUTCOMES = ['warm', 'neutral', 'cold'];

// Parse command line arguments
const args = process.argv.slice(2);
const mode = args[0]; // 'partners' or 'appointments'
const filePath = args[1];
const dryRun = args.includes('--dry-run');

if (!mode || !filePath || !['partners', 'appointments'].includes(mode)) {
    console.error('Usage: node fractional_cfo_ingest.cjs <partners|appointments> <excel_file.xlsx> [--dry-run]');
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
 * Validate UUID format
 */
function isValidUuid(str) {
    if (!str) return false;
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
}

/**
 * Validate LinkedIn URL
 */
function isValidLinkedInUrl(url) {
    if (!url) return true; // Nullable
    return /^https?:\/\/(www\.)?linkedin\.com\//.test(url);
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    if (!email) return true; // Nullable
    return /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email);
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
 * Validate partner row
 */
function validatePartnerRow(row, rowIndex) {
    const errors = [];

    // Required fields
    if (!row.firm_name || !row.firm_name.trim()) {
        errors.push(`Row ${rowIndex}: firm_name is required`);
    }

    if (!row.primary_contact_name || !row.primary_contact_name.trim()) {
        errors.push(`Row ${rowIndex}: primary_contact_name is required`);
    }

    if (!row.source || !row.source.trim()) {
        errors.push(`Row ${rowIndex}: source is required`);
    }

    // LinkedIn URL validation
    if (row.linkedin_url && !isValidLinkedInUrl(row.linkedin_url)) {
        errors.push(`Row ${rowIndex}: invalid linkedin_url format. Must start with https://linkedin.com/`);
    }

    // Email validation
    if (row.email && !isValidEmail(row.email)) {
        errors.push(`Row ${rowIndex}: invalid email format`);
    }

    // Status validation
    if (row.status && !VALID_PARTNER_STATUSES.includes(row.status.toLowerCase())) {
        errors.push(`Row ${rowIndex}: invalid status '${row.status}'. Must be one of: ${VALID_PARTNER_STATUSES.join(', ')}`);
    }

    return {
        errors,
        transformed: errors.length === 0 ? {
            firm_name: row.firm_name.trim(),
            primary_contact_name: row.primary_contact_name.trim(),
            linkedin_url: row.linkedin_url?.trim() || null,
            email: row.email?.trim()?.toLowerCase() || null,
            geography: row.geography?.trim() || null,
            niche_focus: row.niche_focus?.trim() || null,
            source: row.source.trim(),
            source_detail: row.source_detail?.trim() || null,
            status: (row.status || 'prospect').toLowerCase()
        } : null
    };
}

/**
 * Validate appointment row
 */
function validateAppointmentRow(row, rowIndex) {
    const errors = [];

    // Required fields
    if (!row.fractional_cfo_id) {
        errors.push(`Row ${rowIndex}: fractional_cfo_id is required`);
    } else if (!isValidUuid(row.fractional_cfo_id)) {
        errors.push(`Row ${rowIndex}: invalid fractional_cfo_id UUID format`);
    }

    if (!row.meeting_date) {
        errors.push(`Row ${rowIndex}: meeting_date is required`);
    }

    if (!row.meeting_type) {
        errors.push(`Row ${rowIndex}: meeting_type is required`);
    } else if (!VALID_MEETING_TYPES.includes(row.meeting_type.toLowerCase())) {
        errors.push(`Row ${rowIndex}: invalid meeting_type '${row.meeting_type}'. Must be one of: ${VALID_MEETING_TYPES.join(', ')}`);
    }

    if (!row.outcome) {
        errors.push(`Row ${rowIndex}: outcome is required`);
    } else if (!VALID_MEETING_OUTCOMES.includes(row.outcome.toLowerCase())) {
        errors.push(`Row ${rowIndex}: invalid outcome '${row.outcome}'. Must be one of: ${VALID_MEETING_OUTCOMES.join(', ')}`);
    }

    // Date validation
    const meetingDate = parseDate(row.meeting_date);
    if (row.meeting_date && !meetingDate) {
        errors.push(`Row ${rowIndex}: invalid meeting_date format`);
    }

    // Generate UID
    const dateStr = meetingDate ? meetingDate.toISOString().split('T')[0] : '';
    const seq = row.sequence || 1;
    const uid = `${row.fractional_cfo_id}|${dateStr}|${seq}`;

    return {
        errors,
        transformed: errors.length === 0 ? {
            partner_appointment_uid: uid,
            fractional_cfo_id: row.fractional_cfo_id,
            meeting_date: meetingDate,
            meeting_type: row.meeting_type.toLowerCase(),
            outcome: row.outcome.toLowerCase(),
            notes: row.notes?.trim() || null
        } : null
    };
}

/**
 * Ingest partners
 */
async function ingestPartners(rows) {
    console.log(`Found ${rows.length} rows`);

    // Validate all rows
    const validRows = [];
    const allErrors = [];

    for (let i = 0; i < rows.length; i++) {
        const { errors, transformed } = validatePartnerRow(rows[i], i + 2);
        if (errors.length > 0) {
            allErrors.push(...errors);
        } else {
            validRows.push(transformed);
        }
    }

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
        return;
    }

    // Insert into database
    const client = await pool.connect();
    let inserted = 0;
    let errors = 0;

    try {
        console.log('\nInserting rows...');

        for (const row of validRows) {
            try {
                const result = await client.query(`
                    INSERT INTO partners.fractional_cfo_master (
                        firm_name, primary_contact_name, linkedin_url, email,
                        geography, niche_focus, source, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING fractional_cfo_id
                `, [
                    row.firm_name,
                    row.primary_contact_name,
                    row.linkedin_url,
                    row.email,
                    row.geography,
                    row.niche_focus,
                    row.source,
                    row.status
                ]);
                inserted++;
                console.log(`  Inserted: ${row.firm_name} (${result.rows[0].fractional_cfo_id})`);
            } catch (err) {
                errors++;
                console.error(`  Error inserting ${row.firm_name}: ${err.message}`);
            }
        }

        console.log('\n=== Ingest Complete ===');
        console.log(`  Inserted: ${inserted}`);
        console.log(`  Errors: ${errors}`);

    } finally {
        client.release();
    }
}

/**
 * Ingest appointments
 */
async function ingestAppointments(rows) {
    console.log(`Found ${rows.length} rows`);

    // Validate all rows
    const validRows = [];
    const allErrors = [];

    for (let i = 0; i < rows.length; i++) {
        const { errors, transformed } = validateAppointmentRow(rows[i], i + 2);
        if (errors.length > 0) {
            allErrors.push(...errors);
        } else {
            validRows.push(transformed);
        }
    }

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
        return;
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
                    INSERT INTO partners.partner_appointments (
                        partner_appointment_uid, fractional_cfo_id,
                        meeting_date, meeting_type, outcome, notes
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                `, [
                    row.partner_appointment_uid,
                    row.fractional_cfo_id,
                    row.meeting_date,
                    row.meeting_type,
                    row.outcome,
                    row.notes
                ]);
                inserted++;
            } catch (err) {
                if (err.code === '23505') { // Unique violation
                    duplicates++;
                } else if (err.code === '23503') { // FK violation
                    errors++;
                    console.error(`  Error: fractional_cfo_id ${row.fractional_cfo_id} not found`);
                } else {
                    errors++;
                    console.error(`  Error inserting ${row.partner_appointment_uid}: ${err.message}`);
                }
            }
        }

        console.log('\n=== Ingest Complete ===');
        console.log(`  Inserted: ${inserted}`);
        console.log(`  Duplicates (skipped): ${duplicates}`);
        console.log(`  Errors: ${errors}`);

    } finally {
        client.release();
    }
}

/**
 * Main entry point
 */
async function main() {
    console.log(`\n=== Fractional CFO ${mode === 'partners' ? 'Partner' : 'Appointment'} Ingest ===`);
    console.log(`File: ${filePath}`);
    console.log(`Mode: ${mode}`);
    console.log(`Dry Run: ${dryRun}`);
    console.log();

    // Read Excel file
    const absolutePath = path.resolve(filePath);
    const workbook = xlsx.readFile(absolutePath);
    const sheetName = workbook.SheetNames[0];
    const sheet = workbook.Sheets[sheetName];
    const rows = xlsx.utils.sheet_to_json(sheet);

    console.log(`Sheet: ${sheetName}`);

    if (mode === 'partners') {
        await ingestPartners(rows);
    } else {
        await ingestAppointments(rows);
    }

    await pool.end();
}

// Run
main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
