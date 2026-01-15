#!/usr/bin/env python3
"""
DOL Column Metadata Builder

Generates AI & human-ready documentation for all DOL table columns.
Creates unique IDs, descriptions, and search keywords based on DOL naming conventions.
"""

import os
import psycopg2
import re
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# DOL NAMING CONVENTION MAPPINGS
# ============================================================================

# Suffix patterns -> (description suffix, format, category hint)
SUFFIX_PATTERNS = {
    '_amt': ('amount in dollars', 'NUMERIC', 'Financial'),
    '_cnt': ('count/number', 'NUMERIC', 'Metric'),
    '_ind': ('indicator flag', 'Y/N/X', 'Flag'),
    '_date': ('date', 'YYYY-MM-DD', 'Date'),
    '_ein': ('Employer Identification Number', '9 digits (XX-XXXXXXX)', 'Identifier'),
    '_zip': ('ZIP code', '5 or 9 digits', 'Address'),
    '_phone': ('phone number', '10 digits', 'Contact'),
    '_code': ('code value', 'VARCHAR', 'Code'),
    '_text': ('text description', 'TEXT', 'Description'),
    '_name': ('name', 'VARCHAR', 'Name'),
    '_num': ('number/identifier', 'VARCHAR', 'Identifier'),
    '_pct': ('percentage', 'NUMERIC', 'Metric'),
}

# Prefix patterns -> (description prefix, category)
PREFIX_PATTERNS = {
    'spons_': ('Plan Sponsor', 'Sponsor'),
    'sponsor_': ('Plan Sponsor', 'Sponsor'),
    'sf_spons_': ('Plan Sponsor (SF)', 'Sponsor'),
    'sf_sponsor_': ('Plan Sponsor (SF)', 'Sponsor'),
    'admin_': ('Plan Administrator', 'Administrator'),
    'sf_admin_': ('Plan Administrator (SF)', 'Administrator'),
    'ins_': ('Insurance', 'Insurance'),
    'wlfr_': ('Welfare Benefit', 'Welfare'),
    'pension_': ('Pension', 'Pension'),
    'sch_a_': ('Schedule A', 'Schedule A'),
    'sf_': ('Short Form (5500-SF)', 'Form'),
    'form_': ('Form', 'Form'),
    'dfe_': ('Direct Filing Entity', 'Entity'),
    'fdcry_': ('Fiduciary', 'Fiduciary'),
    'preparer_': ('Form Preparer', 'Preparer'),
    'alloc_': ('Allocated Contract', 'Contract'),
    'unalloc_': ('Unallocated Contract', 'Contract'),
    'unal_': ('Unallocated Contract', 'Contract'),
}

