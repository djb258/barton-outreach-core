#!/usr/bin/env python3
"""
Create enrichment tables in Supabase
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    supabase_url = os.getenv('SUPABASE_DB_URL')

    print("[*] Connecting to Supabase...")

    try:
        conn = psycopg2.connect(supabase_url)
        cursor = conn.cursor()

        print("[*] Creating company_needs_enrichment table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.company_needs_enrichment (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                company_name TEXT NOT NULL,
                domain TEXT,
                industry TEXT,
                employee_count INTEGER,
                revenue NUMERIC,
                location TEXT,
                linkedin_url TEXT,
                website TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                enrichment_data JSONB,
                validation_status TEXT NOT NULL DEFAULT 'PENDING',
                validation_errors JSONB,
                validation_warnings JSONB,
                source_repo TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_table TEXT NOT NULL,
                source_environment TEXT DEFAULT 'production',
                batch_id TEXT NOT NULL,
                entity_type TEXT NOT NULL DEFAULT 'company',
                state_code TEXT,
                priority TEXT DEFAULT 'medium',
                needs_review BOOLEAN DEFAULT true,
                enrichment_source TEXT DEFAULT 'external-import',
                reason_code TEXT,
                pulled_at TIMESTAMP,
                imported_at TIMESTAMP DEFAULT NOW(),
                enriched_at TIMESTAMP,
                enriched_by TEXT,
                promoted_at TIMESTAMP,
                promoted_to_neon BOOLEAN DEFAULT false,
                reviewed BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        print("[*] Creating people_needs_enrichment table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.people_needs_enrichment (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                unique_id TEXT,
                full_name TEXT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                title TEXT,
                company_id UUID,
                company_name TEXT,
                company_unique_id TEXT,
                linkedin_url TEXT,
                city TEXT,
                state TEXT,
                enrichment_data JSONB,
                validation_status TEXT NOT NULL DEFAULT 'PENDING',
                validation_errors JSONB,
                validation_warnings JSONB,
                source_repo TEXT NOT NULL,
                source_id TEXT NOT NULL,
                source_table TEXT NOT NULL,
                source_environment TEXT DEFAULT 'production',
                batch_id TEXT NOT NULL,
                entity_type TEXT NOT NULL DEFAULT 'people',
                state_code TEXT,
                priority TEXT DEFAULT 'medium',
                needs_review BOOLEAN DEFAULT true,
                enrichment_source TEXT DEFAULT 'external-import',
                reason_code TEXT,
                pulled_at TIMESTAMP,
                imported_at TIMESTAMP DEFAULT NOW(),
                enriched_at TIMESTAMP,
                enriched_by TEXT,
                promoted_at TIMESTAMP,
                promoted_to_neon BOOLEAN DEFAULT false,
                reviewed BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        print("[*] Creating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_company_enrichment_status
            ON public.company_needs_enrichment(validation_status);

            CREATE INDEX IF NOT EXISTS idx_company_enrichment_batch
            ON public.company_needs_enrichment(batch_id);

            CREATE INDEX IF NOT EXISTS idx_company_enrichment_source
            ON public.company_needs_enrichment(source_repo, source_id);

            CREATE INDEX IF NOT EXISTS idx_company_enrichment_domain
            ON public.company_needs_enrichment(domain);

            CREATE INDEX IF NOT EXISTS idx_people_enrichment_status
            ON public.people_needs_enrichment(validation_status);

            CREATE INDEX IF NOT EXISTS idx_people_enrichment_batch
            ON public.people_needs_enrichment(batch_id);

            CREATE INDEX IF NOT EXISTS idx_people_enrichment_source
            ON public.people_needs_enrichment(source_repo, source_id);

            CREATE INDEX IF NOT EXISTS idx_people_enrichment_email
            ON public.people_needs_enrichment(email);
        """)

        conn.commit()

        print("\n[+] Tables created successfully!")
        print("[+] Ready to receive enrichment data from Neon\n")

        conn.close()

    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()
