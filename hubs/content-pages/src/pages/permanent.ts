import type { WebsitePage } from '../types';
import { dataMoatDiagram } from '../diagrams';

export const permanentPage: WebsitePage = {
  slug: '/permanent',
  ctbAltitude: '5K',
  seo: {
    title: 'Why Insurance Informatics Is Permanent | The Data Moat',
    description: 'Insurance Informatics creates structural dependency — not contracts. Every month of data, every vendor connection, every compliance trail makes the system deeper and harder to replicate.',
    canonical: 'https://insuranceinformatics.com/permanent',
  },
  hero: {
    headline: 'Why It\'s Permanent',
    subhead: 'We don\'t retain clients with contracts. We retain them through structural dependency.',
    ctaLabel: 'Book 15 Minutes',
  },
  sections: [
    {
      heading: 'The IT Moat',
      body: '<p>Every month of operation adds another layer to the data warehouse. Enrollment data, claims history, savings tracking, vendor connections, compliance trails, trend analysis, renewal leverage, benchmarks. It compounds.</p>',
      diagram: dataMoatDiagram,
    },
    {
      heading: 'What Leaving Would Mean',
      body: '<p>To fire Insurance Informatics, a client would have to rebuild:</p>',
      bullets: [
        'Every vendor API connection',
        'Every compliance tracker',
        'Every data feed',
        'Every dashboard',
        'Every enrollment integration',
        'Every historical trend and benchmark',
        'The entire data warehouse from scratch',
      ],
      callout: 'They\'d be starting from zero. We\'d be handing them years of accumulated infrastructure.',
    },
    {
      heading: 'The Structural Dependency Sandwich',
      body: '<p>The data warehouse sits between the vendors and the client. Every vendor feeds into it. Every dashboard reads from it. Every decision references it. Remove it and the entire operational layer collapses back to disconnected vendor portals and spreadsheets.</p><p>This isn\'t lock-in through contracts or penalties. It\'s lock-in through value. The system is more useful every month, not less.</p>',
    },
    {
      heading: 'No Lock-In at Any Point',
      body: '<p>There\'s no BOR letter. No multi-year contract. No exit penalty. The client can leave at any time — and that\'s precisely why they don\'t. The system earns its position every month.</p>',
      callout: 'I encourage you to compete it. Take it to every broker you have. See if anyone else can build this.',
    },
  ],
};
