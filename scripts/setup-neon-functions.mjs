#!/usr/bin/env node

/**
 * Setup Neon SECURITY DEFINER Functions
 * Creates secure functions for MCP integration with existing marketing schema
 */

import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';
import fs from 'fs';

// Load environment variables
dotenv.config();

async function setupNeonFunctions() {
  console.log('🔧 Setting up Neon SECURITY DEFINER functions...\n');
  
  try {
    // Get connection string
    const connectionString = 
      process.env.NEON_DATABASE_URL ||
      process.env.DATABASE_URL;
    
    if (!connectionString) {
      console.error('❌ No database connection string found.');
      return;
    }
    
    const sql = neon(connectionString);
    
    console.log('📡 Connected to Neon database');
    console.log(`🗄️  Database: ${connectionString.split('@')[1].split('/')[1].split('?')[0]}`);
    console.log('');
    
    // Create intake schema if not exists
    console.log('1️⃣ Creating intake schema...');
    await sql`
      CREATE SCHEMA IF NOT EXISTS intake;
    `;
    console.log('   ✅ intake schema ready');
    
    // Create vault schema if not exists  
    console.log('2️⃣ Creating vault schema...');
    await sql`
      CREATE SCHEMA IF NOT EXISTS vault;
    `;
    console.log('   ✅ vault schema ready');
    
    // Create raw_loads table in intake schema
    console.log('3️⃣ Creating intake.raw_loads table...');
    await sql`
      CREATE TABLE IF NOT EXISTS intake.raw_loads (
        load_id BIGSERIAL PRIMARY KEY,
        batch_id TEXT NOT NULL,
        source TEXT NOT NULL,
        raw_data JSONB NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        promoted_at TIMESTAMP WITH TIME ZONE,
        error_message TEXT,
        unique_id TEXT,
        process_id TEXT,
        blueprint_version_hash TEXT
      );
    `;
    console.log('   ✅ raw_loads table ready');
    
    // Create promotion tracking table
    console.log('4️⃣ Creating vault.contact_promotions table...');
    await sql`
      CREATE TABLE IF NOT EXISTS vault.contact_promotions (
        promotion_id BIGSERIAL PRIMARY KEY,
        load_id BIGINT,
        person_id UUID,
        company_id UUID,
        promotion_type TEXT DEFAULT 'contact',
        status TEXT DEFAULT 'success',
        promoted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        error_message TEXT,
        unique_id TEXT,
        process_id TEXT,
        blueprint_version_hash TEXT
      );
    `;
    console.log('   ✅ contact_promotions table ready');
    
    // Create roles for MCP operations
    console.log('5️⃣ Creating MCP roles...');
    try {
      await sql`CREATE ROLE mcp_ingest`;
      console.log('   ✅ mcp_ingest role created');
    } catch (error) {
      if (error.message.includes('already exists')) {
        console.log('   ℹ️  mcp_ingest role already exists');
      } else {
        console.log(`   ⚠️  mcp_ingest role creation: ${error.message}`);
      }
    }
    
    try {
      await sql`CREATE ROLE mcp_promote`;
      console.log('   ✅ mcp_promote role created');
    } catch (error) {
      if (error.message.includes('already exists')) {
        console.log('   ℹ️  mcp_promote role already exists');
      } else {
        console.log(`   ⚠️  mcp_promote role creation: ${error.message}`);
      }
    }
    
    // Create secure ingestion function
    console.log('6️⃣ Creating secure ingestion function...');
    await sql`
      CREATE OR REPLACE FUNCTION intake.f_ingest_json(
        p_rows JSONB[],
        p_source TEXT,
        p_batch_id TEXT DEFAULT NULL
      )
      RETURNS TABLE(
        load_id BIGINT,
        batch_id TEXT,
        status TEXT
      )
      LANGUAGE plpgsql
      SECURITY DEFINER
      SET search_path = intake, vault, people, company
      AS $$
      DECLARE
        v_batch_id TEXT;
        v_row JSONB;
        v_load_id BIGINT;
        v_result_count INT := 0;
      BEGIN
        -- Generate batch ID if not provided
        v_batch_id := COALESCE(p_batch_id, 'batch_' || EXTRACT(epoch FROM NOW()) || '_' || substring(md5(random()::text) from 1 for 8));
        
        -- Insert each row
        FOREACH v_row IN ARRAY p_rows
        LOOP
          INSERT INTO intake.raw_loads (
            batch_id,
            source,
            raw_data,
            status,
            created_at
          ) VALUES (
            v_batch_id,
            p_source,
            v_row,
            'pending',
            NOW()
          ) RETURNING intake.raw_loads.load_id INTO v_load_id;
          
          v_result_count := v_result_count + 1;
          
          RETURN QUERY SELECT v_load_id, v_batch_id, 'ingested'::TEXT;
        END LOOP;
        
        RAISE NOTICE 'Ingested % rows with batch_id: %', v_result_count, v_batch_id;
      END;
      $$;
    `;
    console.log('   ✅ f_ingest_json function created');
    
    // Create secure promotion function
    console.log('7️⃣ Creating secure promotion function...');
    await sql`
      CREATE OR REPLACE FUNCTION vault.f_promote_contacts(
        p_load_ids BIGINT[] DEFAULT NULL
      )
      RETURNS TABLE(
        promoted_count INTEGER,
        updated_count INTEGER,
        failed_count INTEGER,
        message TEXT
      )
      LANGUAGE plpgsql
      SECURITY DEFINER
      SET search_path = vault, intake, people, company
      AS $$
      DECLARE
        v_load RECORD;
        v_data JSONB;
        v_person_id UUID;
        v_company_id UUID;
        v_promoted_count INT := 0;
        v_updated_count INT := 0;
        v_failed_count INT := 0;
      BEGIN
        -- Select loads to promote
        FOR v_load IN 
          SELECT load_id, raw_data, batch_id, source
          FROM intake.raw_loads 
          WHERE status = 'pending'
            AND (p_load_ids IS NULL OR load_id = ANY(p_load_ids))
        LOOP
          BEGIN
            v_data := v_load.raw_data;
            
            -- Find or create company
            SELECT id INTO v_company_id 
            FROM company.marketing_company 
            WHERE company_name = v_data->>'company_name' 
            LIMIT 1;
            
            IF v_company_id IS NULL AND v_data->>'company_name' IS NOT NULL THEN
              INSERT INTO company.marketing_company (
                external_id,
                company_name,
                industry,
                domain,
                linkedin_url,
                created_at,
                source
              ) VALUES (
                v_data->>'external_id',
                v_data->>'company_name',
                v_data->>'industry',
                v_data->>'domain',
                v_data->>'linkedin_url',
                NOW(),
                v_load.source
              ) RETURNING id INTO v_company_id;
            END IF;
            
            -- Insert or update person
            INSERT INTO people.marketing_people (
              external_id,
              company_id,
              first_name,
              last_name,
              full_name,
              email,
              phone,
              title,
              linkedin_url,
              source,
              created_at,
              custom_fields
            ) VALUES (
              v_data->>'external_id',
              v_company_id,
              v_data->>'first_name',
              v_data->>'last_name',
              COALESCE(v_data->>'full_name', CONCAT(v_data->>'first_name', ' ', v_data->>'last_name')),
              v_data->>'email',
              v_data->>'phone',
              v_data->>'title',
              v_data->>'linkedin_url',
              v_load.source,
              NOW(),
              v_data
            ) 
            ON CONFLICT (email) DO UPDATE SET
              first_name = COALESCE(EXCLUDED.first_name, marketing_people.first_name),
              last_name = COALESCE(EXCLUDED.last_name, marketing_people.last_name),
              phone = COALESCE(EXCLUDED.phone, marketing_people.phone),
              title = COALESCE(EXCLUDED.title, marketing_people.title),
              linkedin_url = COALESCE(EXCLUDED.linkedin_url, marketing_people.linkedin_url),
              company_id = COALESCE(EXCLUDED.company_id, marketing_people.company_id),
              custom_fields = EXCLUDED.custom_fields,
              updated_at = NOW()
            RETURNING id INTO v_person_id;
            
            -- Record promotion
            INSERT INTO vault.contact_promotions (
              load_id,
              person_id,
              company_id,
              promotion_type,
              status,
              promoted_at
            ) VALUES (
              v_load.load_id,
              v_person_id,
              v_company_id,
              'contact',
              'success',
              NOW()
            );
            
            -- Mark load as promoted
            UPDATE intake.raw_loads 
            SET status = 'promoted', promoted_at = NOW()
            WHERE load_id = v_load.load_id;
            
            v_promoted_count := v_promoted_count + 1;
            
          EXCEPTION WHEN OTHERS THEN
            -- Record failure
            UPDATE intake.raw_loads 
            SET status = 'failed', error_message = SQLERRM
            WHERE load_id = v_load.load_id;
            
            v_failed_count := v_failed_count + 1;
          END;
        END LOOP;
        
        RETURN QUERY SELECT 
          v_promoted_count,
          v_updated_count,
          v_failed_count,
          format('Promoted: %s, Updated: %s, Failed: %s', v_promoted_count, v_updated_count, v_failed_count);
      END;
      $$;
    `;
    console.log('   ✅ f_promote_contacts function created');
    
    // Grant permissions
    console.log('8️⃣ Setting up permissions...');
    try {
      await sql`GRANT USAGE ON SCHEMA intake TO mcp_ingest`;
      await sql`GRANT USAGE ON SCHEMA vault TO mcp_promote`;
      await sql`GRANT EXECUTE ON FUNCTION intake.f_ingest_json TO mcp_ingest`;
      await sql`GRANT EXECUTE ON FUNCTION vault.f_promote_contacts TO mcp_promote`;
      console.log('   ✅ Permissions granted to MCP roles');
    } catch (error) {
      console.log(`   ⚠️  Permission setup: ${error.message}`);
    }
    
    console.log('\n🎉 Neon SECURITY DEFINER functions setup complete!');
    console.log('\n📋 Created Functions:');
    console.log('   • intake.f_ingest_json() - Secure data ingestion');
    console.log('   • vault.f_promote_contacts() - Secure data promotion');
    console.log('\n🔐 Security Features:');
    console.log('   • SECURITY DEFINER functions for safe MCP operations');
    console.log('   • Role-based access control (mcp_ingest, mcp_promote)');
    console.log('   • Integration with existing marketing_people and marketing_company tables');
    console.log('\n✅ Ready for Composio MCP integration!');
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('   • Check database connection string');
    console.log('   • Verify user has CREATE permissions');
    console.log('   • Ensure database exists and is accessible');
  }
}

// Run the setup
setupNeonFunctions().catch(console.error);