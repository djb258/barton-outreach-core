#!/usr/bin/env node
/**
 * Unified Workflow CLI
 * ====================
 * File → Miro → Linear → Claude Code
 * 
 * Complete workflow orchestration for the Barton system.
 * 
 * Commands:
 *   push <file> [board-id]     Push file to Miro board
 *   linear-sync <file> [team]  Create Linear issues from file
 *   issues [team]              List open Linear issues
 *   claude-ready               List issues ready for implementation
 *   full <file> [board] [team] Run full workflow (Miro + Linear)
 *   help                       Show help
 */

import { uploadMarkdownToMiro } from './miro-uploader.js';
import { 
  createIssuesFromMarkdown, 
  getOpenIssues, 
  getClaudeReadyIssues,
  getTeams 
} from './linear-sync.js';
import path from 'path';
import fs from 'fs';
import { config } from 'dotenv';

// Load environment variables
config({ path: path.resolve(process.cwd(), '.env') });

const VERSION = '1.0.0';

interface WorkflowResult {
  success: boolean;
  miro?: {
    itemCount: number;
    frameId?: string;
  };
  linear?: {
    issueCount: number;
    issues: string[];
  };
  error?: string;
}

/**
 * Print banner
 */
function printBanner() {
  console.log(`
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🔄 Miro → Linear → Claude Code Workflow                    ║
║                                                              ║
║   Version: ${VERSION}                                           ║
║   Barton Enterprises Integration Suite                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
`);
}

/**
 * Print help
 */
function printHelp() {
  console.log(`
Usage: npx tsx workflow.ts <command> [options]

Commands:
  push <file> [board-id]       Push markdown file to Miro board
                               Creates frames, shapes, and sticky notes

  linear-sync <file> [team]    Create Linear issues from file sections
                               Extracts ## headers as issues

  issues [team-key]            List open issues in Linear
                               Optional: filter by team key

  claude-ready                 List issues tagged 'claude-ready'
                               These are ready for implementation

  full <file> [board] [team]   Run full workflow:
                               1. Push to Miro
                               2. Create Linear issues
                               3. Show claude-ready issues

  teams                        List available Linear teams

  help                         Show this help message

Examples:
  # Push BICYCLE_WHEEL_DOCTRINE.md to Miro
  npx tsx workflow.ts push ../../repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md

  # Create Linear issues from PRD
  npx tsx workflow.ts linear-sync ../../docs/prd/HUB_PROCESS_SIGNAL_MATRIX.md ENG

  # Run full workflow
  npx tsx workflow.ts full ../../repo-data-diagrams/BICYCLE_WHEEL_DOCTRINE.md

  # List claude-ready issues for implementation
  npx tsx workflow.ts claude-ready

Environment Variables:
  MIRO_TOKEN       Miro API access token (required for Miro commands)
  MIRO_BOARD_ID    Default Miro board ID
  LINEAR_API_KEY   Linear API key (required for Linear commands)
  LINEAR_TEAM_KEY  Default Linear team key (e.g., ENG)
`);
}

/**
 * Push file to Miro
 */
