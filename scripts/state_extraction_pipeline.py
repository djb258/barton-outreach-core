"""
State Blog → People Extraction Pipeline
========================================

USAGE:
    doppler run -- python scripts/state_extraction_pipeline.py --state WV
    doppler run -- python scripts/state_extraction_pipeline.py --state WV --batch-size 100
    doppler run -- python scripts/state_extraction_pipeline.py --state ALL --batch-size 50

PIPELINE STAGES:
    1. CHECK_BASELINE    - Count companies, URLs, existing people, slot coverage
    2. MINT_ORPHANS      - Create identity bridge entries for orphan companies
    3. INIT_SLOTS        - Create CEO/CFO/HR slots for companies with outreach
    4. FREE_EXTRACT      - httpx + selectolax + regex (NO API CALLS)
    5. ASSIGN_STAGED     - Promote people to master with DOCTRINE IDs
    6. QUEUE_FAILURES    - Send failed URLs to paid_enrichment_queue
    7. REPORT            - Generate before/after comparison

DOCTRINE ID FORMATS:
    Company:  04.04.01.XX.XXXXX.XXX
    Person:   04.04.02.XX.XXXXX.XXX
    Slot:     04.04.05.XX.XXXXX.XXX

SLOT FILL RULES:
    - Name + Title = Fill slot (contact info optional, enriched later)
    - FREE extraction uses regex patterns only
    - Failures go to paid_enrichment_queue for Clay/paid enrichment

TARGET STATES (9 total):
    WV, VT, WY, AK, ND, SD, DE, MT, RI
"""

import os
import re
import sys
import time
import argparse
from datetime import datetime
from typing import Optional, Dict, List, Tuple

import httpx
import psycopg2
from psycopg2.extras import execute_values

try:
    from selectolax.parser import HTMLParser
except ImportError:
    print("Install selectolax: pip install selectolax")
    sys.exit(1)

DATABASE_URL = os.environ.get('DATABASE_URL')

# Target states for extraction (ordered by company count)
TARGET_STATES = ['PA', 'OH', 'VA', 'NC', 'MD', 'KY', 'OK', 'WV', 'DE']

# URL source types that may contain people
PEOPLE_SOURCE_TYPES = ['leadership_page', 'team_page', 'about_page', 'blog']

# Title patterns for role detection (case-insensitive)
TITLE_PATTERNS = {
    'CEO': [
        r'\b(?:chief\s+executive\s+officer|ceo|president|owner|founder|principal)\b',
        r'\b(?:managing\s+director|executive\s+director|general\s+manager)\b',
    ],
    'CFO': [
        r'\b(?:chief\s+financial\s+officer|cfo|controller|treasurer|finance\s+director)\b',
        r'\b(?:vp\s+(?:of\s+)?finance|director\s+of\s+finance)\b',
    ],
    'HR': [
        r'\b(?:chief\s+(?:human\s+resources|people|hr)\s+officer|chro)\b',
        r'\b(?:hr\s+(?:manager|director)|human\s+resources\s+(?:manager|director))\b',
        r'\b(?:director\s+of\s+(?:hr|human\s+resources|people|talent))\b',
        r'\b(?:vp\s+(?:of\s+)?(?:hr|human\s+resources|people))\b',
    ],
}