# Specific field mappings (column_name -> full description)
SPECIFIC_FIELDS = {
    # Form identifiers
    'filing_id': 'Unique filing identifier (UUID)',
    'ack_id': 'DOL acknowledgment ID for the filing',
    'form_id': 'Form type identifier',
    'form_year': 'Tax/plan year for this filing',
    'date_received': 'Date filing was received by DOL',
    'created_at': 'Record creation timestamp',
    'updated_at': 'Record last update timestamp',

    # Sponsor fields
    'sponsor_dfe_name': 'Legal name of the plan sponsor or DFE',
    'sponsor_dfe_dba_name': 'Doing Business As (DBA) name of sponsor',
    'sponsor_dfe_ein': 'Employer Identification Number of sponsor',
    'spons_dfe_mail_us_address1': 'Sponsor mailing address line 1',
    'spons_dfe_mail_us_address2': 'Sponsor mailing address line 2',
    'spons_dfe_mail_us_city': 'Sponsor mailing city',
    'spons_dfe_mail_us_state': 'Sponsor mailing state (2-letter)',
    'spons_dfe_mail_us_zip': 'Sponsor mailing ZIP code',
    'spons_dfe_phone_num': 'Sponsor phone number',

    # Plan info
    'plan_name': 'Official name of the benefit plan',
    'plan_num': 'Plan number (3 digits)',
    'plan_eff_date': 'Plan effective date',
    'type_plan_entity_cd': 'Type of plan entity code',
    'type_dfe_plan_entity_cd': 'Type of DFE plan entity code',

    # Participant counts
    'tot_partcp_boy_cnt': 'Total participants at beginning of year',
    'tot_active_partcp_cnt': 'Total active participants',
    'rtd_sep_partcp_rcvg_cnt': 'Retired/separated participants receiving benefits',
    'partcp_account_bal_cnt': 'Participants with account balances',

    # Financial
    'tot_assets_boy_amt': 'Total assets at beginning of year',
    'tot_assets_eoy_amt': 'Total assets at end of year',
    'tot_liabilities_boy_amt': 'Total liabilities at beginning of year',
    'tot_liabilities_eoy_amt': 'Total liabilities at end of year',
    'net_assets_boy_amt': 'Net assets at beginning of year',
    'net_assets_eoy_amt': 'Net assets at end of year',
    'tot_income_amt': 'Total plan income',
    'tot_expenses_amt': 'Total plan expenses',
    'benefit_paid_amt': 'Benefits paid to participants',
    'admin_total_amt': 'Total administrative expenses',

    # Insurance/Schedule A specific
    'ins_carrier_name': 'Name of insurance carrier',
    'ins_carrier_ein': 'Insurance carrier EIN',
    'ins_carrier_naic_code': 'Insurance carrier NAIC code (5 digits)',
    'ins_contract_num': 'Insurance contract/policy number',
    'ins_prsn_covered_eoy_cnt': 'Persons covered at end of year',
    'ins_policy_from_date': 'Policy effective start date',
    'ins_policy_to_date': 'Policy effective end date',
    'ins_broker_comm_tot_amt': 'Total broker commissions paid',
    'ins_broker_fees_tot_amt': 'Total broker fees paid',

    # Welfare benefit indicators
    'wlfr_bnft_health_ind': 'Plan provides health benefits',
    'wlfr_bnft_dental_ind': 'Plan provides dental benefits',
    'wlfr_bnft_vision_ind': 'Plan provides vision benefits',
    'wlfr_bnft_life_insur_ind': 'Plan provides life insurance',
    'wlfr_bnft_temp_disab_ind': 'Plan provides temporary disability',
    'wlfr_bnft_long_term_disab_ind': 'Plan provides long-term disability',
    'wlfr_bnft_unemp_ind': 'Plan provides unemployment benefits',
    'wlfr_bnft_drug_ind': 'Plan provides prescription drug benefits',
    'wlfr_bnft_stop_loss_ind': 'Plan has stop-loss coverage',
    'wlfr_bnft_hmo_ind': 'Plan uses HMO arrangement',
    'wlfr_bnft_ppo_ind': 'Plan uses PPO arrangement',
    'wlfr_bnft_indemnity_ind': 'Plan uses indemnity arrangement',
    'wlfr_bnft_other_ind': 'Plan provides other welfare benefits',

    # Pension financial
    'pension_eoy_gen_acct_amt': 'Pension general account value at EOY',
    'pension_eoy_sep_acct_amt': 'Pension separate account value at EOY',
    'pension_prem_paid_tot_amt': 'Total pension premiums paid',
    'pension_unpaid_premium_amt': 'Unpaid pension premiums',
    'pension_contract_cost_amt': 'Pension contract cost',
    'pension_contrib_dep_amt': 'Pension contributions deposited',
    'pension_divnd_cr_dep_amt': 'Pension dividend credits deposited',
    'pension_int_cr_dur_yr_amt': 'Pension interest credits during year',
    'pension_bnfts_dsbrsd_amt': 'Pension benefits disbursed',
    'pension_admin_chrg_amt': 'Pension administrative charges',
    'pension_eoy_bal_amt': 'Pension end of year balance',

    # Linkage fields
    'sponsor_state': 'Sponsor state (derived from Form 5500 for Schedule A)',
    'sponsor_name': 'Sponsor name (derived from Form 5500 for Schedule A)',
}

