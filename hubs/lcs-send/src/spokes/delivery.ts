// ═══════════════════════════════════════════════════════════════
// Spoke OUT: Delivery Adapters
// ═══════════════════════════════════════════════════════════════
// Accepts standard MessagePackage. Routes to Mailgun or HeyReach
// via Composio. Dumb delivery. Doesn't know about campaigns.
//
// All integrations through Composio per doctrine.
// Vendors are swappable. Architecture doesn't depend on them.
// ═══════════════════════════════════════════════════════════════

import type { Env, MessagePackage } from '../types';
import { logEvent, logError } from '../utils';
import { asciiNormalize } from '../voice-spec';

export interface DeliveryResult {
  success: boolean;
  provider_id: string | null;
  error: string | null;
}

/** Check suppression before any send */
async function checkSuppression(env: Env, email: string | null): Promise<boolean> {
  if (!email) return false;
  const suppressed = await env.D1.prepare(
    'SELECT email FROM lcs_suppression WHERE email = ?'
  ).bind(email).first();
  return !!suppressed;
}

/** Deliver via Mailgun (email) */
async function deliverMailgun(
  env: Env,
  pkg: MessagePackage,
): Promise<DeliveryResult> {
  if (!pkg.recipient_email) {
    return { success: false, provider_id: null, error: 'No recipient email' };
  }
  if (await checkSuppression(env, pkg.recipient_email)) {
    return { success: false, provider_id: null, error: `Suppressed: ${pkg.recipient_email}` };
  }

  try {
    // ASCII normalization (voice-spec v1.2.0) — single chokepoint at send
    // boundary. See workers/lcs-hub/src/voice-spec.ts asciiNormalize().
    const subjectAscii = asciiNormalize(pkg.subject ?? '');
    const bodyPlainAscii = asciiNormalize(pkg.body_plain ?? '');
    const bodyHtmlAscii = asciiNormalize(pkg.body_html ?? '');

    const form = new FormData();
    form.append('from', `Dave Barton <dave@${env.MAILGUN_DOMAIN}>`);
    form.append('h:Reply-To', 'Dave Barton <marketing@svg.agency>');
    form.append('to', pkg.recipient_email);
    form.append('subject', subjectAscii);
    form.append('text', bodyPlainAscii);
    form.append('html', bodyHtmlAscii);
    // Tag for tracking
    form.append('o:tag', pkg.path_type);
    form.append('o:tag', `seq-${pkg.sequence_num}`);
    form.append('o:tag', pkg.sid_id);
    // Custom variables for webhook tracing
    form.append('v:mid_id', pkg.mid_id);
    form.append('v:sid_id', pkg.sid_id);
    form.append('v:cid_id', pkg.cid_id);
    form.append('v:sovereign_company_id', pkg.sovereign_company_id);

    const resp = await fetch(
      `https://api.mailgun.net/v3/${env.MAILGUN_DOMAIN}/messages`,
      {
        method: 'POST',
        headers: {
          Authorization: `Basic ${btoa(`api:${env.MAILGUN_API_KEY}`)}`,
        },
        body: form,
      },
    );

    if (!resp.ok) {
      const body = await resp.text();
      return { success: false, provider_id: null, error: `Mailgun ${resp.status}: ${body}` };
    }

    const data = await resp.json<{ id?: string }>();
    return { success: true, provider_id: data.id ?? null, error: null };
  } catch (err) {
    return {
      success: false,
      provider_id: null,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

/** Deliver via HeyReach (LinkedIn) */
async function deliverHeyReach(
  env: Env,
  pkg: MessagePackage,
): Promise<DeliveryResult> {
  if (!pkg.recipient_linkedin) {
    return { success: false, provider_id: null, error: 'No recipient LinkedIn URL' };
  }
  if (await checkSuppression(env, pkg.recipient_email)) {
    return { success: false, provider_id: null, error: `Suppressed: ${pkg.recipient_email}` };
  }

  try {
    // HeyReach API — add lead to campaign with personalized message
    const resp = await fetch('https://api.heyreach.io/api/public/v2/leads/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': env.HEYREACH_API_KEY,
      },
      body: JSON.stringify({
        linkedin_url: pkg.recipient_linkedin,
        custom_variables: {
          mid_id: pkg.mid_id,
          sid_id: pkg.sid_id,
          cid_id: pkg.cid_id,
          message: pkg.body_plain,
        },
      }),
    });

    if (!resp.ok) {
      const body = await resp.text();
      return { success: false, provider_id: null, error: `HeyReach ${resp.status}: ${body}` };
    }

    const data = await resp.json<{ id?: string }>();
    return { success: true, provider_id: data.id ?? null, error: null };
  } catch (err) {
    return {
      success: false,
      provider_id: null,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

/** Route delivery to the right adapter based on channel */
export async function deliver(
  env: Env,
  pkg: MessagePackage,
): Promise<DeliveryResult> {
  const result = pkg.channel === 'MG'
    ? await deliverMailgun(env, pkg)
    : await deliverHeyReach(env, pkg);

  // Log the delivery event
  await logEvent(env.D1, {
    sovereign_company_id: pkg.sovereign_company_id,
    cid_id: pkg.cid_id,
    sid_id: pkg.sid_id,
    mid_id: pkg.mid_id,
    event_type: result.success ? 'mid_sent' : 'mid_bounced',
    event_data: {
      channel: pkg.channel,
      path_type: pkg.path_type,
      provider_id: result.provider_id,
      error: result.error,
    },
  });

  if (!result.success) {
    await logError(env.D1, {
      sovereign_company_id: pkg.sovereign_company_id,
      cid_id: pkg.cid_id,
      sid_id: pkg.sid_id,
      mid_id: pkg.mid_id,
      stage: 'mid',
      error_type: 'delivery_failure',
      error_message: result.error ?? 'Unknown delivery error',
      error_detail: { channel: pkg.channel, provider_id: result.provider_id },
    });
  }

  return result;
}
