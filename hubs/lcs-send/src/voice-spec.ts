// =============================================================================
// LCS Hub Voice Spec Bridge
// =============================================================================
//
// The worker runtime consumes the checked-in generated bridge. The generator
// keeps the module synchronized with fleet/content/VOICE-SPEC.yaml without
// re-parsing YAML at runtime.
// =============================================================================

import {
  CHANNEL_RULES,
  CONSUMER_CONTRACT,
  BRAND,
  VOICE_CONSTANTS,
  VOICE_SPEC,
  type BrandSpec,
  type ChannelRules,
  type ConsumerContract,
  type VoiceConstants,
  type VoiceSpec,
} from './voice-spec.generated';

export const EMAIL_VOICE_SPEC = VOICE_SPEC;
export { BRAND, CHANNEL_RULES, CONSUMER_CONTRACT, VOICE_CONSTANTS };
export type { BrandSpec, ChannelRules, ConsumerContract, VoiceConstants, VoiceSpec };

// ── ASCII Normalizer (voice-spec v1.2.0) ───────────────────────────────────
// Single chokepoint that converts drift characters (em-dash, curly quotes,
// ellipsis, middle dot, NBSP, zero-widths, © ® ™) to ASCII equivalents.
// Pure function. No side effects. Applied at the send boundary in compiler-v2
// deliverMailgun + spokes/delivery deliverMailgun BEFORE the Mailgun form POST.
//
// Ordering matters: multi-char replacements first (em-dash → `--`), then
// single-char (en-dash → `-`), then the rest. Zero-widths stripped last.

const ASCII_NORMALIZE_MAP: Array<[RegExp, string]> = [
  [/\u2014/g, '--'],   // — em-dash
  [/\u2013/g, '-'],    // – en-dash
  [/\u00B7/g, '|'],    // · middle dot
  [/[\u2018\u2019]/g, "'"], // ' ' curly singles
  [/[\u201C\u201D]/g, '"'], // " " curly doubles
  [/\u2026/g, '...'],  // … ellipsis
  [/\u00A9/g, '(c)'],  // © copyright
  [/\u00AE/g, '(r)'],  // ® registered
  [/\u2122/g, '(tm)'], // ™ trademark
  [/\u00A0/g, ' '],    // NBSP → regular space
  [/[\u200B\u200C\u200D\uFEFF]/g, ''], // zero-width chars stripped
];

export function asciiNormalize(input: string): string {
  if (!input) return input;
  let out = input;
  for (const [pattern, replacement] of ASCII_NORMALIZE_MAP) {
    out = out.replace(pattern, replacement);
  }
  return out;
}

export function containsNonAscii(input: string): boolean {
  if (!input) return false;
  for (let i = 0; i < input.length; i++) {
    if (input.charCodeAt(i) > 0x7F) return true;
  }
  return false;
}

function firstNonAsciiSample(input: string, limit = 5): string {
  const seen: string[] = [];
  for (let i = 0; i < input.length && seen.length < limit; i++) {
    const code = input.charCodeAt(i);
    if (code > 0x7F) {
      const ch = input[i];
      const hex = `U+${code.toString(16).toUpperCase().padStart(4, '0')}`;
      if (!seen.some((s) => s.startsWith(`${ch}`))) {
        seen.push(`${ch}(${hex})`);
      }
    }
  }
  return seen.join(',');
}

const REQUIRED_FRAME_PHRASES: Record<string, readonly string[]> = {
  'OUT-HAMMER-01': ["Here's how it works.", 'Insurance Informatics'],
  'OUT-HAMMER-01-LITE': ["Here's how it works.", 'Insurance Informatics'],
  'OUT-HAMMER-02': ['The math is simple.', "Premiums don't equal cost."],
  'OUT-HAMMER-03': ["You can't stop claims.", 'Insurance Informatics'],
  'OUT-HAMMER-04': ["Premiums don't equal cost.", 'Insurance Informatics'],
};

function normalizeText(value: string): string {
  return value.replace(/\s+/g, ' ').trim().toLowerCase();
}

function countLinks(content: string): number {
  return (content.match(/https?:\/\/\S+/g) ?? []).length;
}

function hasFactualAnchor(content: string): boolean {
  return /I do insurance informatics|I take zero commission|25 years|90%|100,000|15K\/month/i.test(content);
}