# Keywords for common search terms
KEYWORD_MAPPINGS = {
    'ein': ['ein', 'employer id', 'tax id', 'identification number'],
    'sponsor': ['sponsor', 'employer', 'company', 'organization'],
    'admin': ['administrator', 'admin', 'tpa', 'third party'],
    'carrier': ['carrier', 'insurer', 'insurance company'],
    'broker': ['broker', 'agent', 'advisor', 'commission'],
    'health': ['health', 'medical', 'healthcare'],
    'dental': ['dental', 'teeth', 'oral'],
    'vision': ['vision', 'eye', 'optical'],
    'life': ['life', 'death benefit', 'life insurance'],
    'disability': ['disability', 'disabled', 'ltd', 'std'],
    'pension': ['pension', 'retirement', '401k', 'defined benefit'],
    'participant': ['participant', 'employee', 'member', 'beneficiary'],
    'asset': ['asset', 'investment', 'portfolio', 'holdings'],
    'liability': ['liability', 'debt', 'obligation'],
    'premium': ['premium', 'payment', 'contribution'],
    'benefit': ['benefit', 'coverage', 'plan'],
    'address': ['address', 'location', 'street', 'city', 'state', 'zip'],
    'phone': ['phone', 'telephone', 'contact', 'number'],
    'date': ['date', 'when', 'year', 'period'],
    'amount': ['amount', 'dollars', 'money', 'value', 'cost'],
    'count': ['count', 'number', 'total', 'how many'],
    'renewal': ['renewal', 'plan year', 'effective date', 'policy date'],
    'naic': ['naic', 'national association', 'insurance code'],
    'contract': ['contract', 'policy', 'agreement'],
    'welfare': ['welfare', 'employee benefit', 'fringe'],
}


def get_connection():
    """Get database connection."""
    conn_string = os.getenv('DATABASE_URL') or os.getenv('NEON_CONNECTION_STRING')
    if not conn_string:
        host = os.getenv('NEON_HOST')
        database = os.getenv('NEON_DATABASE')
        user = os.getenv('NEON_USER')
        password = os.getenv('NEON_PASSWORD')
        conn_string = f"postgresql://{user}:{password}@{host}:5432/{database}?sslmode=require"
    return psycopg2.connect(conn_string)


def generate_column_id(table_name: str, column_name: str) -> str:
    """Generate unique column ID like DOL_F5500_SPONSOR_NAME."""
    table_prefix = {
        'form_5500': 'F5500',
        'form_5500_sf': 'F5500SF',
        'schedule_a': 'SCHA',
    }.get(table_name, table_name.upper())

    # Clean column name for ID
    col_id = column_name.upper().replace('_', '_')

    return f"DOL_{table_prefix}_{col_id}"


def generate_description(column_name: str) -> str:
    """Generate human-readable description from column name."""
    # Check specific fields first
    if column_name in SPECIFIC_FIELDS:
        return SPECIFIC_FIELDS[column_name]

    # Start building description
    desc_parts = []
    category = None
    col_lower = column_name.lower()

    # Check prefix patterns
    for prefix, (prefix_desc, cat) in PREFIX_PATTERNS.items():
        if col_lower.startswith(prefix):
            desc_parts.append(prefix_desc)
            category = cat
            col_lower = col_lower[len(prefix):]
            break

    # Check suffix patterns
    suffix_desc = None
    for suffix, (suf_desc, fmt, cat) in SUFFIX_PATTERNS.items():
        if col_lower.endswith(suffix):
            suffix_desc = suf_desc
            if not category:
                category = cat
            col_lower = col_lower[:-len(suffix)]
            break

    # Convert remaining to readable words
    words = col_lower.replace('_', ' ').strip()
    if words:
        # Expand common abbreviations
        words = words.replace(' dfe ', ' Direct Filing Entity ')
        words = words.replace(' partcp ', ' participant ')
        words = words.replace(' rcvg ', ' receiving ')
        words = words.replace(' tot ', ' total ')
        words = words.replace(' eoy ', ' end of year ')
        words = words.replace(' boy ', ' beginning of year ')
        words = words.replace(' prem ', ' premium ')
        words = words.replace(' bnft ', ' benefit ')
        words = words.replace(' bnfts ', ' benefits ')
        words = words.replace(' yr ', ' year ')
        words = words.replace(' bal ', ' balance ')
        words = words.replace(' rtd ', ' retired ')
        words = words.replace(' sep ', ' separated ')
        words = words.replace(' acct ', ' account ')
        words = words.replace(' contrib ', ' contribution ')
        words = words.replace(' dsbrsd ', ' disbursed ')
        words = words.replace(' chrg ', ' charge ')
        words = words.replace(' admin ', ' administrative ')
        words = words.replace(' divnd ', ' dividend ')
        words = words.replace(' cr ', ' credit ')
        words = words.replace(' ded ', ' deduction ')
        words = words.replace(' prsn ', ' persons ')
        words = words.replace(' insur ', ' insurance ')
        words = words.replace(' disab ', ' disability ')
        words = words.replace(' unemp ', ' unemployment ')
        words = words.replace(' comm ', ' commission ')
        words = words.replace(' num ', ' number ')
        words = words.replace(' prev ', ' previous ')
        words = words.replace(' incr ', ' increase ')
        words = words.replace(' decr ', ' decrease ')
        words = words.replace(' acquis ', ' acquisition ')
        words = words.replace(' refund ', ' refund ')
        words = words.replace(' ret ', ' retention ')
        words = words.replace(' oth ', ' other ')
        words = words.replace(' chrgs ', ' charges ')
        words = words.replace(' loc ', ' location ')
        words = words.replace(' prov ', ' province ')
        words = words.replace(' cntry ', ' country ')
        words = words.replace(' fav ', ' favorable ')
        words = words.replace(' determ ', ' determination ')
        words = words.replace(' ltr ', ' letter ')
        words = words.replace(' opin ', ' opinion ')
        words = words.replace(' advi ', ' advisory ')
        words = words.replace(' eff ', ' effective ')

        desc_parts.append(words.strip())

    if suffix_desc:
        desc_parts.append(f"({suffix_desc})")

    description = ' '.join(desc_parts).strip()

    # Capitalize first letter
    if description:
        description = description[0].upper() + description[1:]

    return description or f"Column: {column_name}"


