# n8n Webhook Setup for WV Validation Pipeline

Complete guide for setting up n8n webhooks to route validation failures to Google Sheets.

## Overview

The WV Validation Pipeline uses n8n webhooks to push company and person validation failures to Google Sheets. This document explains how to set up the required n8n workflows.

## n8n Instance

- **URL**: `https://n8n.barton.com`
- **Authentication**: Existing instance (credentials managed separately)

## Required Webhooks

### 1. Company Failures Webhook

**Webhook URL**: `https://n8n.barton.com/webhook/push-company-failures`

**Workflow**: Company Failures → Google Sheets

**Trigger**: Webhook (POST)

**Payload Structure**:
```json
{
  "sheet_name": "WV_Validation_Failures_2025",
  "tab_name": "Company_Failures",
  "data_rows": [
    {
      "company_id": "04.04.02.04.30000.001",
      "company_name": "Acme Corp WV",
      "fail_reason": "Missing industry field",
      "validation_timestamp": "2025-11-17T16:14:35",
      "state": "WV"
    }
  ],
  "timestamp": "2025-11-17T16:14:35",
  "state": "WV",
  "pipeline_id": "WV-VALIDATION-20251117-161435",
  "row_count": 2
}
```

**n8n Workflow Steps**:
1. **Webhook Trigger** (`push-company-failures`)
   - Method: POST
   - Path: `/webhook/push-company-failures`
   - Authentication: None (public endpoint)

2. **Extract Payload**
   - Extract: `sheet_name`, `tab_name`, `data_rows`, `state`, `pipeline_id`

3. **Google Sheets Node** (Append Rows)
   - **Spreadsheet**: `{{ $json.sheet_name }}` (WV_Validation_Failures_2025)
   - **Sheet**: `{{ $json.tab_name }}` (Company_Failures)
   - **Columns**: company_id, company_name, fail_reason, validation_timestamp, state
   - **Data**: `{{ $json.data_rows }}`
   - **Options**:
     - Data Mode: Auto-Map Columns
     - Insert Data: As Array

4. **Response**
   - Status Code: 200
   - Body:
     ```json
     {
       "status": "success",
       "sheet_name": "{{ $json.sheet_name }}",
       "tab_name": "{{ $json.tab_name }}",
       "rows_inserted": "{{ $json.row_count }}"
     }
     ```

---

### 2. Person Failures Webhook

**Webhook URL**: `https://n8n.barton.com/webhook/push-person-failures`

**Workflow**: Person Failures → Google Sheets

**Trigger**: Webhook (POST)

**Payload Structure**:
```json
{
  "sheet_name": "WV_Validation_Failures_2025",
  "tab_name": "Person_Failures",
  "data_rows": [
    {
      "person_id": "04.04.02.04.20000.001",
      "full_name": "John Doe",
      "email": "",
      "company_id": "04.04.02.04.30000.001",
      "company_name": "Acme Corp WV",
      "fail_reason": "Missing email address",
      "validation_timestamp": "2025-11-17T16:14:35",
      "state": "WV"
    }
  ],
  "timestamp": "2025-11-17T16:14:35",
  "state": "WV",
  "pipeline_id": "WV-VALIDATION-20251117-161435",
  "row_count": 3
}
```

**n8n Workflow Steps**:
1. **Webhook Trigger** (`push-person-failures`)
   - Method: POST
   - Path: `/webhook/push-person-failures`
   - Authentication: None (public endpoint)

2. **Extract Payload**
   - Extract: `sheet_name`, `tab_name`, `data_rows`, `state`, `pipeline_id`

3. **Google Sheets Node** (Append Rows)
   - **Spreadsheet**: `{{ $json.sheet_name }}` (WV_Validation_Failures_2025)
   - **Sheet**: `{{ $json.tab_name }}` (Person_Failures)
   - **Columns**: person_id, full_name, email, company_id, company_name, fail_reason, validation_timestamp, state
   - **Data**: `{{ $json.data_rows }}`
   - **Options**:
     - Data Mode: Auto-Map Columns
     - Insert Data: As Array

4. **Response**
   - Status Code: 200
   - Body:
     ```json
     {
       "status": "success",
       "sheet_name": "{{ $json.sheet_name }}",
       "tab_name": "{{ $json.tab_name }}",
       "rows_inserted": "{{ $json.row_count }}"
     }
     ```

---

## Google Sheet Setup

### Sheet Configuration

**Sheet Name**: `WV_Validation_Failures_2025`

**Tab 1: Company_Failures**

