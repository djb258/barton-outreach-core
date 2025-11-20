"""
Data Normalizer
Barton Doctrine ID: 04.04.02.04.80000.003

Clean and standardize data based on normalization rules.
All data cleaning logic lives here.
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse


class Normalizer:
    """
    Normalize and clean data from CSV

    Design: Rule-based data cleaning (config-driven)
    """

    def __init__(self, rules: Dict[str, Any]):
        """Initialize with normalization rules"""
        self.rules = rules

    def normalize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all fields in a row

        Args:
            row: Raw row data

        Returns:
            Normalized row data
        """
        normalized = {}

        # Company name
        normalized['company_name'] = self.normalize_company_name(row.get('company_name', ''))

        # Company domain
        normalized['company_domain'] = self.normalize_company_domain(
            row.get('company_domain', ''),
            row.get('company_website', ''),
            row.get('email', '')
        )

        # Person name
        normalized['full_name'] = self.normalize_person_name(row.get('full_name', ''))
        normalized['first_name'] = self.normalize_person_name(row.get('first_name', ''))
        normalized['last_name'] = self.normalize_person_name(row.get('last_name', ''))

        # If full_name exists but first/last don't, split
        if normalized['full_name'] and not (normalized['first_name'] and normalized['last_name']):
            parts = self.split_full_name(normalized['full_name'])
            normalized['first_name'] = parts['first_name']
            normalized['last_name'] = parts['last_name']

        # Title
        normalized['title'] = self.normalize_title(row.get('title', ''))

        # Email
        normalized['email'] = self.normalize_email(
            row.get('email', ''),
            normalized['company_domain']
        )

        # Phone
        normalized['phone'] = self.normalize_phone(row.get('phone', ''))

        # LinkedIn URL
        normalized['linkedin_url'] = self.normalize_linkedin_url(row.get('linkedin_url', ''))

        # Counts
        normalized['historical_open_count'] = self.normalize_count(row.get('historical_open_count', '0'))
        normalized['historical_reply_count'] = self.normalize_count(row.get('historical_reply_count', '0'))
        normalized['historical_meeting_count'] = self.normalize_count(row.get('historical_meeting_count', '0'))

        # Date
        normalized['last_engaged_at'] = self.normalize_date(row.get('last_engaged_at', ''))

        # Notes (pass through)
        normalized['notes'] = row.get('notes', '').strip()

        return normalized

    def normalize_company_name(self, name: str) -> str:
        """Normalize company name"""
        if not name:
            return ''

        rules = self.rules.get('company_name', {})

        # Trim whitespace
        name = name.strip()

        # Remove extra spaces
        if rules.get('dedupe_spaces', True):
            name = re.sub(r'\s+', ' ', name)

        # Remove common suffixes
        for pattern in rules.get('remove_patterns', []):
            name = name.replace(pattern, '').strip()

        # Title case
        if rules.get('standardize_casing') == 'title':
            name = name.title()

        return name.strip()

    def normalize_company_domain(self, domain: str, website: str, email: str) -> str:
        """
        Normalize company domain

        Tries: direct domain, extract from website, extract from email
        """
        rules = self.rules.get('company_domain', {})

        # Try direct domain first
        if domain:
            domain = self._clean_domain(domain, rules)
            if domain:
                return domain

        # Try extracting from website
        if website and rules.get('extract_from_website', True):
            domain = self._extract_domain_from_url(website)
            if domain:
                return domain

        # Try extracting from email
        if email and rules.get('extract_from_email', True):
            domain = self._extract_domain_from_email(email)
            if domain:
                return domain

        return ''

    def _clean_domain(self, domain: str, rules: Dict[str, Any]) -> str:
        """Clean a domain string"""
        if not domain:
            return ''

        # Lowercase
        if rules.get('lowercase', True):
            domain = domain.lower()

        # Remove protocols
        for protocol in rules.get('remove_protocols', []):
            domain = domain.replace(protocol, '')

        # Remove www
        if rules.get('remove_www', True):
            domain = domain.replace('www.', '')

        # Remove trailing slashes
        domain = domain.rstrip('/')

        # Remove path components
        if '/' in domain:
            domain = domain.split('/')[0]

        return domain.strip()

    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url if '//' in url else f'http://{url}')
            domain = parsed.netloc or parsed.path
            return self._clean_domain(domain, self.rules.get('company_domain', {}))
        except:
            return ''

    def _extract_domain_from_email(self, email: str) -> str:
        """Extract domain from email"""
        if '@' not in email:
            return ''

        domain = email.split('@')[-1].strip().lower()
        return domain

    def normalize_person_name(self, name: str) -> str:
        """Normalize person name"""
        if not name:
            return ''

        rules = self.rules.get('person_name', {})

        # Trim whitespace
        name = name.strip()

        # Remove prefixes
        for prefix in rules.get('remove_prefixes', []):
            if name.startswith(prefix):
                name = name[len(prefix):].strip()

        # Remove suffixes
        for suffix in rules.get('remove_suffixes', []):
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()

        # Title case
        if rules.get('title_case', True):
            name = name.title()

        return name.strip()

    def split_full_name(self, full_name: str) -> Dict[str, str]:
        """
        Split full name into first and last

        Args:
            full_name: Full name string

        Returns:
            {'first_name': str, 'last_name': str}
        """
        if not full_name:
            return {'first_name': '', 'last_name': ''}

        parts = full_name.strip().split()

        if len(parts) == 0:
            return {'first_name': '', 'last_name': ''}
        elif len(parts) == 1:
            return {'first_name': parts[0], 'last_name': ''}
        else:
            return {'first_name': parts[0], 'last_name': ' '.join(parts[1:])}

    def normalize_title(self, title: str) -> str:
        """Normalize job title"""
        if not title:
            return ''

        rules = self.rules.get('title', {})

        # Trim whitespace
        title = title.strip()

        # Standardize abbreviations
        abbreviations = rules.get('standardize_abbreviations', {})
        for standard, variants in abbreviations.items():
            for variant in variants:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(variant), re.IGNORECASE)
                title = pattern.sub(standard, title)

        # Remove extra whitespace
        if rules.get('remove_extra_whitespace', True):
            title = re.sub(r'\s+', ' ', title)

        # Title case
        if rules.get('title_case', True):
            title = title.title()

        return title.strip()

    def normalize_email(self, email: str, preferred_domain: str = '') -> str:
        """
        Normalize email address

        Args:
            email: Email string (may contain multiple emails)
            preferred_domain: Company domain to prefer work email

        Returns:
            Single normalized email (work email preferred)
        """
        if not email:
            return ''

        rules = self.rules.get('email', {})

        # Split multiple emails
        if rules.get('split_multiple', True):
            delimiters = rules.get('delimiter', [',', ';'])
            for delim in delimiters:
                if delim in email:
                    emails = [e.strip() for e in email.split(delim)]
                    # Prefer work email
                    if preferred_domain and rules.get('prefer_work_email', True):
                        work_emails = [e for e in emails if preferred_domain in e.lower()]
                        if work_emails:
                            email = work_emails[0]
                        else:
                            email = emails[0]
                    else:
                        email = emails[0]
                    break

        # Lowercase
        if rules.get('lowercase', True):
            email = email.lower()

        # Trim
        email = email.strip()

        # Basic validation
        if '@' not in email or '.' not in email:
            return ''

        return email

    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number"""
        if not phone:
            return ''

        rules = self.rules.get('phone', {})

        # Remove non-digits
        if rules.get('remove_non_digits', True):
            phone = re.sub(r'\D', '', phone)

        # Validate length
        if rules.get('validate_length', True):
            min_len = rules.get('min_length', 10)
            max_len = rules.get('max_length', 15)

            if len(phone) < min_len or len(phone) > max_len:
                return ''

        # Add country code if missing
        if len(phone) == 10:  # US number without country code
            phone = f"{rules.get('default_country_code', '+1')}{phone}"

        return phone

    def normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL"""
        if not url:
            return ''

        rules = self.rules.get('linkedin_url', {})

        # Lowercase
        if rules.get('lowercase', True):
            url = url.lower()

        # Remove tracking params
        if rules.get('remove_tracking_params', True):
            url = url.split('?')[0]

        # Standardize format
        if 'linkedin.com' in url:
            # Extract just the profile path
            if '/in/' in url:
                parts = url.split('/in/')
                if len(parts) > 1:
                    profile = parts[1].split('/')[0]
                    url = f"https://linkedin.com/in/{profile}"
            elif '/company/' in url:
                parts = url.split('/company/')
                if len(parts) > 1:
                    profile = parts[1].split('/')[0]
                    url = f"https://linkedin.com/company/{profile}"

        return url.strip()

    def normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date to ISO format

        Returns:
            ISO8601 date string or None
        """
        if not date_str or str(date_str).strip() == '':
            return None

        rules = self.rules.get('dates', {}).get('last_engaged_at', {})
        formats = rules.get('formats', ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'])

        for fmt in formats:
            try:
                dt = datetime.strptime(str(date_str).strip(), fmt)

                # Validate year range
                if rules.get('validate_range', False):
                    min_year = rules.get('min_year', 2020)
                    max_year = rules.get('max_year', 2025)

                    if dt.year < min_year or dt.year > max_year:
                        return None

                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

    def normalize_count(self, count: Any) -> int:
        """
        Normalize count field to integer

        Args:
            count: Count value (string or int)

        Returns:
            Integer count (0 if invalid)
        """
        try:
            value = int(count)

            # Validate range
            count_rules = self.rules.get('counts', {})
            min_val = count_rules.get('historical_open_count', {}).get('min', 0)
            max_val = count_rules.get('historical_open_count', {}).get('max', 10000)

            if value < min_val:
                return min_val
            if value > max_val:
                return max_val

            return value
        except (ValueError, TypeError):
            return 0