def get_data_format(column_name: str, data_type: str, max_length: Optional[int]) -> Tuple[str, str]:
    """Get data type and format pattern."""
    col_lower = column_name.lower()

    # Check suffix patterns for format
    for suffix, (_, fmt, _) in SUFFIX_PATTERNS.items():
        if col_lower.endswith(suffix):
            if suffix == '_date':
                return 'DATE', 'YYYY-MM-DD'
            elif suffix == '_ind':
                return 'FLAG', 'Y/N/X or 1/0'
            elif suffix == '_amt':
                return 'CURRENCY', 'Decimal dollars (e.g., 12345.67)'
            elif suffix == '_cnt':
                return 'INTEGER', 'Whole number'
            elif suffix == '_ein':
                return 'EIN', '9 digits (XX-XXXXXXX)'
            elif suffix == '_zip':
                return 'ZIP', '5 or 9 digits'
            elif suffix == '_phone':
                return 'PHONE', '10 digits'
            elif suffix == '_pct':
                return 'PERCENT', 'Decimal (e.g., 0.25 = 25%)'

    # Handle UUID
    if data_type == 'uuid':
        return 'UUID', 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'

    # Handle timestamps
    if 'timestamp' in data_type:
        return 'TIMESTAMP', 'YYYY-MM-DD HH:MM:SS'

    # Handle numeric
    if data_type == 'numeric':
        return 'NUMERIC', 'Decimal number'

    # Default VARCHAR
    if max_length:
        return 'TEXT', f'Up to {max_length} characters'

    return 'TEXT', 'Variable length text'


def get_category(column_name: str) -> str:
    """Determine category for the column."""
    col_lower = column_name.lower()

    for prefix, (_, cat) in PREFIX_PATTERNS.items():
        if col_lower.startswith(prefix):
            return cat

    # Check content-based categories
    if any(x in col_lower for x in ['partcp', 'participant', 'employee']):
        return 'Participant'
    if any(x in col_lower for x in ['asset', 'liability', 'income', 'expense']):
        return 'Financial'
    if any(x in col_lower for x in ['address', 'city', 'state', 'zip', 'phone']):
        return 'Contact'
    if any(x in col_lower for x in ['filing', 'ack', 'form']):
        return 'Filing'
    if any(x in col_lower for x in ['date', 'year']):
        return 'Date'

    return 'General'


