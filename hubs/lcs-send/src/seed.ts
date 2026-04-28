// ═══════════════════════════════════════════════════════════════
// LCS Hub — SEED Functions
// ═══════════════════════════════════════════════════════════════
// Pulls data from Neon vault (via Hyperdrive) into D1 workspace.
// SEED ONLY — these functions run during data load, NOT during
// pipeline operations. The pipeline reads from D1 exclusively.
//
// Neon is the vault. D1 is the workspace. SEED → WORK → PUSH.
// ═══════════════════════════════════════════════════════════════

import type { Env } from './types';

// Use pg client via Hyperdrive
import { Client } from 'pg';

function getNeonClient(env: Env): Client {
  return new Client({ connectionString: env.HD_NEON.connectionString });
}

// ── Discover DOL Schema ─────────────────────────────────────

export async function discoverDolSchema(env: Env): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  try {
    // Get all columns from form_5500
    const f5500Cols = await pg.query(`
      SELECT column_name, data_type FROM information_schema.columns
      WHERE table_schema = 'dol' AND table_name = 'form_5500'
      ORDER BY ordinal_position
    `);

    // Get all columns from schedule_a_part1
    const schACols = await pg.query(`
      SELECT column_name, data_type FROM information_schema.columns
      WHERE table_schema = 'dol' AND table_name = 'schedule_a_part1'
      ORDER BY ordinal_position
    `);

    // Get all columns from schedule_c_part1_item2
    const schCCols = await pg.query(`
      SELECT column_name, data_type FROM information_schema.columns
      WHERE table_schema = 'dol' AND table_name = 'schedule_c_part1_item2'
      ORDER BY ordinal_position
    `);

    // Sample row — just get one to see actual data
    const sample = await pg.query(`SELECT * FROM dol.form_5500 LIMIT 1`);

    return {
      form_5500_columns: f5500Cols.rows,
      schedule_a_columns: schACols.rows,
      schedule_c_columns: schCCols.rows,
      sample_keys: sample.rows.length > 0 ? Object.keys(sample.rows[0]) : [],
      sample_row: sample.rows[0] ?? null,
    };
  } finally {
    await pg.end();
  }
}

// ── Full DOL SEED for a single EIN ──────────────────────────

// ── Full DOL dump — ALL tables, ALL data, ALL schedules for one EIN ──

export async function fullDolDump(env: Env, ein: string): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  try {
    // Get all DOL tables
    const tables = await pg.query(`
      SELECT table_name FROM information_schema.tables
      WHERE table_schema = 'dol' AND table_type = 'BASE TABLE'
      ORDER BY table_name
    `);

    const results: Record<string, any[]> = {};
    let totalRows = 0;

    for (const t of tables.rows) {
      const tbl = t.table_name;

      // Check if table has sponsor_dfe_ein directly
      const hasDirect = await pg.query(`
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'dol' AND table_name = $1
        AND column_name = 'sponsor_dfe_ein'
      `, [tbl]);

      // Check if table has ack_id (join via form_5500)
      const hasAckId = await pg.query(`
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'dol' AND table_name = $1
        AND column_name = 'ack_id'
      `, [tbl]);

      let rows: any[] = [];
      try {
        if (hasDirect.rows.length > 0) {
          const r = await pg.query(`SELECT * FROM dol."${tbl}" WHERE sponsor_dfe_ein = $1`, [ein]);
          rows = r.rows;
        } else if (hasAckId.rows.length > 0 && tbl !== 'form_5500') {
          const r = await pg.query(`
            SELECT t.* FROM dol."${tbl}" t
            JOIN dol.form_5500 f ON t.ack_id = f.ack_id
            WHERE f.sponsor_dfe_ein = $1
          `, [ein]);
          rows = r.rows;
        }
      } catch (e) {
        // Skip tables that error (different schema, missing columns, etc.)
      }

      if (rows.length > 0) {
        results[tbl] = rows;
        totalRows += rows.length;
      }
    }

    return { ein, tables_with_data: Object.keys(results).length, total_rows: totalRows, data: results };
  } finally {
    await pg.end();
  }
}

// ── Full Company Intelligence Dump — ALL sub-hubs, ALL data ──

export async function fullCompanyDump(env: Env, companyId: string): Promise<any> {
  const results: Record<string, any> = {};

  // 1. Company Identity from spine
  const identity = await env.D1.prepare(
    'SELECT * FROM cl_company_identity WHERE company_unique_id = ?'
  ).bind(companyId).first();
  results.identity = identity;

  const outreachId = (identity as any)?.outreach_id;
  const ein = (identity as any)?.sponsor_dfe_ein || null;

  // 2. Company Target from outreach D1
  if (outreachId) {
    const ct = await env.D1_OUTREACH.prepare(
      'SELECT * FROM outreach_company_target WHERE outreach_id = ?'
    ).bind(outreachId).first();
    results.company_target = ct;
  }

  // 3. ALL People slots + contact details
  if (outreachId) {
    const slots = await env.D1_OUTREACH.prepare(
      'SELECT * FROM people_company_slot WHERE outreach_id = ?'
    ).bind(outreachId).all();
    results.people_slots = slots.results;

    // Get full contact detail for each filled slot
    const contacts = [];
    for (const slot of (slots.results || [])) {
      const personId = (slot as any).person_unique_id;
      if (personId) {
        const person = await env.D1_OUTREACH.prepare(
          'SELECT * FROM people_people_master WHERE unique_id = ?'
        ).bind(personId).first();
        contacts.push({ slot: (slot as any).slot_type, person });
      }
    }
    results.people_contacts = contacts;
  }

  // 4. DOL summary from outreach D1
  if (outreachId) {
    const dol = await env.D1_OUTREACH.prepare(
      'SELECT * FROM outreach_dol WHERE outreach_id = ?'
    ).bind(outreachId).all();
    results.dol_outreach = dol.results;
  }

  // 5. Blog data from outreach D1
  if (outreachId) {
    try {
      const blog = await env.D1_OUTREACH.prepare(
        'SELECT * FROM outreach_blog WHERE outreach_id = ?'
      ).bind(outreachId).all();
      results.blog = blog.results;
    } catch { results.blog = []; }
  }

  // 6. Outreach people (delivery contacts)
  if (outreachId) {
    try {
      const outPeople = await env.D1_OUTREACH.prepare(
        'SELECT * FROM outreach_people WHERE outreach_id = ?'
      ).bind(outreachId).all();
      results.outreach_people = outPeople.results;
    } catch { results.outreach_people = []; }
  }

  // 7. Full DOL detail from D1 (seeded from Neon vault)
  const dolEin = ein || (results.dol_outreach as any)?.[0]?.ein;
  if (dolEin) {
    const filings = await env.D1_OUTREACH.prepare(
      'SELECT * FROM dol_form_5500 WHERE sponsor_dfe_ein = ?'
    ).bind(dolEin).all();
    results.dol_filings = filings.results;

    const schA = await env.D1_OUTREACH.prepare(
      'SELECT * FROM dol_schedule_a WHERE sponsor_dfe_ein = ?'
    ).bind(dolEin).all();
    results.dol_schedule_a = schA.results;

    const schC = await env.D1_OUTREACH.prepare(
      'SELECT * FROM dol_schedule_c WHERE sponsor_dfe_ein = ?'
    ).bind(dolEin).all();
    results.dol_schedule_c = schC.results;

    const schOther = await env.D1_OUTREACH.prepare(
      'SELECT * FROM dol_schedule_other WHERE sponsor_dfe_ein = ?'
    ).bind(dolEin).all();
    results.dol_schedule_other = schOther.results;
  }

  // 8. LCS activity from spine (signals, CIDs, SIDs, MIDs, events, errors)
  const signals = await env.D1.prepare(
    'SELECT * FROM lcs_signal_queue WHERE sovereign_company_id = ?'
  ).bind(companyId).all();
  results.lcs_signals = signals.results;

  const cids = await env.D1.prepare(
    'SELECT * FROM lcs_cid WHERE sovereign_company_id = ?'
  ).bind(companyId).all();
  results.lcs_cids = cids.results;

  const events = await env.D1.prepare(
    'SELECT * FROM lcs_event WHERE sovereign_company_id = ?'
  ).bind(companyId).all();
  results.lcs_events = events.results;

  const errors = await env.D1.prepare(
    'SELECT * FROM lcs_err0 WHERE sovereign_company_id = ?'
  ).bind(companyId).all();
  results.lcs_errors = errors.results;

  return {
    company_unique_id: companyId,
    outreach_id: outreachId,
    ein: dolEin,
    sub_hubs: results,
  };
}

// ── Batch SEED: Pull from Neon → Write to D1 for one EIN ────

