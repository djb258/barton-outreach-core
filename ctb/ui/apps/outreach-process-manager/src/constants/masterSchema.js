// Master Schema for Outreach Process - 37 fields from Google Sheets
export const MASTER_SCHEMA = [
  // Core Identity Fields
  { 
    value: 'number', 
    label: 'Number', 
    required: false,
    category: 'core',
    type: 'number',
    description: 'Unique identifier number for the company record'
  },
  { 
    value: 'company', 
    label: 'Company', 
    required: true,
    category: 'core',
    type: 'text',
    description: 'Company name or organization name'
  },
  { 
    value: 'company_name_for_emails', 
    label: 'Company Name for Emails', 
    required: false,
    category: 'core',
    type: 'text',
    description: 'Formatted company name specifically for email communications'
  },

  // Business Information Fields
  { 
    value: 'account_stage', 
    label: 'Account Stage', 
    required: false,
    category: 'business',
    type: 'text',
    description: 'Current stage of the account in the sales pipeline'
  },
  { 
    value: 'lists', 
    label: 'Lists', 
    required: false,
    category: 'business',
    type: 'text',
    description: 'Marketing or sales lists this company belongs to'
  },
  { 
    value: 'num_employees', 
    label: '# Employees', 
    required: false,
    category: 'business',
    type: 'number',
    description: 'Number of employees in the company'
  },
  { 
    value: 'industry', 
    label: 'Industry', 
    required: false,
    category: 'business',
    type: 'text',
    description: 'Industry sector or vertical the company operates in'
  },
  { 
    value: 'account_owner', 
    label: 'Account Owner', 
    required: false,
    category: 'business',
    type: 'text',
    description: 'Sales representative or account manager assigned'
  },

  // Digital Presence Fields
  { 
    value: 'website', 
    label: 'Website', 
    required: false,
    category: 'digital',
    type: 'url',
    description: 'Company website URL'
  },
  { 
    value: 'company_linkedin_url', 
    label: 'Company LinkedIn URL', 
    required: false,
    category: 'digital',
    type: 'url',
    description: 'LinkedIn company page URL'
  },
  { 
    value: 'facebook_url', 
    label: 'Facebook URL', 
    required: false,
    category: 'digital',
    type: 'url',
    description: 'Facebook business page URL'
  },
  { 
    value: 'twitter_url', 
    label: 'Twitter URL', 
    required: false,
    category: 'digital',
    type: 'url',
    description: 'Twitter/X company profile URL'
  },

  // Location Fields
  { 
    value: 'company_street', 
    label: 'Company Street', 
    required: false,
    category: 'location',
    type: 'text',
    description: 'Street address of company headquarters'
  },
  { 
    value: 'company_city', 
    label: 'Company City', 
    required: false,
    category: 'location',
    type: 'text',
    description: 'City where company is located'
  },
  { 
    value: 'company_state', 
    label: 'Company State', 
    required: false,
    category: 'location',
    type: 'text',
    description: 'State or province where company is located'
  },
  { 
    value: 'company_country', 
    label: 'Company Country', 
    required: false,
    category: 'location',
    type: 'text',
    description: 'Country where company is headquartered'
  },
  { 
    value: 'company_postal_code', 
    label: 'Company Postal Code', 
    required: false,
    category: 'location',
    type: 'text',
    description: 'ZIP or postal code of company address'
  },
  { 
    value: 'company_address', 
    label: 'Company Address', 
    required: false,
    category: 'location',
    type: 'text',
    description: 'Full formatted company address'
  },

  // Marketing & Sales Fields
  { 
    value: 'keywords', 
    label: 'Keywords', 
    required: false,
    category: 'marketing',
    type: 'text',
    description: 'Relevant keywords or tags for the company'
  },
  { 
    value: 'company_phone', 
    label: 'Company Phone', 
    required: false,
    category: 'contact',
    type: 'phone',
    description: 'Main company phone number'
  },
  { 
    value: 'seo_description', 
    label: 'SEO Description', 
    required: false,
    category: 'marketing',
    type: 'text',
    description: 'SEO description or meta description of the company'
  },
  { 
    value: 'technologies', 
    label: 'Technologies', 
    required: false,
    category: 'technical',
    type: 'text',
    description: 'Technologies or software stack used by the company'
  },

  // Financial Information Fields
  { 
    value: 'total_funding', 
    label: 'Total Funding', 
    required: false,
    category: 'financial',
    type: 'currency',
    description: 'Total amount of funding raised by the company'
  },
  { 
    value: 'latest_funding', 
    label: 'Latest Funding', 
    required: false,
    category: 'financial',
    type: 'text',
    description: 'Type or round of latest funding (Series A, B, etc.)'
  },
  { 
    value: 'latest_funding_amount', 
    label: 'Latest Funding Amount', 
    required: false,
    category: 'financial',
    type: 'currency',
    description: 'Amount raised in the latest funding round'
  },
  { 
    value: 'last_raised_at', 
    label: 'Last Raised At', 
    required: false,
    category: 'financial',
    type: 'date',
    description: 'Date of the last funding round'
  },
  { 
    value: 'annual_revenue', 
    label: 'Annual Revenue', 
    required: false,
    category: 'financial',
    type: 'currency',
    description: 'Estimated or reported annual revenue'
  },
  { 
    value: 'number_of_retail_locations', 
    label: 'Number of Retail Locations', 
    required: false,
    category: 'business',
    type: 'number',
    description: 'Number of physical retail locations'
  },

  // External System Integration Fields
  { 
    value: 'apollo_account_id', 
    label: 'Apollo Account ID', 
    required: false,
    category: 'integration',
    type: 'text',
    description: 'Account ID from Apollo.io platform'
  },
  { 
    value: 'sic_codes', 
    label: 'SIC Codes', 
    required: false,
    category: 'classification',
    type: 'text',
    description: 'Standard Industrial Classification codes'
  },

  // Company Profile Fields
  { 
    value: 'short_description', 
    label: 'Short Description', 
    required: false,
    category: 'profile',
    type: 'text',
    description: 'Brief description of what the company does'
  },
  { 
    value: 'founded_year', 
    label: 'Founded Year', 
    required: false,
    category: 'profile',
    type: 'number',
    description: 'Year the company was founded'
  },
  { 
    value: 'logo_url', 
    label: 'Logo URL', 
    required: false,
    category: 'profile',
    type: 'url',
    description: 'URL to the company logo image'
  },
  { 
    value: 'subsidiary_of', 
    label: 'Subsidiary of', 
    required: false,
    category: 'profile',
    type: 'text',
    description: 'Parent company if this is a subsidiary'
  },

  // Intent & Scoring Fields
  { 
    value: 'primary_intent_topic', 
    label: 'Primary Intent Topic', 
    required: false,
    category: 'intent',
    type: 'text',
    description: 'Primary area of business intent or interest'
  },
  { 
    value: 'primary_intent_score', 
    label: 'Primary Intent Score', 
    required: false,
    category: 'intent',
    type: 'number',
    description: 'Score indicating strength of primary intent (0-100)'
  },
  { 
    value: 'secondary_intent_topic', 
    label: 'Secondary Intent Topic', 
    required: false,
    category: 'intent',
    type: 'text',
    description: 'Secondary area of business intent or interest'
  },
  { 
    value: 'secondary_intent_score', 
    label: 'Secondary Intent Score', 
    required: false,
    category: 'intent',
    type: 'number',
    description: 'Score indicating strength of secondary intent (0-100)'
  }
];