def get_keywords(column_name: str, description: str) -> List[str]:
    """Generate search keywords for the column."""
    keywords = set()
    col_lower = column_name.lower()
    desc_lower = description.lower()

    # Add keywords based on content
    for key, terms in KEYWORD_MAPPINGS.items():
        if any(term in col_lower or term in desc_lower for term in terms):
            keywords.update(terms)

    # Add column name parts
    for part in column_name.split('_'):
        if len(part) > 2:
            keywords.add(part.lower())

    return list(keywords)[:15]  # Limit to 15 keywords


def is_pii(column_name: str) -> bool:
    """Check if column contains PII."""
    pii_patterns = ['ein', 'phone', 'address', 'name', 'email', 'ssn']
    col_lower = column_name.lower()
    return any(p in col_lower for p in pii_patterns)


def build_metadata():
    """Build metadata for all DOL columns."""
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Enable import mode
        cur.execute("SET session dol.import_mode = 'active'")
        conn.commit()

        # Run the schema migration first
        logger.info("Creating metadata table structure...")
        with open('infra/migrations/2026-01-15-dol-column-metadata.sql', 'r') as f:
            cur.execute(f.read())
        conn.commit()

        # Get all columns from DOL tables
        tables = ['form_5500', 'form_5500_sf', 'schedule_a']
        total_columns = 0

        for table_name in tables:
            logger.info(f"Processing {table_name}...")

            cur.execute('''
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'dol' AND table_name = %s
                ORDER BY ordinal_position
            ''', (table_name,))

            columns = cur.fetchall()

            for col_name, data_type, max_length in columns:
                # Generate metadata
                column_id = generate_column_id(table_name, col_name)
                description = generate_description(col_name)
                dtype, format_pattern = get_data_format(col_name, data_type, max_length)
                category = get_category(col_name)
                keywords = get_keywords(col_name, description)
                pii = is_pii(col_name)

                # Get example values (sample 3)
                try:
                    cur.execute(f'''
                        SELECT DISTINCT {col_name}::TEXT
                        FROM dol.{table_name}
                        WHERE {col_name} IS NOT NULL
                        LIMIT 3
                    ''')
                    examples = [r[0][:50] if r[0] and len(str(r[0])) > 50 else r[0] for r in cur.fetchall()]
                except:
                    examples = []
                    conn.rollback()
                    cur.execute("SET session dol.import_mode = 'active'")

                # Insert metadata
                cur.execute('''
                    INSERT INTO dol.column_metadata
                    (table_name, column_name, column_id, description, category,
                     data_type, format_pattern, max_length, search_keywords,
                     is_pii, is_searchable, example_values)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (table_name, column_name) DO UPDATE SET
                        column_id = EXCLUDED.column_id,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        data_type = EXCLUDED.data_type,
                        format_pattern = EXCLUDED.format_pattern,
                        max_length = EXCLUDED.max_length,
                        search_keywords = EXCLUDED.search_keywords,
                        is_pii = EXCLUDED.is_pii,
                        example_values = EXCLUDED.example_values
                ''', (
                    table_name, col_name, column_id, description, category,
                    dtype, format_pattern, max_length, keywords,
                    pii, True, examples
                ))

                # Add PostgreSQL COMMENT
                comment = f"{description} | ID: {column_id} | Format: {format_pattern}"
                cur.execute(f'''
                    COMMENT ON COLUMN dol.{table_name}.{col_name} IS %s
                ''', (comment,))

                total_columns += 1

            conn.commit()
            logger.info(f"  {len(columns)} columns documented")

        logger.info(f"Total: {total_columns} columns documented")

        # Print summary
        cur.execute('''
            SELECT table_name, COUNT(*) as col_count,
                   COUNT(DISTINCT category) as categories
            FROM dol.column_metadata
            GROUP BY table_name
            ORDER BY table_name
        ''')

        print("\n" + "=" * 60)
        print("COLUMN METADATA SUMMARY")
        print("=" * 60)
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} columns, {row[2]} categories")

        # Show category breakdown
        cur.execute('''
            SELECT category, COUNT(*) as cnt
            FROM dol.column_metadata
            GROUP BY category
            ORDER BY cnt DESC
        ''')
        print("\nCategories:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} columns")

        print("=" * 60)

    finally:
        cur.execute("RESET dol.import_mode")
        conn.commit()
        cur.close()
        conn.close()


if __name__ == "__main__":
    build_metadata()
