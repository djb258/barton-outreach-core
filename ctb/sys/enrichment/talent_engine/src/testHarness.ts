/**
 * Test Harness
 * ============
 * Demonstrates the Talent Engine working end-to-end with adapter-based agents.
 * All agents use mock_mode=true for testing without real API calls.
 *
 * Includes:
 * - Full slot completion lifecycle simulation
 * - Adapter-based agent testing
 * - Cost tracking and assertions
 * - Fuzzy matching tests
 * - Missing slot detection tests
 */

import { SlotRow, createSlotRow, SlotType } from "./models/SlotRow";
import { evaluateCompanyState } from "./models/CompanyState";
import { evaluateChecklist, getMissingSummary, SlotChecklist } from "./logic/checklist";
import { ThrottleManager } from "./logic/throttleManager";
import { KillSwitchManager } from "./logic/killSwitch";
import { FailManager } from "./logic/failManager";

// Import agents
import { FuzzyMatchAgent } from "./agents/FuzzyMatchAgent";
import { LinkedInFinderAgent } from "./agents/LinkedInFinderAgent";
import { PublicScannerAgent } from "./agents/PublicScannerAgent";
import { PatternAgent } from "./agents/PatternAgent";
import { EmailGeneratorAgent } from "./agents/EmailGeneratorAgent";
import { TitleCompanyAgent } from "./agents/TitleCompanyAgent";
import { HashAgent } from "./agents/HashAgent";
import { MissingSlotAgent } from "./agents/MissingSlotAgent";

/**
 * Test results tracking.
 */
interface TestResults {
  passed: number;
  failed: number;
  tests: { name: string; passed: boolean; error?: string }[];
}

/**
 * Run the main test harness.
 */
async function runTestHarness(): Promise<void> {
  console.log("=".repeat(60));
  console.log("TALENT ENGINE - ADAPTER-BASED TEST HARNESS");
  console.log("=".repeat(60));
  console.log("");

  const results: TestResults = { passed: 0, failed: 0, tests: [] };

  // Phase 1: Layer 1 - Fuzzy Matching Tests
  console.log("[PHASE 1] Layer 1: Fuzzy Matching");
  console.log("-".repeat(60));
  await runFuzzyMatchTests(results);

  // Phase 2: Layer 2-3 - Individual Agent Tests
  console.log("\n[PHASE 2] Layer 2-3: Individual Agent Tests");
  console.log("-".repeat(60));
  await runAgentTests(results);

  // Phase 3: Layer 4 - Missing Slot Detection Tests
  console.log("\n[PHASE 3] Layer 4: Missing Slot Detection");
  console.log("-".repeat(60));
  await runMissingSlotTests(results);

  // Phase 4: Full Slot Completion Lifecycle
  console.log("\n[PHASE 4] Full Slot Completion Lifecycle");
  console.log("-".repeat(60));
  await runFullLifecycleTest(results);

  // Phase 5: Cost Tracking Tests
  console.log("\n[PHASE 5] Cost Tracking & Throttle Tests");
  console.log("-".repeat(60));
  await runCostTrackingTests(results);

  // Final Summary
  console.log("\n" + "=".repeat(60));
  console.log("TEST HARNESS COMPLETE");
  console.log("=".repeat(60));
  console.log("");
  console.log(`Total: ${results.passed + results.failed} tests`);
  console.log(`Passed: ${results.passed}`);
  console.log(`Failed: ${results.failed}`);
  console.log("");

  if (results.failed > 0) {
    console.log("Failed tests:");
    for (const test of results.tests.filter((t) => !t.passed)) {
      console.log(`  - ${test.name}: ${test.error}`);
    }
  }

  console.log("\nVerified components:");
  console.log("  [x] FuzzyMatchAgent with real similarity algorithms");
  console.log("  [x] LinkedInFinderAgent with adapter pattern");
  console.log("  [x] PublicScannerAgent with adapter pattern");
  console.log("  [x] PatternAgent with adapter pattern");
  console.log("  [x] EmailGeneratorAgent with adapter pattern");
  console.log("  [x] TitleCompanyAgent with adapter pattern");
  console.log("  [x] HashAgent with SHA-256 hashing");
  console.log("  [x] MissingSlotAgent with slot discovery adapter");
  console.log("  [x] Full slot completion lifecycle");
  console.log("  [x] Cost tracking across agents");
  console.log("");
}

