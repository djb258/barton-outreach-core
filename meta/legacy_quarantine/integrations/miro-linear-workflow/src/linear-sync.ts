/**
 * Linear Sync
 * ===========
 * Create and sync Linear issues from Miro boards or directly.
 * 
 * Workflow: Miro → Linear
 * 
 * Features:
 * - Create Linear issues from file sections
 * - List issues tagged for Claude Code implementation
 * - Update issue status
 * - Sync between Miro stickies and Linear issues
 */

import { LinearClient } from '@linear/sdk';
import path from 'path';
import fs from 'fs';
import { config } from 'dotenv';
import type { LinearIssue, LinearTeam, LinearConfig } from './types.js';

// Load environment variables
config({ path: path.resolve(process.cwd(), '.env') });

/**
 * Create a Linear client instance
 */
function createLinearClient(): LinearClient {
  const apiKey = process.env.LINEAR_API_KEY;
  
  if (!apiKey) {
    throw new Error('LINEAR_API_KEY is required');
  }

  return new LinearClient({ apiKey });
}

/**
 * Get all teams
 */
export async function getTeams(): Promise<LinearTeam[]> {
  const client = createLinearClient();
  const teams = await client.teams();
  
  return teams.nodes.map(t => ({
    id: t.id,
    key: t.key,
    name: t.name,
  }));
}

/**
 * Get team by key
 */
export async function getTeamByKey(teamKey: string): Promise<LinearTeam | null> {
  const teams = await getTeams();
  return teams.find(t => t.key === teamKey) || null;
}

/**
 * Create a new issue
 */
export async function createIssue(
  title: string,
  description: string,
  teamKey?: string,
  labels?: string[],
  priority?: number
): Promise<LinearIssue> {
  const client = createLinearClient();
  const targetTeamKey = teamKey || process.env.LINEAR_TEAM_KEY || 'ENG';
  
  // Get team
  const team = await getTeamByKey(targetTeamKey);
  if (!team) {
    throw new Error(`Team with key "${targetTeamKey}" not found`);
  }

  // Get or create labels
  let labelIds: string[] = [];
  if (labels && labels.length > 0) {
    const teamData = await client.team(team.id);
    const existingLabels = await teamData.labels();
    
    for (const labelName of labels) {
      const existing = existingLabels.nodes.find(l => l.name === labelName);
      if (existing) {
        labelIds.push(existing.id);
      } else {
        // Create label if it doesn't exist
        const newLabel = await client.createIssueLabel({
          teamId: team.id,
          name: labelName,
        });
        if (newLabel.issueLabel) {
          labelIds.push(newLabel.issueLabel.id);
        }
      }
    }
  }

  // Create issue
  const issuePayload = await client.createIssue({
    teamId: team.id,
    title,
    description,
    priority: priority || 2, // Default to Medium priority
    labelIds: labelIds.length > 0 ? labelIds : undefined,
  });

  if (!issuePayload.issue) {
    throw new Error('Failed to create issue');
  }

  const issue = await issuePayload.issue;
  const state = await issue.state;
  const issueLabels = await issue.labels();

  return {
    id: issue.id,
    identifier: issue.identifier,
    title: issue.title,
    description: issue.description || undefined,
    state: state?.name || 'Unknown',
    priority: issue.priority,
    labels: issueLabels.nodes.map(l => l.name),
    url: issue.url,
  };
}

/**
 * Get issues ready for Claude Code implementation
 */
export async function getClaudeReadyIssues(teamKey?: string): Promise<LinearIssue[]> {
  const client = createLinearClient();
  
  // Get issues with 'claude-ready' label or in specific states
  const issues = await client.issues({
    filter: {
      labels: { name: { eq: 'claude-ready' } },
    },
    first: 50,
  });

  const result: LinearIssue[] = [];
  
  for (const issue of issues.nodes) {
    const state = await issue.state;
    const labels = await issue.labels();
    
    result.push({
      id: issue.id,
      identifier: issue.identifier,
      title: issue.title,
      description: issue.description || undefined,
      state: state?.name || 'Unknown',
      priority: issue.priority,
      labels: labels.nodes.map(l => l.name),
      url: issue.url,
    });
  }

  return result;
}

/**
 * Get all open issues for a team
 */
export async function getOpenIssues(teamKey?: string): Promise<LinearIssue[]> {
  const client = createLinearClient();
  const targetTeamKey = teamKey || process.env.LINEAR_TEAM_KEY || 'ENG';
  
  const team = await getTeamByKey(targetTeamKey);
  if (!team) {
    throw new Error(`Team with key "${targetTeamKey}" not found`);
  }

  const issues = await client.issues({
    filter: {
      team: { key: { eq: targetTeamKey } },
      state: { type: { in: ['backlog', 'unstarted', 'started'] } },
    },
    first: 100,
  });

  const result: LinearIssue[] = [];
  
  for (const issue of issues.nodes) {
    const state = await issue.state;
    const labels = await issue.labels();
    
    result.push({
      id: issue.id,
      identifier: issue.identifier,
      title: issue.title,
      description: issue.description || undefined,
      state: state?.name || 'Unknown',
      priority: issue.priority,
      labels: labels.nodes.map(l => l.name),
      url: issue.url,
    });
  }

  return result;
}

