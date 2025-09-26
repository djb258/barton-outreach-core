/**
 * Doctrine Spec:
 * - Barton ID: 08.05.01.07.10000.004
 * - Altitude: 10000 (Execution Layer)
 * - Input: campaign trigger event and target data
 * - Output: automated campaign configuration and launch status
 * - MCP: Composio (Neon integrated)
 */
import type { VercelRequest, VercelResponse } from 'import ComposioNeonBridge from './lib/composio-neon-bridge.js';
@vercel/node';
// Initialize Neon client
// Barton Doctrine Campaign Types
const CAMPAIGN_TYPES = {
  PROMOTION: 'PLE',
  BIT_SIGNAL: 'BIT'
} as const;

// Trigger events that can initiate campaigns
const TRIGGER_EVENTS = {
  PROMOTION: 'promotion',
  BIT_SIGNAL_FIRED: 'bit_signal_fired',
  MARKETING_SCORE_THRESHOLD: 'marketing_score_threshold',
  MANUAL_TRIGGER: 'manual_trigger'
} as const;

interface CampaignCreateRequest {
  trigger_event: string;
  company_unique_id: string;
  people: string[];
  campaign_type?: 'PLE' | 'BIT';
  marketing_score?: number;
  custom_blueprint?: any;
}

interface CampaignCreateResponse {
  status: 'success' | 'failed';
  campaign_id?: string;
  message?: string;
  details?: any;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<CampaignCreateResponse>
) {
  // Doctrine enforcement: Only POST method allowed
  if (req.method !== 'POST') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed. Only POST is permitted by doctrine.'
    });
  }

  try {
    // Initialize MCP bridge for Barton Doctrine compliance
    const mcpBridge = new ComposioNeonBridge();
    await mcpBridge.initialize();

    const {
      trigger_event,
      company_unique_id,
      people,
      campaign_type,
      marketing_score,
      custom_blueprint
    } = req.body as CampaignCreateRequest;

    // Validate required fields
    if (!trigger_event || !company_unique_id || !people || people.length === 0) {
      return res.status(400).json({
        status: 'failed',
        message: 'Missing required fields: trigger_event, company_unique_id, and people array'
      });
    }

    // Validate Barton ID format for company
    if (!isValidBartonId(company_unique_id)) {
      return res.status(400).json({
        status: 'failed',
        message: 'Invalid Barton ID format for company_unique_id'
      });
    }

    // Validate Barton IDs for all people
    const invalidPeople = people.filter(id => !isValidBartonId(id));
    if (invalidPeople.length > 0) {
      return res.status(400).json({
        status: 'failed',
        message: `Invalid Barton ID format for people: ${invalidPeople.join(', ')}`
      });
    }

    // Verify records are promoted (doctrine requirement)
    const promotionCheck = await verifyPromotedRecords(company_unique_id, people);
    if (!promotionCheck.valid) {
      return res.status(400).json({
        status: 'failed',
        message: promotionCheck.message,
        details: promotionCheck.details
      });
    }

    // Determine campaign type based on trigger
    const determinedType = campaign_type || determineCampaignType(trigger_event);

    // Get or create campaign blueprint
    const blueprint = custom_blueprint || await getCampaignBlueprint(
      determinedType,
      trigger_event,
      marketing_score
    );

    // Generate Barton campaign ID
    const campaign_id = await generateCampaignId(determinedType);

    // Begin transaction
    await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: 'BEGIN',
      mode: 'write'
    });

    try {
      // Insert campaign record
      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `INSERT INTO marketing.campaigns (
          campaign_id,
          campaign_type,
          trigger_event,
          template,
          company_unique_id,
          people_ids,
          marketing_score,
          status,
          doctrine_version,
          heir_compliant
        ) VALUES (
          ${campaign_id},
          ${determinedType},
          ${trigger_event},
          ${JSON.stringify(blueprint)},
          ${company_unique_id},
          ${people},
          ${marketing_score || null},
          'draft',
          '04.04.03',
          true
        )`,
      mode: 'write'
    });

      // Create audit log entry
      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `INSERT INTO marketing.campaign_audit_log (
          campaign_id,
          action,
          status,
          details,
          initiated_by,
          mcp_tool
        ) VALUES (
          ${campaign_id},
          'create',
          'success',
          ${JSON.stringify({
            trigger_event,
            company_unique_id,
            people_count: people.length,
            campaign_type: determinedType,
            blueprint_template: blueprint.template_id || 'custom'
          })},
          'system',
          'campaign_auto_create'
        )`,
      mode: 'write'
    });

      // Create execution schedule based on blueprint
      if (blueprint.sequence && Array.isArray(blueprint.sequence)) {
        for (const [index, step] of blueprint.sequence.entries()) {
          const scheduledAt = calculateScheduledTime(step.delay || '0d');

          for (const personId of people) {
            // Get person contact info
            const personInfo = await getPersonContactInfo(personId);

            await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `INSERT INTO marketing.campaign_executions (
                campaign_id,
                execution_step,
                step_type,
                scheduled_at,
                target_person_id,
                target_email,
                target_linkedin,
                status
              ) VALUES (
                ${campaign_id},
                ${index + 1},
                ${step.type},
                ${scheduledAt},
                ${personId},
                ${personInfo.email || null},
                ${personInfo.linkedin || null},
                'pending'
              )`,
      mode: 'write'
    });
          }
        }
      }

      // Commit transaction
      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: 'COMMIT',
      mode: 'write'
    });

      // Log success to console for monitoring
      console.log(`[Campaign Auto-Create] SUCCESS: Created campaign ${campaign_id} for company ${company_unique_id}`);

      return res.status(200).json({
        status: 'success',
        campaign_id,
        message: `Campaign created successfully with ${people.length} targets`,
        details: {
          campaign_type: determinedType,
          trigger_event,
          target_count: people.length,
          blueprint_steps: blueprint.sequence?.length || 0
        }
      });

    } catch (error) {
      // Rollback transaction on error
      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: 'ROLLBACK',
      mode: 'write'
    });
      throw error;
    }

  } catch (error) {
    console.error('[Campaign Auto-Create] ERROR:', error);

    // Log failure to audit log (outside transaction)
    try {
      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
      sql: `INSERT INTO marketing.campaign_audit_log (
          campaign_id,
          action,
          status,
          details,
          initiated_by
        ) VALUES (
          'ERROR_' || ${Date.now()},
          'create',
          'failed',
          ${JSON.stringify({
            error: error instanceof Error ? error.message : 'Unknown error',
            request_body: req.body
          })},
          'system'
        )`,
      mode: 'write'
    });
    } catch (auditError) {
      console.error('[Campaign Auto-Create] Audit log error:', auditError);
    }

    return res.status(500).json({
      status: 'failed',
      message: 'Failed to create campaign',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

// Helper function to validate Barton ID format
function isValidBartonId(id: string): boolean {
  // Barton ID format: XX.XX.XX.XX.XXXXX.XXX
  const bartonIdRegex = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/;
  return bartonIdRegex.test(id);
}

// Verify that records have been promoted (doctrine requirement)
async function verifyPromotedRecords(
  companyId: string,
  peopleIds: string[]
): Promise<{ valid: boolean; message?: string; details?: any }> {
  try {
    // Check company is promoted
    const companyResult = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: `SELECT unique_id, promotion_status
      FROM marketing.company_master
      WHERE unique_id = ${companyId}
      AND promotion_status = 'promoted'`,
      mode: 'read'
    });

    if (!companyResult.success) {
      throw new Error(`MCP operation failed: ${companyResult.error}`);
    }

    if (companyResult.length === 0) {
      return {
        valid: false,
        message: `Company ${companyId} is not promoted or does not exist`,
        details: { company_id: companyId }
      };
    }

    // Check all people are promoted
    const peopleResult = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: `SELECT unique_id, promotion_status
      FROM marketing.people_master
      WHERE unique_id = ANY(${peopleIds})
      AND promotion_status = 'promoted'`,
      mode: 'read'
    });

    if (!peopleResult.success) {
      throw new Error(`MCP operation failed: ${peopleResult.error}`);
    }

    if (peopleResult.length !== peopleIds.length) {
      const promotedIds = peopleResult.map(p => p.unique_id);
      const unpromotedIds = peopleIds.filter(id => !promotedIds.includes(id));

      return {
        valid: false,
        message: `Not all people records are promoted`,
        details: {
          unpromoted_people: unpromotedIds,
          promoted_count: promotedIds.length,
          total_count: peopleIds.length
        }
      };
    }

    return { valid: true };
  } catch (error) {
    console.error('[MCP Verify Promoted Records] Error:', error);
    return {
      valid: false,
      message: 'Failed to verify promotion status',
      details: error
    };
  }
}