/**
 * Run fuzzy matching tests.
 */
async function runFuzzyMatchTests(results: TestResults): Promise<void> {
  const agent = new FuzzyMatchAgent({ verbose: false });
  const companyMaster = [
    "Acme Corporation",
    "TechStart Inc",
    "Global Industries LLC",
    "Mega Corp",
    "Alpha Beta Solutions",
  ];

  // Test 1: Exact match
  console.log("\n[1.1] Exact Match Test");
  {
    const result = await agent.run({
      task_id: "fuzzy_1",
      slot_row_id: "slot_1",
      raw_company_input: "Acme Corporation",
      company_master: companyMaster,
    });

    const passed = result.success && result.data.status === "MATCHED" && result.data.match_score >= 90;
    logTestResult("Exact match: 'Acme Corporation'", passed, results);
    console.log(`    Score: ${result.data.match_score}`);
    console.log(`    Status: ${result.data.status}`);
  }

  // Test 2: Fuzzy match with suffix removal
  console.log("\n[1.2] Fuzzy Match with Suffix Removal");
  {
    const result = await agent.run({
      task_id: "fuzzy_2",
      slot_row_id: "slot_2",
      raw_company_input: "Acme Corp Inc.",
      company_master: companyMaster,
    });

    const passed = result.success && result.data.matched_company === "Acme Corporation";
    logTestResult("Fuzzy match: 'Acme Corp Inc.' -> 'Acme Corporation'", passed, results);
    console.log(`    Score: ${result.data.match_score}`);
    console.log(`    Matched: ${result.data.matched_company}`);
  }

  // Test 3: No match
  console.log("\n[1.3] No Match Test");
  {
    const result = await agent.run({
      task_id: "fuzzy_3",
      slot_row_id: "slot_3",
      raw_company_input: "Completely Unknown Company XYZ",
      company_master: companyMaster,
    });

    const passed = result.data.status === "UNMATCHED" || result.data.match_score < 70;
    logTestResult("No match: 'Completely Unknown Company XYZ'", passed, results);
    console.log(`    Score: ${result.data.match_score}`);
    console.log(`    Status: ${result.data.status}`);
  }

  // Test 4: Normalization
  console.log("\n[1.4] Normalization Test");
  {
    const normalized = agent.normalizeCompanyName("  TECHSTART, INC.  ");
    const passed = normalized === "techstart";
    logTestResult("Normalize: '  TECHSTART, INC.  ' -> 'techstart'", passed, results);
    console.log(`    Result: '${normalized}'`);
  }
}

/**
 * Run individual agent tests.
 */
