/**
 * Google Apps Script: Setup Validation Failure Tabs
 *
 * This script automatically creates and configures tabs for validation failures.
 *
 * Instructions:
 * 1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg/edit
 * 2. Go to: Extensions → Apps Script
 * 3. Delete any existing code
 * 4. Paste this entire script
 * 5. Click the disk icon to save
 * 6. Run: setupValidationTabs() function
 * 7. Authorize the script when prompted
 *
 * Date: 2025-11-17
 * Status: Production Ready
 */

function setupValidationTabs() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  Logger.log("Starting validation tabs setup...");

  // Create Company Failures tab
  createCompanyFailuresTab(ss);

  // Create Person Failures tab
  createPersonFailuresTab(ss);

  Logger.log("✅ Setup complete!");

  // Show success message
  SpreadsheetApp.getUi().alert(
    'Success!',
    'Validation tabs created successfully:\n\n' +
    '✅ Company_Failures tab\n' +
    '✅ Person_Failures tab\n\n' +
    'You can now configure your n8n workflow.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}


/**
 * Create Company Failures Tab
 */
function createCompanyFailuresTab(ss) {
  var sheetName = "Company_Failures";
  var sheet = ss.getSheetByName(sheetName);

  // Create sheet if it doesn't exist
  if (!sheet) {
    Logger.log("Creating " + sheetName + " tab...");
    sheet = ss.insertSheet(sheetName);
  } else {
    Logger.log(sheetName + " tab already exists, updating...");
    sheet.clear(); // Clear existing data
  }

  // Column headers
  var headers = [
    "company_id",
    "company_name",
    "fail_reason",
    "state",
    "validation_timestamp",
    "pipeline_id"
  ];

  // Set headers in row 1
  var headerRange = sheet.getRange(1, 1, 1, headers.length);
  headerRange.setValues([headers]);

  // Format headers
  headerRange.setFontWeight("bold");
  headerRange.setBackground("#4285F4"); // Google Blue
  headerRange.setFontColor("#FFFFFF"); // White text
  headerRange.setHorizontalAlignment("center");

  // Set column widths
  sheet.setColumnWidth(1, 200); // company_id
  sheet.setColumnWidth(2, 250); // company_name
  sheet.setColumnWidth(3, 200); // fail_reason
  sheet.setColumnWidth(4, 80);  // state
  sheet.setColumnWidth(5, 180); // validation_timestamp
  sheet.setColumnWidth(6, 250); // pipeline_id

  // Freeze header row
  sheet.setFrozenRows(1);

  // Add data validation / filters
  sheet.getRange(1, 1, 1, headers.length).createFilter();

  Logger.log("✅ " + sheetName + " tab configured");
}


/**
 * Create Person Failures Tab
 */
function createPersonFailuresTab(ss) {
  var sheetName = "Person_Failures";
  var sheet = ss.getSheetByName(sheetName);

  // Create sheet if it doesn't exist
  if (!sheet) {
    Logger.log("Creating " + sheetName + " tab...");
    sheet = ss.insertSheet(sheetName);
  } else {
    Logger.log(sheetName + " tab already exists, updating...");
    sheet.clear(); // Clear existing data
  }

  // Column headers
  var headers = [
    "person_id",
    "person_name",
    "fail_reason",
    "state",
    "validation_timestamp",
    "pipeline_id"
  ];

  // Set headers in row 1
  var headerRange = sheet.getRange(1, 1, 1, headers.length);
  headerRange.setValues([headers]);

  // Format headers
  headerRange.setFontWeight("bold");
  headerRange.setBackground("#34A853"); // Google Green
  headerRange.setFontColor("#FFFFFF"); // White text
  headerRange.setHorizontalAlignment("center");

  // Set column widths
  sheet.setColumnWidth(1, 200); // person_id
  sheet.setColumnWidth(2, 200); // person_name
  sheet.setColumnWidth(3, 200); // fail_reason
  sheet.setColumnWidth(4, 80);  // state
  sheet.setColumnWidth(5, 180); // validation_timestamp
  sheet.setColumnWidth(6, 250); // pipeline_id

  // Freeze header row
  sheet.setFrozenRows(1);

  // Add data validation / filters
  sheet.getRange(1, 1, 1, headers.length).createFilter();

  Logger.log("✅ " + sheetName + " tab configured");
}


/**
 * Add sample data for testing (optional)
 */
function addSampleData() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // Sample company failure
  var companySheet = ss.getSheetByName("Company_Failures");
  if (companySheet) {
    var sampleCompany = [
      "04.04.01.33.00033.033",
      "WV SUPREME COURT",
      "Missing industry",
      "WV",
      new Date().toISOString(),
      "SAMPLE-TEST-001"
    ];
    companySheet.getRange(2, 1, 1, 6).setValues([sampleCompany]);
    Logger.log("✅ Added sample company data");
  }

  // Sample person failure (if needed)
  var personSheet = ss.getSheetByName("Person_Failures");
  if (personSheet) {
    var samplePerson = [
      "04.04.02.01.00001.001",
      "John Doe",
      "Missing email",
      "WV",
      new Date().toISOString(),
      "SAMPLE-TEST-001"
    ];
    personSheet.getRange(2, 1, 1, 6).setValues([samplePerson]);
    Logger.log("✅ Added sample person data");
  }

  SpreadsheetApp.getUi().alert(
    'Sample Data Added',
    'Sample validation failures have been added to both tabs for testing.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}


/**
 * Delete validation tabs (cleanup)
 */
function deleteValidationTabs() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  var ui = SpreadsheetApp.getUi();
  var response = ui.alert(
    'Confirm Deletion',
    'Are you sure you want to delete the validation tabs?\n\n' +
    'This will remove:\n' +
    '- Company_Failures tab\n' +
    '- Person_Failures tab\n\n' +
    'This action cannot be undone.',
    ui.ButtonSet.YES_NO
  );

  if (response == ui.Button.YES) {
    var companySheet = ss.getSheetByName("Company_Failures");
    if (companySheet) {
      ss.deleteSheet(companySheet);
      Logger.log("Deleted Company_Failures tab");
    }

    var personSheet = ss.getSheetByName("Person_Failures");
    if (personSheet) {
      ss.deleteSheet(personSheet);
      Logger.log("Deleted Person_Failures tab");
    }

    ui.alert('Deleted', 'Validation tabs have been deleted.', ui.ButtonSet.OK);
  }
}


/**
 * Create custom menu for easy access
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('Validation Setup')
      .addItem('Setup Validation Tabs', 'setupValidationTabs')
      .addItem('Add Sample Data', 'addSampleData')
      .addSeparator()
      .addItem('Delete Validation Tabs', 'deleteValidationTabs')
      .addToUi();
}
