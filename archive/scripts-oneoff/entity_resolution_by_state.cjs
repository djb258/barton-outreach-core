/**
 * Entity Resolution by State
 *
 * Matches Clay company records to DOL Form 5500 records using:
 * - Geographic narrowing (state + ZIP)
 * - Fuzzy name matching (trigram similarity)
 *
 * Usage:
 *   doppler run -- node scripts/entity_resolution_by_state.cjs PA VA MD
 *   doppler run -- node scripts/entity_resolution_by_state.cjs --all
 *
 * Output:
 *   - Console: Match statistics
 *   - File: exports/entity_resolution_candidates_[STATE]_[DATE].json
 */

const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

// All target states
const ALL_STATES = ['PA', 'VA', 'MD', 'OH', 'KY', 'NC', 'OK', 'WV', 'DE'];

// Parse command line arguments
const args = process.argv.slice(2);
let states = [];

if (args.includes('--all')) {
    states = ALL_STATES;
} else if (args.length > 0) {
    states = args.map(s => s.toUpperCase()).filter(s => ALL_STATES.includes(s));
    if (states.length === 0) {
        console.error('Error: No valid states provided.');
        console.error('Valid states:', ALL_STATES.join(', '));
        console.error('Usage: node scripts/entity_resolution_by_state.cjs PA VA MD');
        process.exit(1);
    }
} else {
    console.error('Usage: node scripts/entity_resolution_by_state.cjs [STATES...]');
    console.error('       node scripts/entity_resolution_by_state.cjs --all');
    console.error('Valid states:', ALL_STATES.join(', '));
    process.exit(1);
}

// Trigram similarity functions
function trigrams(str) {
    if (!str) return new Set();
    const s = str.toLowerCase().replace(/[^a-z0-9]/g, '');
    const t = new Set();
    for (let i = 0; i <= s.length - 3; i++) {
        t.add(s.substring(i, i + 3));
    }
    return t;
}

function similarity(s1, s2) {
    const t1 = trigrams(s1);
    const t2 = trigrams(s2);
    if (t1.size === 0 || t2.size === 0) return 0;
    let intersection = 0;
    t1.forEach(t => { if (t2.has(t)) intersection++; });
    return intersection / Math.max(t1.size, t2.size);
}

function normalizeZip(zip) {
    if (!zip) return null;
    const cleaned = zip.toString().replace(/[^0-9]/g, '');
    return cleaned.substring(0, 5) || null;
}

async function processState(client, state) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`Processing: ${state}`);
    console.log('='.repeat(50));

    // Extract unmatched Clay companies
    const clayQuery = `
        SELECT
            cm.company_unique_id,
            cm.company_name,
            cm.website_url,
            cm.address_state,
            cm.address_city,
            cm.address_zip
        FROM company.company_master cm
        WHERE cm.ein IS NULL
        AND cm.address_state = $1
        ORDER BY cm.address_city;
    `;
    const clayResult = await client.query(clayQuery, [state]);
    console.log(`Unmatched Clay: ${clayResult.rows.length}`);

    // Extract DOL mid-market
    const dolQuery = `
        WITH form_5500_dedup AS (
            SELECT DISTINCT ON (sponsor_dfe_ein)
                sponsor_dfe_ein::text as ein,
                sponsor_dfe_name as legal_name,
                spons_dfe_dba_name as dba_name,
                spons_dfe_mail_us_state as state,
                spons_dfe_mail_us_city as city,
                spons_dfe_mail_us_zip as zip,
                tot_active_partcp_cnt as participants
            FROM dol.form_5500
            WHERE spons_dfe_mail_us_state = $1
            AND tot_active_partcp_cnt BETWEEN 50 AND 5000
            ORDER BY sponsor_dfe_ein, ack_id DESC
        ),
        form_5500_sf_dedup AS (
            SELECT DISTINCT ON (sf_spons_ein)
                sf_spons_ein::text as ein,
                sf_sponsor_name as legal_name,
                NULL::text as dba_name,
                sf_spons_us_state as state,
                sf_spons_us_city as city,
                sf_spons_us_zip as zip,
                sf_tot_partcp_boy_cnt as participants
            FROM dol.form_5500_sf
            WHERE sf_spons_us_state = $1
            AND sf_tot_partcp_boy_cnt BETWEEN 50 AND 5000
            ORDER BY sf_spons_ein, ack_id DESC
        ),
        dol_combined AS (
            SELECT * FROM form_5500_dedup
            UNION ALL
            SELECT * FROM form_5500_sf_dedup
        )
        SELECT DISTINCT ON (ein)
            ein, legal_name, dba_name, state, city, zip, participants
        FROM dol_combined
        ORDER BY ein;
    `;
    const dolResult = await client.query(dolQuery, [state]);
    console.log(`DOL mid-market: ${dolResult.rows.length}`);

    // Geographic bucketing
    const buckets = {};
    clayResult.rows.forEach(clay => {
        const zip5 = normalizeZip(clay.address_zip);
        if (!zip5) return;
        const key = `${state}|${zip5}`;
        if (!buckets[key]) buckets[key] = { clay: [], dol: [] };
        buckets[key].clay.push(clay);
    });

    dolResult.rows.forEach(dol => {
        const zip5 = normalizeZip(dol.zip);
        if (!zip5) return;
        const key = `${state}|${zip5}`;
        if (!buckets[key]) buckets[key] = { clay: [], dol: [] };
        buckets[key].dol.push(dol);
    });

    // Count matchable buckets
    let matchableBuckets = 0;
    let totalPairs = 0;
    Object.entries(buckets).forEach(([key, bucket]) => {
        if (bucket.clay.length > 0 && bucket.dol.length > 0) {
            matchableBuckets++;
            totalPairs += bucket.clay.length * bucket.dol.length;
        }
    });
    console.log(`Matchable ZIP buckets: ${matchableBuckets}`);
    console.log(`Total pairs to evaluate: ${totalPairs}`);

    // Fuzzy name matching
    const candidates = [];
    Object.entries(buckets).forEach(([key, bucket]) => {
        if (bucket.clay.length === 0 || bucket.dol.length === 0) return;

        bucket.clay.forEach(clay => {
            bucket.dol.forEach(dol => {
                const legalScore = similarity(clay.company_name, dol.legal_name);
                let dbaScore = 0;
                if (dol.dba_name && dol.dba_name.trim()) {
                    dbaScore = similarity(clay.company_name, dol.dba_name);
                }
                const bestScore = Math.max(legalScore, dbaScore);
                const matchedOn = dbaScore > legalScore ? 'DBA' : 'LEGAL';

                let tier;
                if (bestScore >= 0.7) tier = 'HIGH';
                else if (bestScore >= 0.5) tier = 'MEDIUM';
                else tier = 'LOW';

                if (tier !== 'LOW') {
                    candidates.push({
                        company_unique_id: clay.company_unique_id,
                        company_name: clay.company_name,
                        website_url: clay.website_url,
                        clay_city: clay.address_city,
                        sponsor_dfe_ein: dol.ein,
                        sponsor_dfe_name: dol.legal_name,
                        spons_dfe_dba_name: dol.dba_name,
                        dol_city: dol.city,
                        state: state,
                        zip: key.split('|')[1],
                        match_score: parseFloat(bestScore.toFixed(3)),
                        match_tier: tier,
                        matched_on: matchedOn
                    });
                }
            });
        });
    });

    // Sort by score
    candidates.sort((a, b) => b.match_score - a.match_score);

    const highTier = candidates.filter(c => c.match_tier === 'HIGH');
    const mediumTier = candidates.filter(c => c.match_tier === 'MEDIUM');

    console.log(`\nCandidates found: ${candidates.length}`);
    console.log(`  HIGH (0.7+): ${highTier.length}`);
    console.log(`  MEDIUM (0.5-0.69): ${mediumTier.length}`);

    if (highTier.length > 0) {
        console.log('\nTop HIGH matches:');
        highTier.slice(0, 5).forEach(c => {
            console.log(`  [${c.match_score.toFixed(3)}] "${c.company_name}" ↔ "${c.sponsor_dfe_name}"`);
        });
    }

    return {
        state,
        stats: {
            unmatched_clay: clayResult.rows.length,
            dol_midmarket: dolResult.rows.length,
            matchable_zips: matchableBuckets,
            total_pairs: totalPairs,
            candidates_high: highTier.length,
            candidates_medium: mediumTier.length,
            candidates_total: candidates.length
        },
        candidates
    };
}