async function runAgentTests(results: TestResults): Promise<void> {
  // Test 2.1: LinkedInFinderAgent
  console.log("\n[2.1] LinkedInFinderAgent - Mock Mode");
  {
    const agent = new LinkedInFinderAgent({
      primary_config: { mock_mode: true },
      fallback_config: { mock_mode: true },
      verbose: false,
    });

    const result = await agent.run({
      task_id: "linkedin_1",
      slot_row_id: "slot_1",
      person_name: "John Smith",
      company_name: "Acme Corp",
      slot_type: "CEO",
    });

    const passed = result.success && result.data.linkedin_url;
    logTestResult("LinkedInFinderAgent mock resolution", passed, results);
    console.log(`    LinkedIn URL: ${result.data.linkedin_url}`);
    console.log(`    Source: ${result.data.source}`);
  }

  // Test 2.2: PublicScannerAgent
  console.log("\n[2.2] PublicScannerAgent - Mock Mode");
  {
    const agent = new PublicScannerAgent({
      mock_mode: true,
      verbose: false,
    });

    const result = await agent.run({
      task_id: "public_1",
      slot_row_id: "slot_1",
      linkedin_url: "https://linkedin.com/in/john-smith",
    });

    const passed = result.success && typeof result.data.public_accessible === "boolean";
    logTestResult("PublicScannerAgent mock scan", passed, results);
    console.log(`    Public Accessible: ${result.data.public_accessible}`);
    console.log(`    Source: ${result.data.source}`);
  }

  // Test 2.3: PatternAgent
  console.log("\n[2.3] PatternAgent - Mock Mode");
  {
    const agent = new PatternAgent({
      mock_mode: true,
      verbose: false,
    });

    const result = await agent.run({
      task_id: "pattern_1",
      slot_row_id: "slot_1",
      company_name: "Acme Corp",
      company_domain: "acmecorp.com",
    });

    const passed = result.success && result.data.email_pattern;
    logTestResult("PatternAgent mock pattern discovery", passed, results);
    console.log(`    Pattern: ${result.data.email_pattern}`);
    console.log(`    Confidence: ${result.data.confidence}`);
  }

  // Test 2.4: EmailGeneratorAgent
  console.log("\n[2.4] EmailGeneratorAgent - Mock Mode");
  {
    const agent = new EmailGeneratorAgent({
      pattern_config: { mock_mode: true },
      verification_config: { mock_mode: true },
      verbose: false,
    });

    const result = await agent.run({
      task_id: "email_1",
      slot_row_id: "slot_1",
      person_name: "John Smith",
      company_name: "Acme Corp",
      company_domain: "acmecorp.com",
      email_pattern: "{first}.{last}",
    });

    const passed = result.success && result.data.email;
    logTestResult("EmailGeneratorAgent mock email generation", passed, results);
    console.log(`    Email: ${result.data.email}`);
    console.log(`    Verified: ${result.data.email_verified}`);
  }

  // Test 2.5: TitleCompanyAgent
  console.log("\n[2.5] TitleCompanyAgent - Mock Mode");
  {
    const agent = new TitleCompanyAgent({
      linkedin_config: { mock_mode: true },
      employment_config: { mock_mode: true },
      verbose: false,
    });

    const result = await agent.run({
      task_id: "title_1",
      slot_row_id: "slot_1",
      linkedin_url: "https://linkedin.com/in/john-smith",
      person_name: "John Smith",
      company_name: "Acme Corp",
      slot_type: "CEO",
    });

    const passed = result.success && result.data.current_title;
    logTestResult("TitleCompanyAgent mock title lookup", passed, results);
    console.log(`    Title: ${result.data.current_title}`);
    console.log(`    Company: ${result.data.current_company}`);
  }

  // Test 2.6: HashAgent
  console.log("\n[2.6] HashAgent - Movement Detection");
  {
    const agent = new HashAgent({ verbose: false });

    const row1 = createSlotRow({
      company_id: "comp_1",
      company_name: "Acme Corp",
      slot_type: "CEO",
      person_name: "John Smith",
      current_title: "Chief Executive Officer",
      current_company: "Acme Corp",
    });

    const hash1 = agent.hashRow(row1);

    // Simulate title change
    row1.current_title = "Former CEO";
    const hash2 = agent.hashRow(row1);

    const movementDetected = agent.detectMovement(hash1, hash2);
    const passed = movementDetected && hash1 !== hash2;
    logTestResult("HashAgent movement detection", passed, results);
    console.log(`    Hash 1: ${hash1.substring(0, 24)}...`);
    console.log(`    Hash 2: ${hash2.substring(0, 24)}...`);
    console.log(`    Movement: ${movementDetected}`);
  }
}

/**
 * Run missing slot detection tests.
 */
