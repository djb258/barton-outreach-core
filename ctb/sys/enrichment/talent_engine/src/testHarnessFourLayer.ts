/**
 * Test Harness for Talent Engine Four-Layer Architecture
 * ======================================================
 * Tests all four layers of the Talent Engine:
 *
 * Layer 1: Fuzzy Matching Intake
 * Layer 2: Slot Completion Checklist
 * Layer 3: Company-Level Missing-Slot Detection
 * Layer 4: Missing-Slot Agent Trigger
 *
 * Plus: Throttles, Kill Switches, Failure Manager, Agent Registry, Dispatcher
 */

import { SlotRow, ALL_SLOT_TYPES, SlotType } from "./models/SlotRow";
import { evaluateCompanyState, CompanyState } from "./models/CompanyState";

// Logic imports
import {
  processFuzzyMatch,
  DEFAULT_FUZZY_CONFIG,
  getRowsNeedingFuzzyMatch,
} from "./logic/fuzzyMatch";
import {
  evaluateChecklist,
  getNeededAgent,
  batchEvaluateChecklists,
} from "./logic/checklist";
import {
  checkCompany,
  batchCheckCompanies,
  generateCompanySummaryReport,
} from "./logic/companyChecker";
import { FailManager, globalFailManager } from "./logic/failManager";
import {
  ThrottleManager,
  AgentThrottleRegistry,
  globalThrottleRegistry,
} from "./logic/throttleManager";
import { KillSwitchManager, globalKillSwitchManager } from "./logic/killSwitch";
import { AgentRegistry, globalAgentRegistry } from "./logic/agentRegistry";
import {
  dispatcher,
  batchDispatcher,
  getDispatchStats,
  createDryRunDispatcher,
} from "./logic/dispatcher";

// Agent imports
import { FuzzyMatchAgent } from "./agents/FuzzyMatchAgent";
import { MissingSlotAgent } from "./agents/MissingSlotAgent";

/**
 * Test result interface.
 */
interface TestResult {
  name: string;
  passed: boolean;
  message: string;
  duration_ms: number;
}

/**
 * Test suite interface.
 */
interface TestSuite {
  name: string;
  tests: TestResult[];
  passed: number;
  failed: number;
  duration_ms: number;
}

/**
 * Run a single test with timing.
 */
async function runTest(
  name: string,
  testFn: () => Promise<void> | void
): Promise<TestResult> {
  const start = Date.now();
  try {
    await testFn();
    return {
      name,
      passed: true,
      message: "PASS",
      duration_ms: Date.now() - start,
    };
  } catch (error) {
    return {
      name,
      passed: false,
      message: error instanceof Error ? error.message : "Unknown error",
      duration_ms: Date.now() - start,
    };
  }
}

/**
 * Assert helper.
 */
function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

/**
 * Create sample company master list.
 */
function createSampleCompanyMaster(): string[] {
  return [
    "Acme Corporation",
    "Global Tech Industries",
    "Smith & Associates",
    "Johnson Manufacturing",
    "Pacific Healthcare Group",
    "Delta Financial Services",
    "Alpine Construction Co",
    "Sunset Media Group",
    "Northern Logistics Inc",
    "Eastern Energy Solutions",
  ];
}

/**
 * Create sample SlotRows.
 */
function createSampleRows(): SlotRow[] {
  const rows: SlotRow[] = [];

  // Company 1: Acme Corporation - has CEO, missing others
  rows.push(
    new SlotRow({
      id: "row_1",
      company_name: "Acme Corporation",
      company_id: "company_acme_corporation",
      slot_type: "CEO",
      person_name: "John Smith",
      linkedin_url: "https://linkedin.com/in/johnsmith",
      email: "john.smith@acme.com",
      email_pattern: "{first}.{last}@acme.com",
      title: "Chief Executive Officer",
      md5_hash: "abc123",
      fuzzy_match_status: "MATCHED",
    })
  );

  // Company 2: Global Tech - needs fuzzy matching
  rows.push(
    new SlotRow({
      id: "row_2",
      raw_company_input: "Global Tech Ind",
      slot_type: "CFO",
      person_name: "Jane Doe",
      fuzzy_match_status: "PENDING",
    })
  );

  // Company 3: Smith & Associates - partially filled
  rows.push(
    new SlotRow({
      id: "row_3",
      company_name: "Smith & Associates",
      company_id: "company_smith_associates",
      slot_type: "HR",
      person_name: "Bob Wilson",
      linkedin_url: "https://linkedin.com/in/bobwilson",
      fuzzy_match_status: "MATCHED",
    })
  );

  // Company 4: Johnson Manufacturing - incomplete CEO
  rows.push(
    new SlotRow({
      id: "row_4",
      company_name: "Johnson Manufacturing",
      company_id: "company_johnson_manufacturing",
      slot_type: "CEO",
      person_name: null, // Missing person
      fuzzy_match_status: "MATCHED",
    })
  );

  return rows;
}

