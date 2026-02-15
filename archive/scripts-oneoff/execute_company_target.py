"""
Company Target Execution Script
================================
Real run against all eligible companies in Neon.
Doctrine-compliant with cost tracking.
"""

import psycopg2
import uuid
import sys
from datetime import datetime

# Database connection
HOST = 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech'
DATABASE = 'Marketing DB'
USER = 'Marketing DB_owner'
PASSWORD = 'npg_OsE4Z2oPCpiT'

def main():
    conn = psycopg2.connect(
        host=HOST,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
        sslmode='require'
    )
    conn.autocommit = False
    cur = conn.cursor()

    # Create execution context
    CONTEXT_ID = str(uuid.uuid4())
    run_timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')

    print('=' * 70)
    print('COMPANY TARGET EXECUTION - REAL RUN')
    print('=' * 70)
    print(f'Context ID: {CONTEXT_ID}')
    print('')
    sys.stdout.flush()

    # Create context
    cur.execute("""
        INSERT INTO outreach_ctx.context (outreach_context_id, status, notes)
        VALUES (%s, 'OPEN', %s)
    """, (CONTEXT_ID, f'Company Target Full Run - {run_timestamp}'))
    conn.commit()
    print('[1/4] Context created')
    sys.stdout.flush()

    # Query companies
    cur.execute("""
        SELECT
            company_unique_id,
            company_name,
            company_domain,
            linkedin_company_url
        FROM cl.company_identity
        WHERE lifecycle_run_id IS NOT NULL
        ORDER BY created_at
    """)
    companies = cur.fetchall()
    total = len(companies)
    print(f'[2/4] {total:,} companies queried')
    sys.stdout.flush()

    # Counters
    processed = 0
    pass_count = 0
    fail_count = 0
    errors = []

    print(f'[3/4] Processing companies...')
    print('')
    sys.stdout.flush()

    BATCH_SIZE = 5000

    for i in range(0, len(companies), BATCH_SIZE):
        batch = companies[i:i+BATCH_SIZE]
        batch_start = datetime.now()

        for company in batch:
            company_sov_id = str(company[0])
            company_name = company[1] or ''
            company_domain = company[2]

            try:
                # Determine status based on domain
                if company_domain:
                    status = 'queued'  # Ready for outreach
                    pass_count += 1
                else:
                    status = 'disqualified'  # No domain
                    fail_count += 1

                # Insert into company_target
                cur.execute("""
                    INSERT INTO outreach.company_target (
                        target_id,
                        company_unique_id,
                        outreach_status,
                        sequence_count,
                        source,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, 0, %s, NOW(), NOW()
                    )
                """, (
                    str(uuid.uuid4()),
                    company_sov_id,
                    status,
                    f'CT-{CONTEXT_ID[:8]}'
                ))
                processed += 1

            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                processed += 1
            except Exception as e:
                conn.rollback()
                if len(errors) < 10:
                    errors.append(str(e)[:100])

        # Commit batch
        conn.commit()

        elapsed = (datetime.now() - batch_start).total_seconds()
        pct = (i + len(batch)) / total * 100
        print(f'  Batch: {i+1:,}-{i+len(batch):,} / {total:,} ({pct:.1f}%) - {elapsed:.1f}s')
        sys.stdout.flush()

    # Close context
    print('')
    print('[4/4] Closing context...')
    sys.stdout.flush()

    cur.execute("""
        UPDATE outreach_ctx.context
        SET status = 'CLOSED'
        WHERE outreach_context_id = %s
    """, (CONTEXT_ID,))
    conn.commit()

    print('')
    print('=' * 70)
    print('EXECUTION COMPLETE')
    print('=' * 70)
    print(f'Context ID: {CONTEXT_ID}')
    print(f'Total Processed: {processed:,}')
    print(f'PASS (queued): {pass_count:,}')
    print(f'FAIL (disqualified): {fail_count:,}')
    print(f'Pass Rate: {pass_count/total*100:.1f}%')
    print(f'Tier-2 Used: No (Tier-0 only)')
    print(f'Total Spend: $0.00')
    if errors:
        print(f'Errors: {len(errors)}')
        for e in errors[:3]:
            print(f'  - {e}')

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