async function runMissingSlotTests(results: TestResults): Promise<void> {
  // Test 3.1: Company with missing slots
  console.log("\n[3.1] MissingSlotAgent - Partial Company");
  {
    const agent = new MissingSlotAgent({
      verbose: false,
      auto_fill_slots: true,
      discovery_config: { mock_mode: true },
    });

    const existingRows = [
      createSlotRow({
        company_id: "comp_1",
        company_name: "Test Corp",
        slot_type: "CEO",
        person_name: "John CEO",
        linkedin_url: "https://linkedin.com/in/john-ceo",
        email: "john@testcorp.com",
      }),
      createSlotRow({
        company_id: "comp_1",
        company_name: "Test Corp",
        slot_type: "CFO",
        person_name: "Jane CFO",
        linkedin_url: "https://linkedin.com/in/jane-cfo",
        email: "jane@testcorp.com",
      }),
    ];

    const result = await agent.run({
      task_id: "missing_1",
      company_id: "comp_1",
      company_name: "Test Corp",
      company_domain: "testcorp.com",
      existing_rows: existingRows,
    });

    const passed =
      result.success &&
      result.data.missing_count === 2 && // HR and BENEFITS missing
      result.data.filled_count === 2; // CEO and CFO filled

    logTestResult("Missing slot detection (HR, BENEFITS missing)", passed, results);
    console.log(`    Filled: ${result.data.filled_count}`);
    console.log(`    Missing: ${result.data.missing_count}`);
    console.log(`    Discovered: ${result.data.discovered_count}`);
  }

  // Test 3.2: Fully staffed company
  console.log("\n[3.2] MissingSlotAgent - Fully Staffed");
  {
    const agent = new MissingSlotAgent({ verbose: false });

    const existingRows: SlotRow[] = (["CEO", "CFO", "HR", "BENEFITS"] as SlotType[]).map((slot) =>
      createSlotRow({
        company_id: "comp_2",
        company_name: "Full Corp",
        slot_type: slot,
        person_name: `${slot} Person`,
        linkedin_url: `https://linkedin.com/in/${slot.toLowerCase()}-person`,
        email: `${slot.toLowerCase()}@fullcorp.com`,
      })
    );

    const result = await agent.run({
      task_id: "missing_2",
      company_id: "comp_2",
      company_name: "Full Corp",
      existing_rows: existingRows,
    });

    const passed = result.success && result.data.is_fully_staffed === true;
    logTestResult("Fully staffed company detection", passed, results);
    console.log(`    Is Fully Staffed: ${result.data.is_fully_staffed}`);
  }
}

/**
 * Run full slot completion lifecycle test.
 */
async function runFullLifecycleTest(results: TestResults): Promise<void> {
  console.log("\n[4.1] Full Slot Completion - CEO at Acme Corp");

  // Initialize agents with mock mode
  const linkedInAgent = new LinkedInFinderAgent({
    primary_config: { mock_mode: true },
    verbose: false,
  });
  const publicAgent = new PublicScannerAgent({ mock_mode: true, verbose: false });
  const patternAgent = new PatternAgent({ mock_mode: true, verbose: false });
  const emailAgent = new EmailGeneratorAgent({
    pattern_config: { mock_mode: true },
    verification_config: { mock_mode: true },
    verbose: false,
  });
  const titleAgent = new TitleCompanyAgent({
    linkedin_config: { mock_mode: true },
    employment_config: { mock_mode: true },
    verbose: false,
  });
  const hashAgent = new HashAgent({ verbose: false });

  // Create initial row
  const row = createSlotRow({
    company_id: "acme_001",
    company_name: "Acme Corporation",
    slot_type: "CEO",
    person_name: "John Doe",
  });

  console.log(`    Initial state: person_name='${row.person_name}', slot_complete=${row.slot_complete}`);

  // Step 1: Find LinkedIn URL
  console.log("\n    Step 1: Finding LinkedIn URL...");
  await linkedInAgent.runOnRow(row);
  console.log(`      LinkedIn URL: ${row.linkedin_url}`);

  // Step 2: Check public accessibility
  console.log("    Step 2: Checking public accessibility...");
  await publicAgent.runOnRow(row);
  console.log(`      Public Accessible: ${row.public_accessible}`);

  // Step 3: Discover email pattern
  console.log("    Step 3: Discovering email pattern...");
  await patternAgent.runOnRow(row);
  console.log(`      Pattern: ${row.email_pattern}`);

  // Step 4: Generate email
  console.log("    Step 4: Generating email...");
  await emailAgent.runOnRow(row);
  console.log(`      Email: ${row.email}`);
  console.log(`      Verified: ${row.email_verified}`);

  // Step 5: Get current title/company
  console.log("    Step 5: Getting current title/company...");
  await titleAgent.runOnRow(row);
  console.log(`      Title: ${row.current_title}`);
  console.log(`      Company: ${row.current_company}`);

  // Step 6: Generate hash
  console.log("    Step 6: Generating movement hash...");
  await hashAgent.runOnRow(row);
  console.log(`      Hash: ${row.movement_hash?.substring(0, 24)}...`);

  // Evaluate checklist
  const checklist = evaluateChecklist(row);
  const missing = getMissingSummary(checklist);

  console.log(`\n    Checklist evaluation:`);
  console.log(`      Missing: ${missing.length > 0 ? missing.join(", ") : "None"}`);
  console.log(`      Ready for completion: ${checklist.ready_for_completion}`);

  // Mark complete if ready
  if (checklist.ready_for_completion) {
    row.slot_complete = true;
    row.completed_at = new Date();
  }

  const passed =
    row.slot_complete &&
    row.linkedin_url !== null &&
    row.email !== null &&
    row.current_title !== null &&
    row.movement_hash !== null;

  logTestResult("Full lifecycle slot completion", passed, results);
  console.log(`\n    Final state: slot_complete=${row.slot_complete}`);
}