function hasInsight(content: string): boolean {
  return /The math is simple\.|Premiums don't equal cost\.|You can't stop claims\./i.test(content);
}

function hasAsk(content: string): boolean {
  return /15 minutes|want to see it|worth a conversation|compete it/i.test(content);
}

function opensWithoutPleasantry(content: string): boolean {
  const lines = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2) return false;
  const firstTwo = `${lines[0]} ${lines[1]}`.toLowerCase();
  return !/^(hi|hello|hey|hope)\b/.test(lines[0].toLowerCase()) &&
    firstTwo.includes('dave barton. i do insurance informatics');
}

function hasBrandSignature(content: string): boolean {
  return normalizeText(content).includes(EMAIL_VOICE_SPEC.brand.name.toLowerCase());
}

function hasSupportedBrandAnchor(content: string): boolean {
  const lower = normalizeText(content);
  if (lower.includes(EMAIL_VOICE_SPEC.brand.name.toLowerCase())) return true;
  if (lower.includes(EMAIL_VOICE_SPEC.brand.synthesis_statement.toLowerCase())) return true;
  return Object.values(EMAIL_VOICE_SPEC.brand.positioning_anchors ?? {}).some((anchor) =>
    lower.includes(anchor.toLowerCase())
  );
}

function hasBannedMarkers(body: string): string[] {
  const issues: string[] = [];
  if (/[!]/.test(body)) issues.push('exclamation_marks');
  if (/[\u{1F300}-\u{1FAFF}]/u.test(body)) issues.push('emoji');
  return issues;
}

export function validateOutboundEmailCopy(subject: string, body: string, frameId: string): string[] {
  const issues: string[] = [];
  const content = `${subject}\n${body}`;
  const lower = normalizeText(content);

  for (const phrase of EMAIL_VOICE_SPEC.voice_constants.forbidden_phrases) {
    if (lower.includes(phrase.toLowerCase())) {
      issues.push(`forbidden_phrase:${phrase}`);
    }
  }

  for (const marker of hasBannedMarkers(content)) {
    issues.push(`banned_marker:${marker}`);
  }

  for (const phrase of EMAIL_VOICE_SPEC.voice_constants.required_phrases) {
    if (!content.includes(phrase)) {
      issues.push(`missing_required_phrase:${phrase}`);
    }
  }

  const frameRequired = REQUIRED_FRAME_PHRASES[frameId] ?? [];
  for (const phrase of frameRequired) {
    if (!content.includes(phrase)) {
      issues.push(`missing_required_phrase:${phrase}`);
    }
  }

  const channelIssues: string[] = [];
  if (!hasFactualAnchor(content)) channelIssues.push('one_factual_anchor');
  if (!hasInsight(content)) channelIssues.push('one_insight');
  if (!hasAsk(content)) channelIssues.push('one_ask');
  if (!content.includes('https://calendar.app.google/')) channelIssues.push('booking_link_or_direct_next_step');
  if (!hasBrandSignature(content)) channelIssues.push('signature_with_brand');
  if (!opensWithoutPleasantry(content)) channelIssues.push('lead_with_fact');
  if (countLinks(content) > 1) channelIssues.push('one_link_only');
  if (!hasSupportedBrandAnchor(content)) channelIssues.push('unsupported_brand_anchor');

  if (channelIssues.length > 0) {
    issues.push(`channel_rule_violation:${channelIssues.join('|')}`);
  }

  // ── voice-spec v1.2.0: non-ASCII warning (NON-BLOCKING) ───────────────────
  // The compiler-v2 deliverMailgun boundary runs asciiNormalize() on the
  // final body right before Mailgun POST. That's the safety net. This
  // warning is advisory so authors see drift in drafts — not a hard fail.
  if (containsNonAscii(body)) {
    issues.push(`non_ascii_content:${firstNonAsciiSample(body)}`);
  }

  return issues;
}

export function buildSignatureFooter(baseLines: string[]): string {
  const lines = [...baseLines];
  if (!lines.includes(EMAIL_VOICE_SPEC.brand.name)) {
    lines.push(EMAIL_VOICE_SPEC.brand.name);
  }
  return lines.join('\n');
}