// =============================================================================
// TEST SUITES
// =============================================================================

/**
 * Test Suite 1: Fuzzy Matching (Layer 1)
 */
async function testFuzzyMatching(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Layer 1: Fuzzy Matching",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  const companyMaster = createSampleCompanyMaster();

  // Test 1: Exact match
  suite.tests.push(
    await runTest("Exact match scores 100", () => {
      const result = processFuzzyMatch("Acme Corporation", companyMaster);
      assert(result.status === "MATCHED", `Expected MATCHED, got ${result.status}`);
      assert(result.match_score === 100, `Expected 100, got ${result.match_score}`);
    })
  );

  // Test 2: Close match (above auto-accept threshold)
  suite.tests.push(
    await runTest("Close match auto-accepts", () => {
      const result = processFuzzyMatch("Acme Corp", companyMaster);
      assert(
        result.status === "MATCHED" || result.status === "MANUAL_REVIEW",
        `Expected MATCHED or MANUAL_REVIEW, got ${result.status}`
      );
    })
  );

  // Test 3: No match
  suite.tests.push(
    await runTest("No match returns UNMATCHED", () => {
      const result = processFuzzyMatch("XYZ Unknown Company", companyMaster);
      assert(result.status === "UNMATCHED", `Expected UNMATCHED, got ${result.status}`);
    })
  );

  // Test 4: Fuzzy match agent
  suite.tests.push(
    await runTest("FuzzyMatchAgent processes row", async () => {
      const agent = new FuzzyMatchAgent();
      const row = new SlotRow({
        id: "test_row",
        raw_company_input: "Global Tech Industries",
        fuzzy_match_status: "PENDING",
      });
      const processed = await agent.runOnRow(row, companyMaster);
      assert(processed.fuzzy_match_status === "MATCHED", "Expected MATCHED status");
      assert(processed.company_name === "Global Tech Industries", "Expected matched company name");
    })
  );

  // Test 5: Rows needing fuzzy match
  suite.tests.push(
    await runTest("getRowsNeedingFuzzyMatch filters correctly", () => {
      const rows = createSampleRows();
      const needsMatch = getRowsNeedingFuzzyMatch(rows);
      assert(needsMatch.length === 1, `Expected 1 row, got ${needsMatch.length}`);
      assert(needsMatch[0].id === "row_2", "Expected row_2");
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

/**
 * Test Suite 2: Checklist (Layer 2)
 */
async function testChecklist(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Layer 2: Slot Completion Checklist",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  // Test 1: Complete row
  suite.tests.push(
    await runTest("Complete row passes checklist", () => {
      const row = new SlotRow({
        id: "complete",
        company_name: "Test Co",
        person_name: "John Doe",
        linkedin_url: "https://linkedin.com/in/johndoe",
        email: "john@test.com",
        email_pattern: "{first}@test.com",
        title: "CEO",
        md5_hash: "hash123",
        fuzzy_match_status: "MATCHED",
      });
      const result = evaluateChecklist(row);
      assert(result.all_complete, "Expected all_complete to be true");
    })
  );

  // Test 2: Missing LinkedIn
  suite.tests.push(
    await runTest("Missing LinkedIn detected", () => {
      const row = new SlotRow({
        id: "missing_li",
        company_name: "Test Co",
        person_name: "John Doe",
        email: "john@test.com",
        fuzzy_match_status: "MATCHED",
      });
      const result = evaluateChecklist(row);
      assert(!result.all_complete, "Expected not all_complete");
      assert(!result.has_linkedin, "Expected has_linkedin to be false");
    })
  );

  // Test 3: Get needed agent
  suite.tests.push(
    await runTest("getNeededAgent returns correct agent", () => {
      const row = new SlotRow({
        id: "need_linkedin",
        company_name: "Test Co",
        person_name: "John Doe",
        fuzzy_match_status: "MATCHED",
      });
      const result = evaluateChecklist(row);
      const needed = getNeededAgent(result);
      assert(needed === "LinkedInFinderAgent", `Expected LinkedInFinderAgent, got ${needed}`);
    })
  );

  // Test 4: Batch evaluate
  suite.tests.push(
    await runTest("batchEvaluateChecklists processes all rows", () => {
      const rows = createSampleRows();
      const results = batchEvaluateChecklists(rows);
      assert(results.length === rows.length, "Expected same number of results");
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

/**
 * Test Suite 3: Company Checker (Layer 3)
 */
async function testCompanyChecker(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Layer 3: Company-Level Detection",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  const companyMaster = createSampleCompanyMaster();

  // Test 1: Company with missing slots
  suite.tests.push(
    await runTest("Detects missing slots", () => {
      const rows = [
        new SlotRow({
          id: "ceo",
          company_name: "Test Co",
          slot_type: "CEO",
          slot_complete: true,
          fuzzy_match_status: "MATCHED",
        }),
      ];
      const result = checkCompany("company_test", "Test Co", rows);
      assert(result.state.missing_slots.length === 3, "Expected 3 missing slots");
      assert(result.should_trigger_missing_slot_agent, "Expected trigger");
    })
  );

  // Test 2: Fully staffed company
  suite.tests.push(
    await runTest("Fully staffed company detected", () => {
      const rows = ALL_SLOT_TYPES.map(
        (slotType) =>
          new SlotRow({
            id: `slot_${slotType}`,
            company_name: "Full Co",
            slot_type: slotType,
            slot_complete: true,
            fuzzy_match_status: "MATCHED",
          })
      );
      const result = checkCompany("company_full", "Full Co", rows);
      assert(result.state.is_fully_staffed, "Expected fully staffed");
      assert(!result.should_trigger_missing_slot_agent, "Should not trigger");
    })
  );

  // Test 3: Batch check companies
  suite.tests.push(
    await runTest("batchCheckCompanies processes all", () => {
      const rows = createSampleRows();
      const results = batchCheckCompanies(rows, companyMaster);
      assert(results.length === companyMaster.length, "Expected all companies checked");
    })
  );

  // Test 4: Generate summary report
  suite.tests.push(
    await runTest("generateCompanySummaryReport creates output", () => {
      const rows = createSampleRows();
      const results = batchCheckCompanies(rows, companyMaster);
      const report = generateCompanySummaryReport(results);
      assert(report.includes("Company State Summary"), "Expected summary header");
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

/**
 * Test Suite 4: Missing Slot Agent (Layer 4)
 */
async function testMissingSlotAgent(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Layer 4: Missing Slot Agent",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  // Test 1: Agent creates missing rows
  suite.tests.push(
    await runTest("MissingSlotAgent creates placeholder rows", async () => {
      const agent = new MissingSlotAgent({ auto_create_rows: true });
      const existingRows = [
        new SlotRow({
          id: "existing_ceo",
          company_name: "Test Co",
          slot_type: "CEO",
          slot_complete: true,
          fuzzy_match_status: "MATCHED",
        }),
      ];
      const result = await agent.run({
        task_id: "test_task",
        company_id: "company_test",
        company_name: "Test Co",
        existing_rows: existingRows,
      });
      assert(result.success, "Expected success");
      assert(result.data.created_rows.length === 3, "Expected 3 new rows");
    })
  );

  // Test 2: Agent skips fully staffed
  suite.tests.push(
    await runTest("MissingSlotAgent skips fully staffed", async () => {
      const agent = new MissingSlotAgent();
      const existingRows = ALL_SLOT_TYPES.map(
        (slotType) =>
          new SlotRow({
            id: `slot_${slotType}`,
            company_name: "Full Co",
            slot_type: slotType,
            slot_complete: true,
            fuzzy_match_status: "MATCHED",
          })
      );
      const result = await agent.run({
        task_id: "test_task",
        company_id: "company_full",
        company_name: "Full Co",
        existing_rows: existingRows,
      });
      assert(result.success, "Expected success");
      assert(result.data.skipped === true, "Expected skipped");
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

/**
 * Test Suite 5: Throttle Manager
 */
async function testThrottleManager(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Throttle Manager",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  // Test 1: Not throttled initially
  suite.tests.push(
    await runTest("Not throttled initially", () => {
      const throttle = new ThrottleManager({ max_calls_per_minute: 10, max_calls_per_day: 100 });
      assert(!throttle.isThrottled(), "Expected not throttled");
    })
  );

  // Test 2: Throttled after limit
  suite.tests.push(
    await runTest("Throttled after limit reached", () => {
      const throttle = new ThrottleManager({ max_calls_per_minute: 3, max_calls_per_day: 100 });
      throttle.recordCall();
      throttle.recordCall();
      throttle.recordCall();
      assert(throttle.isThrottled(), "Expected throttled");
    })
  );

  // Test 3: Registry tracks per-agent
  suite.tests.push(
    await runTest("Registry tracks per-agent throttles", () => {
      const registry = new AgentThrottleRegistry();
      registry.recordAgentCall("LinkedInFinderAgent");
      const remaining = registry.getThrottle("LinkedInFinderAgent").getRemainingThisMinute();
      assert(remaining === 29, `Expected 29 remaining, got ${remaining}`);
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

/**
 * Test Suite 6: Kill Switch
 */
async function testKillSwitch(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Kill Switch",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  // Test 1: All active initially
  suite.tests.push(
    await runTest("All agents active initially", () => {
      const ks = new KillSwitchManager();
      assert(ks.isActive("LinkedInFinderAgent"), "Expected active");
      assert(!ks.hasKilledAgents(), "Expected no killed agents");
    })
  );

  // Test 2: Kill agent
  suite.tests.push(
    await runTest("Kill agent works", () => {
      const ks = new KillSwitchManager();
      ks.kill("LinkedInFinderAgent", "Test kill", "tester");
      assert(ks.isKilled("LinkedInFinderAgent"), "Expected killed");
      assert(ks.hasKilledAgents(), "Expected has killed");
    })
  );

  // Test 3: Revive agent
  suite.tests.push(
    await runTest("Revive agent works", () => {
      const ks = new KillSwitchManager();
      ks.kill("LinkedInFinderAgent", "Test", "tester");
      ks.revive("LinkedInFinderAgent");
      assert(ks.isActive("LinkedInFinderAgent"), "Expected active after revive");
    })
  );

  // Test 4: Kill all
  suite.tests.push(
    await runTest("Kill all agents works", () => {
      const ks = new KillSwitchManager();
      ks.killAll("Emergency");
      const killed = ks.getKilledAgents();
      assert(killed.length === 8, `Expected 8 killed, got ${killed.length}`);
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

/**
 * Test Suite 7: Fail Manager
 */
async function testFailManager(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Fail Manager",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  // Test 1: Classify temporary error
  suite.tests.push(
    await runTest("Classifies temporary errors", () => {
      const fm = new FailManager();
      const type = fm.classifyError("Rate limit exceeded, try again later");
      assert(type === "TEMPORARY", `Expected TEMPORARY, got ${type}`);
    })
  );

  // Test 2: Classify permanent error
  suite.tests.push(
    await runTest("Classifies permanent errors", () => {
      const fm = new FailManager();
      const type = fm.classifyError("Profile not found");
      assert(type === "PERMANENT", `Expected PERMANENT, got ${type}`);
    })
  );

  // Test 3: Record failure
  suite.tests.push(
    await runTest("Records failures correctly", () => {
      const fm = new FailManager();
      const row = new SlotRow({ id: "test_row" });
      const result = {
        task_id: "task_1",
        agent_type: "LinkedInFinderAgent" as const,
        slot_row_id: "test_row",
        success: false,
        data: {},
        error: "Rate limit exceeded",
        completed_at: new Date(),
      };
      const record = fm.recordFailure(row, result);
      assert(record.attempt_count === 1, "Expected 1 attempt");
      assert(!record.is_permanent, "Expected not permanent");
    })
  );

  // Test 4: Permanent after max retries
  suite.tests.push(
    await runTest("Becomes permanent after max retries", () => {
      const fm = new FailManager({ max_retries: 2, base_delay_ms: 10, max_delay_ms: 100, backoff_multiplier: 2 });
      const row = new SlotRow({ id: "test_row_2" });
      const result = {
        task_id: "task_1",
        agent_type: "LinkedInFinderAgent" as const,
        slot_row_id: "test_row_2",
        success: false,
        data: {},
        error: "Timeout",
        completed_at: new Date(),
      };
      fm.recordFailure(row, result);
      fm.recordFailure(row, result);
      const stats = fm.getStats();
      assert(stats.permanent >= 1, "Expected at least 1 permanent failure");
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

/**
 * Test Suite 8: Dispatcher Integration
 */
async function testDispatcher(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Dispatcher Integration",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  const companyMaster = createSampleCompanyMaster();

  // Reset globals before tests
  globalAgentRegistry.reset();
  globalThrottleRegistry.resetAll();
  globalKillSwitchManager.reset();

  // Test 1: Process matched row
  suite.tests.push(
    await runTest("Dispatcher processes matched row", async () => {
      const row = new SlotRow({
        id: "dispatch_test_1",
        company_name: "Acme Corporation",
        slot_type: "CEO",
        fuzzy_match_status: "MATCHED",
      });
      const result = await dispatcher(row, [row], companyMaster);
      assert(result.success, `Expected success, error: ${result.error}`);
      assert(result.step_reached >= 2, `Expected at least step 2, got ${result.step_reached}`);
    })
  );

  // Test 2: Process row needing fuzzy match
  suite.tests.push(
    await runTest("Dispatcher handles fuzzy matching", async () => {
      const row = new SlotRow({
        id: "dispatch_test_2",
        raw_company_input: "Acme Corp",
        slot_type: "CFO",
        fuzzy_match_status: "PENDING",
      });
      const result = await dispatcher(row, [row], companyMaster);
      // May fail fuzzy match but should reach step 1
      assert(result.step_reached >= 1, `Expected at least step 1, got ${result.step_reached}`);
    })
  );

  // Test 3: Dry run mode
  suite.tests.push(
    await runTest("Dry run mode works", async () => {
      const dryRun = createDryRunDispatcher({ verbose: false });
      const row = new SlotRow({
        id: "dispatch_test_3",
        company_name: "Test Co",
        slot_type: "CEO",
        fuzzy_match_status: "MATCHED",
      });
      const result = await dryRun(row, [row], companyMaster);
      assert(result.agent_results.length === 0, "Dry run should have no agent results");
    })
  );

  // Test 4: Batch dispatcher
  suite.tests.push(
    await runTest("Batch dispatcher processes multiple rows", async () => {
      const rows = [
        new SlotRow({
          id: "batch_1",
          company_name: "Acme Corporation",
          slot_type: "CEO",
          fuzzy_match_status: "MATCHED",
        }),
        new SlotRow({
          id: "batch_2",
          company_name: "Acme Corporation",
          slot_type: "CFO",
          fuzzy_match_status: "MATCHED",
        }),
      ];
      const result = await batchDispatcher(rows, companyMaster);
      assert(result.processed === 2, `Expected 2 processed, got ${result.processed}`);
    })
  );

  // Test 5: Get dispatch stats
  suite.tests.push(
    await runTest("getDispatchStats generates report", async () => {
      const rows = createSampleRows().filter((r) => r.fuzzy_match_status === "MATCHED");
      const result = await batchDispatcher(rows, companyMaster);
      const stats = getDispatchStats(result);
      assert(stats.includes("Dispatch Statistics"), "Expected stats header");
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

/**
 * Test Suite 9: Agent Registry
 */
async function testAgentRegistry(): Promise<TestSuite> {
  const suite: TestSuite = {
    name: "Agent Registry",
    tests: [],
    passed: 0,
    failed: 0,
    duration_ms: 0,
  };
  const start = Date.now();

  // Test 1: Get agent
  suite.tests.push(
    await runTest("Registry provides agents", () => {
      const registry = new AgentRegistry();
      const agent = registry.getAgent("FuzzyMatchAgent");
      assert(agent !== null, "Expected agent");
    })
  );

  // Test 2: Can execute check
  suite.tests.push(
    await runTest("canExecute checks kill switch and throttle", () => {
      const registry = new AgentRegistry();
      const result = registry.canExecute("FuzzyMatchAgent");
      assert(result.allowed, "Expected allowed");
    })
  );

  // Test 3: Get agents by layer
  suite.tests.push(
    await runTest("getAgentsByLayer filters correctly", () => {
      const registry = new AgentRegistry();
      const layer1 = registry.getAgentsByLayer(1);
      assert(layer1.includes("FuzzyMatchAgent"), "Expected FuzzyMatchAgent in layer 1");
    })
  );

  // Test 4: Estimate cost
  suite.tests.push(
    await runTest("estimateCost calculates correctly", () => {
      const registry = new AgentRegistry();
      const cost = registry.estimateCost(["LinkedInFinderAgent", "PatternAgent"]);
      assert(cost > 0, "Expected positive cost");
    })
  );

  // Calculate results
  suite.duration_ms = Date.now() - start;
  suite.passed = suite.tests.filter((t) => t.passed).length;
  suite.failed = suite.tests.filter((t) => !t.passed).length;

  return suite;
}

// =============================================================================
// MAIN TEST RUNNER
// =============================================================================

/**
 * Run all test suites.
 */
export async function runAllTests(): Promise<void> {
  console.log("╔═══════════════════════════════════════════════════════════════╗");
  console.log("║       TALENT ENGINE FOUR-LAYER TEST HARNESS                   ║");
  console.log("╚═══════════════════════════════════════════════════════════════╝\n");

  const suites: TestSuite[] = [];

  // Run all test suites
  suites.push(await testFuzzyMatching());
  suites.push(await testChecklist());
  suites.push(await testCompanyChecker());
  suites.push(await testMissingSlotAgent());
  suites.push(await testThrottleManager());
  suites.push(await testKillSwitch());
  suites.push(await testFailManager());
  suites.push(await testDispatcher());
  suites.push(await testAgentRegistry());

  // Print results
  let totalPassed = 0;
  let totalFailed = 0;

  for (const suite of suites) {
    console.log(`\n┌─ ${suite.name} ─────────────────────────────────────────`);

    for (const test of suite.tests) {
      const status = test.passed ? "✓" : "✗";
      const color = test.passed ? "\x1b[32m" : "\x1b[31m";
      console.log(`│ ${color}${status}\x1b[0m ${test.name} (${test.duration_ms}ms)`);
      if (!test.passed) {
        console.log(`│   └─ ${test.message}`);
      }
    }

    console.log(`└─ ${suite.passed}/${suite.tests.length} passed (${suite.duration_ms}ms)`);

    totalPassed += suite.passed;
    totalFailed += suite.failed;
  }

  // Summary
  console.log("\n╔═══════════════════════════════════════════════════════════════╗");
  console.log("║                       TEST SUMMARY                            ║");
  console.log("╠═══════════════════════════════════════════════════════════════╣");
  console.log(`║  Total Tests:  ${(totalPassed + totalFailed).toString().padStart(3)}                                        ║`);
  console.log(`║  Passed:       \x1b[32m${totalPassed.toString().padStart(3)}\x1b[0m                                        ║`);
  console.log(`║  Failed:       \x1b[31m${totalFailed.toString().padStart(3)}\x1b[0m                                        ║`);
  console.log("╚═══════════════════════════════════════════════════════════════╝");

  if (totalFailed > 0) {
    console.log("\n\x1b[31m⚠ Some tests failed!\x1b[0m");
    process.exit(1);
  } else {
    console.log("\n\x1b[32m✓ All tests passed!\x1b[0m");
  }
}

// Run if executed directly
if (require.main === module) {
  runAllTests().catch(console.error);
}