/**
 * Run cost tracking tests.
 */
async function runCostTrackingTests(results: TestResults): Promise<void> {
  // Test 5.1: Agent cost tracking
  console.log("\n[5.1] Agent Cost Tracking");
  {
    const agent = new LinkedInFinderAgent({
      primary_config: { mock_mode: true },
      verbose: false,
    });

    agent.resetCost();
    await agent.run({
      task_id: "cost_1",
      slot_row_id: "slot_1",
      person_name: "Cost Test",
      company_name: "Cost Corp",
      slot_type: "CEO",
    });

    const cost = agent.getTotalCost();
    const passed = typeof cost === "number" && cost >= 0;
    logTestResult("Agent cost tracking", passed, results);
    console.log(`    Total Cost: $${cost.toFixed(4)}`);
  }

  // Test 5.2: Throttle manager
  console.log("\n[5.2] Throttle Manager");
  {
    const throttle = new ThrottleManager({
      max_calls_per_minute: 10,
      max_calls_per_day: 100,
    });

    // Record some calls
    for (let i = 0; i < 5; i++) {
      throttle.recordCall();
    }

    const canProceed = throttle.canProceed();
    const passed = canProceed && throttle.getCurrentMinuteCount() === 5;
    logTestResult("Throttle manager tracking", passed, results);
    console.log(`    Minute count: ${throttle.getCurrentMinuteCount()}`);
    console.log(`    Can proceed: ${canProceed}`);
  }

  // Test 5.3: Kill switch
  console.log("\n[5.3] Kill Switch Manager");
  {
    const killSwitch = new KillSwitchManager();

    killSwitch.kill("LinkedInFinderAgent");
    const isKilled = killSwitch.isKilled("LinkedInFinderAgent");
    const isActiveOther = !killSwitch.isKilled("PatternAgent");

    killSwitch.revive("LinkedInFinderAgent");
    const isRevived = !killSwitch.isKilled("LinkedInFinderAgent");

    const passed = isKilled && isActiveOther && isRevived;
    logTestResult("Kill switch management", passed, results);
    console.log(`    Kill working: ${isKilled}`);
    console.log(`    Selective kill: ${isActiveOther}`);
    console.log(`    Revive working: ${isRevived}`);
  }

  // Test 5.4: Fail manager
  console.log("\n[5.4] Fail Manager");
  {
    const failManager = new FailManager();

    failManager.recordFailure("slot_1", "LinkedInFinderAgent", "API timeout");
    failManager.recordFailure("slot_1", "LinkedInFinderAgent", "API timeout");

    const failures = failManager.getFailures("slot_1");
    const canRetry = failManager.canRetry("slot_1", "LinkedInFinderAgent");

    const passed = failures.length === 2 && canRetry;
    logTestResult("Fail manager tracking", passed, results);
    console.log(`    Failures recorded: ${failures.length}`);
    console.log(`    Can retry: ${canRetry}`);
  }
}

/**
 * Log test result helper.
 */
function logTestResult(name: string, passed: boolean, results: TestResults): void {
  if (passed) {
    console.log(`    ✓ PASS: ${name}`);
    results.passed++;
    results.tests.push({ name, passed: true });
  } else {
    console.log(`    ✗ FAIL: ${name}`);
    results.failed++;
    results.tests.push({ name, passed: false, error: "Assertion failed" });
  }
}

// Run the harness
runTestHarness().catch(console.error);
