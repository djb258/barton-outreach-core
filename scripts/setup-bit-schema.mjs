#!/usr/bin/env node

/**
 * Set up BIT (Business Intelligence Trigger) Schema
 * Creates bit.signal table for tracking important business events and triggers
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function setupBitSchema() {
  console.log('📊 Setting up BIT (Business Intelligence Trigger) Schema in Neon...\n');
  
  try {
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    if (!connectionString) {
      console.error('❌ No database connection string found.');
      return;
    }
    
    const sql = neon(connectionString);
    
    console.log('📡 Connected to Neon database');
    console.log('');
    
    // Step 1: Create bit schema
    console.log('1️⃣ Creating bit schema...');
    await sql`CREATE SCHEMA IF NOT EXISTS bit`;
    console.log('   ✅ bit schema created');
    
    // Step 2: Create bit.signal table
    console.log('2️⃣ Creating bit.signal table...');
    await sql`
      CREATE TABLE IF NOT EXISTS bit.signal (
        signal_id    BIGSERIAL PRIMARY KEY,
        company_id   BIGINT REFERENCES company.company(company_id) ON DELETE CASCADE,
        reason       TEXT NOT NULL,      -- 'renewal_window_open_120d' | 'executive_movement' | ...
        payload      JSONB,              -- compact blob with evidence
        created_at   TIMESTAMPTZ DEFAULT NOW(),
        processed_at TIMESTAMPTZ
      )
    `;
    console.log('   ✅ bit.signal table created');
    console.log('   🔔 Tracks business intelligence triggers and events');
    
    // Step 3: Create performance index
    console.log('3️⃣ Creating performance index...');
    await sql`CREATE INDEX IF NOT EXISTS ix_bit_signal_unprocessed ON bit.signal(processed_at)`;
    console.log('   ✅ Index created: ix_bit_signal_unprocessed');
    console.log('   ⚡ Fast queries for unprocessed signals');
    
    // Step 4: Create additional helpful indexes
    console.log('4️⃣ Creating additional indexes...');
    await sql`CREATE INDEX IF NOT EXISTS ix_bit_signal_company ON bit.signal(company_id)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_bit_signal_reason ON bit.signal(reason)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_bit_signal_created ON bit.signal(created_at DESC)`;
    console.log('   ✅ Additional indexes created for performance');
    
    // Step 5: Create test signals to demonstrate the system
    console.log('5️⃣ Creating test business intelligence signals...');
    
    // Get test company for signals
    const companies = await sql`SELECT company_id, company_name, renewal_month FROM company.company LIMIT 1`;
    
    if (companies.length > 0) {
      const company = companies[0];
      
      // Create different types of signals
      const testSignals = [
        {
          reason: 'renewal_window_open_120d',
          payload: {
            renewal_month: company.renewal_month,
            notice_window_days: 120,
            current_month: new Date().getMonth() + 1,
            days_until_renewal: 45,
            contract_value: 250000,
            risk_score: 'medium'
          }
        },
        {
          reason: 'executive_movement',
          payload: {
            previous_ceo: 'John CEO Smith',
            new_ceo: 'Jane New Executive',
            movement_date: new Date().toISOString(),
            source: 'linkedin_tracking',
            confidence: 0.92
          }
        },
        {
          reason: 'booking_event_scheduled',
          payload: {
            contact_name: 'Bob HR Wilson',
            booking_type: 'discovery_call',
            scheduled_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            calley_ref: 'CAL-2025-001',
            priority: 'high'
          }
        },
        {
          reason: 'campaign_engagement_spike',
          payload: {
            campaign_name: 'Q1 2025 Outreach Campaign',
            engagement_increase: 0.35,
            reply_rate: 0.18,
            previous_reply_rate: 0.05,
            trigger_threshold: 0.15,
            contacts_engaged: 12
          }
        }
      ];
      
      for (const signal of testSignals) {
        await sql`
          INSERT INTO bit.signal (company_id, reason, payload)
          VALUES (${company.company_id}, ${signal.reason}, ${JSON.stringify(signal.payload)})
        `;
      }
      
      console.log(`   ✅ Created ${testSignals.length} test signals for ${company.company_name}`);
    }
    
    // Step 6: Demonstrate signal processing workflow
    console.log('6️⃣ Testing signal processing workflow...');
    
    // Query unprocessed signals
    const unprocessedSignals = await sql`
      SELECT signal_id, company_id, reason, payload, created_at
      FROM bit.signal 
      WHERE processed_at IS NULL
      ORDER BY created_at ASC
    `;
    
    console.log(`   📋 Found ${unprocessedSignals.length} unprocessed signals:`);
    
    unprocessedSignals.forEach((signal, i) => {
      console.log(`      ${i + 1}. ${signal.reason}`);
      console.log(`         Company ID: ${signal.company_id}`);
      console.log(`         Created: ${new Date(signal.created_at).toLocaleDateString()}`);
      console.log(`         Signal ID: ${signal.signal_id}`);
      
      // Show sample payload data
      const payload = signal.payload;
      if (payload) {
        const keys = Object.keys(payload).slice(0, 3); // Show first 3 keys
        keys.forEach(key => {
          console.log(`         ${key}: ${payload[key]}`);
        });
        if (Object.keys(payload).length > 3) {
          console.log(`         ... ${Object.keys(payload).length - 3} more fields`);
        }
      }
      console.log('');
    });
    
    // Mark first signal as processed to demonstrate
    if (unprocessedSignals.length > 0) {
      await sql`
        UPDATE bit.signal 
        SET processed_at = NOW() 
        WHERE signal_id = ${unprocessedSignals[0].signal_id}
      `;
      console.log(`   ✅ Marked signal ${unprocessedSignals[0].signal_id} (${unprocessedSignals[0].reason}) as processed`);
    }
    
    // Step 7: Create a comprehensive signal overview query
    console.log('7️⃣ Creating signal analytics overview...');
    const signalOverview = await sql`
      SELECT 
        comp.company_name,
        s.reason,
        s.signal_id,
        s.created_at,
        CASE WHEN s.processed_at IS NOT NULL THEN 'Processed' ELSE 'Pending' END AS status,
        s.processed_at
      FROM bit.signal s
      JOIN company.company comp ON s.company_id = comp.company_id
      ORDER BY s.created_at DESC
    `;
    
    console.log('\n📊 Complete Signal Analytics Overview:');
    signalOverview.forEach(overview => {
      console.log(`   🔔 ${overview.reason}`);
      console.log(`      Company: ${overview.company_name}`);
      console.log(`      Status: ${overview.status}`);
      console.log(`      Created: ${new Date(overview.created_at).toLocaleString()}`);
      if (overview.processed_at) {
        console.log(`      Processed: ${new Date(overview.processed_at).toLocaleString()}`);
      }
      console.log('');
    });
    
    console.log('🎉 BIT Schema Setup Complete!');
    console.log('\n📋 BIT Schema Structure:');
    console.log('✅ bit.signal:');
    console.log('   • signal_id (BIGSERIAL PRIMARY KEY)');
    console.log('   • company_id → company.company(company_id) CASCADE DELETE');
    console.log('   • reason (TEXT NOT NULL) - signal type identifier');
    console.log('   • payload (JSONB) - flexible evidence/data blob');
    console.log('   • created_at, processed_at (TIMESTAMPTZ)');
    console.log('');
    console.log('✅ Performance Indexes:');
    console.log('   • ix_bit_signal_unprocessed on (processed_at) - fast unprocessed queries');
    console.log('   • ix_bit_signal_company on (company_id) - company-specific signals');
    console.log('   • ix_bit_signal_reason on (reason) - signal type filtering');
    console.log('   • ix_bit_signal_created on (created_at DESC) - chronological queries');
    console.log('');
    console.log('🎯 Common Signal Types:');
    console.log('   • renewal_window_open_120d - Contract renewal opportunities');
    console.log('   • executive_movement - Leadership changes');
    console.log('   • booking_event_scheduled - Meeting bookings');
    console.log('   • campaign_engagement_spike - Campaign performance triggers');
    console.log('   • company_growth_signal - Business expansion indicators');
    console.log('   • competitive_threat - Competitor activity');
    console.log('');
    console.log('🔄 Processing Workflow:');
    console.log('   1. Signals generated automatically by triggers/events');
    console.log('   2. Query unprocessed signals: WHERE processed_at IS NULL');
    console.log('   3. Process signal (take action, send alert, etc.)');
    console.log('   4. Mark as processed: UPDATE SET processed_at = NOW()');
    console.log('\n✅ Ready for business intelligence signal processing!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify user has CREATE permissions');
    console.log('   • Ensure company.company table exists');
  }
}

setupBitSchema().catch(console.error);