| Column | Type | Description |
|--------|------|-------------|
| company_id | Text | Barton ID (04.04.02.04.30000.###) |
| company_name | Text | Company name |
| fail_reason | Text | Validation failure reason |
| validation_timestamp | DateTime | Timestamp of validation |
| state | Text | State code (WV) |

**Headers Row 1**:
```
company_id | company_name | fail_reason | validation_timestamp | state
```

**Tab 2: Person_Failures**

| Column | Type | Description |
|--------|------|-------------|
| person_id | Text | Barton ID (04.04.02.04.20000.###) |
| full_name | Text | Person full name |
| email | Text | Email address (may be empty) |
| company_id | Text | Associated company Barton ID |
| company_name | Text | Associated company name |
| fail_reason | Text | Validation failure reason |
| validation_timestamp | DateTime | Timestamp of validation |
| state | Text | State code (WV) |

**Headers Row 1**:
```
person_id | full_name | email | company_id | company_name | fail_reason | validation_timestamp | state
```

### Google Sheets API Setup

1. **Enable Google Sheets API** in Google Cloud Console
2. **Create Service Account** with Sheets API access
3. **Share Sheet** with service account email
4. **Configure n8n** with service account credentials:
   - Go to n8n Settings → Credentials
   - Add Google Sheets OAuth2 API credential
   - Or use Service Account JSON

---

## Testing the Webhooks

### Test Company Failures Webhook

```bash
curl -X POST https://n8n.barton.com/webhook/push-company-failures \
  -H "Content-Type: application/json" \
  -d '{
    "sheet_name": "WV_Validation_Failures_2025",
    "tab_name": "Company_Failures",
    "data_rows": [
      {
        "company_id": "04.04.02.04.30000.999",
        "company_name": "Test Company",
        "fail_reason": "Test failure reason",
        "validation_timestamp": "2025-11-17T16:00:00",
        "state": "WV"
      }
    ],
    "timestamp": "2025-11-17T16:00:00",
    "state": "WV",
    "pipeline_id": "TEST-001",
    "row_count": 1
  }'
```

**Expected Response**:
```json
{
  "status": "success",
  "sheet_name": "WV_Validation_Failures_2025",
  "tab_name": "Company_Failures",
  "rows_inserted": "1"
}
```

### Test Person Failures Webhook

```bash
curl -X POST https://n8n.barton.com/webhook/push-person-failures \
  -H "Content-Type: application/json" \
  -d '{
    "sheet_name": "WV_Validation_Failures_2025",
    "tab_name": "Person_Failures",
    "data_rows": [
      {
        "person_id": "04.04.02.04.20000.999",
        "full_name": "Test Person",
        "email": "test@example.com",
        "company_id": "04.04.02.04.30000.999",
        "company_name": "Test Company",
        "fail_reason": "Test failure reason",
        "validation_timestamp": "2025-11-17T16:00:00",
        "state": "WV"
      }
    ],
    "timestamp": "2025-11-17T16:00:00",
    "state": "WV",
    "pipeline_id": "TEST-001",
    "row_count": 1
  }'
```

**Expected Response**:
```json
{
  "status": "success",
  "sheet_name": "WV_Validation_Failures_2025",
  "tab_name": "Person_Failures",
  "rows_inserted": "1"
}
```

---

## Integration with WV Validation Pipeline

### Python Integration

The WV validation pipeline automatically calls these webhooks via:

```python
from backend.google_sheets.push_to_sheet import push_company_failures, push_person_failures

# Push company failures
push_company_failures(
    sheet_name="WV_Validation_Failures_2025",
    failures=[...],
    state="WV",
    pipeline_id="WV-VALIDATION-20251117-161435"
)

# Push person failures
push_person_failures(
    sheet_name="WV_Validation_Failures_2025",
    failures=[...],
    state="WV",
    pipeline_id="WV-VALIDATION-20251117-161435"
)
```

### Retry Logic

Both webhooks implement retry logic:
- **Max Retries**: 3 attempts
- **Backoff**: Exponential [2s, 4s, 8s]
- **5xx Errors**: Retry with backoff
- **4xx Errors**: No retry (permanent failure)
- **Connection Errors**: Retry
- **Timeouts**: Retry

---

## Existing Webhooks (for reference)

### Phase 1b Person Validation

- **URL**: `https://n8n.barton.com/webhook/route-person-failure`
- **Sheet ID**: `1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg`
- **Tab**: Invalid_People

### Phase 1 Company Validation

- **URL**: `https://n8n.barton.com/webhook/route-company-failure`
- **Sheet ID**: `1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg`
- **Tab**: Invalid_Companies

---

## Troubleshooting

### Webhook Returns 404

**Problem**: Webhook endpoint not found

**Solution**:
1. Verify webhook is activated in n8n
2. Check webhook URL matches exactly
3. Ensure workflow is published (not in draft mode)

### Webhook Times Out

**Problem**: Request exceeds 30-second timeout

**Solution**:
1. Check n8n workflow execution time
2. Verify Google Sheets API is responding
3. Check for large batch sizes (consider chunking)

### Data Not Appearing in Sheet

**Problem**: Webhook succeeds but no data in Google Sheet

**Solution**:
1. Verify sheet_name matches exactly
2. Check tab_name is correct
3. Verify Google Sheets credentials in n8n
4. Check service account has edit access to sheet

### 403 Forbidden Error

**Problem**: Google Sheets API permission denied

**Solution**:
1. Share sheet with n8n service account email
2. Verify service account has "Editor" permission
3. Check Google Sheets API is enabled in Cloud Console

---

## Production Checklist

Before running production WV validation pipeline:

- [ ] Both n8n workflows created and activated
- [ ] Google Sheet "WV_Validation_Failures_2025" created
- [ ] Tab "Company_Failures" exists with headers
- [ ] Tab "Person_Failures" exists with headers
- [ ] Sheet shared with n8n service account
- [ ] Service account has "Editor" permission
- [ ] Test webhooks with curl (both should return 200)
- [ ] Verify test data appears in Google Sheet
- [ ] Delete test rows from sheet
- [ ] Run WV pipeline in dry-run mode: `python backend/run_wv_validation.py --dry-run`
- [ ] Run WV pipeline with limited scope: `python backend/run_wv_validation.py --limit 5`
- [ ] Verify failures appear in Google Sheet
- [ ] Run full production pipeline: `python backend/run_wv_validation.py`

---

## Support

**n8n Instance**: https://n8n.barton.com
**Documentation**: This file
**Related Files**:
- `backend/google_sheets/push_to_sheet.py` - Python integration
- `backend/run_wv_validation.py` - WV validation pipeline
- `backend/validator/webhook.py` - Existing webhook implementation (reference)

**Date**: 2025-11-17
**Status**: Ready for n8n configuration