// Schema categories for organizing the fields
export const SCHEMA_CATEGORIES = {
  core: { label: 'Core Identity', color: 'blue', icon: 'Building2' },
  business: { label: 'Business Info', color: 'green', icon: 'Briefcase' },
  digital: { label: 'Digital Presence', color: 'purple', icon: 'Globe' },
  location: { label: 'Location', color: 'orange', icon: 'MapPin' },
  contact: { label: 'Contact', color: 'cyan', icon: 'Phone' },
  marketing: { label: 'Marketing', color: 'pink', icon: 'Megaphone' },
  technical: { label: 'Technical', color: 'indigo', icon: 'Code' },
  financial: { label: 'Financial', color: 'emerald', icon: 'DollarSign' },
  integration: { label: 'Integration', color: 'yellow', icon: 'Link' },
  classification: { label: 'Classification', color: 'red', icon: 'Tag' },
  profile: { label: 'Profile', color: 'violet', icon: 'User' },
  intent: { label: 'Intent & Scoring', color: 'teal', icon: 'Target' }
};

// Required fields for validation
export const REQUIRED_FIELDS = MASTER_SCHEMA?.filter(field => field?.required)?.map(field => field?.value);

// Field groups for easier management
export const getFieldsByCategory = (category) => {
  return MASTER_SCHEMA?.filter(field => field?.category === category);
};

