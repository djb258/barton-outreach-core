# Apollo URL Parameters Documentation

## Working Example URL
```
https://app.apollo.io/#/people?finderViewId=5b8050d050a3893c382e9360&personLocations[]=Germany&page=1&sortByField=recommendations_score&organizationNumEmployeesRanges[]=5000%2C5200&organizationIndustryTagIds[]=5567e0bf7369641d115f0200&organizationIndustryTagIds[]=5567e3f3736964395d7a0000
```

## URL Structure Breakdown

### Base URL
- `https://app.apollo.io/#/people` - Apollo people search endpoint

### Query Parameters

#### 1. **finderViewId**
- Value: `5b8050d050a3893c382e9360`
- Purpose: Identifies a saved search view or filter preset in Apollo

#### 2. **personLocations[]**
- Value: `Germany`
- Purpose: Filters contacts by geographic location
- Format: Array parameter (can have multiple locations)

#### 3. **page**
- Value: `1`
- Purpose: Pagination control for results
- Note: Apollo typically shows 25-50 results per page

#### 4. **sortByField**
- Value: `recommendations_score`
- Purpose: Sorts results by Apollo's recommendation algorithm
- Other possible values: `name`, `title`, `company`, `last_activity`

#### 5. **organizationNumEmployeesRanges[]**
- Value: `5000%2C5200` (URL encoded: `5000,5200`)
- Purpose: Filters by company size (employee count range)
- Format: `min,max` employee count
- In this case: Companies with 5000-5200 employees

#### 6. **organizationIndustryTagIds[]**
- Values: 
  - `5567e0bf7369641d115f0200`
  - `5567e3f3736964395d7a0000`
- Purpose: Filters by industry categories
- Format: Apollo's internal industry classification IDs
- Note: Multiple industries can be specified (array parameter)

## Scraper Configuration

### Input Parameters
```json
{
    "url": "[Apollo URL with filters]",
    "cleanOutput": false,
    "totalRecords": 1000,
    "fileName": "[company_name]_contacts"
}
```

### Configuration Options

#### cleanOutput
- `false`: Returns raw data with all fields
- `true`: Returns cleaned/normalized data with selected fields only
- **Current Setting**: `false` (to preserve all data)

#### totalRecords
- Maximum number of contacts to scrape
- Default: `1000`
- Can be increased to `50000` for larger datasets
- Note: Higher values consume more Apify credits

#### fileName
- Pattern: `{company_name}_contacts`
- Spaces replaced with underscores
- Converted to lowercase
- Example: "German Tech Corp" → "german_tech_corp_contacts"

## Target Audience

Based on the URL parameters, this scraper targets:
- **Location**: Germany
- **Company Size**: Large enterprises (5000-5200 employees)
- **Industries**: Specific industry sectors (identified by Apollo IDs)
- **Sort Order**: Prioritizes contacts by Apollo's recommendation score

## Usage Notes

1. **Apollo Login Required**: The Apify actor must be configured with Apollo credentials
2. **Rate Limiting**: Apollo has rate limits; the scraper should handle these gracefully
3. **Data Freshness**: Apollo data is updated regularly; results may vary between runs
4. **Pagination**: For large result sets, multiple pages may need to be scraped
5. **Filtering**: Post-scraping filtering is applied to target specific job titles

## Common Industry Tag IDs

While the specific IDs in your URL are proprietary to Apollo, common industries include:
- Technology/Software
- Financial Services
- Healthcare
- Manufacturing
- Retail
- Telecommunications

To find specific industry IDs:
1. Perform a manual search in Apollo
2. Apply industry filters
3. Check the URL for the `organizationIndustryTagIds` parameter

## Troubleshooting

### No Results
- Verify the Apollo URL is accessible
- Check if filters are too restrictive
- Ensure Apollo account has access to the filtered data

### Incomplete Data
- Increase `totalRecords` parameter
- Check if pagination is working correctly
- Verify Apollo account permissions

### Authentication Issues
- Verify Apify actor has valid Apollo credentials
- Check if Apollo session has expired
- Ensure IP is not blocked by Apollo