/**
 * Update issue state (e.g., mark as done)
 */
export async function updateIssueState(
  issueId: string,
  stateName: 'Todo' | 'In Progress' | 'Done' | 'Cancelled'
): Promise<void> {
  const client = createLinearClient();
  
  // Get the issue to find its team
  const issue = await client.issue(issueId);
  const team = await issue.team;
  
  if (!team) {
    throw new Error('Could not find team for issue');
  }

  // Get workflow states for the team
  const states = await team.states();
  const targetState = states.nodes.find(s => s.name === stateName);
  
  if (!targetState) {
    throw new Error(`State "${stateName}" not found for team`);
  }

  await client.updateIssue(issueId, {
    stateId: targetState.id,
  });
}

/**
 * Create issues from a markdown file's sections
 */
export async function createIssuesFromMarkdown(
  filePath: string,
  teamKey?: string,
  prefix?: string
): Promise<LinearIssue[]> {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  
  const issues: LinearIssue[] = [];
  const filePrefix = prefix || path.basename(filePath, '.md');
  
  // Extract ## headers as issues
  for (const line of lines) {
    if (line.startsWith('## ')) {
      const title = line.slice(3).trim();
      
      // Skip certain sections
      if (['Summary', 'Related Files', 'Version History'].includes(title)) {
        continue;
      }
      
      console.log(`Creating issue: ${filePrefix} - ${title}`);
      
      const issue = await createIssue(
        `[${filePrefix}] ${title}`,
        `Implement: ${title}\n\nSource: ${filePath}`,
        teamKey,
        ['claude-ready', 'documentation'],
        2
      );
      
      issues.push(issue);
    }
  }

  return issues;
}

/**
 * Format issue for display
 */
function formatIssue(issue: LinearIssue): string {
  const priorityEmoji = ['', '🔴', '🟠', '🟡', '🟢'][issue.priority] || '⚪';
  const labels = issue.labels.length > 0 ? ` [${issue.labels.join(', ')}]` : '';
  return `${priorityEmoji} [${issue.identifier}] ${issue.title}${labels} - ${issue.state}`;
}

// CLI entry point
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  try {
    switch (command) {
      case 'teams': {
        console.log('📋 Available teams:\n');
        const teams = await getTeams();
        teams.forEach(t => console.log(`  [${t.key}] ${t.name}`));
        break;
      }
      
      case 'issues': {
        const teamKey = args[1];
        console.log(`📋 Open issues${teamKey ? ` for team ${teamKey}` : ''}:\n`);
        const issues = await getOpenIssues(teamKey);
        issues.forEach(i => console.log(`  ${formatIssue(i)}`));
        console.log(`\nTotal: ${issues.length} issues`);
        break;
      }
      
      case 'claude-ready': {
        console.log('🤖 Issues ready for Claude Code:\n');
        const issues = await getClaudeReadyIssues();
        if (issues.length === 0) {
          console.log('  No issues found with "claude-ready" label');
        } else {
          issues.forEach(i => console.log(`  ${formatIssue(i)}`));
        }
        break;
      }
      
      case 'create': {
        const title = args[1];
        const description = args[2] || '';
        const teamKey = args[3];
        
        if (!title) {
          console.log('Usage: npx tsx linear-sync.ts create <title> [description] [team-key]');
          process.exit(1);
        }
        
        console.log(`Creating issue: ${title}`);
        const issue = await createIssue(title, description, teamKey, ['claude-ready']);
        console.log(`✅ Created: ${formatIssue(issue)}`);
        console.log(`   URL: ${issue.url}`);
        break;
      }
      
      case 'from-file': {
        const filePath = args[1];
        const teamKey = args[2];
        
        if (!filePath) {
          console.log('Usage: npx tsx linear-sync.ts from-file <file-path> [team-key]');
          process.exit(1);
        }
        
        console.log(`Creating issues from: ${filePath}\n`);
        const issues = await createIssuesFromMarkdown(filePath, teamKey);
        console.log(`\n✅ Created ${issues.length} issues`);
        break;
      }
      
      case 'done': {
        const issueId = args[1];
        
        if (!issueId) {
          console.log('Usage: npx tsx linear-sync.ts done <issue-id>');
          process.exit(1);
        }
        
        await updateIssueState(issueId, 'Done');
        console.log(`✅ Marked ${issueId} as Done`);
        break;
      }
      
      default:
        console.log('Linear Sync CLI');
        console.log('================\n');
        console.log('Commands:');
        console.log('  teams                         List available teams');
        console.log('  issues [team-key]             List open issues');
        console.log('  claude-ready                  List issues ready for Claude Code');
        console.log('  create <title> [desc] [team]  Create a new issue');
        console.log('  from-file <path> [team]       Create issues from markdown file');
        console.log('  done <issue-id>               Mark issue as done');
    }
  } catch (error) {
    console.error('❌ Error:', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

main();


