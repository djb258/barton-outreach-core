-- ============================================================================
-- Create Sample West Virginia Data for Validation
-- ============================================================================

-- Create company_raw_wv table with sample data
CREATE TABLE IF NOT EXISTS marketing.company_raw_wv (
  company_unique_id TEXT PRIMARY KEY,
  company_name TEXT,
  domain TEXT,
  website TEXT,
  industry TEXT,
  employee_count INTEGER,
  phone TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  created_at TIMESTAMP DEFAULT now()
);

-- Create people_raw_wv table with sample data
CREATE TABLE IF NOT EXISTS marketing.people_raw_wv (
  unique_id TEXT PRIMARY KEY,
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
  created_at TIMESTAMP DEFAULT now()
);

-- Insert sample company data (mix of valid and invalid)
INSERT INTO marketing.company_raw_wv (company_unique_id, company_name, domain, website, industry, employee_count, phone, address, city, state, zip)
VALUES
  -- Valid companies
  ('04.04.02.04.30000.001', 'West Virginia Mining Co', 'wvmining.com', 'https://wvmining.com', 'Mining', 250, '304-555-0101', '123 Coal St', 'Charleston', 'WV', '25301'),
  ('04.04.02.04.30000.002', 'Mountaineer Manufacturing', 'mountaineermfg.com', 'https://mountaineermfg.com', 'Manufacturing', 150, '304-555-0102', '456 Industrial Blvd', 'Huntington', 'WV', '25701'),
  ('04.04.02.04.30000.003', 'WV Tech Solutions', 'wvtech.io', 'https://wvtech.io', 'Technology', 75, '304-555-0103', '789 Innovation Dr', 'Morgantown', 'WV', '26501'),
  ('04.04.02.04.30000.004', 'Appalachian Energy LLC', 'appalachianenergy.com', 'https://appalachianenergy.com', 'Energy', 500, '304-555-0104', '321 Power Plant Rd', 'Charleston', 'WV', '25302'),
  ('04.04.02.04.30000.005', 'Valley Healthcare Services', 'valleyhealthwv.org', 'https://valleyhealthwv.org', 'Healthcare', 300, '304-555-0105', '654 Medical Center Dr', 'Parkersburg', 'WV', '26101'),

  -- Invalid companies (will fail validation)
  ('04.04.02.04.30000.006', '', 'invalid', '', 'Technology', 0, 'invalid-phone', '', 'Charleston', 'WV', '25301'),  -- Empty name
  ('04.04.02.04.30000.007', 'Test Company', 'test.com', '', 'Manufacturing', -10, '', '', 'Huntington', 'WV', '25701'),  -- Invalid domain, negative employees
  ('04.04.02.04.30000.008', 'Example Inc', 'example.com', '', 'Services', 0, '', '', 'Morgantown', 'WV', '26501'),  -- Invalid domain (example.com)
  ('04.04.02.04.30000.009', 'n/a', 'n/a', '', 'Unknown', 0, '', '', 'Charleston', 'WV', '25302'),  -- Invalid name
  ('04.04.02.04.30000.010', 'Short Name X', 'verylongdomainnamethatshouldnotbevalid', '', 'Technology', 0, '', '', 'Parkersburg', 'WV', '26101')  -- Invalid domain format
ON CONFLICT (company_unique_id) DO NOTHING;

-- Insert sample people data (mix of valid and invalid)
INSERT INTO marketing.people_raw_wv (unique_id, full_name, first_name, last_name, email, phone, title, company_name, company_unique_id, linkedin_url, city, state)
VALUES
  -- Valid people
  ('04.04.02.04.20000.001', 'John Smith', 'John', 'Smith', 'john.smith@wvmining.com', '304-555-1001', 'CEO', 'West Virginia Mining Co', '04.04.02.04.30000.001', 'https://linkedin.com/in/johnsmith', 'Charleston', 'WV'),
  ('04.04.02.04.20000.002', 'Sarah Johnson', 'Sarah', 'Johnson', 'sarah.johnson@mountaineermfg.com', '304-555-1002', 'CFO', 'Mountaineer Manufacturing', '04.04.02.04.30000.002', 'https://linkedin.com/in/sarahjohnson', 'Huntington', 'WV'),
  ('04.04.02.04.20000.003', 'Michael Williams', 'Michael', 'Williams', 'michael.williams@wvtech.io', '304-555-1003', 'CTO', 'WV Tech Solutions', '04.04.02.04.30000.003', 'https://linkedin.com/in/michaelwilliams', 'Morgantown', 'WV'),
  ('04.04.02.04.20000.004', 'Emily Davis', 'Emily', 'Davis', 'emily.davis@appalachianenergy.com', '304-555-1004', 'VP Operations', 'Appalachian Energy LLC', '04.04.02.04.30000.004', 'https://linkedin.com/in/emilydavis', 'Charleston', 'WV'),
  ('04.04.02.04.20000.005', 'Robert Brown', 'Robert', 'Brown', 'robert.brown@valleyhealthwv.org', '304-555-1005', 'Medical Director', 'Valley Healthcare Services', '04.04.02.04.30000.005', 'https://linkedin.com/in/robertbrown', 'Parkersburg', 'WV'),

  -- Invalid people (will fail validation)
  ('04.04.02.04.20000.006', 'Jane', '', '', 'invalid-email', '', 'CEO', 'Test Company', '04.04.02.04.30000.006', 'invalid-url', 'Charleston', 'WV'),  -- No last name, invalid email
  ('04.04.02.04.20000.007', '', 'Test', 'User', 'test@test.com', '', 'Manager', 'Example Inc', '04.04.02.04.30000.007', '', 'Huntington', 'WV'),  -- Empty full name, test email
  ('04.04.02.04.20000.008', 'Sample Person', 'Sample', 'Person', 'noreply@example.com', '', 'Director', 'Example Inc', '04.04.02.04.30000.008', '', 'Morgantown', 'WV'),  -- Invalid email (noreply)
  ('04.04.02.04.20000.009', 'n/a', '', '', 'email@test.com', '', 'Unknown', 'n/a', '04.04.02.04.30000.009', '', 'Charleston', 'WV'),  -- Invalid name
  ('04.04.02.04.20000.010', 'John', 'John', '', 'john@sample.com', '', 'CEO', 'Short Name X', '04.04.02.04.30000.010', 'not-a-linkedin-url', 'Parkersburg', 'WV')  -- No last name, invalid LinkedIn
ON CONFLICT (unique_id) DO NOTHING;

-- Verify data was inserted
SELECT
  'company_raw_wv' as table_name,
  COUNT(*) as total_records,
  COUNT(*) FILTER (WHERE state = 'WV') as wv_records
FROM marketing.company_raw_wv
UNION ALL
SELECT
  'people_raw_wv',
  COUNT(*),
  COUNT(*) FILTER (WHERE state = 'WV')
FROM marketing.people_raw_wv;

-- ============================================================================
-- Sample Data Created
-- ============================================================================
-- Companies: 10 total (5 valid, 5 invalid)
-- People: 10 total (5 valid, 5 invalid)
-- Ready for validation!
-- ============================================================================
