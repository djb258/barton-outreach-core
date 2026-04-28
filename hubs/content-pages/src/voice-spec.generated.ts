// Generated from fleet/content/VOICE-SPEC.yaml by scripts/gen-voice-spec.mjs
// Do not edit by hand.

export const VOICE_SPEC = {
  "spec_name": "Insurance Informatics Voice Spec",
  "spec_version": "1.2.0",
  "authority": "Dave Barton",
  "source_docs": [
    "law/VOICE-LIBRARY.md",
    "fleet/content/logos/BRAND-STORY.md",
    "fleet/content/INSURANCE-INFORMATICS-CTB.md"
  ],
  "purpose": "Machine-consumable voice and positioning spec for email, LinkedIn, and website writers.",
  "brand": {
    "name": "Insurance Informatics",
    "destination_domain": "insuranceinformatics.com",
    "synthesis_statement": "Insurance Informatics is the merger of insurance discipline and IT discipline under one named field.",
    "positioning_anchors": {
      "merger_story": "25 years of insurance / broker discipline + 25 years of IT / systems discipline, consolidated into one named discipline.",
      "dot_com_market_proof": "The exact-match .com was available because nobody else was operating this as a named discipline at depth.",
      "informatics_naming_pattern": "Insurance is the missing sibling in the established -informatics naming pattern.",
      "career_discipline": "This is a whole career, not a campaign.",
      "three_layer_defense": "The pattern, the gap, and the operational machine all reinforce the claim."
    }
  },
  "voice_constants": {
    "persona": "George Patton in a benefits office",
    "posture": "direct, confident, challenging, blunt about reality, zero desperation",
    "sentence_rules": [
      "Short declarative sentences.",
      "One idea per sentence.",
      "Use \"you\" and \"your\" when addressing the reader.",
      "Use concrete numbers when they are available.",
      "No hedging language."
    ],
    "required_phrases": [
      "Insurance Informatics"
    ],
    "forbidden_phrases": [
      "I think",
      "maybe we could",
      "if you're interested",
      "let me know if you have questions",
      "we'd love the opportunity",
      "reach out",
      "touch base",
      "circle back",
      "best-in-class",
      "world-class",
      "cutting-edge",
      "honestly",
      "to be transparent",
      "I hope this finds you well"
    ],
    "banned_markers": [
      "emoji",
      "exclamation_marks",
      "corporate_speak",
      "desperation_language",
      "vague_claims"
    ]
  },
  "channel_rules": {
    "email": {
      "target_use": "cold outreach, movement outreach, renewal touch, short form follow-up",
      "required_elements": [
        "one factual anchor",
        "one insight",
        "one ask",
        "booking_link_or_direct_next_step",
        "signature_with_brand"
      ],
      "opening_shape": [
        "lead_with_fact",
        "category_first",
        "no pleasantry_warmup"
      ],
      "closing_shape": [
        "explicit_next_step",
        "one_link_only"
      ]
    },
    "linkedin": {
      "target_use": "public education, authority building, short commentary",
      "required_elements": [
        "one concept per post",
        "short declarative lines",
        "CTA or follow prompt",
        "brand anchor"
      ],
      "opening_shape": [
        "hook_with_fact_or_frame",
        "no corporate_intro"
      ],
      "closing_shape": [
        "booking_link_or_follow",
        "no soft_close"
      ]
    },
    "website": {
      "target_use": "homepage, landing page, explanation pages, CF Pages copy",
      "required_elements": [
        "category_first_positioning",
        "direct explanation",
        "one clear CTA",
        "brand destination"
      ],
      "opening_shape": [
        "direct_statement",
        "no padding"
      ],
      "closing_shape": [
        "one_action",
        "no multi-option clutter"
      ]
    }
  },
  "consumer_contract": {
    "load_order": [
      "fleet/content/VOICE-SPEC.yaml",
      "law/VOICE-LIBRARY.md"
    ],
    "merge_rule": "The YAML spec is the machine layer. The voice library is the human-readable source. Consumers should load the YAML first and fall back to the voice library only if the YAML is missing.",
    "fail_closed_on": [
      "forbidden_phrase_match",
      "missing_required_phrase_when_applicable",
      "unsupported_brand_anchor",
      "channel_rule_violation"
    ],
    "downstream_targets": [
      "workers/lcs-hub/src/compiler-v2.ts",
      "fleet/content/PLATFORM-LINKEDIN.md",
      "docs/processes/CLIENT-CF-PAGE-RUNBOOK.md",
      "docs/processes/PROCESS-OUTREACH-MESSAGES.md"
    ],
    "example_flow": {
      "email": "Load spec -> validate subject and body -> inject tone markers -> reject draft on any forbidden phrase.",
      "linkedin": "Load spec -> validate draft against channel_rules.linkedin -> publish only after voice audit.",
      "website": "Load spec -> shape hero, explainer, and CTA copy -> keep the direct category-first frame."
    }
  },
  "validation": {
    "parse_requirements": [
      "yaml_must_parse",
      "brand_anchors_must_exist",
      "forbidden_phrases_must_be_listed",
      "required_phrases_must_be_listed",
      "channel_rules_must_exist_for_email_linkedin_website"
    ],
    "source_alignment": [
      "law/VOICE-LIBRARY.md",
      "fleet/content/logos/BRAND-STORY.md",
      "fleet/content/INSURANCE-INFORMATICS-CTB.md"
    ],
    "notes": [
      "This file is the extracted machine-readable layer for downstream writers.",
      "No channel should improvise tone when this file is available."
    ]
  },
  "compliance": {
    "ascii_normalization": {
      "enabled": true,
      "enforcement": "warn_and_normalize",
      "map": {
        "em_dash": "--",
        "en_dash": "-",
        "middle_dot": "|",
        "curly_single": "'",
        "curly_double": "\"",
        "ellipsis": "...",
        "copyright": "(c)",
        "registered": "(r)",
        "trademark": "(tm)"
      }
    }
  }
} as const;

export const BRAND = VOICE_SPEC.brand;
export const VOICE_CONSTANTS = VOICE_SPEC.voice_constants;
export const CHANNEL_RULES = VOICE_SPEC.channel_rules;
export const CONSUMER_CONTRACT = VOICE_SPEC.consumer_contract;
export const VALIDATION = VOICE_SPEC.validation;

export type VoiceSpec = typeof VOICE_SPEC;
export type BrandSpec = typeof BRAND;
export type VoiceConstants = typeof VOICE_CONSTANTS;
export type ChannelRules = typeof CHANNEL_RULES;
export type ConsumerContract = typeof CONSUMER_CONTRACT;
export type ValidationSpec = typeof VALIDATION;
