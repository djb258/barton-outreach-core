<!--
─────────────────────────────────────────────
📁 CTB Classification Metadata
─────────────────────────────────────────────
CTB Branch: docs
Barton ID: 06.01.00
Unique ID: CTB-10793FD3
Blueprint Hash:
Last Updated: 2025-10-23
Enforcement: ORBT
─────────────────────────────────────────────
-->

# Database Schema Diagram

```mermaid
erDiagram

    bit_signal {
        bigint NOT_NULL PK signal_id
        bigint company_id
        text NOT_NULL reason
        jsonb payload
        timestamp with time zone created_at
        timestamp with time zone processed_at
    }

    company_company {
        bigint NOT_NULL PK company_id
        text company_name
        text ein
        text website_url
        text linkedin_url
        text news_url
        text address_line1
        text address_line2
        text city
        text state
        text postal_code
        text country
        smallint renewal_month
        integer renewal_notice_window_days
        timestamp with time zone last_site_checked_at
        timestamp with time zone last_linkedin_checked_at
        timestamp with time zone last_news_checked_at
    }

    company_company_slot {
        bigint NOT_NULL PK company_slot_id
        bigint NOT_NULL company_id
        text NOT_NULL role_code
        bigint contact_id
    }

    company_next_company_urls_30d {
        bigint company_id
        text url_type
        text url
        timestamp with time zone last_checked_at
    }

    company_vw_anchor_staleness {
        bigint company_id
        text company_name
        text website_url
        text website_status
        text linkedin_url
        text linkedin_status
        text news_url
        text news_status
        text overall_status
    }

    company_vw_company_slots {
        bigint company_id
        text company_name
        bigint company_slot_id
        text role_code
        bigint contact_id
        text full_name
        text title
        text email
        text phone
        text profile_source_url
        text email_status
        timestamp with time zone email_checked_at
        text website_url
        text linkedin_url
        text news_url
    }

    company_vw_due_renewals_ready {
        bigint company_id
        text company_name
        date next_renewal_date
        date campaign_window_start
        boolean has_green_contact
    }

    company_vw_next_renewal {
        bigint company_id
        text company_name
        smallint renewal_month
        integer notice_days
        date next_renewal_date
        date campaign_window_start
    }

    marketing_ac_handoff {
        bigint NOT_NULL PK ac_handoff_id
        bigint booking_event_id
        timestamp with time zone created_at
    }

    marketing_booking_event {
        bigint NOT_NULL PK booking_event_id
        bigint company_id
        bigint contact_id
        text calley_ref
        timestamp with time zone created_at
    }

    marketing_campaign {
        bigint NOT_NULL PK campaign_id
        text name
        timestamp with time zone created_at
    }

    marketing_campaign_contact {
        bigint NOT_NULL PK campaign_contact_id
        bigint campaign_id
        bigint contact_id
        timestamp with time zone created_at
    }

    marketing_company_raw_intake {
        bigint NOT_NULL PK intake_id
        text company
        text company_name_for_emails
        text account
        text lists
        integer num_employees
        text industry
        text account_owner
        text website
        text company_linkedin_url
        text facebook_url
        text twitter_url
        text company_street
        text company_city
        text company_state
        text company_country
        text company_postal_code
        text company_address
        text company_phone
        text technologies
        text total_funding
        text latest_funding
        numeric latest_funding_amount
        date last_raised_at
        text annual_revenue
        integer number_of_retail_locations
        text apollo_account_id
        text sic_codes
        text naics_codes
        integer founded_year
        text logo_url
        text subsidiary_of
        text short_description
        text keywords
        text primary_intent_topic
        numeric primary_intent_score
        text secondary_intent_topic
        numeric secondary_intent_score
        text batch_id
        text source
        text status
        timestamp with time zone created_at
        timestamp with time zone updated_at
        timestamp with time zone processed_at
        text error_message
    }

    marketing_message_log {
        bigint NOT_NULL PK message_id
        bigint campaign_id
        bigint contact_id
        text status
        timestamp with time zone created_at
    }

    people_company_role_slots {
        uuid NOT_NULL id
        uuid NOT_NULL company_id
        text NOT_NULL role_type
        integer target_count
        integer priority_level
        text slot_status
        integer filled_count
        ARRAY seniority_requirements
        ARRAY department_preferences
        ARRAY title_keywords
        text process_id
        text unique_id
        text blueprint_version_hash
        timestamp without time zone created_at
        timestamp without time zone updated_at
        text created_by
    }

    people_contact {
        bigint NOT_NULL PK contact_id
        text full_name
        text title
        text email
        text phone
        timestamp with time zone created_at
        timestamp with time zone updated_at
        text profile_source_url
        timestamp with time zone last_profile_checked_at
    }

    people_contact_history {
        uuid NOT_NULL id
        uuid NOT_NULL person_id
        text NOT_NULL change_type
        jsonb old_values
        jsonb new_values
        ARRAY changed_fields
        text source_system
        text source_session_id
        text initiated_by
        text process_id
        text unique_id
        text blueprint_version_hash
        timestamp without time zone created_at
        text notes
    }

    people_contact_verification {
        bigint NOT_NULL contact_id
        text email_status
        timestamp with time zone email_checked_at
        integer email_confidence
        text email_source_url
    }

    people_due_email_recheck_30d {
        bigint contact_id
        text full_name
        text title
        text email
        text email_status
        timestamp with time zone email_checked_at
        timestamp with time zone last_checked_at
    }

    people_next_profile_urls_30d {
        bigint contact_id
        text url
        timestamp with time zone last_checked_at
    }

    people_slot_history {
        uuid NOT_NULL id
        uuid NOT_NULL slot_id
        uuid person_id
        text NOT_NULL action_type
        text old_status
        text new_status
        text source_system
        text scrape_session_id
        text process_id
        text unique_id
        text blueprint_version_hash
        timestamp without time zone created_at
        text initiated_by
        text notes
    }

    people_validation_status {
        uuid NOT_NULL id
        uuid NOT_NULL person_id
        text NOT_NULL email
        text NOT_NULL validation_provider
        text NOT_NULL validation_status
        numeric validation_score
        text validation_reason
        jsonb provider_response
        timestamp without time zone validated_at
        numeric validation_cost
        text process_id
        text unique_id
        text blueprint_version_hash
    }

    people_vw_profile_monitoring {
        bigint contact_id
        text full_name
        text email
        text profile_source_url
        timestamp with time zone last_profile_checked_at
        text email_status
        timestamp with time zone email_checked_at
        text profile_status
        text email_verification_status
        text assignment_status
    }

    people_vw_profile_staleness {
        bigint contact_id
        text full_name
        text email
        text profile_source_url
        text email_source_url
        text profile_status
        text email_status
    }

    company_company_slot }|--|| company_company : "belongs to"
    marketing_ac_handoff }|--|| marketing_booking_event : "belongs to"
    marketing_campaign_contact }|--|| marketing_campaign : "belongs to"
    marketing_message_log }|--|| marketing_campaign : "belongs to"
    people_contact_verification }|--|| people_contact : "belongs to"

```

## Schema Relationships Summary

### Core Tables
- **company.company**: Central company repository
- **company.company_slot**: Role-based contact slots (CEO, CFO, HR)
- **people.contact**: Contact information
- **people.contact_verification**: Email verification status

### Marketing Tables
- **marketing.campaign**: Campaign definitions
- **marketing.campaign_contact**: Campaign participants
- **marketing.message_log**: Communication tracking
- **marketing.booking_event**: Meeting bookings
- **marketing.ac_handoff**: Account handoffs

### Intent Tracking
- **bit.signal**: Buyer intent signals

### Key Relationships
1. Each company has exactly 3 slots (CEO, CFO, HR)
2. Each slot can have one contact assigned
3. Each contact has one verification record
4. Contacts can participate in multiple campaigns
5. All communications are logged in message_log

### Queue Views (Auto-Generated)
- `company.next_company_urls_30d` - URLs due for scraping
- `people.next_profile_urls_30d` - Profiles due for scraping  
- `people.due_email_recheck_30d` - Emails due for verification
- `company.vw_due_renewals_ready` - Companies ready for renewal campaigns