// Auto-mapping suggestions based on common CSV header patterns
export const getAutoMappingSuggestions = (csvHeader) => {
  const header = csvHeader?.toLowerCase()?.replace(/[^a-z0-9]/g, '');
  
  const mappingPatterns = {
    // Core fields
    'number': ['number', 'id', 'recordnumber', 'recordid'],
    'company': ['company', 'companyname', 'name', 'organization', 'business'],
    'company_name_for_emails': ['companynameforemail', 'emailcompanyname', 'companyemail'],
    
    // Business fields
    'account_stage': ['accountstage', 'stage', 'salesstage', 'pipeline'],
    'lists': ['lists', 'segments', 'tags', 'categories'],
    'num_employees': ['employees', 'numemployees', 'employeecount', 'headcount', 'size'],
    'industry': ['industry', 'sector', 'vertical', 'businesstype'],
    'account_owner': ['accountowner', 'owner', 'rep', 'salesrep', 'manager'],
    
    // Digital presence
    'website': ['website', 'url', 'domain', 'site', 'web'],
    'company_linkedin_url': ['linkedin', 'linkedinurl', 'companylinkedin'],
    'facebook_url': ['facebook', 'facebookurl', 'fb'],
    'twitter_url': ['twitter', 'twitterurl', 'x'],
    
    // Location
    'company_street': ['street', 'address1', 'streetaddress', 'companystreet'],
    'company_city': ['city', 'companycity'],
    'company_state': ['state', 'province', 'companystate'],
    'company_country': ['country', 'companycountry'],
    'company_postal_code': ['postalcode', 'zipcode', 'zip', 'postcode'],
    'company_address': ['address', 'fulladdress', 'companyaddress'],
    
    // Contact & Marketing
    'company_phone': ['phone', 'telephone', 'companyphone', 'phonenumber'],
    'keywords': ['keywords', 'tags', 'searchterms'],
    'seo_description': ['seodescription', 'metadescription', 'description'],
    'technologies': ['technologies', 'tech', 'software', 'stack'],
    
    // Financial
    'total_funding': ['totalfunding', 'funding', 'investment'],
    'latest_funding': ['latestfunding', 'lastfunding', 'fundingtype'],
    'latest_funding_amount': ['latestfundingamount', 'lastfundingamount'],
    'last_raised_at': ['lastraisedat', 'fundingdate', 'lastfunded'],
    'annual_revenue': ['annualrevenue', 'revenue', 'sales'],
    'number_of_retail_locations': ['retaillocations', 'locations', 'stores'],
    
    // Integration & Classification
    'apollo_account_id': ['apolloaccountid', 'apolloid'],
    'sic_codes': ['siccodes', 'sic', 'industrycode'],
    
    // Profile
    'short_description': ['shortdescription', 'description', 'about', 'summary'],
    'founded_year': ['foundedyear', 'founded', 'established'],
    'logo_url': ['logourl', 'logo', 'companylogo'],
    'subsidiary_of': ['subsidiaryof', 'parentcompany', 'parent'],
    
    // Intent
    'primary_intent_topic': ['primaryintenttopic', 'primaryintent', 'intent1'],
    'primary_intent_score': ['primaryintentscore', 'intentscore1'],
    'secondary_intent_topic': ['secondaryintenttopic', 'secondaryintent', 'intent2'],
    'secondary_intent_score': ['secondaryintentscore', 'intentscore2']
  };
  
  for (const [fieldValue, patterns] of Object.entries(mappingPatterns)) {
    if (patterns?.some(pattern => header?.includes(pattern))) {
      return fieldValue;
    }
  }
  
  return null;
};