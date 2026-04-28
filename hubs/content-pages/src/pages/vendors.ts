import type { WebsitePage } from '../types';
import { hubSpokeDiagram } from '../diagrams';

export const vendorsPage: WebsitePage = {
  slug: '/vendors',
  ctbAltitude: '40K–20K',
  seo: {
    title: 'Insurance Informatics for Vendors | Integrate Once, Get All Clients',
    description: 'For insurance vendors: Insurance Informatics offers many-to-one integration. Connect to the hub once and access all clients. Two contacts per vendor. We don\'t replace your process — we put structure in front.',
    canonical: 'https://insuranceinformatics.com/vendors',
  },
  hero: {
    headline: 'For Vendors',
    subhead: 'Integrate once. Get all clients. We\'re not replacing your process — we\'re putting structure in front.',
    ctaLabel: 'Talk to Dave',
  },
  sections: [
    {
      heading: 'Many-to-One Integration',
      body: '<p>Traditional model: every vendor connects to every client separately. N vendors times M clients = N×M integration points.</p><p>Insurance Informatics model: every vendor connects to the hub once. The hub connects to every client. N + M integration points. Dramatically simpler.</p>',
      diagram: hubSpokeDiagram,
    },
    {
      heading: 'Two Contacts Per Vendor',
      body: '<p>Every vendor gets exactly two contacts from Dave\'s operation:</p>',
      bullets: [
        'Account Manager — strategic. Assigned to Dave\'s book. Escalations, contract issues, relationship.',
        'Customer Service — tactical. Handles routine tickets. Claim status, employee questions.',
        'The orchestrator rides the account manager in babysitter mode during high-dollar claims.',
        'The ticketing system routes routine questions to customer service.',
      ],
    },
    {
      heading: 'Where You Fit in the Process',
      body: '<p>The 10/85 process — where 10% of employees cause 85% of claims cost — is where specialized vendors shine. Dave\'s orchestrator packages intake information and routes it to the right vendor in the waterfall.</p>',
      bullets: [
        'Hospital claims: PPO network → Reference-Based Pricing → 501R financial assistance',
        'Drug claims: MAP/PAP manufacturer programs → International pharmacy → 340B federal discount',
        'You get clean intake data. You execute your process. You send results back.',
        'Dave dashboards the outcome for the client.',
      ],
    },
    {
      heading: 'Volume Without Sales Cost',
      body: '<p>Every client Dave brings on is another client that routes through your integration. One setup, compounding volume. No per-client sales cycle for the vendor — just execution.</p>',
      callout: 'We don\'t replace your process. We put structure in front of it and volume behind it.',
    },
  ],
};