class StatePipeline:
    """Orchestrates the full extraction pipeline for a state."""
    
    def __init__(self, state: str, batch_size: int = 50, verbose: bool = True):
        self.state = state.upper()
        self.batch_size = batch_size
        self.verbose = verbose
        self.conn = psycopg2.connect(DATABASE_URL)
        self.stats = {
            'baseline': {},
            'extraction': {},
            'assignment': {},
            'final': {},
        }
    
    def log(self, msg: str):
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def close(self):
        self.conn.close()
    
    # =========================================================================
    # STAGE 1: CHECK BASELINE
    # =========================================================================
    
    def check_baseline(self) -> Dict:
        """Gather baseline metrics before extraction."""
        self.log(f"STAGE 1: Checking baseline for {self.state}...")
        cur = self.conn.cursor()
        
        # Company count
        cur.execute('''
            SELECT COUNT(*) FROM company.company_master 
            WHERE address_state = %s
        ''', (self.state,))
        companies = cur.fetchone()[0]
        
        # URLs available
        cur.execute('''
            SELECT COUNT(*) FROM company.company_source_urls csu
            JOIN cl.company_identity_bridge cib ON csu.company_unique_id = cib.source_company_id
            JOIN company.company_master cm ON cib.source_company_id = cm.company_unique_id
            WHERE cm.address_state = %s
            AND csu.source_type IN %s
            AND csu.source_url IS NOT NULL
        ''', (self.state, tuple(PEOPLE_SOURCE_TYPES)))
        urls = cur.fetchone()[0]
        
        # Existing people
        cur.execute('''
            SELECT COUNT(*) FROM people.people_master pm
            WHERE pm.company_unique_id IN (
                SELECT cib.source_company_id 
                FROM cl.company_identity_bridge cib
                JOIN company.company_master cm ON cib.source_company_id = cm.company_unique_id
                WHERE cm.address_state = %s
            )
        ''', (self.state,))
        existing_people = cur.fetchone()[0]
        
        # Slot coverage
        cur.execute('''
            SELECT cs.slot_type, 
                   SUM(CASE WHEN cs.is_filled THEN 1 ELSE 0 END) as filled,
                   COUNT(*) as total
            FROM people.company_slot cs
            JOIN cl.company_identity_bridge cib ON cs.company_unique_id = cib.company_sov_id::text
            JOIN company.company_master cm ON cib.source_company_id = cm.company_unique_id
            WHERE cm.address_state = %s
            GROUP BY cs.slot_type
        ''', (self.state,))
        slots = {r[0]: {'filled': r[1], 'total': r[2]} for r in cur.fetchall()}
        
        self.stats['baseline'] = {
            'companies': companies,
            'urls': urls,
            'existing_people': existing_people,
            'slots': slots,
        }
        
        self.log(f"  Companies: {companies}")
        self.log(f"  URLs: {urls}")
        self.log(f"  Existing people: {existing_people}")
        for slot_type, data in slots.items():
            pct = (data['filled'] / data['total'] * 100) if data['total'] > 0 else 0
            self.log(f"  {slot_type} slots: {data['filled']}/{data['total']} ({pct:.1f}%)")
        
        return self.stats['baseline']
    
    # =========================================================================
    # STAGE 2: MINT ORPHANS
    # =========================================================================
    
    def mint_orphans(self) -> int:
        """Create identity bridge entries for orphan companies."""
        self.log(f"STAGE 2: Minting orphans for {self.state}...")
        cur = self.conn.cursor()
        
        # Find companies without bridge entries
        cur.execute('''
            SELECT cm.company_unique_id, cm.company_name
            FROM company.company_master cm
            LEFT JOIN cl.company_identity_bridge cib ON cm.company_unique_id = cib.source_company_id
            WHERE cm.address_state = %s
            AND cib.source_company_id IS NULL
        ''', (self.state,))
        orphans = cur.fetchall()
        
        if not orphans:
            self.log("  No orphans found")
            return 0
        
        self.log(f"  Found {len(orphans)} orphans, minting...")
        
        for company_id, company_name in orphans:
            # Generate a new sovereign ID (UUID)
            cur.execute('SELECT gen_random_uuid()')
            sov_id = cur.fetchone()[0]
            
            # Create bridge record (source_company_id is TEXT, holds DOCTRINE ID)
            cur.execute('''
                INSERT INTO cl.company_identity_bridge (
                    bridge_id, source_company_id, company_sov_id, source_system, minted_at
                ) VALUES (gen_random_uuid(), %s, %s, 'orphan_mint', NOW())
                ON CONFLICT DO NOTHING
            ''', (company_id, sov_id))
        
        self.conn.commit()
        self.log(f"  Minted {len(orphans)} orphan companies")
        return len(orphans)
    
    # =========================================================================
    # STAGE 3: INIT SLOTS
    # =========================================================================
    
    def init_slots(self) -> int:
        """Create CEO/CFO/HR slots for companies with outreach records."""
        self.log(f"STAGE 3: Initializing slots for {self.state}...")
        cur = self.conn.cursor()
        
        # Find companies with outreach but missing slots
        cur.execute('''
            SELECT DISTINCT cib.company_sov_id, o.outreach_id
            FROM cl.company_identity_bridge cib
            JOIN company.company_master cm ON cib.source_company_id = cm.company_unique_id
            JOIN outreach.outreach o ON o.sovereign_id = cib.company_sov_id
            WHERE cm.address_state = %s
            AND NOT EXISTS (
                SELECT 1 FROM people.company_slot cs 
                WHERE cs.company_unique_id = cib.company_sov_id::text
            )
        ''', (self.state,))
        companies = cur.fetchall()
        
        if not companies:
            self.log("  No new slots needed")
            return 0
        
        slots_created = 0
        for sov_id, outreach_id in companies:
            for slot_type in ['CEO', 'CFO', 'HR']:
                cur.execute('''
                    INSERT INTO people.company_slot (
                        slot_id, outreach_id, company_unique_id, slot_type, is_filled
                    ) VALUES (
                        gen_random_uuid(), %s, %s, %s, false
                    ) ON CONFLICT DO NOTHING
                ''', (outreach_id, str(sov_id), slot_type))
                slots_created += 1
        
        self.conn.commit()
        self.log(f"  Created {slots_created} slots for {len(companies)} companies")
        return slots_created
    
    # =========================================================================
    # STAGE 4: FREE EXTRACTION
    # =========================================================================
    
    def extract_from_url(self, url: str) -> List[Dict]:
        """Extract people from a single URL using FREE methods only."""
        people = []
        
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                resp = client.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                if resp.status_code != 200:
                    return []
                html = resp.text
        except Exception:
            return []
        
        try:
            tree = HTMLParser(html)
        except Exception:
            return []
        
        # Extract text from common containers
        text_blocks = []
        for selector in ['article', 'main', '.team', '.leadership', '.about', '.staff', 'body']:
            for node in tree.css(selector):
                text_blocks.append(node.text(separator=' '))
        
        full_text = ' '.join(text_blocks)
        
        # Pattern: "Name, Title" or "Name - Title" or "Name | Title"
        name_title_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)[\s,\-–|]+([A-Za-z\s&]+(?:Officer|Director|Manager|President|CEO|CFO|HR|Owner|Founder|Principal|Controller|Treasurer))'
        
        for match in re.finditer(name_title_pattern, full_text):
            name = match.group(1).strip()
            title = match.group(2).strip()
            
            # Validate name (2+ parts, not too long)
            name_parts = name.split()
            if len(name_parts) < 2 or len(name) > 50:
                continue
            
            # Determine role from title
            role = self._classify_title(title)
            
            people.append({
                'raw_name': name,
                'first_name': name_parts[0],
                'last_name': ' '.join(name_parts[1:]),
                'raw_title': title,
                'normalized_title': title.title(),
                'mapped_slot_type': role,
            })
        
        return people
    
    def _classify_title(self, title: str) -> str:
        """Classify a title into CEO/CFO/HR/UNKNOWN."""
        title_lower = title.lower()
        for role, patterns in TITLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    return role
        return 'UNKNOWN'
    
    def _refresh_connection(self):
        """Refresh the database connection."""
        try:
            self.conn.close()
        except:
            pass
        self.conn = psycopg2.connect(DATABASE_URL)
    
    def run_extraction(self) -> Dict:
        """Run FREE extraction on all unprocessed URLs."""
        self.log(f"STAGE 4: Running FREE extraction for {self.state}...")
        cur = self.conn.cursor()
        
        # Get unprocessed URLs
        cur.execute('''
            SELECT csu.source_id, csu.source_url, csu.company_unique_id, cib.company_sov_id
            FROM company.company_source_urls csu
            JOIN cl.company_identity_bridge cib ON csu.company_unique_id = cib.source_company_id
            JOIN company.company_master cm ON cib.source_company_id = cm.company_unique_id
            WHERE cm.address_state = %s
            AND csu.source_type IN %s
            AND csu.source_url IS NOT NULL
            AND (csu.extraction_status IS NULL OR csu.extraction_status = 'pending')
            LIMIT %s
        ''', (self.state, tuple(PEOPLE_SOURCE_TYPES), self.batch_size))
        
        urls = cur.fetchall()
        self.log(f"  Processing {len(urls)} URLs...")
        
        stats = {'processed': 0, 'success': 0, 'people_found': 0, 'queued': 0}
        
        for source_id, url, company_doctrine_id, company_sov_id in urls:
            stats['processed'] += 1
            
            people = self.extract_from_url(url)
            
            # Reconnect for each URL to avoid idle timeout
            try:
                cur.execute("SELECT 1")
            except:
                self._refresh_connection()
                cur = self.conn.cursor()
            
            if people:
                stats['success'] += 1
                stats['people_found'] += len(people)
                
                # Stage the people
                for person in people:
                    cur.execute('''
                        INSERT INTO people.people_staging (
                            source_url_id, company_unique_id, raw_name, first_name, last_name,
                            raw_title, normalized_title, mapped_slot_type, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                        ON CONFLICT DO NOTHING
                    ''', (
                        source_id, str(company_sov_id), 
                        person['raw_name'][:255] if person['raw_name'] else None,
                        person['first_name'][:100] if person['first_name'] else None,
                        person['last_name'][:100] if person['last_name'] else None,
                        person['raw_title'][:255] if person['raw_title'] else None,
                        person['normalized_title'][:100] if person['normalized_title'] else None,
                        person['mapped_slot_type'][:20]
                    ))
                
                # Update URL status
                cur.execute('''
                    UPDATE company.company_source_urls 
                    SET extraction_status = 'complete', 
                        extracted_at = NOW(),
                        people_extracted = %s
                    WHERE source_id = %s
                ''', (len(people), source_id))
            else:
                # Queue for paid enrichment
                stats['queued'] += 1
                cur.execute('''
                    INSERT INTO people.paid_enrichment_queue (
                        source_url_id, company_unique_id, source_url, queued_at
                    ) VALUES (%s, %s, %s, NOW())
                    ON CONFLICT DO NOTHING
                ''', (source_id, str(company_sov_id), url))
                
                cur.execute('''
                    UPDATE company.company_source_urls 
                    SET extraction_status = 'queued_for_paid',
                        requires_paid_enrichment = true
                    WHERE source_id = %s
                ''', (source_id,))
            
            # Commit each URL immediately
            self.conn.commit()
            
            # Progress update every 50 URLs
            if stats['processed'] % 50 == 0:
                self.log(f"    Processed {stats['processed']}/{len(urls)}...")
        
        self.stats['extraction'] = stats
        
        self.log(f"  Processed: {stats['processed']}")
        self.log(f"  Success: {stats['success']}")
        self.log(f"  People found: {stats['people_found']}")
        self.log(f"  Queued for paid: {stats['queued']}")
        
        return stats
    
    # =========================================================================
    # STAGE 5: ASSIGN STAGED
    # =========================================================================
    
    def _generate_person_doctrine_id(self, sequence: int) -> str:
        """Generate a person DOCTRINE ID from sequence number."""
        seg4 = str(sequence % 100).zfill(2)
        seg5 = str(sequence).zfill(5)
        seg6 = str(sequence % 1000).zfill(3)
        return f"04.04.02.{seg4}.{seg5}.{seg6}"
    
    def _person_id_to_slot_id(self, person_id: str) -> str:
        """Convert person DOCTRINE ID to slot DOCTRINE ID."""
        return person_id.replace("04.04.02", "04.04.05")
    
    def assign_staged(self) -> Dict:
        """Assign staged people to slots with DOCTRINE IDs."""
        self.log(f"STAGE 5: Assigning staged people to slots...")
        cur = self.conn.cursor()
        
        # Get max person sequence (extract 5th segment as integer)
        cur.execute('''
            SELECT MAX(CAST(SPLIT_PART(unique_id, '.', 5) AS INTEGER)) 
            FROM people.people_master 
            WHERE unique_id LIKE '04.04.02.%'
        ''')
        max_seq = cur.fetchone()[0]
        current_seq = (max_seq or 0) + 1
        self.log(f"  Starting sequence: {current_seq}")
        
        # Get assignable staged people
        cur.execute('''
            SELECT DISTINCT ON (ps.id)
                ps.id AS staging_id,
                ps.first_name,
                ps.last_name,
                ps.normalized_title AS title,
                ps.email,
                ps.linkedin_url,
                ps.mapped_slot_type,
                ps.company_unique_id AS company_uuid,
                cib.source_company_id AS company_doctrine_id,
                cs.slot_id AS slot_uuid,
                cs.slot_type
            FROM people.people_staging ps
            JOIN cl.company_identity_bridge cib 
                ON ps.company_unique_id = cib.company_sov_id::text
            JOIN people.company_slot cs 
                ON cs.company_unique_id = ps.company_unique_id
                AND cs.is_filled = false
                AND (
                    (ps.mapped_slot_type = 'CEO' AND cs.slot_type = 'CEO')
                    OR (ps.mapped_slot_type = 'CFO' AND cs.slot_type = 'CFO')
                    OR (ps.mapped_slot_type = 'HR' AND cs.slot_type = 'HR')
                )
            WHERE ps.status = 'pending'
            AND ps.first_name IS NOT NULL
            AND ps.last_name IS NOT NULL
            ORDER BY ps.id, cs.slot_id
        ''')
        
        rows = cur.fetchall()
        self.log(f"  Found {len(rows)} assignable people")
        
        stats = {'assigned': 0, 'failed': 0}
        
        for row in rows:
            staging_id = row[0]
            first_name = row[1]
            last_name = row[2]
            title = row[3]
            email = row[4]
            linkedin_url = row[5]
            company_doctrine_id = row[8]
            slot_uuid = row[9]
            
            person_doctrine_id = self._generate_person_doctrine_id(current_seq)
            slot_doctrine_id = self._person_id_to_slot_id(person_doctrine_id)
            
            try:
                # Use savepoint for individual transactions
                cur.execute("SAVEPOINT person_insert")
                
                # Insert into people_master
                cur.execute('''
                    INSERT INTO people.people_master (
                        unique_id, first_name, last_name, title, email, linkedin_url,
                        company_unique_id, company_slot_unique_id, source_system
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'free_extraction')
                ''', (
                    person_doctrine_id, first_name, last_name, title,
                    email, linkedin_url, company_doctrine_id, slot_doctrine_id
                ))
                
                # Update slot
                cur.execute('''
                    UPDATE people.company_slot
                    SET is_filled = true, filled_at = NOW(), 
                        person_unique_id = %s, source_system = 'free_extraction'
                    WHERE slot_id = %s
                ''', (person_doctrine_id, slot_uuid))
                
                # Mark staging as promoted
                cur.execute('''
                    UPDATE people.people_staging
                    SET status = 'promoted', processed_at = NOW()
                    WHERE id = %s
                ''', (staging_id,))
                
                cur.execute("RELEASE SAVEPOINT person_insert")
                stats['assigned'] += 1
                current_seq += 1
                
            except Exception as e:
                cur.execute("ROLLBACK TO SAVEPOINT person_insert")
                stats['failed'] += 1
                if stats['failed'] <= 3:  # Only log first 3 failures
                    self.log(f"    Failed: {e}")
        
        self.conn.commit()
        self.stats['assignment'] = stats
        
        self.log(f"  Assigned: {stats['assigned']}")
        self.log(f"  Failed: {stats['failed']}")
        
        return stats
    
    # =========================================================================
    # STAGE 6: CREATE MISSING OUTREACH/SLOTS
    # =========================================================================
    
    def create_missing_outreach_and_slots(self) -> Dict:
        """Create outreach records and slots for companies that need them."""
        self.log(f"STAGE 6: Creating missing outreach/slots...")
        cur = self.conn.cursor()
        
        # Find companies in staging without outreach
        cur.execute('''
            SELECT DISTINCT ps.company_unique_id, cm.company_name, cm.website_url
            FROM people.people_staging ps
            JOIN cl.company_identity_bridge cib ON ps.company_unique_id = cib.company_sov_id::text
            JOIN company.company_master cm ON cib.source_company_id = cm.company_unique_id
            LEFT JOIN outreach.outreach o ON o.sovereign_id = cib.company_sov_id
            WHERE ps.status = 'pending'
            AND o.outreach_id IS NULL
        ''')
        
        companies = cur.fetchall()
        stats = {'outreach_created': 0, 'slots_created': 0}
        
        if not companies:
            self.log("  No missing outreach records")
            return stats
        
        for company_sov_id, company_name, website_url in companies:
            # Extract domain from website
            domain = None
            if website_url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(website_url).netloc.replace('www.', '')
                except:
                    pass
            
            # Create outreach record
            cur.execute('''
                INSERT INTO outreach.outreach (outreach_id, sovereign_id, domain, created_at, updated_at)
                VALUES (gen_random_uuid(), %s, %s, NOW(), NOW())
                RETURNING outreach_id
            ''', (company_sov_id, domain))
            outreach_id = cur.fetchone()[0]
            stats['outreach_created'] += 1
            
            # Create slots
            for slot_type in ['CEO', 'CFO', 'HR']:
                cur.execute('''
                    INSERT INTO people.company_slot (
                        slot_id, outreach_id, company_unique_id, slot_type, is_filled
                    ) VALUES (gen_random_uuid(), %s, %s, %s, false)
                    ON CONFLICT DO NOTHING
                ''', (outreach_id, company_sov_id, slot_type))
                stats['slots_created'] += 1
        
        self.conn.commit()
        self.log(f"  Created {stats['outreach_created']} outreach records")
        self.log(f"  Created {stats['slots_created']} slots")
        
        return stats
    
    # =========================================================================
    # STAGE 7: REPORT
    # =========================================================================
    
    def generate_report(self) -> str:
        """Generate final report comparing before/after."""
        self.log(f"STAGE 7: Generating report...")
        cur = self.conn.cursor()
        
        # Get final stats
        cur.execute('''
            SELECT COUNT(*) FROM people.people_master pm
            WHERE pm.company_unique_id IN (
                SELECT cib.source_company_id 
                FROM cl.company_identity_bridge cib
                JOIN company.company_master cm ON cib.source_company_id = cm.company_unique_id
                WHERE cm.address_state = %s
            )
        ''', (self.state,))
        final_people = cur.fetchone()[0]
        
        cur.execute('''
            SELECT cs.slot_type, 
                   SUM(CASE WHEN cs.is_filled THEN 1 ELSE 0 END) as filled,
                   COUNT(*) as total
            FROM people.company_slot cs
            JOIN cl.company_identity_bridge cib ON cs.company_unique_id = cib.company_sov_id::text
            JOIN company.company_master cm ON cib.source_company_id = cm.company_unique_id
            WHERE cm.address_state = %s
            GROUP BY cs.slot_type
        ''', (self.state,))
        final_slots = {r[0]: {'filled': r[1], 'total': r[2]} for r in cur.fetchall()}
        
        cur.execute('SELECT status, COUNT(*) FROM people.people_staging GROUP BY status')
        staging = dict(cur.fetchall())
        
        cur.execute('SELECT COUNT(*) FROM people.paid_enrichment_queue')
        paid_queue = cur.fetchone()[0]
        
        # Build report
        report = f"""
{'='*60}
{self.state} EXTRACTION PIPELINE REPORT
{'='*60}

BASELINE (Before):
  Companies: {self.stats['baseline'].get('companies', 'N/A')}
  URLs available: {self.stats['baseline'].get('urls', 'N/A')}
  Existing people: {self.stats['baseline'].get('existing_people', 'N/A')}

EXTRACTION RESULTS:
  URLs processed: {self.stats['extraction'].get('processed', 0)}
  Successful extractions: {self.stats['extraction'].get('success', 0)}
  People found: {self.stats['extraction'].get('people_found', 0)}
  Queued for paid: {self.stats['extraction'].get('queued', 0)}

ASSIGNMENT RESULTS:
  People assigned to slots: {self.stats['assignment'].get('assigned', 0)}
  Assignment failures: {self.stats['assignment'].get('failed', 0)}

STAGING STATUS:
  Promoted: {staging.get('promoted', 0)}
  Pending: {staging.get('pending', 0)}

PAID ENRICHMENT QUEUE: {paid_queue}

FINAL RESULTS:
  Total people: {final_people}
  Change: +{final_people - self.stats['baseline'].get('existing_people', 0)}

SLOT COVERAGE:"""
        
        for slot_type in ['CEO', 'CFO', 'HR']:
            if slot_type in final_slots:
                data = final_slots[slot_type]
                pct = (data['filled'] / data['total'] * 100) if data['total'] > 0 else 0
                report += f"\n  {slot_type}: {data['filled']}/{data['total']} ({pct:.1f}%)"
        
        report += f"\n\n{'='*60}\n"
        
        print(report)
        return report
    
    # =========================================================================
    # MAIN PIPELINE
    # =========================================================================
    
    def run_full_pipeline(self):
        """Run the complete extraction pipeline."""
        print(f"\n{'#'*60}")
        print(f"# STARTING PIPELINE FOR {self.state}")
        print(f"{'#'*60}\n")
        
        start_time = time.time()
        
        # Stage 1: Baseline
        self.check_baseline()
        
        # Stage 2: Mint orphans
        self.mint_orphans()
        
        # Stage 3: Init slots
        self.init_slots()
        
        # Stage 4: Extract
        self.run_extraction()
        
        # Stage 5: Create missing outreach/slots
        self.create_missing_outreach_and_slots()
        
        # Stage 6: Assign (run twice to catch newly created slots)
        self.assign_staged()
        self.assign_staged()  # Second pass for new slots
        
        # Stage 7: Report
        self.generate_report()
        
        elapsed = time.time() - start_time
        self.log(f"Pipeline completed in {elapsed:.1f} seconds")


def main():
    parser = argparse.ArgumentParser(description='State Blog → People Extraction Pipeline')
    parser.add_argument('--state', required=True, help='State code (e.g., WV) or ALL')
    parser.add_argument('--batch-size', type=int, default=100, help='URLs per batch')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')
    
    args = parser.parse_args()
    
    if args.state.upper() == 'ALL':
        states = TARGET_STATES
    else:
        states = [args.state.upper()]
    
    for state in states:
        if state not in TARGET_STATES:
            print(f"Warning: {state} not in target states {TARGET_STATES}")
        
        pipeline = StatePipeline(
            state=state,
            batch_size=args.batch_size,
            verbose=not args.quiet
        )
        
        try:
            pipeline.run_full_pipeline()
        finally:
            pipeline.close()


if __name__ == '__main__':
    main()