async function pushToMiro(filePath: string, boardId?: string): Promise<WorkflowResult> {
  console.log('\n📤 Pushing to Miro...\n');
  
  const resolvedPath = path.resolve(process.cwd(), filePath);
  
  if (!fs.existsSync(resolvedPath)) {
    return { success: false, error: `File not found: ${resolvedPath}` };
  }

  try {
    const result = await uploadMarkdownToMiro(resolvedPath, boardId);
    return {
      success: true,
      miro: {
        itemCount: result.itemCount,
        frameId: result.frameId,
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Create Linear issues from file
 */
async function syncToLinear(filePath: string, teamKey?: string): Promise<WorkflowResult> {
  console.log('\n📋 Creating Linear issues...\n');
  
  const resolvedPath = path.resolve(process.cwd(), filePath);
  
  if (!fs.existsSync(resolvedPath)) {
    return { success: false, error: `File not found: ${resolvedPath}` };
  }

  try {
    const issues = await createIssuesFromMarkdown(resolvedPath, teamKey);
    return {
      success: true,
      linear: {
        issueCount: issues.length,
        issues: issues.map(i => `[${i.identifier}] ${i.title}`),
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Run full workflow
 */
async function runFullWorkflow(
  filePath: string,
  boardId?: string,
  teamKey?: string
): Promise<WorkflowResult> {
  console.log('\n🚀 Running full workflow: File → Miro → Linear\n');
  
  const result: WorkflowResult = { success: true };
  
  // Step 1: Push to Miro
  console.log('Step 1/3: Pushing to Miro...');
  const miroResult = await pushToMiro(filePath, boardId);
  if (!miroResult.success) {
    console.log(`  ⚠️  Miro push failed: ${miroResult.error}`);
    console.log('  Continuing with Linear...\n');
  } else {
    result.miro = miroResult.miro;
    console.log(`  ✅ Created ${miroResult.miro?.itemCount} items on Miro\n`);
  }
  
  // Step 2: Create Linear issues
  console.log('Step 2/3: Creating Linear issues...');
  const linearResult = await syncToLinear(filePath, teamKey);
  if (!linearResult.success) {
    console.log(`  ⚠️  Linear sync failed: ${linearResult.error}\n`);
  } else {
    result.linear = linearResult.linear;
    console.log(`  ✅ Created ${linearResult.linear?.issueCount} Linear issues\n`);
  }
  
  // Step 3: Show claude-ready issues
  console.log('Step 3/3: Issues ready for Claude Code:');
  try {
    const claudeReady = await getClaudeReadyIssues();
    if (claudeReady.length === 0) {
      console.log('  No issues with "claude-ready" label found');
    } else {
      claudeReady.forEach(i => {
        console.log(`  🤖 [${i.identifier}] ${i.title}`);
      });
    }
  } catch (error) {
    console.log(`  ⚠️  Could not fetch claude-ready issues`);
  }
  
  return result;
}

/**
 * List open issues
 */
async function listIssues(teamKey?: string): Promise<void> {
  console.log(`\n📋 Open issues${teamKey ? ` for team ${teamKey}` : ''}:\n`);
  
  try {
    const issues = await getOpenIssues(teamKey);
    
    if (issues.length === 0) {
      console.log('  No open issues found');
      return;
    }
    
    // Group by state
    const byState = new Map<string, typeof issues>();
    issues.forEach(issue => {
      const state = issue.state;
      if (!byState.has(state)) {
        byState.set(state, []);
      }
      byState.get(state)!.push(issue);
    });
    
    // Print by state
    for (const [state, stateIssues] of byState) {
      console.log(`  ${state}:`);
      stateIssues.forEach(i => {
        const priority = ['', '🔴', '🟠', '🟡', '🟢'][i.priority] || '⚪';
        console.log(`    ${priority} [${i.identifier}] ${i.title}`);
      });
      console.log();
    }
    
    console.log(`Total: ${issues.length} issues`);
  } catch (error) {
    console.error('❌ Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * List claude-ready issues
 */
async function listClaudeReady(): Promise<void> {
  console.log('\n🤖 Issues ready for Claude Code implementation:\n');
  
  try {
    const issues = await getClaudeReadyIssues();
    
    if (issues.length === 0) {
      console.log('  No issues found with "claude-ready" label');
      console.log('\n  To tag an issue for Claude Code:');
      console.log('  1. Open the issue in Linear');
      console.log('  2. Add the "claude-ready" label');
      return;
    }
    
    issues.forEach(i => {
      const priority = ['', '🔴', '🟠', '🟡', '🟢'][i.priority] || '⚪';
      console.log(`  ${priority} [${i.identifier}] ${i.title}`);
      if (i.description) {
        const desc = i.description.slice(0, 80).replace(/\n/g, ' ');
        console.log(`     ${desc}${i.description.length > 80 ? '...' : ''}`);
      }
      console.log(`     ${i.url}`);
      console.log();
    });
    
    console.log(`Total: ${issues.length} issues ready for implementation`);
  } catch (error) {
    console.error('❌ Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * List teams
 */
async function listTeams(): Promise<void> {
  console.log('\n📋 Available Linear teams:\n');
  
  try {
    const teams = await getTeams();
    teams.forEach(t => {
      console.log(`  [${t.key}] ${t.name}`);
    });
  } catch (error) {
    console.error('❌ Error:', error instanceof Error ? error.message : error);
  }
}

/**
 * Main CLI entry point
 */
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  printBanner();

  switch (command) {
    case 'push': {
      const filePath = args[1];
      const boardId = args[2];
      
      if (!filePath) {
        console.log('Usage: npx tsx workflow.ts push <file-path> [board-id]');
        process.exit(1);
      }
      
      const result = await pushToMiro(filePath, boardId);
      if (result.success) {
        console.log(`\n✅ Success! Created ${result.miro?.itemCount} items on Miro`);
      } else {
        console.error(`\n❌ Failed: ${result.error}`);
        process.exit(1);
      }
      break;
    }
    
    case 'linear-sync': {
      const filePath = args[1];
      const teamKey = args[2];
      
      if (!filePath) {
        console.log('Usage: npx tsx workflow.ts linear-sync <file-path> [team-key]');
        process.exit(1);
      }
      
      const result = await syncToLinear(filePath, teamKey);
      if (result.success) {
        console.log(`\n✅ Success! Created ${result.linear?.issueCount} Linear issues`);
        result.linear?.issues.forEach(i => console.log(`  • ${i}`));
      } else {
        console.error(`\n❌ Failed: ${result.error}`);
        process.exit(1);
      }
      break;
    }
    
    case 'issues': {
      await listIssues(args[1]);
      break;
    }
    
    case 'claude-ready': {
      await listClaudeReady();
      break;
    }
    
    case 'teams': {
      await listTeams();
      break;
    }
    
    case 'full': {
      const filePath = args[1];
      const boardId = args[2];
      const teamKey = args[3];
      
      if (!filePath) {
        console.log('Usage: npx tsx workflow.ts full <file-path> [board-id] [team-key]');
        process.exit(1);
      }
      
      const result = await runFullWorkflow(filePath, boardId, teamKey);
      
      console.log('\n' + '═'.repeat(60));
      console.log('                    WORKFLOW COMPLETE');
      console.log('═'.repeat(60));
      
      if (result.miro) {
        console.log(`\n📊 Miro: ${result.miro.itemCount} items created`);
      }
      if (result.linear) {
        console.log(`📋 Linear: ${result.linear.issueCount} issues created`);
      }
      
      console.log('\n🎯 Next steps:');
      console.log('   1. Review items in Miro board');
      console.log('   2. Check issues in Linear');
      console.log('   3. Run "claude-ready" to see implementation tasks');
      break;
    }
    
    case 'help':
    default:
      printHelp();
  }
}

main().catch(error => {
  console.error('❌ Unhandled error:', error);
  process.exit(1);
});


