import type { WebsitePage } from '../types';
import { duckDiagram, twoAggregatorsDiagram, hospitalWaterfallDiagram } from '../diagrams';

export const executivesPage: WebsitePage = {
  slug: '/executives',
  ctbAltitude: '40K',
  seo: {
    title: 'Insurance Informatics for CEOs and CFOs | Two Bills, One Dashboard, Zero Commission',
    description: 'For CEOs and CFOs: Insurance Informatics delivers two consolidated bills, one real-time dashboard, zero commission, and a hospital bill audit that cuts 30% before the waterfall even starts.',
    canonical: 'https://insuranceinformatics.com/executives',
  },
  hero: {
    headline: 'For CEOs & CFOs',
    subhead: 'Two bills. One dashboard. Zero commission. The duck is smooth on top — we handle the paddling.',
    ctaLabel: 'Book 15 Minutes',
  },
  sections: [
    {
      heading: 'The Duck',
      body: '<p>From the CFO\'s seat, it looks simple: two bills, one dashboard, employees are happy. That\'s by design. Underneath, there\'s a machine running 10+ vendors, two claim pipes, two waterfalls, enrollment feeds, HR-branded comms, drug flags, pre-certs, bill audits, and a real-time data warehouse.</p>',
      diagram: duckDiagram,
    },
    {
      heading: 'Two Bills. Zero Vendor Chasing.',
      body: '<p>Every month, the CFO sees exactly two numbers. One consolidated fixed-cost invoice from Dave. One consolidated claims bill from the TPA. No chasing 8 vendors for 8 invoices. No reconciling portals. One view.</p>',
      diagram: twoAggregatorsDiagram,
    },
    {
      heading: 'Hospital Bills Get Audited First',
      body: '<p>Before a hospital bill hits the waterfall, it gets audited line by line against Medicare rates. Wrong codes, duplicate charges, inflated items, services not rendered — caught and cut before the repricing even starts.</p>',
      diagram: hospitalWaterfallDiagram,
    },
    {
      heading: 'The Monte Carlo Reality',
      body: '<p>Two employers start with the same claims. One stays with traditional brokerage — compounding off a higher base every year. The other switches to Insurance Informatics — compounding off a lower base. After five years, the gap is massive.</p>',
      callout: 'I\'m not predicting claims. I\'m showing you the mechanics. You\'re compounding off a higher base. We compound off a lower base.',
    },
    {
      heading: 'Zero Commission — Same Side of the Table',
      body: '<p>Flat PEPM fee. No commission. No BOR letter required. No hidden revenue from carrier overrides. When the bill goes down, our fee doesn\'t change — we\'re not incentivized to keep costs high.</p>',
      bullets: [
        'Traditional broker: paid by the carrier. Incentive misaligned.',
        'Insurance Informatics: paid by the employer. Flat fee. Same side.',
        '$27M in data failures happen when incentives don\'t align with outcomes.',
      ],
    },
  ],
};
