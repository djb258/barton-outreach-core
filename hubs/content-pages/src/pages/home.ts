import type { WebsitePage } from '../types';
import { hubSpokeDiagram, paradigmShiftDiagram } from '../diagrams';

export const homePage: WebsitePage = {
  slug: '/',
  ctbAltitude: '50K',
  seo: {
    title: 'Insurance Informatics — The Named Discipline | insuranceinformatics.com',
    description: 'Insurance Informatics merges 25 years of IT data architecture with 25 years of insurance operations into one closed-loop system. One hub. Two bills. Zero commission.',
    canonical: 'https://insuranceinformatics.com/',
  },
  hero: {
    headline: 'Insurance Informatics',
    subhead: 'We don\'t sell an insurance product. We install a mechanical, closed-loop operational machine. Perfect inputs guarantee predictable outputs.',
    ctaLabel: 'Book 15 Minutes',
  },
  sections: [
    {
      heading: 'A Named Discipline — Not a Brand',
      body: '<p>Insurance Informatics sits parallel to medical informatics and clinical informatics. It\'s the merger of IT data architecture and insurance operations into a single, measurable system.</p><p>While you\'re trying to fix your core business software, your healthcare vendors are running wild in completely disconnected silos. We fix that.</p>',
    },
    {
      heading: 'One Hub. Every Vendor. Two Bills.',
      diagram: hubSpokeDiagram,
      body: '<p>Dave sits at the center — aggregating 10+ vendors into one consolidated view. The CFO sees exactly two numbers: one fixed bill, one claims bill. Zero vendor chasing. Zero hidden invoices.</p>',
    },
    {
      heading: 'The Paradigm Shift',
      diagram: paradigmShiftDiagram,
      callout: 'Your data. Our infrastructure. One permanent operational layer.',
    },
    {
      heading: 'The Math Does the Talking',
      bullets: [
        '84% of CIOs identify unifying data as their top priority.',
        'Zero commission — flat PEPM fee. Same side of the table.',
        'Every month of data makes the system deeper and harder to replicate.',
        'We don\'t retain clients with contracts. We retain them through structural dependency.',
      ],
      callout: '15 minutes. Four videos. The math does the talking.',
    },
  ],
};
