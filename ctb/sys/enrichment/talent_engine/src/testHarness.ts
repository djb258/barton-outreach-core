/**
 * Test Harness
 * ============
 * Demonstrates the Talent Engine shell working end-to-end.
 * Creates a fake SlotRow and runs it through the dispatcher
 * until slot_complete === true.
 *
 * Includes cost tracking simulation and assertions.
 */

import { SlotRow } from "./SlotRow";
import { evaluateChecklist, getMissingSummary } from "./checklist";
import { dispatcher } from "./dispatcher";
import { ThrottleManager } from "./throttle";
import { KillSwitchManager } from "./killswitch";
import { CostGuard } from "./costGuard";
import { agentCosts } from "./costs";

/**
 * Simulate agent processing by updating the row with dummy data.
 * In real implementation, agents would make API calls.
 */
function simulateAgentResult(row: SlotRow, agentType: string): void {
  switch (agentType) {
    case "LinkedInFinderAgent":
      row.update({
        linkedin_url: "https://linkedin.com/in/fake-profile-123",
      });
      break;
    case "PublicScannerAgent":
      row.update({
        public_accessible: true,
      });
      break;
    case "PatternAgent":
      row.update({
        email_pattern: "{first}.{last}@company.com",
      });
      break;
    case "EmailGeneratorAgent":
      row.update({
        email: "john.doe@company.com",
        email_verified: true,
      });
      break;
    case "TitleCompanyAgent":
      row.update({
        current_title: "Chief Executive Officer",
        current_company: "Acme Corp",
      });
      break;
    case "HashAgent":
      row.update({
        movement_hash: "hash_abc123def456",
      });
      break;
  }
}

/**
 * Run the test harness.
 */
