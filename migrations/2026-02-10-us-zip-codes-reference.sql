-- Migration: US Zip Code Reference Table
-- Date: 2026-02-10
-- Source: uszips.xlsx (SimpleMaps)
-- Purpose: Searchable US zip code lookup with demographics, coordinates, and county data

-- Create reference schema for lookup/reference data
CREATE SCHEMA IF NOT EXISTS reference;

-- Create the zip codes table
CREATE TABLE reference.us_zip_codes (
    zip              TEXT PRIMARY KEY,
    lat              NUMERIC(10,5),
    lng              NUMERIC(10,5),
    city             TEXT,
    state_id         TEXT,          -- 2-letter abbreviation (NY, CA, TX)
    state_name       TEXT,
    zcta             BOOLEAN,
    parent_zcta      TEXT,
    population       INTEGER,
    density          NUMERIC(10,1),
    county_fips      TEXT,
    county_name      TEXT,
    county_weights   JSONB,
    county_names_all TEXT,
    county_fips_all  TEXT,
    imprecise        BOOLEAN,
    military         BOOLEAN,
    timezone         TEXT,

    -- Demographics
    age_median                    NUMERIC(5,1),
    male                          NUMERIC(5,1),   -- percentage
    female                        NUMERIC(5,1),   -- percentage
    married                       NUMERIC(5,1),   -- percentage
    family_size                   NUMERIC(4,2),
    income_household_median       INTEGER,
    income_household_six_figure   NUMERIC(5,1),   -- percentage
    home_ownership                NUMERIC(5,1),   -- percentage
    home_value                    INTEGER,
    rent_median                   INTEGER,
    education_college_or_above    NUMERIC(5,1),   -- percentage
    labor_force_participation     NUMERIC(5,1),   -- percentage
    unemployment_rate             NUMERIC(5,1),   -- percentage

    -- Race demographics (percentages)
    race_white                    NUMERIC(5,1),
    race_black                    NUMERIC(5,1),
    race_asian                    NUMERIC(5,1),
    race_native                   NUMERIC(5,1),
    race_pacific                  NUMERIC(5,1),
    race_other                    NUMERIC(5,1),
    race_multiple                 NUMERIC(5,1),

    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for searchability
CREATE INDEX idx_zip_state_id ON reference.us_zip_codes (state_id);
CREATE INDEX idx_zip_city ON reference.us_zip_codes (city);
CREATE INDEX idx_zip_city_state ON reference.us_zip_codes (city, state_id);
CREATE INDEX idx_zip_county_fips ON reference.us_zip_codes (county_fips);
CREATE INDEX idx_zip_county_name ON reference.us_zip_codes (county_name);
CREATE INDEX idx_zip_timezone ON reference.us_zip_codes (timezone);
CREATE INDEX idx_zip_population ON reference.us_zip_codes (population DESC NULLS LAST);

-- Table comment
COMMENT ON TABLE reference.us_zip_codes IS 'US zip code reference table with demographics, coordinates, and county data. Source: SimpleMaps uszips.xlsx';
COMMENT ON COLUMN reference.us_zip_codes.zip IS 'US zip code (text to preserve leading zeros)';
COMMENT ON COLUMN reference.us_zip_codes.state_id IS '2-letter state abbreviation';
COMMENT ON COLUMN reference.us_zip_codes.zcta IS 'TRUE if this is a ZIP Code Tabulation Area';
COMMENT ON COLUMN reference.us_zip_codes.county_weights IS 'JSON mapping county_fips to percentage weight';
