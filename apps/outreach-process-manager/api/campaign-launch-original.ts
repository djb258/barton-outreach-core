import type { VercelRequest, VercelResponse } from '@vercel/node';
import { neon } from '@neondatabase/serverless';

// Initialize Neon client
const sql = neon(process.env.NEON_DB_URL || '');

// MCP Tool integrations (via Composio bridge)
const MCP_TOOLS = {
  INSTANTLY: 'instantly',
  HEYREACH: 'heyreach',
  LEMLIST: 'lemlist',
  APOLLO: 'apollo',
  SALESFORCE: 'salesforce',
  HUBSPOT: 'hubspot'
} as const;

interface CampaignLaunchRequest {
  campaign_id: string;
  launch_mode?: 'immediate' | 'scheduled';
  target_tools?: string[];
  test_mode?: boolean;
}

interface CampaignLaunchResponse {
  status: 'success' | 'failed';
  campaign_id?: string;
  message?: string;
  launched_to?: string[];
  execution_ids?: string[];
  details?: any;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<CampaignLaunchResponse>
) {
  // Doctrine enforcement: Only POST method allowed
  if (req.method !== 'POST') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed. Only POST is permitted by doctrine.'
    });
  }

  try {
    const {
      campaign_id,
      launch_mode = 'immediate',
      target_tools = ['instantly', 'heyreach'],
      test_mode = false
    } = req.body as CampaignLaunchRequest;

    // Validate campaign_id
    if (!campaign_id) {
      return res.status(400).json({
        status: 'failed',
        message: 'Missing required field: campaign_id'
      });
    }

    // Validate Barton ID format
    if (!isValidCampaignId(campaign_id)) {
      return res.status(400).json({
        status: 'failed',
        message: 'Invalid campaign_id format. Must be a valid Barton ID.'
      });
    }

    // Fetch campaign details
    const campaign = await getCampaignDetails(campaign_id);
    if (!campaign) {
      return res.status(404).json({
        status: 'failed',
        message: `Campaign ${campaign_id} not found`
      });
    }

    // Verify campaign status
    if (campaign.status === 'active') {
      return res.status(400).json({
        status: 'failed',
        message: 'Campaign is already active'
      });
    }

    if (campaign.status === 'completed') {
      return res.status(400).json({
        status: 'failed',
        message: 'Cannot launch a completed campaign'
      });
    }

    // Begin transaction
    await sql('BEGIN');

    try {
      // Update campaign status
      await sql`
        UPDATE marketing.campaigns
        SET status = 'active',
            launched_at = NOW(),
            updated_at = NOW()
        WHERE campaign_id = ${campaign_id}
      `;

      // Create launch audit log
      await sql`
        INSERT INTO marketing.campaign_audit_log (
          campaign_id,
          action,
          status,
          details,
          initiated_by,
          mcp_tool
        ) VALUES (
          ${campaign_id},
          'launch',
          'pending',
          ${JSON.stringify({
            launch_mode,
            target_tools,
            test_mode,
            campaign_type: campaign.campaign_type,
            target_count: campaign.people_ids.length
          })},
          'system',
          'campaign_launcher'
        )
      `;

      // Launch to each target tool
      const launchResults = [];
      const executionIds = [];

      for (const tool of target_tools) {
        try {
          // Launch campaign to specific tool via Composio bridge
          const launchResult = await launchToTool(
            tool,
            campaign,
            test_mode
          );

          if (launchResult.success) {
            launchResults.push(tool);
            executionIds.push(...(launchResult.execution_ids || []));

            // Update execution records
            if (launchResult.execution_ids) {
              for (const execId of launchResult.execution_ids) {
                await sql`
                  UPDATE marketing.campaign_executions
                  SET status = 'executing',
                      response = ${JSON.stringify({
                        tool,
                        external_id: execId,
                        launched_at: new Date().toISOString()
                      })}
                  WHERE campaign_id = ${campaign_id}
                  AND status = 'pending'
                `;
              }
            }

            // Log success for this tool
            await sql`
              INSERT INTO marketing.campaign_audit_log (
                campaign_id,
                action,
                status,
                details,
                mcp_tool
              ) VALUES (
                ${campaign_id},
                'launch',
                'success',
                ${JSON.stringify({
                  tool,
                  execution_ids: launchResult.execution_ids,
                  message: `Successfully launched to ${tool}`
                })},
                ${tool}
              )
            `;
          } else {
            // Log failure for this tool
            await sql`
              INSERT INTO marketing.campaign_audit_log (
                campaign_id,
                action,
                status,
                details,
                mcp_tool
              ) VALUES (
                ${campaign_id},
                'launch',
                'failed',
                ${JSON.stringify({
                  tool,
                  error: launchResult.error,
                  message: `Failed to launch to ${tool}`
                })},
                ${tool}
              )
            `;
          }
        } catch (toolError) {
          console.error(`[Campaign Launch] Error launching to ${tool}:`, toolError);

          // Log error for this tool
          await sql`
            INSERT INTO marketing.campaign_audit_log (
              campaign_id,
              action,
              status,
              details,
              mcp_tool
            ) VALUES (
              ${campaign_id},
              'launch',
              'failed',
              ${JSON.stringify({
                tool,
                error: toolError instanceof Error ? toolError.message : 'Unknown error'
              })},
              ${tool}
            )
          `;
        }
      }

      // Update overall launch status
      const overallStatus = launchResults.length > 0 ? 'success' : 'failed';
      await sql`
        UPDATE marketing.campaign_audit_log
        SET status = ${overallStatus},
            details = details || ${JSON.stringify({
              launched_to: launchResults,
              failed_tools: target_tools.filter(t => !launchResults.includes(t))
            })}
        WHERE campaign_id = ${campaign_id}
        AND action = 'launch'
        AND status = 'pending'
      `;

      // Commit transaction
      await sql('COMMIT');

      // Log success
      console.log(`[Campaign Launch] SUCCESS: Launched campaign ${campaign_id} to ${launchResults.join(', ')}`);

      return res.status(200).json({
        status: overallStatus,
        campaign_id,
        message: `Campaign launched to ${launchResults.length} of ${target_tools.length} tools`,
        launched_to: launchResults,
        execution_ids: executionIds,
        details: {
          campaign_type: campaign.campaign_type,
          target_count: campaign.people_ids.length,
          test_mode
        }
      });

    } catch (error) {
      // Rollback transaction
      await sql('ROLLBACK');
      throw error;
    }

  } catch (error) {
    console.error('[Campaign Launch] ERROR:', error);

    // Log failure
    try {
      await sql`
        INSERT INTO marketing.campaign_audit_log (
          campaign_id,
          action,
          status,
          details
        ) VALUES (
          ${req.body.campaign_id || 'UNKNOWN'},
          'launch',
          'failed',
          ${JSON.stringify({
            error: error instanceof Error ? error.message : 'Unknown error',
            request_body: req.body
          })}
        )
      `;
    } catch (auditError) {
      console.error('[Campaign Launch] Audit log error:', auditError);
    }

    return res.status(500).json({
      status: 'failed',
      message: 'Failed to launch campaign',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

// Validate campaign ID format
function isValidCampaignId(id: string): boolean {
  // Campaign Barton ID format: 04.04.03.XX.XXXXX.XXX
  const campaignIdRegex = /^04\.04\.03\.\d{2}\.\d{5}\.\d{3}$/;
  return campaignIdRegex.test(id);
}

// Get campaign details from database
async function getCampaignDetails(campaignId: string): Promise<any> {
  try {
    const result = await sql`
      SELECT
        campaign_id,
        campaign_type,
        trigger_event,
        template,
        company_unique_id,
        people_ids,
        marketing_score,
        status,
        created_at,
        launched_at
      FROM marketing.campaigns
      WHERE campaign_id = ${campaignId}
    `;

    return result[0] || null;
  } catch (error) {
    console.error('[Get Campaign Details] Error:', error);
    return null;
  }
}

// Launch campaign to specific tool via Composio bridge
async function launchToTool(
  tool: string,
  campaign: any,
  testMode: boolean
): Promise<{ success: boolean; execution_ids?: string[]; error?: string }> {
  try {
    // Get Composio configuration
    const composioConfig = {
      apiKey: process.env.COMPOSIO_API_KEY,
      baseUrl: process.env.COMPOSIO_BASE_URL || 'https://backend.composio.dev/api/v1'
    };

    // Prepare campaign data for tool
    const campaignData = await prepareCampaignData(campaign, tool);

    // Call Composio to launch campaign
    const response = await fetch(`${composioConfig.baseUrl}/execute`, {
      method: 'POST',
      headers: {
        'X-API-KEY': composioConfig.apiKey!,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        app: tool.toUpperCase(),
        action: testMode ? 'create_test_campaign' : 'create_campaign',
        params: campaignData
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Composio API error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();

    // Parse execution IDs from response
    const executionIds = extractExecutionIds(result, tool);

    return {
      success: true,
      execution_ids: executionIds
    };

  } catch (error) {
    console.error(`[Launch to ${tool}] Error:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

// Prepare campaign data for specific tool format
async function prepareCampaignData(campaign: any, tool: string): Promise<any> {
  const blueprint = campaign.template;
  const baseData = {
    campaign_name: `Campaign ${campaign.campaign_id}`,
    campaign_type: campaign.campaign_type,
    recipients: []
  };

  // Get recipient details
  const recipients = await sql`
    SELECT
      pm.unique_id,
      pm.first_name,
      pm.last_name,
      pm.email,
      pm.linkedin_url,
      pm.phone,
      cm.company_name,
      cm.industry
    FROM marketing.people_master pm
    LEFT JOIN marketing.company_master cm ON cm.unique_id = ${campaign.company_unique_id}
    WHERE pm.unique_id = ANY(${campaign.people_ids})
  `;

  // Format recipients for specific tool
  switch (tool.toLowerCase()) {
    case 'instantly':
      return {
        ...baseData,
        campaign_name: `Barton Campaign ${campaign.campaign_id}`,
        email_sequence: blueprint.sequence
          ?.filter((s: any) => s.type === 'email')
          .map((step: any, index: number) => ({
            step: index + 1,
            subject: step.content?.subject || `Email ${index + 1}`,
            body: step.content?.body || '',
            delay_days: parseInt(step.delay) || 0
          })),
        recipients: recipients.map(r => ({
          email: r.email,
          first_name: r.first_name,
          last_name: r.last_name,
          company: r.company_name,
          custom_variables: {
            barton_id: r.unique_id,
            industry: r.industry
          }
        }))
      };

    case 'heyreach':
      return {
        ...baseData,
        campaign_name: `LinkedIn Campaign ${campaign.campaign_id}`,
        linkedin_sequence: blueprint.sequence
          ?.filter((s: any) => s.type === 'linkedin_connect')
          .map((step: any, index: number) => ({
            action: 'connect',
            message: step.message || '',
            delay_days: parseInt(step.delay) || 0
          })),
        recipients: recipients.map(r => ({
          linkedin_url: r.linkedin_url,
          first_name: r.first_name,
          last_name: r.last_name,
          company: r.company_name
        }))
      };

    case 'lemlist':
      return {
        ...baseData,
        campaign_name: `Multi-channel ${campaign.campaign_id}`,
        steps: blueprint.sequence?.map((step: any) => ({
          type: step.type,
          content: step.content || step.message || step.script,
          delay: step.delay
        })),
        leads: recipients.map(r => ({
          email: r.email,
          firstName: r.first_name,
          lastName: r.last_name,
          companyName: r.company_name,
          linkedInUrl: r.linkedin_url,
          phone: r.phone
        }))
      };

    default:
      return {
        ...baseData,
        blueprint,
        recipients: recipients.map(r => ({
          id: r.unique_id,
          email: r.email,
          name: `${r.first_name} ${r.last_name}`,
          company: r.company_name,
          linkedin: r.linkedin_url,
          phone: r.phone
        }))
      };
  }
}

// Extract execution IDs from tool response
function extractExecutionIds(response: any, tool: string): string[] {
  const ids: string[] = [];

  switch (tool.toLowerCase()) {
    case 'instantly':
      if (response.campaign_id) {
        ids.push(response.campaign_id);
      }
      if (response.email_ids) {
        ids.push(...response.email_ids);
      }
      break;

    case 'heyreach':
      if (response.campaign_uuid) {
        ids.push(response.campaign_uuid);
      }
      if (response.connection_requests) {
        ids.push(...response.connection_requests.map((r: any) => r.id));
      }
      break;

    case 'lemlist':
      if (response.campaignId) {
        ids.push(response.campaignId);
      }
      if (response.leadIds) {
        ids.push(...response.leadIds);
      }
      break;

    default:
      if (response.id) {
        ids.push(response.id);
      }
      if (response.execution_id) {
        ids.push(response.execution_id);
      }
      if (Array.isArray(response.ids)) {
        ids.push(...response.ids);
      }
  }

  return ids;
}