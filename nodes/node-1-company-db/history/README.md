# History Policy Sub-Node

**Altitude**: 30k (Declaration Only)
**Status**: Stub/Placeholder

## Purpose

The History sub-node manages data freshness and historical tracking:

- Track when company data was last updated
- Manage contact information freshness 
- Handle data versioning and change logs
- Implement skip strategies for stale data

## Skip Strategy (Declared)

### Freshness Thresholds
- **Company Data**: Skip if updated within 30 days
- **Contact Info**: Skip if validated within 7 days  
- **Lead Status**: Skip if scored within 24 hours

### Skip Policies
- `SKIP_FRESH`: Don't re-process recent data
- `SKIP_VALIDATED`: Don't re-validate confirmed contacts
- `SKIP_FAILED`: Don't retry permanently failed records

## Events (Placeholder)

### Tracking Events
- `data.stale` - Information exceeds freshness threshold
- `validation.expired` - Contact validation needs refresh
- `history.archived` - Old records moved to archive

### Skip Events
- `process.skipped` - Operation skipped due to freshness
- `validation.skipped` - Validation skipped, still valid
- `retry.skipped` - Retry skipped due to failure policy

## Future Design (20k+)

At higher altitudes, this sub-node will implement:
- Automated freshness monitoring
- Smart skip logic based on data age
- Historical change tracking
- Data archival and cleanup

## Current State

⚠️ **30k Scaffolding Only**: This directory contains policy declarations only. No implementation exists at 30k altitude.