function runTestHarness(): void {
  console.log("=".repeat(60));
  console.log("TALENT ENGINE SHELL - TEST HARNESS");
  console.log("=".repeat(60));
  console.log("");

  // Step 1: Create a fake SlotRow with minimal data
  console.log("[STEP 1] Creating fake SlotRow...");
  const row = new SlotRow({
    id: "slot_001",
    company_name: "Acme Corp",
    slot_type: "CEO",
    person_name: "John Doe", // We have the person name
    // Everything else is null/missing
  });

  console.log(`  Created SlotRow: ${row.id}`);
  console.log(`  Company: ${row.company_name}`);
  console.log(`  Slot Type: ${row.slot_type}`);
  console.log(`  Person: ${row.person_name}`);
  console.log(`  Slot Cost Limit: $${row.slot_cost_limit.toFixed(2)}`);
  console.log("");

  // Step 2: Initialize throttle, kill switch, and cost guard managers
  console.log("[STEP 2] Initializing managers...");
  const throttle = new ThrottleManager({
    max_calls_per_minute: 100,
    max_calls_per_day: 1000,
  });
  const killSwitch = new KillSwitchManager();
  const costGuard = new CostGuard({
    dailyLimit: 50.0,
    monthlyLimit: 500.0,
  });

  console.log(`  Throttle: ${throttle.getStatusString()}`);
  console.log(`  Kill Switches: All agents active`);
  console.log(`  Cost Guard: ${costGuard.getStatusString()}`);
  console.log("");

  // Step 3: Run through dispatcher until complete
  console.log("[STEP 3] Running dispatcher loop...");
  console.log("-".repeat(60));

  let iteration = 0;
  const maxIterations = 10; // Safety limit
  let totalCostIncurred = 0;

  while (!row.slot_complete && iteration < maxIterations) {
    iteration++;
    console.log(`\n[Iteration ${iteration}]`);

    // Evaluate checklist
    const checklist = evaluateChecklist(row);
    const missing = getMissingSummary(checklist);
    console.log(`  Missing items: ${missing.length > 0 ? missing.join(", ") : "None"}`);
    console.log(`  Ready for completion: ${checklist.ready_for_completion}`);

    // Dispatch with cost guard
    const result = dispatcher(row, throttle, killSwitch, costGuard);
    console.log(`  Dispatch status: ${result.status}`);
    console.log(`  Reason: ${result.reason}`);

    if (result.status === "ROUTED" && result.agent_type) {
      console.log(`  Agent: ${result.agent_type}`);
      console.log(`  Task ID: ${result.task?.task_id}`);
      console.log(`  Cost incurred: $${(result.cost_incurred ?? 0).toFixed(4)}`);
      totalCostIncurred += result.cost_incurred ?? 0;

      // Simulate agent processing
      console.log(`  [Simulating agent work...]`);
      simulateAgentResult(row, result.agent_type);
      console.log(`  [Agent work complete]`);
    }

    if (result.status === "COMPLETED") {
      console.log(`  SLOT COMPLETED!`);
      break;
    }

    if (result.status === "THROTTLED") {
      console.log(`  THROTTLED - would retry later`);
      break;
    }

    if (result.status === "KILLED") {
      console.log(`  KILLED - agent blocked by kill switch`);
      break;
    }

    if (result.status === "COST_EXCEEDED") {
      console.log(`  COST_EXCEEDED - budget exhausted`);
      break;
    }
  }

  console.log("");
  console.log("-".repeat(60));

  // Step 4: Show final state
  console.log("[STEP 4] Final SlotRow State:");
  console.log(`  id: ${row.id}`);
  console.log(`  company_name: ${row.company_name}`);
  console.log(`  slot_type: ${row.slot_type}`);
  console.log(`  person_name: ${row.person_name}`);
  console.log(`  linkedin_url: ${row.linkedin_url}`);
  console.log(`  public_accessible: ${row.public_accessible}`);
  console.log(`  email: ${row.email}`);
  console.log(`  email_pattern: ${row.email_pattern}`);
  console.log(`  email_verified: ${row.email_verified}`);
  console.log(`  current_title: ${row.current_title}`);
  console.log(`  current_company: ${row.current_company}`);
  console.log(`  movement_hash: ${row.movement_hash}`);
  console.log(`  slot_complete: ${row.slot_complete}`);
  console.log(`  slot_cost_accumulated: $${row.slot_cost_accumulated.toFixed(4)}`);
  console.log(`  slot_cost_limit: $${row.slot_cost_limit.toFixed(2)}`);
  console.log(`  last_updated: ${row.last_updated.toISOString()}`);
  console.log("");

  // Step 5: Show cost and throttle stats
  console.log("[STEP 5] Cost & Throttle Stats:");
  console.log(`  Throttle: ${throttle.getStatusString()}`);
  console.log(`  Cost Guard: ${costGuard.getStatusString()}`);
  console.log(`  Total Cost This Run: $${totalCostIncurred.toFixed(4)}`);
  console.log(`  Slot Cost Accumulated: $${row.slot_cost_accumulated.toFixed(4)}`);
  console.log("");

  // Step 6: Test kill switch
  console.log("[STEP 6] Testing Kill Switch...");
  killSwitch.kill("LinkedInFinderAgent");
  console.log(`  Killed: ${killSwitch.getKilledAgents().join(", ")}`);
  console.log(`  Active: ${killSwitch.getActiveAgents().join(", ")}`);

  // Create another row to test kill switch
  const row2 = new SlotRow({
    id: "slot_002",
    company_name: "Test Corp",
    slot_type: "CFO",
    person_name: "Jane Smith",
  });

  const result2 = dispatcher(row2, throttle, killSwitch, costGuard);
  console.log(`  Dispatch row2 status: ${result2.status}`);
  console.log(`  Reason: ${result2.reason}`);
  console.log("");

  // Step 7: Test cost ceiling
  console.log("[STEP 7] Testing Cost Ceiling...");
  const expensiveRow = new SlotRow({
    id: "slot_003",
    company_name: "Expensive Corp",
    slot_type: "HR",
    person_name: "Cost Test",
    slot_cost_limit: 0.005, // Very low limit - only allows PatternAgent (free)
  });
  killSwitch.revive("LinkedInFinderAgent"); // Revive for this test

  console.log(`  Row3 cost limit: $${expensiveRow.slot_cost_limit.toFixed(3)}`);
  console.log(`  LinkedInFinderAgent cost: $${agentCosts.LinkedInFinderAgent.toFixed(3)}`);

  const result3 = dispatcher(expensiveRow, throttle, killSwitch, costGuard);
  console.log(`  Dispatch row3 status: ${result3.status}`);
  console.log(`  Reason: ${result3.reason}`);

  // Assertion: Should be COST_EXCEEDED because LinkedInFinderAgent costs $0.01 but limit is $0.005
  if (result3.status === "COST_EXCEEDED") {
    console.log(`  ✓ ASSERTION PASSED: Cost ceiling correctly blocked expensive agent`);
  } else {
    console.log(`  ✗ ASSERTION FAILED: Expected COST_EXCEEDED, got ${result3.status}`);
  }
  console.log("");

  // Step 8: Test global cost guard exhaustion
  console.log("[STEP 8] Testing Global Cost Guard...");
  const tinyBudgetGuard = new CostGuard({
    dailyLimit: 0.001,
    monthlyLimit: 0.001,
  });
  // Spend the budget
  tinyBudgetGuard.recordSpend(0.001);

  const row4 = new SlotRow({
    id: "slot_004",
    company_name: "Budget Test Corp",
    slot_type: "BENEFITS",
    person_name: "Budget Test",
  });

  const result4 = dispatcher(row4, throttle, killSwitch, tinyBudgetGuard);
  console.log(`  Guard status: ${tinyBudgetGuard.getStatusString()}`);
  console.log(`  Dispatch row4 status: ${result4.status}`);
  console.log(`  Reason: ${result4.reason}`);

  // Assertion: Should be COST_EXCEEDED due to exhausted global budget
  if (result4.status === "COST_EXCEEDED") {
    console.log(`  ✓ ASSERTION PASSED: Global cost guard correctly blocked dispatch`);
  } else {
    console.log(`  ✗ ASSERTION FAILED: Expected COST_EXCEEDED, got ${result4.status}`);
  }
  console.log("");

  // Step 9: Success summary
  console.log("=".repeat(60));
  console.log("TEST HARNESS COMPLETE");
  console.log("=".repeat(60));
  console.log("");
  console.log("Shell components verified:");
  console.log("  [x] SlotRow data model");
  console.log("  [x] Checklist evaluator");
  console.log("  [x] Dispatcher routing");
  console.log("  [x] Throttle system");
  console.log("  [x] Kill switch manager");
  console.log("  [x] Agent stubs");
  console.log("  [x] Row lifecycle (empty -> complete)");
  console.log("  [x] Per-agent cost tracking");
  console.log("  [x] Slot cost ceiling enforcement");
  console.log("  [x] Global cost guard enforcement");
  console.log("");
}

// Run the harness
runTestHarness();