async function run() {
    const client = new Client({
        connectionString: process.env.DATABASE_URL,
        ssl: { rejectUnauthorized: false }
    });
    await client.connect();

    console.log('='.repeat(60));
    console.log('ENTITY RESOLUTION BY STATE');
    console.log(`States: ${states.join(', ')}`);
    console.log('='.repeat(60));

    const results = [];
    const allCandidates = [];

    for (const state of states) {
        const result = await processState(client, state);
        results.push(result);
        allCandidates.push(...result.candidates);
    }

    // Summary
    console.log('\n' + '='.repeat(60));
    console.log('SUMMARY');
    console.log('='.repeat(60));
    console.log('\nState | Unmatched | DOL | ZIPs | Pairs | HIGH | MEDIUM | Total');
    console.log('-'.repeat(70));

    let totalUnmatched = 0, totalDol = 0, totalCandidates = 0;
    results.forEach(r => {
        const s = r.stats;
        console.log(`${r.state}    | ${s.unmatched_clay.toString().padStart(9)} | ${s.dol_midmarket.toString().padStart(3)} | ${s.matchable_zips.toString().padStart(4)} | ${s.total_pairs.toString().padStart(5)} | ${s.candidates_high.toString().padStart(4)} | ${s.candidates_medium.toString().padStart(6)} | ${s.candidates_total.toString().padStart(5)}`);
        totalUnmatched += s.unmatched_clay;
        totalDol += s.dol_midmarket;
        totalCandidates += s.candidates_total;
    });
    console.log('-'.repeat(70));
    console.log(`TOTAL: ${totalUnmatched} unmatched, ${totalDol} DOL, ${totalCandidates} candidates`);

    // Export candidates to JSON
    const date = new Date().toISOString().split('T')[0];
    const stateStr = states.join('_');
    const exportDir = path.join(process.cwd(), 'exports');

    if (!fs.existsSync(exportDir)) {
        fs.mkdirSync(exportDir, { recursive: true });
    }

    const exportFile = path.join(exportDir, `entity_resolution_candidates_${stateStr}_${date}.json`);
    fs.writeFileSync(exportFile, JSON.stringify({
        generated: new Date().toISOString(),
        states: states,
        total_candidates: allCandidates.length,
        candidates: allCandidates
    }, null, 2));

    console.log(`\nExported to: ${exportFile}`);
    console.log('Next step: Run URL verification on HIGH + MEDIUM candidates');

    await client.end();
}

run().catch(e => { console.error(e); process.exit(1); });
