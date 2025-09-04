#!/usr/bin/env node

/**
 * Set up Marketing Schema - Campaign tracking and handoff system
 * Creates marketing.campaign, campaign_contact, message_log, booking_event, ac_handoff
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function setupMarketingSchema() {
  console.log('📧 Setting up Marketing Schema in Neon...\n');
  
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
    
    // Step 1: Create marketing schema
    console.log('1️⃣ Creating marketing schema...');
    await sql`CREATE SCHEMA IF NOT EXISTS marketing`;
    console.log('   ✅ marketing schema created');
    
    // Step 2: Create campaign table
    console.log('2️⃣ Creating marketing.campaign table...');
    await sql`
      CREATE TABLE IF NOT EXISTS marketing.campaign (
        campaign_id BIGSERIAL PRIMARY KEY,
        name        TEXT,
        created_at  TIMESTAMPTZ DEFAULT NOW()
      )
    `;
    console.log('   ✅ marketing.campaign table created');
    
    // Step 3: Create campaign_contact junction table
    console.log('3️⃣ Creating marketing.campaign_contact table...');
    await sql`
      CREATE TABLE IF NOT EXISTS marketing.campaign_contact (
        campaign_contact_id BIGSERIAL PRIMARY KEY,
        campaign_id BIGINT REFERENCES marketing.campaign(campaign_id) ON DELETE CASCADE,
        contact_id  BIGINT REFERENCES people.contact(contact_id) ON DELETE CASCADE,
        created_at  TIMESTAMPTZ DEFAULT NOW()
      )
    `;
    console.log('   ✅ marketing.campaign_contact table created');
    console.log('   🔗 Links campaigns to contacts with cascade deletes');
    
    // Step 4: Create message_log table
    console.log('4️⃣ Creating marketing.message_log table...');
    await sql`
      CREATE TABLE IF NOT EXISTS marketing.message_log (
        message_id  BIGSERIAL PRIMARY KEY,
        campaign_id BIGINT REFERENCES marketing.campaign(campaign_id) ON DELETE SET NULL,
        contact_id  BIGINT REFERENCES people.contact(contact_id) ON DELETE CASCADE,
        status      TEXT,     -- 'sent'|'bounced'|'replied' (future use)
        created_at  TIMESTAMPTZ DEFAULT NOW()
      )
    `;
    console.log('   ✅ marketing.message_log table created');
    console.log('   📨 Tracks message status: sent|bounced|replied');
    
    // Step 5: Create booking_event table (handoff trigger)
    console.log('5️⃣ Creating marketing.booking_event table...');
    await sql`
      CREATE TABLE IF NOT EXISTS marketing.booking_event (
        booking_event_id BIGSERIAL PRIMARY KEY,
        company_id  BIGINT REFERENCES company.company(company_id) ON DELETE SET NULL,
        contact_id  BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
        calley_ref  TEXT,
        created_at  TIMESTAMPTZ DEFAULT NOW()
      )
    `;
    console.log('   ✅ marketing.booking_event table created');
    console.log('   📅 Tracks booking events that trigger handoffs');
    
    // Step 6: Create ac_handoff table
    console.log('6️⃣ Creating marketing.ac_handoff table...');
    await sql`
      CREATE TABLE IF NOT EXISTS marketing.ac_handoff (
        ac_handoff_id     BIGSERIAL PRIMARY KEY,
        booking_event_id  BIGINT REFERENCES marketing.booking_event(booking_event_id) ON DELETE CASCADE,
        created_at        TIMESTAMPTZ DEFAULT NOW()
      )
    `;
    console.log('   ✅ marketing.ac_handoff table created');
    console.log('   🤝 Tracks handoffs from cold outreach to account management');
    
    // Step 7: Create helpful indexes for performance
    console.log('7️⃣ Creating performance indexes...');
    await sql`CREATE INDEX IF NOT EXISTS ix_campaign_contact_campaign ON marketing.campaign_contact(campaign_id)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_campaign_contact_contact ON marketing.campaign_contact(contact_id)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_message_log_campaign ON marketing.message_log(campaign_id)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_message_log_contact ON marketing.message_log(contact_id)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_message_log_status ON marketing.message_log(status)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_booking_event_company ON marketing.booking_event(company_id)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_booking_event_contact ON marketing.booking_event(contact_id)`;
    await sql`CREATE INDEX IF NOT EXISTS ix_ac_handoff_booking ON marketing.ac_handoff(booking_event_id)`;
    console.log('   ✅ Performance indexes created');
    
    // Step 8: Create test data to demonstrate the workflow
    console.log('8️⃣ Creating test marketing workflow...');
    
    // Create a test campaign
    const testCampaign = await sql`
      INSERT INTO marketing.campaign (name) 
      VALUES ('Q1 2025 Outreach Campaign')
      RETURNING campaign_id, name
    `;
    console.log(`   ✅ Test campaign created: ${testCampaign[0].name} (ID: ${testCampaign[0].campaign_id})`);
    
    // Get some test contacts to add to campaign
    const testContacts = await sql`
      SELECT contact_id, full_name, email 
      FROM people.contact 
      WHERE email IS NOT NULL 
      LIMIT 3
    `;
    
    if (testContacts.length > 0) {
      // Add contacts to campaign
      for (const contact of testContacts) {
        await sql`
          INSERT INTO marketing.campaign_contact (campaign_id, contact_id)
          VALUES (${testCampaign[0].campaign_id}, ${contact.contact_id})
        `;
      }
      console.log(`   ✅ Added ${testContacts.length} contacts to campaign`);
      
      // Create some message logs
      const messageStatuses = ['sent', 'sent', 'replied'];
      for (let i = 0; i < testContacts.length; i++) {
        await sql`
          INSERT INTO marketing.message_log (campaign_id, contact_id, status)
          VALUES (
            ${testCampaign[0].campaign_id}, 
            ${testContacts[i].contact_id}, 
            ${messageStatuses[i]}
          )
        `;
      }
      console.log('   ✅ Created message logs with different statuses');
      
      // Create booking event for the contact who replied
      const repliedContact = testContacts[2]; // The one with 'replied' status
      const companies = await sql`SELECT company_id FROM company.company LIMIT 1`;
      
      if (companies.length > 0) {
        const bookingEvent = await sql`
          INSERT INTO marketing.booking_event (company_id, contact_id, calley_ref)
          VALUES (
            ${companies[0].company_id}, 
            ${repliedContact.contact_id}, 
            'CAL-2025-001'
          )
          RETURNING booking_event_id
        `;
        
        // Create handoff record
        await sql`
          INSERT INTO marketing.ac_handoff (booking_event_id)
          VALUES (${bookingEvent[0].booking_event_id})
        `;
        
        console.log(`   ✅ Created booking event and handoff for ${repliedContact.full_name}`);
      }
    }
    
    // Step 9: Demonstrate the complete workflow with a query
    console.log('9️⃣ Testing complete marketing workflow...');
    const workflowTest = await sql`
      SELECT 
        camp.name AS campaign_name,
        c.full_name AS contact_name,
        c.email,
        cv.email_status AS dot_color,
        ml.status AS message_status,
        CASE WHEN be.booking_event_id IS NOT NULL THEN 'Booked' ELSE 'In Campaign' END AS stage,
        CASE WHEN ah.ac_handoff_id IS NOT NULL THEN 'Handed Off' ELSE 'Cold Outreach' END AS handoff_status
      FROM marketing.campaign camp
      JOIN marketing.campaign_contact cc ON camp.campaign_id = cc.campaign_id
      JOIN people.contact c ON cc.contact_id = c.contact_id
      LEFT JOIN people.contact_verification cv ON c.contact_id = cv.contact_id
      LEFT JOIN marketing.message_log ml ON camp.campaign_id = ml.campaign_id AND c.contact_id = ml.contact_id
      LEFT JOIN marketing.booking_event be ON c.contact_id = be.contact_id
      LEFT JOIN marketing.ac_handoff ah ON be.booking_event_id = ah.booking_event_id
      WHERE camp.name = 'Q1 2025 Outreach Campaign'
      ORDER BY c.full_name
    `;
    
    console.log('\n📊 Complete Marketing Workflow Test:');
    workflowTest.forEach(w => {
      console.log(`   📧 ${w.contact_name} (${w.email})`);
      console.log(`      Campaign: ${w.campaign_name}`);
      console.log(`      Email Status: ${w.dot_color || 'unknown'} dot`);
      console.log(`      Message: ${w.message_status || 'not sent'}`);
      console.log(`      Stage: ${w.stage}`);
      console.log(`      Status: ${w.handoff_status}`);
      console.log('');
    });
    
    console.log('🎉 Marketing Schema Setup Complete!');
    console.log('\n📋 Marketing Schema Structure:');
    console.log('✅ marketing.campaign:');
    console.log('   • campaign_id, name, created_at');
    console.log('');
    console.log('✅ marketing.campaign_contact:');
    console.log('   • Links campaigns to contacts (many-to-many)');
    console.log('   • CASCADE DELETE on both campaign and contact');
    console.log('');
    console.log('✅ marketing.message_log:');
    console.log('   • Tracks message status: sent|bounced|replied');
    console.log('   • Links to campaign (SET NULL) and contact (CASCADE)');
    console.log('');
    console.log('✅ marketing.booking_event:');
    console.log('   • Triggers handoff from cold outreach');
    console.log('   • Links to company and contact (SET NULL)');
    console.log('   • Includes calley_ref for booking system integration');
    console.log('');
    console.log('✅ marketing.ac_handoff:');
    console.log('   • Tracks successful handoffs to account management');
    console.log('   • Links to booking_event (CASCADE DELETE)');
    console.log('');
    console.log('🎯 Complete Marketing Pipeline:');
    console.log('   1. Create Campaign');
    console.log('   2. Add Contacts to Campaign');
    console.log('   3. Send Messages (track in message_log)');
    console.log('   4. Contact Replies → Booking Event');
    console.log('   5. Booking Event → AC Handoff');
    console.log('   6. Exit from cold outreach system');
    console.log('\n✅ Ready for marketing campaign management!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify user has CREATE permissions');
    console.log('   • Ensure people.contact table exists');
  }
}

setupMarketingSchema().catch(console.error);