export async function seedDolToD1(env: Env, ein: string, outreachId: string | null): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  let filingCount = 0;
  let schACount = 0;
  let schCCount = 0;
  let otherCount = 0;

  try {
    // 1. Form 5500 — all filings
    const filings = await pg.query(`SELECT * FROM dol.form_5500 WHERE sponsor_dfe_ein = $1`, [ein]);

    for (const f of filings.rows) {
      await env.D1_OUTREACH.prepare(`
        INSERT OR REPLACE INTO dol_form_5500 (
          ack_id, outreach_id, sponsor_dfe_ein, sponsor_dfe_name, plan_name, plan_number,
          plan_eff_date, form_year, form_tax_prd,
          spons_dfe_mail_us_city, spons_dfe_mail_us_state, spons_dfe_mail_us_zip,
          tot_active_partcp_cnt, tot_partcp_boy_cnt, admin_name, admin_ein,
          type_plan_entity_cd, sch_a_attached_ind, num_sch_a_attached_cnt,
          filing_status, date_received, all_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        f.ack_id, outreachId, f.sponsor_dfe_ein, f.sponsor_dfe_name, f.plan_name, f.plan_number,
        f.plan_eff_date, f.form_year, f.form_tax_prd,
        f.spons_dfe_mail_us_city, f.spons_dfe_mail_us_state, f.spons_dfe_mail_us_zip,
        f.tot_active_partcp_cnt, f.tot_partcp_boy_cnt, f.admin_name, f.admin_ein,
        f.type_plan_entity_cd, f.sch_a_attached_ind, f.num_sch_a_attached_cnt,
        f.filing_status, f.date_received, JSON.stringify(f),
      ).run();
      filingCount++;
    }

    // 2. Schedule A Part 1 — broker/insurance
    const schA = await pg.query(`
      SELECT sa.*, f.sponsor_dfe_ein FROM dol.schedule_a_part1 sa
      JOIN dol.form_5500 f ON sa.ack_id = f.ack_id
      WHERE f.sponsor_dfe_ein = $1
    `, [ein]);

    for (const a of schA.rows) {
      await env.D1_OUTREACH.prepare(`
        INSERT INTO dol_schedule_a (
          ack_id, outreach_id, sponsor_dfe_ein, form_year, row_order,
          ins_broker_name, ins_broker_us_city, ins_broker_us_state, ins_broker_us_zip,
          ins_broker_comm_pd_amt, ins_broker_fees_pd_amt, ins_broker_code, all_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        a.ack_id, outreachId, a.sponsor_dfe_ein, a.form_year, a.row_order,
        a.ins_broker_name, a.ins_broker_us_city, a.ins_broker_us_state, a.ins_broker_us_zip,
        a.ins_broker_comm_pd_amt, a.ins_broker_fees_pd_amt, a.ins_broker_code,
        JSON.stringify(a),
      ).run();
      schACount++;
    }

    // 3. Schedule C Part 1 Item 2 — service providers
    const schC = await pg.query(`
      SELECT sc.*, f.sponsor_dfe_ein FROM dol.schedule_c_part1_item2 sc
      JOIN dol.form_5500 f ON sc.ack_id = f.ack_id
      WHERE f.sponsor_dfe_ein = $1
    `, [ein]);

    for (const c of schC.rows) {
      await env.D1_OUTREACH.prepare(`
        INSERT INTO dol_schedule_c (
          ack_id, outreach_id, sponsor_dfe_ein, form_year, row_order,
          provider_name, provider_ein, provider_us_city, provider_us_state,
          provider_srvc_codes, provider_relation,
          provider_direct_comp_amt, provider_indirect_comp_amt, all_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        c.ack_id, outreachId, c.sponsor_dfe_ein, c.form_year, c.row_order,
        c.provider_other_name, c.provider_other_ein,
        c.provider_other_us_city, c.provider_other_us_state,
        c.provider_other_srvc_codes, c.provider_other_relation,
        c.provider_other_direct_comp_amt, c.prov_other_tot_ind_comp_amt,
        JSON.stringify(c),
      ).run();
      schCCount++;
    }

    // 4. ALL other schedules — D, G, H, I, etc. — store as JSON in dol_schedule_other
    const otherTables = [
      'schedule_a', 'schedule_c', 'schedule_c_part1_item1', 'schedule_c_part1_item3',
      'schedule_c_part2', 'schedule_c_part3',
      'schedule_d', 'schedule_d_part1', 'schedule_d_part2',
      'schedule_g', 'schedule_g_part1', 'schedule_g_part2', 'schedule_g_part3',
      'schedule_h', 'schedule_h_part1',
      'schedule_i', 'schedule_i_part1',
      'schedule_dcg',
      'form_5500_sf', 'form_5500_sf_part7',
    ];

    for (const tbl of otherTables) {
      try {
        // Check if table has ack_id for joining
        const hasAck = await pg.query(`
          SELECT 1 FROM information_schema.columns
          WHERE table_schema = 'dol' AND table_name = $1 AND column_name = 'ack_id'
        `, [tbl]);

        if (hasAck.rows.length > 0) {
          const rows = await pg.query(`
            SELECT t.* FROM dol."${tbl}" t
            JOIN dol.form_5500 f ON t.ack_id = f.ack_id
            WHERE f.sponsor_dfe_ein = $1
          `, [ein]);

          for (const r of rows.rows) {
            await env.D1_OUTREACH.prepare(`
              INSERT INTO dol_schedule_other (
                ack_id, outreach_id, sponsor_dfe_ein, schedule_type, form_year, row_order, all_data
              ) VALUES (?, ?, ?, ?, ?, ?, ?)
            `).bind(
              r.ack_id, outreachId, ein, tbl, r.form_year ?? null, r.row_order ?? null,
              JSON.stringify(r),
            ).run();
            otherCount++;
          }
        }
      } catch {
        // Skip tables that don't exist or error
      }
    }

    return {
      ein, outreach_id: outreachId,
      seeded: { form_5500: filingCount, schedule_a: schACount, schedule_c: schCCount, other_schedules: otherCount },
      total_rows: filingCount + schACount + schCCount + otherCount,
    };
  } finally {
    await pg.end();
  }
}

export async function seedDolForEin(env: Env, ein: string): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  try {
    // Form 5500 — all years, all available columns
    const filings = await pg.query(`
      SELECT *
      FROM dol.form_5500
      WHERE sponsor_dfe_ein = $1
      ORDER BY ack_id DESC
    `, [ein]);

    // Schedule A — broker/insurance detail (commissions, fees)
    const scheduleA = await pg.query(`
      SELECT sa.ack_id, sa.ins_broker_name, sa.ins_broker_us_city, sa.ins_broker_us_state,
             sa.ins_broker_comm_pd_amt, sa.ins_broker_fees_pd_amt, sa.ins_broker_code,
             sa.form_year, sa.row_order
      FROM dol.schedule_a_part1 sa
      JOIN dol.form_5500 f ON sa.ack_id = f.ack_id
      WHERE f.sponsor_dfe_ein = $1
      ORDER BY sa.form_year DESC, sa.row_order
    `, [ein]);

    // Schedule C — service providers (brokers, advisors, their compensation)
    const scheduleC = await pg.query(`
      SELECT sc.ack_id, sc.provider_other_name, sc.provider_other_ein,
             sc.provider_other_us_city, sc.provider_other_us_state,
             sc.provider_other_srvc_codes, sc.provider_other_relation,
             sc.provider_other_direct_comp_amt, sc.prov_other_tot_ind_comp_amt,
             sc.form_year, sc.row_order
      FROM dol.schedule_c_part1_item2 sc
      JOIN dol.form_5500 f ON sc.ack_id = f.ack_id
      WHERE f.sponsor_dfe_ein = $1
      ORDER BY sc.form_year DESC, sc.row_order
    `, [ein]);

    // ICP filtered — enriched summary (may not have all same columns)
    let icp = { rows: [] as any[] };
    try {
      icp = await pg.query(`
        SELECT * FROM dol.form_5500_icp_filtered WHERE sponsor_dfe_ein = $1
      `, [ein]);
    } catch { /* table may not exist or have different schema */ }

    return {
      ein,
      company_name: filings.rows[0]?.sponsor_dfe_name ?? null,
      filing_count: filings.rows.length,
      filings: filings.rows,
      schedule_a_count: scheduleA.rows.length,
      schedule_a: scheduleA.rows,
      schedule_c_count: scheduleC.rows.length,
      schedule_c: scheduleC.rows,
      icp_filtered: icp.rows,
    };
  } finally {
    await pg.end();
  }
}

// ── BATCH SEED: All agent-assigned companies, ALL sub-hub data ──
// Pulls from Neon vault → writes to D1 outreach workspace.
// This runs ONCE to populate D1, then periodic refreshes.

export async function batchSeedAllCompanies(
  env: Env,
  options: { limit?: number; offset?: number } = {},
): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  const limit = options.limit ?? 100;  // process in batches
  const offset = options.offset ?? 0;
  let companiesProcessed = 0;
  let dolRowsSeeded = 0;
  let errors: string[] = [];

  try {
    // 1. Get agent-assigned companies with EINs from Neon
    // Join outreach.company_target → outreach.dol to get EINs
    // Filter by coverage zones (companies assigned to agents)
    const companies = await pg.query(`
      SELECT DISTINCT
        ct.outreach_id,
        ct.company_unique_id,
        d.ein,
        ct.state,
        ct.postal_code,
        sa.agent_name,
        sa.agent_number
      FROM outreach.company_target ct
      JOIN outreach.dol d ON ct.outreach_id = d.outreach_id
      JOIN coverage.v_service_agent_coverage_zips cz ON ct.postal_code = cz.zip
      JOIN coverage.service_agent sa ON cz.service_agent_id = sa.service_agent_id
      WHERE d.filing_present = true
        AND d.ein IS NOT NULL
        AND d.ein != ''
      ORDER BY ct.outreach_id
      LIMIT $1 OFFSET $2
    `, [limit, offset]);

    console.log(`[batchSeed] Found ${companies.rows.length} companies (offset=${offset}, limit=${limit})`);

    // 2. For each company, SEED full DOL data
    for (const co of companies.rows) {
      try {
        // DOL Form 5500 — all filings
        const filings = await pg.query(
          `SELECT * FROM dol.form_5500 WHERE sponsor_dfe_ein = $1`, [co.ein]
        );

        for (const f of filings.rows) {
          await env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO dol_form_5500 (
              ack_id, outreach_id, sponsor_dfe_ein, sponsor_dfe_name, plan_name, plan_number,
              plan_eff_date, form_year, form_tax_prd,
              spons_dfe_mail_us_city, spons_dfe_mail_us_state, spons_dfe_mail_us_zip,
              tot_active_partcp_cnt, tot_partcp_boy_cnt, admin_name, admin_ein,
              type_plan_entity_cd, sch_a_attached_ind, num_sch_a_attached_cnt,
              filing_status, date_received, all_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            f.ack_id, co.outreach_id, f.sponsor_dfe_ein, f.sponsor_dfe_name,
            f.plan_name, f.plan_number, f.plan_eff_date, f.form_year, f.form_tax_prd,
            f.spons_dfe_mail_us_city, f.spons_dfe_mail_us_state, f.spons_dfe_mail_us_zip,
            f.tot_active_partcp_cnt, f.tot_partcp_boy_cnt, f.admin_name, f.admin_ein,
            f.type_plan_entity_cd, f.sch_a_attached_ind, f.num_sch_a_attached_cnt,
            f.filing_status, f.date_received, JSON.stringify(f),
          ).run();
          dolRowsSeeded++;
        }

        // Schedule A — broker/insurance
        const schA = await pg.query(`
          SELECT sa.*, f.sponsor_dfe_ein FROM dol.schedule_a_part1 sa
          JOIN dol.form_5500 f ON sa.ack_id = f.ack_id
          WHERE f.sponsor_dfe_ein = $1
        `, [co.ein]);

        for (const a of schA.rows) {
          await env.D1_OUTREACH.prepare(`
            INSERT INTO dol_schedule_a (
              ack_id, outreach_id, sponsor_dfe_ein, form_year, row_order,
              ins_broker_name, ins_broker_us_city, ins_broker_us_state, ins_broker_us_zip,
              ins_broker_comm_pd_amt, ins_broker_fees_pd_amt, ins_broker_code, all_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            a.ack_id, co.outreach_id, co.ein, a.form_year, a.row_order,
            a.ins_broker_name, a.ins_broker_us_city, a.ins_broker_us_state, a.ins_broker_us_zip,
            a.ins_broker_comm_pd_amt, a.ins_broker_fees_pd_amt, a.ins_broker_code,
            JSON.stringify(a),
          ).run();
          dolRowsSeeded++;
        }

        // Schedule C — service providers
        const schC = await pg.query(`
          SELECT sc.*, f.sponsor_dfe_ein FROM dol.schedule_c_part1_item2 sc
          JOIN dol.form_5500 f ON sc.ack_id = f.ack_id
          WHERE f.sponsor_dfe_ein = $1
        `, [co.ein]);

        for (const c of schC.rows) {
          await env.D1_OUTREACH.prepare(`
            INSERT INTO dol_schedule_c (
              ack_id, outreach_id, sponsor_dfe_ein, form_year, row_order,
              provider_name, provider_ein, provider_us_city, provider_us_state,
              provider_srvc_codes, provider_relation,
              provider_direct_comp_amt, provider_indirect_comp_amt, all_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            c.ack_id, co.outreach_id, co.ein, c.form_year, c.row_order,
            c.provider_other_name, c.provider_other_ein,
            c.provider_other_us_city, c.provider_other_us_state,
            c.provider_other_srvc_codes, c.provider_other_relation,
            c.provider_other_direct_comp_amt, c.prov_other_tot_ind_comp_amt,
            JSON.stringify(c),
          ).run();
          dolRowsSeeded++;
        }

        // Other schedules as JSON
        const otherTables = [
          'schedule_a', 'schedule_c', 'schedule_d', 'schedule_d_part1', 'schedule_d_part2',
          'schedule_g', 'schedule_g_part1', 'schedule_g_part2', 'schedule_g_part3',
          'schedule_h', 'schedule_h_part1', 'schedule_i', 'schedule_i_part1', 'schedule_dcg',
        ];

        for (const tbl of otherTables) {
          try {
            const hasAck = await pg.query(`
              SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'dol' AND table_name = $1 AND column_name = 'ack_id'
            `, [tbl]);

            if (hasAck.rows.length > 0) {
              const rows = await pg.query(`
                SELECT t.* FROM dol."${tbl}" t
                JOIN dol.form_5500 f ON t.ack_id = f.ack_id
                WHERE f.sponsor_dfe_ein = $1
              `, [co.ein]);

              for (const r of rows.rows) {
                await env.D1_OUTREACH.prepare(`
                  INSERT INTO dol_schedule_other (
                    ack_id, outreach_id, sponsor_dfe_ein, schedule_type, form_year, row_order, all_data
                  ) VALUES (?, ?, ?, ?, ?, ?, ?)
                `).bind(
                  r.ack_id, co.outreach_id, co.ein, tbl, r.form_year ?? null, r.row_order ?? null,
                  JSON.stringify(r),
                ).run();
                dolRowsSeeded++;
              }
            }
          } catch { /* skip tables that error */ }
        }

        companiesProcessed++;
        if (companiesProcessed % 10 === 0) {
          console.log(`[batchSeed] Progress: ${companiesProcessed}/${companies.rows.length} companies, ${dolRowsSeeded} rows seeded`);
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        errors.push(`${co.ein} (${co.outreach_id}): ${msg}`);
      }
    }

    return {
      batch: { offset, limit },
      companies_found: companies.rows.length,
      companies_processed: companiesProcessed,
      dol_rows_seeded: dolRowsSeeded,
      errors: errors.length,
      error_details: errors.slice(0, 20), // first 20 errors
      has_more: companies.rows.length === limit,
      next_offset: offset + limit,
    };
  } finally {
    await pg.end();
  }
}

// ══════════════════════════════════════════════════════════════════
// SEED FIX #1: Re-SEED people_people_master
// ══════════════════════════════════════════════════════════════════
// Problem: 94.8% of filled slots point to person_unique_ids that
// don't exist in D1's people_people_master. The original SEED
// brought a subset. This pulls ALL referenced people from Neon.

export async function seedFixPeopleMaster(
  env: Env,
  options: { batchSize?: number } = {},
): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  const batchSize = options.batchSize ?? 500;
  let seeded = 0;
  let alreadyExist = 0;
  let notInNeon = 0;
  const errors: string[] = [];

  try {
    // 1. Get all person_unique_ids from filled slots in D1
    const slots = await env.D1_OUTREACH.prepare(
      'SELECT DISTINCT person_unique_id FROM people_company_slot WHERE is_filled = 1 AND person_unique_id IS NOT NULL'
    ).all<{ person_unique_id: string }>();

    const personIds = (slots.results || []).map(s => s.person_unique_id);
    console.log(`[seedFixPeopleMaster] ${personIds.length} unique person IDs from filled slots`);

    // 2. Check which ones already exist in D1 (small batches to avoid bind limit)
    const existing = new Set<string>();
    for (let i = 0; i < personIds.length; i += 50) {
      const batch = personIds.slice(i, i + 50);
      const placeholders = batch.map(() => '?').join(',');
      const found = await env.D1_OUTREACH.prepare(
        `SELECT unique_id FROM people_people_master WHERE unique_id IN (${placeholders})`
      ).bind(...batch).all<{ unique_id: string }>();
      for (const r of (found.results || [])) {
        existing.add(r.unique_id);
      }
    }
    alreadyExist = existing.size;

    // 3. Filter to missing ones
    const missing = personIds.filter(id => !existing.has(id));
    console.log(`[seedFixPeopleMaster] ${missing.length} missing, ${alreadyExist} already in D1`);

    // 4. Pull missing people from Neon in batches
    for (let i = 0; i < missing.length; i += batchSize) {
      const batch = missing.slice(i, i + batchSize);
      const placeholders = batch.map((_, idx) => `$${idx + 1}`).join(',');

      try {
        const people = await pg.query(
          `SELECT * FROM people.people_master WHERE unique_id IN (${placeholders})`,
          batch,
        );

        // Track IDs not found in Neon
        const foundIds = new Set(people.rows.map((r: any) => r.unique_id));
        for (const id of batch) {
          if (!foundIds.has(id)) notInNeon++;
        }

        // Batch insert into D1 (chunks of 20 to stay under bind limit: 20 × 35 = 700 < 999)
        const insertChunkSize = 20;
        for (let j = 0; j < people.rows.length; j += insertChunkSize) {
          const insertChunk = people.rows.slice(j, j + insertChunkSize);
          const statements: D1PreparedStatement[] = insertChunk.map((p: any) =>
            env.D1_OUTREACH.prepare(`
              INSERT OR REPLACE INTO people_people_master (
                unique_id, company_unique_id, company_slot_unique_id,
                first_name, last_name, full_name, title, seniority, department,
                email, work_phone_e164, personal_phone_e164,
                linkedin_url, twitter_url, facebook_url,
                bio, skills, education, certifications,
                source_system, source_record_id,
                promoted_from_intake_at, promotion_audit_log_id,
                created_at, updated_at,
                email_verified, message_key_scheduled,
                email_verification_source, email_verified_at,
                validation_status, last_verified_at,
                last_enrichment_attempt, is_decision_maker,
                outreach_ready, outreach_ready_at
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            `).bind(
              p.unique_id, p.company_unique_id, p.company_slot_unique_id ?? '',
              p.first_name ?? '', p.last_name ?? '', p.full_name, p.title, p.seniority, p.department,
              p.email, p.work_phone_e164, p.personal_phone_e164,
              p.linkedin_url, p.twitter_url, p.facebook_url,
              p.bio, p.skills ? JSON.stringify(p.skills) : null, p.education,
              p.certifications ? JSON.stringify(p.certifications) : null,
              p.source_system ?? 'neon_seed', p.source_record_id,
              p.promoted_from_intake_at?.toISOString() ?? new Date().toISOString(),
              p.promotion_audit_log_id,
              p.created_at?.toISOString() ?? null, p.updated_at?.toISOString() ?? null,
              p.email_verified ? 1 : 0, p.message_key_scheduled,
              p.email_verification_source, p.email_verified_at?.toISOString() ?? null,
              p.validation_status, p.last_verified_at?.toISOString() ?? new Date().toISOString(),
              p.last_enrichment_attempt?.toISOString() ?? null,
              p.is_decision_maker ? 1 : 0,
              p.outreach_ready ? 1 : 0, p.outreach_ready_at?.toISOString() ?? null,
            )
          );

          try {
            await env.D1_OUTREACH.batch(statements);
            seeded += insertChunk.length;
          } catch (e) {
            errors.push(`d1batch ${i}+${j}: ${e instanceof Error ? e.message : String(e)}`);
          }
        }

      } catch (e) {
        errors.push(`batch ${i}: ${e instanceof Error ? e.message : String(e)}`);
      }

      if ((i + batchSize) % 2000 === 0) {
        console.log(`[seedFixPeopleMaster] Progress: ${Math.min(i + batchSize, missing.length)}/${missing.length}`);
      }
    }

    return {
      action: 'seedFixPeopleMaster',
      filled_slots_total: personIds.length,
      already_in_d1: alreadyExist,
      missing: missing.length,
      seeded,
      not_in_neon: notInNeon,
      errors: errors.length,
      error_details: errors.slice(0, 20),
    };
  } finally {
    await pg.end();
  }
}

// ══════════════════════════════════════════════════════════════════
// SEED FIX #2: Create missing CEO/CFO/HR slots
// ══════════════════════════════════════════════════════════════════
// Problem: 18,301 companies have NO slots at all.
// This is D1-only — no Neon needed.

export async function seedFixMissingSlots(
  env: Env,
  options: { limit?: number; offset?: number } = {},
): Promise<any> {
  const limit = options.limit ?? 3000; // 3000 companies × 3 slots = 9000 D1 writes max
  const offset = options.offset ?? 0;
  let created = 0;
  const errors: string[] = [];
  const slotTypes = ['CEO', 'CFO', 'HR'];

  // Get companies that have no slots (paginated)
  const noSlots = await env.D1_OUTREACH.prepare(`
    SELECT oo.outreach_id, ct.company_unique_id
    FROM outreach_outreach oo
    JOIN outreach_company_target ct ON oo.outreach_id = ct.outreach_id
    WHERE oo.outreach_id NOT IN (SELECT DISTINCT outreach_id FROM people_company_slot)
    ORDER BY oo.outreach_id
    LIMIT ? OFFSET ?
  `).bind(limit, offset).all<{ outreach_id: string; company_unique_id: string }>();

  const companies = noSlots.results || [];
  console.log(`[seedFixMissingSlots] ${companies.length} companies in this batch (offset=${offset})`);

  // Use D1 batch for efficiency
  const batchSize = 100; // 100 companies × 3 slots = 300 statements per batch
  for (let i = 0; i < companies.length; i += batchSize) {
    const chunk = companies.slice(i, i + batchSize);
    const statements: D1PreparedStatement[] = [];

    for (const co of chunk) {
      for (const slotType of slotTypes) {
        const slotId = crypto.randomUUID();
        statements.push(
          env.D1_OUTREACH.prepare(`
            INSERT INTO people_company_slot (
              slot_id, outreach_id, company_unique_id, slot_type,
              is_filled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 0, datetime('now'), datetime('now'))
          `).bind(slotId, co.outreach_id, co.company_unique_id, slotType)
        );
      }
    }

    try {
      await env.D1_OUTREACH.batch(statements);
      created += statements.length;
    } catch (e) {
      errors.push(`batch ${i}: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  // Count remaining
  const remaining = await env.D1_OUTREACH.prepare(`
    SELECT COUNT(DISTINCT oo.outreach_id) as c
    FROM outreach_outreach oo
    WHERE oo.outreach_id NOT IN (SELECT DISTINCT outreach_id FROM people_company_slot)
  `).first<{ c: number }>();

  return {
    action: 'seedFixMissingSlots',
    batch: { offset, limit },
    companies_in_batch: companies.length,
    slots_created: created,
    remaining_companies: remaining?.c ?? 0,
    has_more: companies.length === limit,
    next_offset: offset + limit,
    errors: errors.length,
    error_details: errors.slice(0, 20),
  };
}

// ══════════════════════════════════════════════════════════════════
// SEED FIX #3: Agent assignment per company
// ══════════════════════════════════════════════════════════════════
// Problem: No way to know which agent owns which company in D1.
// Queries Neon coverage view to get the assignment, then writes
// agent_id + agent_name to outreach_company_target in D1.

export async function seedFixAgentAssignment(env: Env): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  let updated = 0;
  let noAgent = 0;
  const errors: string[] = [];

  try {
    // Add columns if they don't exist
    try {
      await env.D1_OUTREACH.prepare(
        'ALTER TABLE outreach_company_target ADD COLUMN service_agent_id TEXT'
      ).run();
    } catch { /* column may already exist */ }

    try {
      await env.D1_OUTREACH.prepare(
        'ALTER TABLE outreach_company_target ADD COLUMN service_agent_name TEXT'
      ).run();
    } catch { /* column may already exist */ }

    try {
      await env.D1_OUTREACH.prepare(
        'ALTER TABLE outreach_company_target ADD COLUMN service_agent_number TEXT'
      ).run();
    } catch { /* column may already exist */ }

    // Query Neon for agent assignments via coverage view
    const assignments = await pg.query(`
      SELECT DISTINCT
        ct.outreach_id,
        sa.service_agent_id,
        sa.agent_name,
        sa.agent_number
      FROM outreach.company_target ct
      JOIN coverage.v_service_agent_coverage_zips cz ON ct.postal_code = cz.zip
      JOIN coverage.service_agent sa ON cz.service_agent_id = sa.service_agent_id
      WHERE sa.status = 'active'
        AND ct.outreach_id IS NOT NULL
      ORDER BY ct.outreach_id
    `);

    console.log(`[seedFixAgentAssignment] ${assignments.rows.length} agent assignments from Neon`);

    // Build a map (some companies might match multiple agents — take first)
    const agentMap = new Map<string, { agent_id: string; agent_name: string; agent_number: string }>();
    for (const a of assignments.rows) {
      if (!agentMap.has(a.outreach_id)) {
        agentMap.set(a.outreach_id, {
          agent_id: a.service_agent_id,
          agent_name: a.agent_name,
          agent_number: a.agent_number,
        });
      }
    }

    // Update D1 in batches
    const entries = Array.from(agentMap.entries());
    const updateBatchSize = 100;
    for (let i = 0; i < entries.length; i += updateBatchSize) {
      const chunk = entries.slice(i, i + updateBatchSize);
      const statements: D1PreparedStatement[] = chunk.map(([outreachId, agent]) =>
        env.D1_OUTREACH.prepare(`
          UPDATE outreach_company_target
          SET service_agent_id = ?,
              service_agent_name = ?,
              service_agent_number = ?
          WHERE outreach_id = ?
        `).bind(agent.agent_id, agent.agent_name, agent.agent_number, outreachId)
      );

      try {
        await env.D1_OUTREACH.batch(statements);
        updated += chunk.length;
      } catch (e) {
        errors.push(`batch ${i}: ${e instanceof Error ? e.message : String(e)}`);
      }
    }

    // Count companies with no agent match
    const totalCompanies = await env.D1_OUTREACH.prepare(
      'SELECT COUNT(*) as c FROM outreach_company_target'
    ).first<{ c: number }>();
    noAgent = (totalCompanies?.c ?? 0) - updated;

    return {
      action: 'seedFixAgentAssignment',
      neon_assignments: assignments.rows.length,
      unique_companies_assigned: agentMap.size,
      d1_updated: updated,
      no_agent_match: noAgent,
      errors: errors.length,
      error_details: errors.slice(0, 20),
    };
  } finally {
    await pg.end();
  }
}

// ══════════════════════════════════════════════════════════════════
// GLOBAL SEED: US ZIP Codes → imo-d1-global
// ══════════════════════════════════════════════════════════════════
// Copies reference.us_zip_codes from Neon into IMO-Creator's
// global D1 database. Static reference table, 41,551 rows.
// Any business silo can bind read-only.

// ══════════════════════════════════════════════════════════════════
// SEED FIX #4: Match existing people to empty slots
// ══════════════════════════════════════════════════════════════════
// Problem: 31,095 people records with titles NOT linked to any slot.
// 16,644 can be matched to empty slots by company_unique_id + title
// pattern → slot_type. Pure D1. Zero external calls.

// ══════════════════════════════════════════════════════════════════
// SEED FIX #5: Full people_people_master re-SEED from Neon
// ══════════════════════════════════════════════════════════════════
// Problem: D1 has 51K people but Neon has 182K. Neon already has
// correct slot assignments. Pull ALL people for agent-assigned
// companies from Neon → D1, and update slots to match.

export async function seedFullPeopleMaster(
  env: Env,
  options: { limit?: number; offset?: number } = {},
): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  const limit = options.limit ?? 5000;
  const offset = options.offset ?? 0;
  let seeded = 0;
  let slotsUpdated = 0;
  const errors: string[] = [];

  try {
    // Simple approach: Neon slots already have outreach_id.
    // Pull slots from Neon that match D1 outreach_ids, then pull their people.

    // Step 1: Pull SLOTS from Neon with pagination
    // The slot table has outreach_id — we filter by outreach_ids in D1
    const slots = await pg.query(`
      SELECT cs.slot_id::text as slot_id, cs.outreach_id::text as outreach_id,
             cs.company_unique_id, cs.slot_type, cs.person_unique_id,
             cs.is_filled, cs.filled_at, cs.confidence_score, cs.source_system,
             cs.created_at, cs.updated_at
      FROM people.company_slot cs
      WHERE cs.outreach_id IN (
        SELECT outreach_id FROM outreach.outreach
        WHERE outreach_id IS NOT NULL
      )
      ORDER BY cs.slot_id
      LIMIT $1 OFFSET $2
    `, [limit, offset]);

    console.log(`[seedFullPeopleMaster] ${slots.rows.length} slots from Neon (offset=${offset})`);

    // Step 2: Upsert slots into D1
    const slotBatchSize = 50;
    for (let si = 0; si < slots.rows.length; si += slotBatchSize) {
      const chunk = slots.rows.slice(si, si + slotBatchSize);
      const stmts: D1PreparedStatement[] = chunk.map((s: any) =>
        env.D1_OUTREACH.prepare(`
          INSERT OR REPLACE INTO people_company_slot (
            slot_id, outreach_id, company_unique_id, slot_type,
            person_unique_id, is_filled, filled_at, confidence_score,
            source_system, created_at, updated_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).bind(
          s.slot_id, s.outreach_id, s.company_unique_id, s.slot_type,
          s.person_unique_id, s.is_filled ? 1 : 0,
          s.filled_at?.toISOString() ?? null, s.confidence_score,
          s.source_system, s.created_at?.toISOString() ?? null,
          s.updated_at?.toISOString() ?? null,
        )
      );
      try {
        await env.D1_OUTREACH.batch(stmts);
        slotsUpdated += chunk.length;
      } catch (e) {
        errors.push(`slot batch ${si}: ${e instanceof Error ? e.message : String(e)}`);
      }
    }

    // Step 3: Get unique person_unique_ids from these slots
    const personIds = [...new Set(
      slots.rows.filter((s: any) => s.person_unique_id).map((s: any) => s.person_unique_id)
    )];

    // Step 4: Pull those people from Neon
    const people = { rows: [] as any[] };
    const pidBatchSize = 500;
    for (let pi = 0; pi < personIds.length; pi += pidBatchSize) {
      const pidBatch = personIds.slice(pi, pi + pidBatchSize);
      const placeholders = pidBatch.map((_, idx) => `$${idx + 1}`).join(',');
      const batch = await pg.query(
        `SELECT * FROM people.people_master WHERE unique_id IN (${placeholders})`,
        pidBatch,
      );
      people.rows.push(...batch.rows);
    }
    console.log(`[seedFullPeopleMaster] ${people.rows.length} people from Neon for ${personIds.length} slot refs`);

    // Use filtered = people.rows (all are valid)
    const filtered = people.rows;

    console.log(`[seedFullPeopleMaster] ${people.rows.length} people from Neon (offset=${offset})`);

    // Batch insert into D1
    const insertBatchSize = 20;
    for (let i = 0; i < people.rows.length; i += insertBatchSize) {
      const chunk = people.rows.slice(i, i + insertBatchSize);
      const statements: D1PreparedStatement[] = chunk.map((p: any) =>
        env.D1_OUTREACH.prepare(`
          INSERT OR REPLACE INTO people_people_master (
            unique_id, company_unique_id, company_slot_unique_id,
            first_name, last_name, full_name, title, seniority, department,
            email, work_phone_e164, personal_phone_e164,
            linkedin_url, twitter_url, facebook_url,
            bio, skills, education, certifications,
            source_system, source_record_id,
            promoted_from_intake_at, promotion_audit_log_id,
            created_at, updated_at,
            email_verified, message_key_scheduled,
            email_verification_source, email_verified_at,
            validation_status, last_verified_at,
            last_enrichment_attempt, is_decision_maker,
            outreach_ready, outreach_ready_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).bind(
          p.unique_id, p.company_unique_id, p.company_slot_unique_id ?? '',
          p.first_name ?? '', p.last_name ?? '', p.full_name, p.title, p.seniority, p.department,
          p.email, p.work_phone_e164, p.personal_phone_e164,
          p.linkedin_url, p.twitter_url, p.facebook_url,
          p.bio, p.skills ? JSON.stringify(p.skills) : null, p.education,
          p.certifications ? JSON.stringify(p.certifications) : null,
          p.source_system ?? 'neon_full_seed', p.source_record_id,
          p.promoted_from_intake_at?.toISOString() ?? new Date().toISOString(),
          p.promotion_audit_log_id,
          p.created_at?.toISOString() ?? null, p.updated_at?.toISOString() ?? null,
          p.email_verified ? 1 : 0, p.message_key_scheduled,
          p.email_verification_source, p.email_verified_at?.toISOString() ?? null,
          p.validation_status, p.last_verified_at?.toISOString() ?? new Date().toISOString(),
          p.last_enrichment_attempt?.toISOString() ?? null,
          p.is_decision_maker ? 1 : 0,
          p.outreach_ready ? 1 : 0, p.outreach_ready_at?.toISOString() ?? null,
        )
      );

      try {
        await env.D1_OUTREACH.batch(statements);
        seeded += chunk.length;
      } catch (e) {
        errors.push(`insert batch ${i}: ${e instanceof Error ? e.message : String(e)}`);
      }
    }

    // Slots already updated in Step 2 above — no duplicate update needed

    return {
      action: 'seedFullPeopleMaster',
      batch: { offset, limit },
      people_from_neon: people.rows.length,
      people_seeded: seeded,
      slots_updated: slotsUpdated,
      has_more: people.rows.length === limit,
      next_offset: offset + limit,
      errors: errors.length,
      error_details: errors.slice(0, 20),
    };
  } finally {
    await pg.end();
  }
}

export async function seedFixMatchPeopleToSlots(
  env: Env,
  options: { limit?: number } = {},
): Promise<any> {
  const limit = options.limit ?? 1000;
  let filled = 0;
  const errors: string[] = [];

  // Get matchable records: empty slot + existing person for same company + title matches slot type
  const matches = await env.D1_OUTREACH.prepare(`
    SELECT cs.slot_id, cs.outreach_id, cs.company_unique_id, cs.slot_type,
           pm.unique_id as person_id, pm.first_name, pm.last_name, pm.title
    FROM people_company_slot cs
    JOIN people_people_master pm ON cs.company_unique_id = pm.company_unique_id
    JOIN people_title_slot_mapping tsm ON LOWER(pm.title) LIKE '%' || LOWER(tsm.title_pattern) || '%'
      AND tsm.slot_type = cs.slot_type
    WHERE cs.is_filled = 0
      AND pm.unique_id NOT IN (SELECT person_unique_id FROM people_company_slot WHERE person_unique_id IS NOT NULL)
    ORDER BY cs.outreach_id, cs.slot_type
    LIMIT ?
  `).bind(limit).all<{
    slot_id: string; outreach_id: string; company_unique_id: string; slot_type: string;
    person_id: string; first_name: string; last_name: string; title: string;
  }>();

  const rows = matches.results || [];
  console.log(`[seedFixMatchPeopleToSlots] ${rows.length} matches found (limit=${limit})`);

  // Dedupe: one person per slot (first match wins)
  const usedSlots = new Set<string>();
  const usedPeople = new Set<string>();

  // Batch update
  const batchSize = 50; // 50 × 2 statements = 100 per batch
  for (let i = 0; i < rows.length; i += batchSize) {
    const chunk = rows.slice(i, i + batchSize);
    const statements: D1PreparedStatement[] = [];

    for (const match of chunk) {
      if (usedSlots.has(match.slot_id) || usedPeople.has(match.person_id)) continue;
      usedSlots.add(match.slot_id);
      usedPeople.add(match.person_id);

      // Update slot to filled
      statements.push(
        env.D1_OUTREACH.prepare(`
          UPDATE people_company_slot
          SET person_unique_id = ?, is_filled = 1, filled_at = datetime('now'),
              source_system = 'existing_match', confidence_score = 0.8, updated_at = datetime('now')
          WHERE slot_id = ? AND is_filled = 0
        `).bind(match.person_id, match.slot_id)
      );

      // Update people_master to link to slot
      statements.push(
        env.D1_OUTREACH.prepare(`
          UPDATE people_people_master
          SET company_slot_unique_id = ?, updated_at = datetime('now')
          WHERE unique_id = ?
        `).bind(match.slot_id, match.person_id)
      );
    }

    if (statements.length > 0) {
      try {
        await env.D1_OUTREACH.batch(statements);
        filled += statements.length / 2;
      } catch (e) {
        errors.push(`batch ${i}: ${e instanceof Error ? e.message : String(e)}`);
      }
    }
  }

  // Count remaining
  const remaining = await env.D1_OUTREACH.prepare(
    'SELECT COUNT(*) as c FROM people_company_slot WHERE is_filled = 0'
  ).first<{ c: number }>();

  return {
    action: 'seedFixMatchPeopleToSlots',
    matches_found: rows.length,
    slots_filled: filled,
    remaining_empty: remaining?.c ?? 0,
    errors: errors.length,
    error_details: errors.slice(0, 20),
  };
}

// ══════════════════════════════════════════════════════════════════
// CLEAN SEED — Reads from seed_views.* in Neon, pours into D1
// ══════════════════════════════════════════════════════════════════
// Source of truth: seed_views schema in Neon (Marketing DB)
// Gate: seed_views.v_agent_companies (32,702 companies)
// Every view is scoped. The SEED is a dumb copy. No filtering here.
// ══════════════════════════════════════════════════════════════════

export async function seedClean(
  env: Env,
  options: { table?: string; limit?: number; offset?: number } = {},
): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  const table = options.table ?? 'all';
  const limit = options.limit ?? 5000;
  const offset = options.offset ?? 0;
  const results: Record<string, any> = {};

  // ── helpers ──────────────────────────────────────────────────
  const ts = (v: any): string | null => (v instanceof Date ? v.toISOString() : v ?? null);
  const bool = (v: any): number => (v ? 1 : 0);

  try {
    // ── 1. outreach_company_target ─────────────────────────────
    // JOIN outreach.company_target (full row) with seed_views.v_agent_companies (agent info filter)
    if (table === 'all' || table === 'company_target') {
      const rows = await pg.query(`
        SELECT
          ct.target_id, ct.company_unique_id, ct.outreach_status, ct.bit_score_snapshot,
          ct.first_targeted_at, ct.last_targeted_at, ct.sequence_count, ct.active_sequence_id,
          ct.source, ct.created_at, ct.updated_at, ct.outreach_id, ct.email_method,
          ct.method_type, ct.confidence_score, ct.execution_status, ct.imo_completed_at,
          ct.is_catchall,
          ct.industry, ct.employees, ct.country, ct.state, ct.city, ct.postal_code,
          ct.data_year, ct.postal_code_source, ct.postal_code_updated_at,
          agg.service_agents, agg.agent_count
        FROM outreach.company_target ct
        JOIN seed_views.v_agent_companies v ON ct.outreach_id = v.outreach_id
        LEFT JOIN (
          SELECT ct2.outreach_id,
            string_agg(DISTINCT sa.agent_number, ',' ORDER BY sa.agent_number) as service_agents,
            COUNT(DISTINCT sa.agent_number) as agent_count
          FROM outreach.company_target ct2
          JOIN coverage.v_service_agent_coverage_zips cz ON ct2.postal_code = cz.zip
          JOIN coverage.service_agent sa ON cz.service_agent_id = sa.service_agent_id AND sa.status = 'active'
          GROUP BY ct2.outreach_id
        ) agg ON ct.outreach_id = agg.outreach_id
        ORDER BY ct.outreach_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO outreach_company_target (
              target_id, company_unique_id, outreach_status, bit_score_snapshot,
              first_targeted_at, last_targeted_at, sequence_count, active_sequence_id,
              source, created_at, updated_at, outreach_id, email_method,
              method_type, confidence_score, execution_status, imo_completed_at,
              is_catchall, industry, employees, country, state, city, postal_code,
              data_year, postal_code_source, postal_code_updated_at,
              service_agents, agent_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.target_id, r.company_unique_id, r.outreach_status ?? 'queued', r.bit_score_snapshot,
            ts(r.first_targeted_at), ts(r.last_targeted_at), r.sequence_count ?? 0, r.active_sequence_id,
            r.source, ts(r.created_at), ts(r.updated_at), r.outreach_id, r.email_method,
            r.method_type, r.confidence_score, r.execution_status, ts(r.imo_completed_at),
            bool(r.is_catchall), r.industry, r.employees, r.country, r.state, r.city, r.postal_code,
            r.data_year, r.postal_code_source, ts(r.postal_code_updated_at),
            r.service_agents, r.agent_count,
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.company_target = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] company_target: ${seeded} rows`);
    }

    // ── 2. outreach_outreach ───────────────────────────────────
    // Read from outreach.outreach filtered by seed_views.v_agent_companies
    if (table === 'all' || table === 'outreach') {
      const rows = await pg.query(`
        SELECT
          o.outreach_id, o.sovereign_id, o.created_at, o.updated_at,
          o.domain, o.ein, o.has_appointment
        FROM outreach.outreach o
        WHERE o.outreach_id IN (SELECT outreach_id FROM seed_views.v_agent_companies)
        ORDER BY o.outreach_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO outreach_outreach (
              outreach_id, sovereign_id, created_at, updated_at,
              domain, ein, has_appointment
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.outreach_id, r.sovereign_id, ts(r.created_at), ts(r.updated_at),
            r.domain, r.ein, bool(r.has_appointment),
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.outreach = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] outreach: ${seeded} rows`);
    }

    // ── 3. outreach_blog (materialized view) ───────────────────
    // Read from seed_views.v_agent_blog — generate blog_id if NULL
    if (table === 'all' || table === 'blog') {
      const rows = await pg.query(`
        SELECT
          outreach_id as blog_id, outreach_id, context_summary, source_url,
          about_url, last_extracted_at,
          domain as source_type, extraction_status as extraction_method,
          has_sitemap, domain_reachable, people_extracted
        FROM seed_views.v_agent_blog
        ORDER BY outreach_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO outreach_blog (
              blog_id, outreach_id, context_summary, source_url,
              about_url, last_extracted_at, source_type, extraction_method,
              created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
          `).bind(
            r.blog_id, r.outreach_id, r.context_summary, r.source_url,
            r.about_url, ts(r.last_extracted_at), r.source_type, r.extraction_method,
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.blog = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] blog: ${seeded} rows`);
    }

    // ── 4. outreach_dol ────────────────────────────────────────
    // Read from outreach.dol filtered by seed_views.v_agent_companies
    if (table === 'all' || table === 'dol') {
      const rows = await pg.query(`
        SELECT
          dol_id, outreach_id, ein, filing_present, funding_type,
          broker_or_advisor, carrier, created_at, updated_at,
          renewal_month, outreach_start_month
        FROM seed_views.v_agent_dol
        ORDER BY outreach_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO outreach_dol (
              dol_id, outreach_id, ein, filing_present, funding_type,
              broker_or_advisor, carrier, created_at, updated_at,
              renewal_month, outreach_start_month
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.dol_id ?? r.outreach_id, r.outreach_id, r.ein, bool(r.filing_present), r.funding_type,
            r.broker_or_advisor, r.carrier, ts(r.created_at), ts(r.updated_at),
            r.renewal_month, r.outreach_start_month,
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.dol = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] dol: ${seeded} rows`);
    }

    // ── 5. people_company_slot ─────────────────────────────────
    // Read directly from seed_views.v_agent_slots (all needed columns)
    if (table === 'all' || table === 'slots') {
      const rows = await pg.query(`
        SELECT
          slot_id, outreach_id, company_unique_id, slot_type,
          person_unique_id, is_filled, filled_at, confidence_score,
          source_system, created_at, updated_at
        FROM seed_views.v_agent_slots
        ORDER BY outreach_id, slot_type
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO people_company_slot (
              slot_id, outreach_id, company_unique_id, slot_type,
              person_unique_id, is_filled, filled_at, confidence_score,
              source_system, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.slot_id?.toString(), r.outreach_id, r.company_unique_id, r.slot_type,
            r.person_unique_id, bool(r.is_filled),
            ts(r.filled_at), r.confidence_score,
            r.source_system, ts(r.created_at), ts(r.updated_at),
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.slots = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] slots: ${seeded} rows`);
    }

    // ── 6. people_people_master ────────────────────────────────
    // Read directly from seed_views.v_agent_people (all needed columns)
    if (table === 'all' || table === 'people') {
      const rows = await pg.query(`
        SELECT
          unique_id, company_unique_id, company_slot_unique_id,
          first_name, last_name, full_name, title, seniority, department,
          email, work_phone_e164, personal_phone_e164,
          linkedin_url, twitter_url, facebook_url, bio, skills, education, certifications,
          source_system, source_record_id, promoted_from_intake_at, promotion_audit_log_id,
          created_at, updated_at, email_verified, message_key_scheduled,
          email_verification_source, email_verified_at, validation_status,
          last_verified_at, last_enrichment_attempt,
          is_decision_maker, outreach_ready, outreach_ready_at
        FROM seed_views.v_agent_people
        ORDER BY unique_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 20) {
        const chunk = rows.rows.slice(i, i + 20);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO people_people_master (
              unique_id, company_unique_id, company_slot_unique_id,
              first_name, last_name, full_name, title, seniority, department,
              email, work_phone_e164, personal_phone_e164,
              linkedin_url, twitter_url, facebook_url, bio, skills, education, certifications,
              source_system, source_record_id, promoted_from_intake_at, promotion_audit_log_id,
              created_at, updated_at, email_verified, message_key_scheduled,
              email_verification_source, email_verified_at, validation_status,
              last_verified_at, last_enrichment_attempt,
              is_decision_maker, outreach_ready, outreach_ready_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.unique_id, r.company_unique_id, r.company_slot_unique_id ?? '',
            r.first_name ?? '', r.last_name ?? '', r.full_name, r.title, r.seniority, r.department,
            r.email, r.work_phone_e164, r.personal_phone_e164,
            r.linkedin_url, r.twitter_url, r.facebook_url, r.bio, r.skills, r.education, r.certifications,
            r.source_system ?? 'neon_clean_seed', r.source_record_id, ts(r.promoted_from_intake_at), r.promotion_audit_log_id,
            ts(r.created_at), ts(r.updated_at), bool(r.email_verified), r.message_key_scheduled,
            r.email_verification_source, ts(r.email_verified_at), r.validation_status,
            ts(r.last_verified_at), ts(r.last_enrichment_attempt),
            bool(r.is_decision_maker), bool(r.outreach_ready), ts(r.outreach_ready_at),
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.people = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] people: ${seeded} rows`);
    }

    // ── 7. cl_company_identity → spine D1 ──────────────────────
    // Read directly from seed_views.v_agent_cl_identity (all needed columns)
    if (table === 'all' || table === 'cl_identity') {
      const rows = await pg.query(`
        SELECT
          company_unique_id, company_name, company_domain, linkedin_company_url,
          source_system, created_at, company_fingerprint, lifecycle_run_id,
          existence_verified, verification_run_id, verified_at, domain_status_code,
          name_match_score, state_match_result, canonical_name, state_verified,
          employee_count_band, identity_pass, identity_status, last_pass_at,
          eligibility_status, exclusion_reason, entity_role, sovereign_company_id,
          final_outcome, final_reason, outreach_id, sales_process_id, client_id,
          outreach_attached_at, sales_opened_at, client_promoted_at,
          normalized_domain, updated_at, state_code, lcs_id, lcs_attached_at
        FROM seed_views.v_agent_cl_identity
        ORDER BY outreach_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1.prepare(`
            INSERT OR REPLACE INTO cl_company_identity (
              company_unique_id, company_name, company_domain, linkedin_company_url,
              source_system, created_at, company_fingerprint, lifecycle_run_id,
              existence_verified, verification_run_id, verified_at, domain_status_code,
              name_match_score, state_match_result, canonical_name, state_verified,
              employee_count_band, identity_pass, identity_status, last_pass_at,
              eligibility_status, exclusion_reason, entity_role, sovereign_company_id,
              final_outcome, final_reason, outreach_id, sales_process_id, client_id,
              outreach_attached_at, sales_opened_at, client_promoted_at,
              normalized_domain, updated_at, state_code, lcs_id, lcs_attached_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.company_unique_id, r.company_name, r.company_domain, r.linkedin_company_url,
            r.source_system, ts(r.created_at), r.company_fingerprint, r.lifecycle_run_id,
            bool(r.existence_verified), r.verification_run_id, ts(r.verified_at), r.domain_status_code,
            r.name_match_score, r.state_match_result, r.canonical_name, bool(r.state_verified),
            r.employee_count_band, bool(r.identity_pass), r.identity_status, ts(r.last_pass_at),
            r.eligibility_status, r.exclusion_reason, r.entity_role, r.sovereign_company_id,
            r.final_outcome, r.final_reason, r.outreach_id, r.sales_process_id, r.client_id,
            ts(r.outreach_attached_at), ts(r.sales_opened_at), ts(r.client_promoted_at),
            r.normalized_domain, ts(r.updated_at), r.state_code, r.lcs_id, ts(r.lcs_attached_at),
          )
        );
        await env.D1.batch(stmts);
        seeded += chunk.length;
      }
      results.cl_identity = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] cl_identity: ${seeded} rows`);
    }

    // ── 8. enrichment_hunter_contact ──────────────────────────
    // Verified emails + people from Hunter.io — the gold mine
    if (table === 'all' || table === 'hunter_contacts') {
      const rows = await pg.query(`
        SELECT
          id, outreach_id, company_unique_id, domain,
          first_name, last_name, full_name, email, email_type,
          email_verified, confidence_score, job_title, title_normalized,
          seniority_level, department, department_normalized,
          linkedin_url, phone_number, num_sources,
          is_decision_maker, outreach_priority, data_quality_score,
          source, source_file, created_at
        FROM seed_views.v_agent_hunter_contacts
        ORDER BY outreach_id, id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO enrichment_hunter_contact (
              id, outreach_id, company_unique_id, domain,
              first_name, last_name, full_name, email, email_type,
              email_verified, confidence_score, job_title, title_normalized,
              seniority_level, department, department_normalized,
              linkedin_url, phone_number, num_sources,
              is_decision_maker, outreach_priority, data_quality_score,
              source, source_file, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.id, r.outreach_id, r.company_unique_id, r.domain,
            r.first_name, r.last_name, r.full_name, r.email, r.email_type,
            bool(r.email_verified), r.confidence_score, r.job_title, r.title_normalized,
            r.seniority_level, r.department, r.department_normalized,
            r.linkedin_url, r.phone_number, r.num_sources,
            bool(r.is_decision_maker), r.outreach_priority, r.data_quality_score,
            r.source, r.source_file, ts(r.created_at),
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.hunter_contacts = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] hunter_contacts: ${seeded} rows`);
    }

    // ── 9. enrichment_hunter_company (email patterns) ─────────
    // One row per domain with email_pattern like "{first}.{last}"
    if (table === 'all' || table === 'hunter_patterns') {
      const rows = await pg.query(`
        SELECT
          id, outreach_id, company_unique_id, domain, organization,
          email_pattern, industry, industry_normalized, company_type,
          headcount, headcount_min, headcount_max,
          country, state, city, postal_code, street, location_full,
          data_quality_score, source, enriched_at, created_at, updated_at
        FROM seed_views.v_agent_hunter_patterns
        ORDER BY outreach_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO enrichment_hunter_company (
              id, outreach_id, company_unique_id, domain, organization,
              email_pattern, industry, industry_normalized, company_type,
              headcount, headcount_min, headcount_max,
              country, state, city, postal_code, street, location_full,
              data_quality_score, source, enriched_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.id, r.outreach_id, r.company_unique_id, r.domain, r.organization,
            r.email_pattern, r.industry, r.industry_normalized, r.company_type,
            r.headcount, r.headcount_min, r.headcount_max,
            r.country, r.state, r.city, r.postal_code, r.street, r.location_full,
            r.data_quality_score, r.source, ts(r.enriched_at), ts(r.created_at), ts(r.updated_at),
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.hunter_patterns = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] hunter_patterns: ${seeded} rows`);
    }

    // ── 10. vendor_people ──────────────────────────────────────
    // Enriched contacts from vendor pipeline — overlaps hunter but has slot mapping
    if (table === 'all' || table === 'vendor_people') {
      const rows = await pg.query(`
        SELECT
          vendor_row_id, outreach_id, company_unique_id, domain,
          first_name, last_name, full_name, email, email_type,
          email_verified, confidence_score, job_title, title_normalized,
          seniority_level, department, department_normalized,
          mapped_slot_type, linkedin_url, phone_number, work_phone, personal_phone,
          num_sources, is_decision_maker, company_name,
          city, state, country,
          source_system, backfill_source, enriched_by,
          data_quality_score, source_table,
          original_created_at as created_at, original_updated_at as updated_at
        FROM seed_views.v_agent_vendor_people
        ORDER BY outreach_id, vendor_row_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO vendor_people (
              vendor_row_id, outreach_id, company_unique_id, domain,
              first_name, last_name, full_name, email, email_type,
              email_verified, confidence_score, job_title, title_normalized,
              seniority_level, department, department_normalized,
              mapped_slot_type, linkedin_url, phone_number, work_phone, personal_phone,
              num_sources, is_decision_maker, company_name,
              city, state, country,
              source_system, backfill_source, enriched_by,
              data_quality_score, source_table, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.vendor_row_id, r.outreach_id, r.company_unique_id, r.domain,
            r.first_name, r.last_name, r.full_name, r.email, r.email_type,
            bool(r.email_verified), r.confidence_score, r.job_title, r.title_normalized,
            r.seniority_level, r.department, r.department_normalized,
            r.mapped_slot_type, r.linkedin_url, r.phone_number, r.work_phone, r.personal_phone,
            r.num_sources, bool(r.is_decision_maker), r.company_name,
            r.city, r.state, r.country,
            r.source_system, r.backfill_source, r.enriched_by,
            r.data_quality_score, r.source_table, ts(r.created_at), ts(r.updated_at),
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.vendor_people = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] vendor_people: ${seeded} rows`);
    }

    // ── 11. vendor_ct ──────────────────────────────────────────
    if (table === 'all' || table === 'vendor_ct') {
      const rows = await pg.query(`
        SELECT
          vendor_row_id, outreach_id, company_unique_id, domain,
          company_name, email_pattern, email_pattern_confidence,
          email_pattern_source, email_pattern_verified_at,
          company_phone, company_type, employee_count,
          industry, industry_normalized, description,
          city, state, country, postal_code,
          linkedin_url, facebook_url, twitter_url,
          ein, duns, source_system, enriched_by,
          data_quality_score, enriched_at, source_table,
          original_created_at as created_at, original_updated_at as updated_at
        FROM seed_views.v_agent_vendor_ct
        ORDER BY outreach_id, vendor_row_id
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      let seeded = 0;
      for (let i = 0; i < rows.rows.length; i += 50) {
        const chunk = rows.rows.slice(i, i + 50);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO vendor_ct (
              vendor_row_id, outreach_id, company_unique_id, domain,
              company_name, email_pattern, email_pattern_confidence,
              email_pattern_source, email_pattern_verified_at,
              company_phone, company_type, employee_count,
              industry, industry_normalized, description,
              city, state, country, postal_code,
              linkedin_url, facebook_url, twitter_url,
              ein, duns, source_system, enriched_by,
              data_quality_score, enriched_at, source_table,
              created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.vendor_row_id, r.outreach_id, r.company_unique_id, r.domain,
            r.company_name, r.email_pattern, r.email_pattern_confidence,
            r.email_pattern_source, ts(r.email_pattern_verified_at),
            r.company_phone, r.company_type, r.employee_count,
            r.industry, r.industry_normalized, r.description,
            r.city, r.state, r.country, r.postal_code,
            r.linkedin_url, r.facebook_url, r.twitter_url,
            r.ein, r.duns, r.source_system, r.enriched_by,
            r.data_quality_score, ts(r.enriched_at), r.source_table,
            ts(r.created_at), ts(r.updated_at),
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.vendor_ct = { seeded, total: rows.rows.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] vendor_ct: ${seeded} rows`);
    }

    // ── 12. slot_workbench (materialized view) ──────────────────
    // The master work order: one row per slot, all constants, readiness tier
    if (table === 'all' || table === 'workbench') {
      const rows = await pg.query(`
        SELECT
          slot_id, outreach_id, company_unique_id, slot_type,
          is_filled, person_unique_id,
          city, state, postal_code, industry, employees,
          service_agents, agent_count,
          company_name, company_domain, canonical_name,
          domain, ein, has_appointment,
          filing_present, funding_type, carrier, broker_or_advisor, renewal_month,
          about_url, blog_source_url,
          hunter_email_pattern, vendor_email_pattern, company_phone,
          person_first_name, person_last_name, person_full_name,
          person_email, person_email_verified, person_linkedin, person_source,
          hunter_contact_id, hunter_first_name, hunter_last_name,
          hunter_email, hunter_confidence, hunter_linkedin,
          hunter_phone, hunter_title,
          has_name, has_email, has_verified_email, has_linkedin,
          has_hunter_candidate, has_email_pattern,
          readiness_tier
        FROM seed_views.v_slot_workbench
        ORDER BY outreach_id, slot_type
        LIMIT $1 OFFSET $2
      `, [limit, offset]);

      // Deduplicate by slot_id (materialized view may have minor dupes from joins)
      const seen = new Set<string>();
      const deduped = rows.rows.filter((r: any) => {
        if (seen.has(r.slot_id)) return false;
        seen.add(r.slot_id);
        return true;
      });

      let seeded = 0;
      for (let i = 0; i < deduped.length; i += 25) {
        const chunk = deduped.slice(i, i + 25);
        const stmts = chunk.map((r: any) =>
          env.D1_OUTREACH.prepare(`
            INSERT OR REPLACE INTO slot_workbench (
              slot_id, outreach_id, company_unique_id, slot_type,
              is_filled, person_unique_id,
              city, state, postal_code, industry, employees,
              service_agents, agent_count,
              company_name, company_domain, canonical_name,
              domain, ein, has_appointment,
              filing_present, funding_type, carrier, broker_or_advisor, renewal_month,
              about_url, blog_source_url,
              hunter_email_pattern, vendor_email_pattern, company_phone,
              person_first_name, person_last_name, person_full_name,
              person_email, person_email_verified, person_linkedin, person_source,
              hunter_contact_id, hunter_first_name, hunter_last_name,
              hunter_email, hunter_confidence, hunter_linkedin,
              hunter_phone, hunter_title,
              has_name, has_email, has_verified_email, has_linkedin,
              has_hunter_candidate, has_email_pattern,
              readiness_tier
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          `).bind(
            r.slot_id, r.outreach_id, r.company_unique_id, r.slot_type,
            bool(r.is_filled), r.person_unique_id,
            r.city, r.state, r.postal_code, r.industry, r.employees,
            r.service_agents, r.agent_count,
            r.company_name, r.company_domain, r.canonical_name,
            r.domain, r.ein, bool(r.has_appointment),
            bool(r.filing_present), r.funding_type, r.carrier, r.broker_or_advisor, r.renewal_month,
            r.about_url, r.blog_source_url,
            r.hunter_email_pattern, r.vendor_email_pattern, r.company_phone,
            r.person_first_name, r.person_last_name, r.person_full_name,
            r.person_email, bool(r.person_email_verified), r.person_linkedin, r.person_source,
            r.hunter_contact_id, r.hunter_first_name, r.hunter_last_name,
            r.hunter_email, r.hunter_confidence, r.hunter_linkedin,
            r.hunter_phone, r.hunter_title,
            bool(r.has_name), bool(r.has_email), bool(r.has_verified_email), bool(r.has_linkedin),
            bool(r.has_hunter_candidate), bool(r.has_email_pattern),
            r.readiness_tier,
          )
        );
        await env.D1_OUTREACH.batch(stmts);
        seeded += chunk.length;
      }
      results.workbench = { seeded, total: deduped.length, has_more: rows.rows.length === limit };
      console.log(`[seedClean] workbench: ${seeded} rows`);
    }

    return {
      action: 'seedClean',
      table,
      batch: { limit, offset },
      results,
    };
  } finally {
    await pg.end();
  }
}

export async function seedGlobalZipCodes(env: Env): Promise<any> {
  const pg = getNeonClient(env);
  await pg.connect();

  let seeded = 0;
  const errors: string[] = [];

  try {
    // Create the table if it doesn't exist
    await env.D1_GLOBAL.prepare(`
      CREATE TABLE IF NOT EXISTS us_zip_codes (
        zip TEXT PRIMARY KEY,
        city TEXT,
        state_code TEXT,
        state_name TEXT,
        county TEXT,
        latitude REAL,
        longitude REAL,
        timezone TEXT,
        population INTEGER,
        seeded_at TEXT NOT NULL DEFAULT (datetime('now'))
      )
    `).run();

    // Check how many we already have
    const existing = await env.D1_GLOBAL.prepare(
      'SELECT COUNT(*) as c FROM us_zip_codes'
    ).first<{ c: number }>();

    if ((existing?.c ?? 0) > 40000) {
      return {
        action: 'seedGlobalZipCodes',
        status: 'already_seeded',
        existing_rows: existing?.c,
      };
    }

    // Get column info from Neon
    const colCheck = await pg.query(`
      SELECT column_name FROM information_schema.columns
      WHERE table_schema = 'reference' AND table_name = 'us_zip_codes'
      ORDER BY ordinal_position
    `);
    const columns = colCheck.rows.map((r: any) => r.column_name);
    console.log(`[seedGlobalZipCodes] Neon columns: ${columns.join(', ')}`);

    // Discover actual columns first
    const sampleRow = await pg.query(`SELECT * FROM reference.us_zip_codes LIMIT 1`);
    const availableCols = sampleRow.rows.length > 0 ? Object.keys(sampleRow.rows[0]) : [];
    console.log(`[seedGlobalZipCodes] Available columns: ${availableCols.join(', ')}`);

    // Map columns — handle variations in naming
    const colMap = {
      zip: availableCols.find(c => c === 'zip' || c === 'zipcode' || c === 'zip_code') || 'zip',
      city: availableCols.find(c => c === 'city' || c === 'primary_city') || 'city',
      state_code: availableCols.find(c => c === 'state_code' || c === 'state' || c === 'state_id') || 'state',
      state_name: availableCols.find(c => c === 'state_name' || c === 'state_full') || null,
      county: availableCols.find(c => c === 'county' || c === 'county_name') || null,
      latitude: availableCols.find(c => c === 'latitude' || c === 'lat') || null,
      longitude: availableCols.find(c => c === 'longitude' || c === 'lng' || c === 'lon') || null,
      timezone: availableCols.find(c => c === 'timezone' || c === 'tz') || null,
      population: availableCols.find(c => c === 'population' || c === 'estimated_population') || null,
    };
    console.log(`[seedGlobalZipCodes] Column mapping: ${JSON.stringify(colMap)}`);

    // Pull all ZIP codes from Neon using discovered columns
    const selectCols = Object.entries(colMap)
      .filter(([, v]) => v !== null)
      .map(([alias, col]) => col === alias ? col : `${col} as ${alias}`)
      .join(', ');

    const zips = await pg.query(`SELECT ${selectCols} FROM reference.us_zip_codes ORDER BY ${colMap.zip}`);

    console.log(`[seedGlobalZipCodes] ${zips.rows.length} ZIP codes from Neon`);

    // Batch insert into D1 (100 per batch)
    const batchSize = 100;
    for (let i = 0; i < zips.rows.length; i += batchSize) {
      const chunk = zips.rows.slice(i, i + batchSize);
      const statements: D1PreparedStatement[] = chunk.map((z: any) =>
        env.D1_GLOBAL.prepare(`
          INSERT OR REPLACE INTO us_zip_codes (
            zip, city, state_code, state_name, county,
            latitude, longitude, timezone, population
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `).bind(
          z.zip, z.city, z.state_code, z.state_name, z.county,
          z.latitude, z.longitude, z.timezone, z.population,
        )
      );

      try {
        await env.D1_GLOBAL.batch(statements);
        seeded += chunk.length;
      } catch (e) {
        errors.push(`batch ${i}: ${e instanceof Error ? e.message : String(e)}`);
      }

      if ((i + batchSize) % 5000 === 0) {
        console.log(`[seedGlobalZipCodes] Progress: ${Math.min(i + batchSize, zips.rows.length)}/${zips.rows.length}`);
      }
    }

    return {
      action: 'seedGlobalZipCodes',
      neon_rows: zips.rows.length,
      seeded,
      errors: errors.length,
      error_details: errors.slice(0, 20),
    };
  } finally {
    await pg.end();
  }
}