// Determine campaign type based on trigger event
function determineCampaignType(trigger: string): 'PLE' | 'BIT' {
  if (trigger.includes('bit') || trigger.includes('signal')) {
    return CAMPAIGN_TYPES.BIT_SIGNAL;
  }
  return CAMPAIGN_TYPES.PROMOTION;
}

// Get campaign blueprint based on type and conditions
async function getCampaignBlueprint(
  type: 'PLE' | 'BIT',
  trigger: string,
  marketingScore?: number
): Promise<any> {
  try {
    // Get doctrine-approved template
    const templateResult = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: `SELECT blueprint
      FROM marketing.campaign_templates
      WHERE template_type = ${type}
      AND doctrine_approved = true
      LIMIT 1`,
      mode: 'read'
    });

    if (!templateResult.success) {
      throw new Error(`MCP operation failed: ${templateResult.error}`);
    }

    if (templateResult.length > 0) {
      const blueprint = templateResult[0].blueprint;

      // Modify blueprint based on marketing score if provided
      if (marketingScore !== undefined) {
        blueprint.conditions = blueprint.conditions || {};
        blueprint.conditions.marketing_score = `>= ${marketingScore}`;
      }

      return blueprint;
    }
  } catch (error) {
    console.error('[MCP Get Campaign Blueprint] Error:', error);
  }

  // Return default blueprint if no template found
  if (type === 'BIT') {
    return {
      trigger,
      template_id: 'BIT_DEFAULT',
      conditions: {
        signal_strength: '>= 70',
        has_contact_info: true
      },
      sequence: [
        { type: 'email', template: 'bit_urgent', delay: '0h' },
        { type: 'phone_call', delay: '2h', priority: 'high' }
      ]
    };
  }

  return {
    trigger,
    template_id: 'PLE_DEFAULT',
    conditions: {
      marketing_score: `>= ${marketingScore || 80}`,
      has_email: true
    },
    sequence: [
      { type: 'email', template: 'intro_email', delay: '0d' },
      { type: 'linkedin_connect', delay: '3d' },
      { type: 'email', template: 'follow_up', delay: '7d' }
    ]
  };
}

