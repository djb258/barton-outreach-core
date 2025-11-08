-- Create company_invalid table
CREATE TABLE IF NOT EXISTS marketing.company_invalid (
  id BIGSERIAL PRIMARY KEY,
  company_unique_id TEXT UNIQUE NOT NULL,
  company_name TEXT,
  domain TEXT,
  industry TEXT,
  employee_count INTEGER,
  website TEXT,
  phone TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  validation_status TEXT DEFAULT 'FAILED',
  reason_code TEXT NOT NULL,
  validation_errors JSONB NOT NULL,
  validation_warnings JSONB,
  failed_at TIMESTAMP DEFAULT now(),
  reviewed BOOLEAN DEFAULT false,
  batch_id TEXT,
  source_table TEXT DEFAULT 'marketing.company_raw_wv',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Create people_invalid table
CREATE TABLE IF NOT EXISTS marketing.people_invalid (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,
  full_name TEXT,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  phone TEXT,
  title TEXT,
  company_name TEXT,
  company_unique_id TEXT,
  linkedin_url TEXT,
  city TEXT,
  state TEXT,
  validation_status TEXT DEFAULT 'FAILED',
  reason_code TEXT NOT NULL,
  validation_errors JSONB NOT NULL,
  validation_warnings JSONB,
  failed_at TIMESTAMP DEFAULT now(),
  reviewed BOOLEAN DEFAULT false,
  batch_id TEXT,
  source_table TEXT DEFAULT 'marketing.people_raw_wv',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Verification
SELECT 'company_invalid' as table_name, COUNT(*) as row_count FROM marketing.company_invalid
UNION ALL
SELECT 'people_invalid', COUNT(*) FROM marketing.people_invalid;
