#!/usr/bin/env python3
"""
Create enrichment tables in Neon to store Hunter data.
"""
import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Create enrichment schema if not exists
    cur.execute("CREATE SCHEMA IF NOT EXISTS enrichment")
    
    # Table 1: Company enrichment (one row per domain)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrichment.hunter_company (
            id SERIAL PRIMARY KEY,
            domain VARCHAR(255) NOT NULL UNIQUE,
            organization VARCHAR(500),
            headcount VARCHAR(50),
            country VARCHAR(10),
            state VARCHAR(50),
            city VARCHAR(100),
            postal_code VARCHAR(20),
            street VARCHAR(255),
            email_pattern VARCHAR(100),
            company_type VARCHAR(100),
            industry VARCHAR(255),
            enriched_at TIMESTAMP DEFAULT NOW(),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Table 2: Contacts from Hunter (multiple per domain)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrichment.hunter_contact (
            id SERIAL PRIMARY KEY,
            domain VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            department VARCHAR(100),
            job_title VARCHAR(255),
            position_raw VARCHAR(500),
            linkedin_url VARCHAR(500),
            twitter_handle VARCHAR(100),
            phone_number VARCHAR(50),
            confidence_score INTEGER,
            email_type VARCHAR(20),
            num_sources INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            CONSTRAINT fk_hunter_contact_domain 
                FOREIGN KEY (domain) REFERENCES enrichment.hunter_company(domain)
        )
    """)
    
    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hunter_company_domain ON enrichment.hunter_company(domain)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hunter_contact_domain ON enrichment.hunter_contact(domain)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hunter_contact_email ON enrichment.hunter_contact(email)")
    
    conn.commit()
    
    print('Tables created:')
    print('  enrichment.hunter_company - Company data (1 per domain)')
    print('  enrichment.hunter_contact - Contact data (multiple per domain)')
    
    # Verify
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'enrichment'
    """)
    tables = [r[0] for r in cur.fetchall()]
    print(f'\nTables in enrichment schema: {tables}')
    
    conn.close()

if __name__ == '__main__':
    main()
