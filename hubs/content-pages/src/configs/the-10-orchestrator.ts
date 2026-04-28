import type { ContentConfig } from '../types';

// The 10% with the Orchestrator — Vendor Operational Explainer
// Route: /the-10-percent-with-orchestrator
//
// Audience: pre-cert vendors, specialty drug flag vendors, and Layer 2
// execution shops (PPO, RBP, 501(r), PAP/MAP, international sourcing, 340B)
// who have already agreed to work with SVG. This is an operational explainer,
// not a sales pitch. See:
//   fleet/content/vendor-video-the-10-operational-briefing.md v0.3.0
//   fleet/content/videos/rendered/the-10-percent-with-orchestrator.md
export const contentThe10Orchestrator: ContentConfig = {
  brand: 'svg',
  title: 'The 10% with the Orchestrator',
  subtitle: 'Vendor Operational Explainer',
  description:
    'How a case flows through the SVG orchestrator from trigger to billing. For the vendors inside the 10% — pre-cert shops, specialty drug flag vendors, and the execution shops running PPO, RBP, 501(r), PAP/MAP, international sourcing, and 340B. This is not a sales pitch. It is the operational mechanics: what happens, in order, on your side of the handoff.',

  video: {
    streamId: 'f287ac78c267deecf55c653841800456',
    title: 'The 10% with the Orchestrator — Vendor Operational Explainer',
  },
};
