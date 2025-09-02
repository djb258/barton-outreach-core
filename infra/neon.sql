-- Barton Outreach Core - Neon PostgreSQL Schema
-- This file will contain the database schema provided by the user

-- Placeholder schema structure
-- TODO: Replace with actual Neon schema when provided

-- Example staging table for data ingestion
-- CREATE TABLE IF NOT EXISTS staged_data (
--   id SERIAL PRIMARY KEY,
--   batch_id VARCHAR(255) NOT NULL,
--   source VARCHAR(100) NOT NULL DEFAULT 'unknown',
--   raw_data JSONB NOT NULL,
--   promoted BOOLEAN DEFAULT FALSE,
--   created_at TIMESTAMP DEFAULT NOW(),
--   updated_at TIMESTAMP DEFAULT NOW()
-- );

-- Example contacts table for promoted data
-- CREATE TABLE IF NOT EXISTS contacts (
--   id SERIAL PRIMARY KEY,
--   email VARCHAR(255) UNIQUE,
--   name VARCHAR(255),
--   phone VARCHAR(50),
--   company VARCHAR(255),
--   title VARCHAR(255),
--   source VARCHAR(100) NOT NULL DEFAULT 'unknown',
--   tags JSONB,
--   custom_fields JSONB,
--   created_at TIMESTAMP DEFAULT NOW(),
--   updated_at TIMESTAMP DEFAULT NOW()
-- );

-- Indexes for performance
-- CREATE INDEX IF NOT EXISTS idx_staged_data_batch_id ON staged_data(batch_id);
-- CREATE INDEX IF NOT EXISTS idx_staged_data_source ON staged_data(source);
-- CREATE INDEX IF NOT EXISTS idx_staged_data_promoted ON staged_data(promoted);
-- CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
-- CREATE INDEX IF NOT EXISTS idx_contacts_source ON contacts(source);
-- CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at);

-- User will provide the actual schema here