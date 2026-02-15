"""
Create and populate the outreach.appointments table.

This table stores historical appointment data - companies we've already met with.
Used to identify "lukewarm" outreach opportunities vs cold outreach.

Table Design:
- appointment_id: Unique identifier (UUID)
- outreach_id: Link to outreach.outreach (NULL if not in pipeline yet)
- domain: Company domain for matching
- prospect_keycode_id: Original system ID from source data
- appt_number: Appointment reference number
- appt_date: Date of the appointment
- contact_first_name: First name of appointment contact
- contact_last_name: Last name of appointment contact  
- contact_title: Job title of appointment contact
- contact_email: Email of appointment contact
- contact_phone: Full phone number (area + number)
- company_name: Company name
- address_1: Street address
- address_2: Address line 2
- city: City
- state: State code
- zip: Zip code
- county: County name
- notes: Combined Q&A notes from appointment
- created_at: Record creation timestamp
- updated_at: Record update timestamp
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

# SQL to create the appointments table
CREATE_TABLE_SQL = """
-- Drop if exists for clean recreation
DROP TABLE IF EXISTS outreach.appointments CASCADE;

-- Create appointments table
CREATE TABLE outreach.appointments (
    -- Primary key
    appointment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign key to outreach pipeline (nullable - may not be in pipeline yet)
    outreach_id UUID REFERENCES outreach.outreach(outreach_id) ON DELETE SET NULL,
    
    -- Domain for matching (indexed)
    domain VARCHAR(255),
    
    -- Source system identifiers
    prospect_keycode_id BIGINT,
    appt_number VARCHAR(50),
    appt_date DATE,
    
    -- Contact information (the person we met with)
    contact_first_name VARCHAR(100),
    contact_last_name VARCHAR(100),
    contact_title VARCHAR(200),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    
    -- Company information
    company_name VARCHAR(255) NOT NULL,
    address_1 VARCHAR(255),
    address_2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(10),
    zip VARCHAR(20),
    county VARCHAR(100),
    
    -- Appointment notes (combined Q&A)
    notes TEXT,
    
    -- Metadata
    source_file VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX idx_appointments_domain ON outreach.appointments(domain);
CREATE INDEX idx_appointments_outreach_id ON outreach.appointments(outreach_id);
CREATE INDEX idx_appointments_company_name ON outreach.appointments(company_name);
CREATE INDEX idx_appointments_appt_date ON outreach.appointments(appt_date);

-- Add table comment for AI readability
COMMENT ON TABLE outreach.appointments IS 'Historical appointment records - companies we have already met with. Used to identify warm/lukewarm outreach opportunities.';

-- Add column comments for AI readability
COMMENT ON COLUMN outreach.appointments.appointment_id IS 'Unique identifier for this appointment record (UUID format)';
COMMENT ON COLUMN outreach.appointments.outreach_id IS 'Foreign key linking to outreach.outreach table - NULL if company not yet in outreach pipeline';
COMMENT ON COLUMN outreach.appointments.domain IS 'Company website domain (e.g., acme.com) - used for matching to other tables';
COMMENT ON COLUMN outreach.appointments.prospect_keycode_id IS 'Original prospect ID from source appointment system';
COMMENT ON COLUMN outreach.appointments.appt_number IS 'Appointment reference number from source system';
COMMENT ON COLUMN outreach.appointments.appt_date IS 'Date the appointment occurred';
COMMENT ON COLUMN outreach.appointments.contact_first_name IS 'First name of the person we met with';
COMMENT ON COLUMN outreach.appointments.contact_last_name IS 'Last name of the person we met with';
COMMENT ON COLUMN outreach.appointments.contact_title IS 'Job title of the appointment contact (e.g., HR Manager, CFO)';
COMMENT ON COLUMN outreach.appointments.contact_email IS 'Email address of the appointment contact';
COMMENT ON COLUMN outreach.appointments.contact_phone IS 'Phone number of the appointment contact (format: area code + number)';
COMMENT ON COLUMN outreach.appointments.company_name IS 'Legal or common name of the company';
COMMENT ON COLUMN outreach.appointments.address_1 IS 'Primary street address';
COMMENT ON COLUMN outreach.appointments.address_2 IS 'Secondary address line (suite, floor, etc.)';
COMMENT ON COLUMN outreach.appointments.city IS 'City name';
COMMENT ON COLUMN outreach.appointments.state IS 'State code (2-letter abbreviation)';
COMMENT ON COLUMN outreach.appointments.zip IS 'ZIP/postal code';
COMMENT ON COLUMN outreach.appointments.county IS 'County name';
COMMENT ON COLUMN outreach.appointments.notes IS 'Combined appointment notes and Q&A responses from the meeting';
COMMENT ON COLUMN outreach.appointments.source_file IS 'Name of the file this record was imported from';
COMMENT ON COLUMN outreach.appointments.created_at IS 'Timestamp when this record was created';
COMMENT ON COLUMN outreach.appointments.updated_at IS 'Timestamp when this record was last updated';
"""


def load_appointments_file(filepath: str) -> pd.DataFrame:
    """Load and parse the appointments CSV file."""
    df = pd.read_csv(filepath)
    return df


def extract_unique_appointments(df: pd.DataFrame) -> pd.DataFrame:
    """Extract unique appointment records (one per company)."""
    # Get unique appointments by ProspectKeycodeId
    unique_df = df.drop_duplicates(subset=['ProspectKeycodeId']).copy()
    return unique_df


def combine_qa_notes(row: pd.Series) -> str:
    """Combine Q1-Q75 columns into a single notes field."""
    notes_parts = []
    for i in range(1, 76):
        col = f'Q{i}'
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            notes_parts.append(str(row[col]).strip())
    return '\n\n'.join(notes_parts) if notes_parts else None


def format_phone(area: str, phone: str) -> str:
    """Format area code and phone number into full phone."""
    if pd.isna(area) or pd.isna(phone):
        return None
    area_str = str(int(area)) if isinstance(area, float) else str(area)
    phone_str = str(int(phone)) if isinstance(phone, float) else str(phone)
    # Format as (XXX) XXX-XXXX
    if len(phone_str) == 7:
        return f"({area_str}) {phone_str[:3]}-{phone_str[3:]}"
    return f"({area_str}) {phone_str}"


def parse_date(date_str: str):
    """Parse appointment date string."""
    if pd.isna(date_str) or not date_str:
        return None
    try:
        # Try MM-DD-YY format
        return datetime.strptime(str(date_str), '%m-%d-%y').date()
    except ValueError:
        try:
            # Try other formats
            return datetime.strptime(str(date_str), '%Y-%m-%d').date()
        except ValueError:
            return None


def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print("=== CREATING APPOINTMENTS TABLE ===")
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    print("✓ Table created with indexes and comments")
    
    # Load the appointments file
    filepath = r'C:\Users\CUSTOM PC\Desktop\appts-already-had-2129971 full email addresses.csv'
    print(f"\n=== LOADING APPOINTMENTS FROM FILE ===")
    df = load_appointments_file(filepath)
    print(f"Total rows: {len(df)}")
    
    # Extract unique appointments
    unique_df = extract_unique_appointments(df)
    print(f"Unique appointments: {len(unique_df)}")
    
    # Get existing outreach records for linking
    cur.execute("SELECT outreach_id, domain FROM outreach.outreach WHERE domain IS NOT NULL")
    outreach_lookup = {row[1].lower(): row[0] for row in cur.fetchall() if row[1]}
    print(f"Outreach records available for linking: {len(outreach_lookup)}")
    
    # Prepare records for insert
    print("\n=== PREPARING APPOINTMENT RECORDS ===")
    records = []
    linked_count = 0
    
    for _, row in unique_df.iterrows():
        domain = str(row['Domain']).lower() if pd.notna(row['Domain']) else None
        
        # Try to link to outreach
        outreach_id = outreach_lookup.get(domain) if domain else None
        if outreach_id:
            linked_count += 1
        
        # Combine notes
        notes = combine_qa_notes(row)
        
        # Format phone
        phone = format_phone(row.get('Area'), row.get('Phone'))
        
        # Parse date
        appt_date = parse_date(row.get('Appt Date'))
        
        record = (
            str(uuid.uuid4()),  # appointment_id
            str(outreach_id) if outreach_id else None,  # outreach_id
            domain,  # domain
            int(row['ProspectKeycodeId']) if pd.notna(row['ProspectKeycodeId']) else None,
            str(row['Appt #']) if pd.notna(row.get('Appt #')) else None,
            appt_date,
            str(row['First']) if pd.notna(row['First']) else None,
            str(row['Last']) if pd.notna(row['Last']) else None,
            str(row['Title']) if pd.notna(row['Title']) else None,
            str(row['Email']) if pd.notna(row['Email']) else None,
            phone,
            str(row['Company']) if pd.notna(row['Company']) else None,
            str(row['Address 1']) if pd.notna(row.get('Address 1')) else None,
            str(row['Address 2']) if pd.notna(row.get('Address 2')) else None,
            str(row['City']) if pd.notna(row['City']) else None,
            str(row['State']) if pd.notna(row['State']) else None,
            str(row['Zip']) if pd.notna(row['Zip']) else None,
            str(row['County']) if pd.notna(row.get('County')) else None,
            notes,
            'appts-already-had-2129971 full email addresses.csv'
        )
        records.append(record)
    
    # Insert records
    print(f"\n=== INSERTING {len(records)} APPOINTMENT RECORDS ===")
    insert_sql = """
        INSERT INTO outreach.appointments (
            appointment_id, outreach_id, domain, prospect_keycode_id, appt_number, appt_date,
            contact_first_name, contact_last_name, contact_title, contact_email, contact_phone,
            company_name, address_1, address_2, city, state, zip, county, notes, source_file
        ) VALUES %s
    """
    execute_values(cur, insert_sql, records)
    conn.commit()
    
    print(f"✓ Inserted {len(records)} appointment records")
    print(f"✓ Linked {linked_count} to existing outreach records")
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM outreach.appointments")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM outreach.appointments WHERE outreach_id IS NOT NULL")
    linked = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM outreach.appointments WHERE contact_email IS NOT NULL")
    with_email = cur.fetchone()[0]
    
    print(f"\n=== SUMMARY ===")
    print(f"Total appointments: {total}")
    print(f"Linked to outreach: {linked}")
    print(f"With contact email: {with_email}")
    
    # Show sample
    print(f"\n=== SAMPLE RECORDS ===")
    cur.execute("""
        SELECT company_name, contact_first_name, contact_last_name, contact_title, domain, 
               CASE WHEN outreach_id IS NOT NULL THEN 'Yes' ELSE 'No' END as linked
        FROM outreach.appointments 
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {row[0][:30]:30} | {row[1] or ''} {row[2] or ''} | {row[3] or 'N/A'} | {row[5]}")
    
    conn.close()
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
