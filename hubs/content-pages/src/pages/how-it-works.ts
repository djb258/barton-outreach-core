import type { WebsitePage } from '../types';
import { ruleOfTwosDiagram, hubSpokeDiagram, twoAggregatorsDiagram } from '../diagrams';

export const howItWorksPage: WebsitePage = {
  slug: '/how-it-works',
  ctbAltitude: '40K–30K',
  seo: {
    title: 'How Insurance Informatics Works | Two Sides, Two Bills, One Hub',
    description: 'Insurance Informatics splits insurance into fixed costs and variable costs, manages 10+ vendors through one hub, and runs two separate systems for the 90% routine and 10% high-dollar employees.',
    canonical: 'https://insuranceinformatics.com/how-it-works',
  },
  hero: {
    headline: 'How It Works',
    subhead: 'Two sides. Two bills. One hub. The architecture is simple — the execution is where everyone else fails.',
    ctaLabel: 'Book 15 Minutes',
  },
  sections: [
    {
      heading: 'The Two Sides of Insurance',
      body: '<p>Every self-insured employer has two cost categories:</p><p><strong>Fixed costs</strong> — stop loss, life insurance, dental, vision, EAP, FSA, COBRA. Could be 8-12 separate vendors, each with their own bill and portal. Dave normalizes all of it into one consolidated invoice.</p><p><strong>Variable costs</strong> — medical claims (TPA) and pharmacy claims (PBM). Two pipes, two completely different money flows.</p>',
      diagram: twoAggregatorsDiagram,
    },
    {
      heading: 'The Hub-and-Spoke Architecture',
      body: '<p>Dave sits at the center. Every vendor connects through the hub — not to each other, not to the client directly. One integration point. One data warehouse. One view.</p><p>The TPA doesn\'t touch the fixed side. They don\'t even know those vendors exist. Dave sees both. That\'s the moat.</p>',
      diagram: hubSpokeDiagram,
    },
    {
      heading: 'The Rule of Twos',
      body: '<p>The employee population splits into two groups that require completely different systems:</p>',
      diagram: ruleOfTwosDiagram,
    },
    {
      heading: 'How Money Actually Flows',
      body: '<p>TPA and PBM handle money in opposite directions:</p>',
      bullets: [
        'TPA (hospitals/doctors): Event happens → bill comes in AFTER → reprice → employer pays. Reactive.',
        'PBM (pharmacy): Employee swipes card → PBM pays pharmacy FIRST → bills TPA → employer reimburses. PBM fronts the money.',
        'Stop loss: Caps the employer\'s total exposure. Specific (per person) and aggregate (total).',
      ],
      callout: 'Understanding the money flow is half the battle. Most CFOs have never seen this explained clearly.',
    },
    {
      heading: 'Enrollment Is the Front Door',
      body: '<p>Enrollment isn\'t paperwork — it\'s the first step of claims management. Dave\'s enrollment process captures standard info AND extra questions that high-dollar vendors will need later. By the time a $200K cancer claim hits, the orchestrator already has the intake data.</p>',
      bullets: [
        'Standard enrollment info pushed to ALL vendors via hub-and-spoke',
        'Extra questions embedded for future high-dollar vendor needs',
        'Golden Record — one flawless record per employee in Dave\'s database',
        'Pre-loads the 10/85 side before a claim ever happens',
      ],
    },
  ],
};