// Generate Barton Campaign ID
async function generateCampaignId(type: 'PLE' | 'BIT'): Promise<string> {
  try {
    const result = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: `SELECT marketing.generate_campaign_id(${type}) as campaign_id`,
      mode: 'read'
    });

    if (!result.success) {
      throw new Error(`MCP operation failed: ${result.error}`);
    }
    return result.data.rows[0].campaign_id;
  } catch (error) {
    // Fallback ID generation
    const typeCode = type === 'PLE' ? '04' : '05';
    const sequence = Math.floor(Math.random() * 99999).toString().padStart(5, '0');
    const checksum = Math.floor(Math.random() * 999).toString().padStart(3, '0');
    return `04.04.03.${typeCode}.${sequence}.${checksum}`;
  }
}

// Calculate scheduled time based on delay string (e.g., '2d', '4h')
function calculateScheduledTime(delay: string): Date {
  const now = new Date();
  const match = delay.match(/^(\d+)([dhm])$/);

  if (!match) return now;

  const [, amount, unit] = match;
  const value = parseInt(amount);

  switch (unit) {
    case 'd':
      now.setDate(now.getDate() + value);
      break;
    case 'h':
      now.setHours(now.getHours() + value);
      break;
    case 'm':
      now.setMinutes(now.getMinutes() + value);
      break;
  }

  return now;
}

// Get person contact information
async function getPersonContactInfo(personId: string): Promise<any> {
  try {
    const result = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: `SELECT email, linkedin_url
      FROM marketing.people_master
      WHERE unique_id = ${personId}`,
      mode: 'read'
    });

    if (!result.success) {
      throw new Error(`MCP operation failed: ${result.error}`);
    }

    return result.data.rows[0] || { email: null, linkedin: null };
  } catch (error) {
    console.error('[MCP Get Person Contact] Error:', error);
    return { email: null, linkedin: null };
  }
}