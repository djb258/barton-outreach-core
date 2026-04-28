import type { WebsitePage } from '../types';

export const aboutPage: WebsitePage = {
  slug: '/about',
  ctbAltitude: '50K',
  seo: {
    title: 'Dave Barton | Founder of Insurance Informatics',
    description: 'Dave Barton created Insurance Informatics — the merger of 25 years in IT data architecture with 25 years in insurance operations. Not a broker. An operational layer.',
    canonical: 'https://insuranceinformatics.com/about',
  },
  hero: {
    headline: 'About Dave Barton',
    subhead: '25 years IT. 25 years insurance. One discipline that didn\'t exist before.',
    ctaLabel: 'Book 15 Minutes',
  },
  sections: [
    {
      heading: 'The Genesis of Insurance Informatics',
      body: '<p>Medical informatics exists. Clinical informatics exists. Insurance informatics didn\'t — until Dave built it.</p><p>The IT career taught the data architecture: how to build systems that aggregate, normalize, and warehouse information from dozens of disconnected sources into one queryable view. The insurance career taught what questions to ask and where the money actually leaks.</p><p>Put them together and you get a discipline where the data infrastructure IS the product — not a bolt-on, not an afterthought.</p>',
    },
    {
      heading: 'Not a Broker',
      body: '<p>Dave sits BESIDE the client — at the same table, facing the same direction. Not below them in a vendor stack. Not through a carrier relationship. Direct.</p><p>There\'s no Broker of Record letter. No carrier commission. No hidden revenue from vendor overrides. The fee is flat, transparent, and Per Employee Per Month.</p>',
      callout: 'The traditional broker is paid by the carrier to keep costs where they are. We\'re paid by the employer to push costs down. Different incentive. Different outcome.',
    },
    {
      heading: 'Bloomberg for Healthcare',
      body: '<p>Think of what Bloomberg did for financial data — aggregating thousands of data sources into one terminal that traders can\'t live without. Insurance Informatics does the same for employer healthcare data.</p><p>Every vendor feed, every claims file, every enrollment record, every bill — aggregated into one data warehouse that the CFO, HR, underwriting, and service teams all read from. Different views, same source of truth.</p>',
    },
    {
      heading: 'The MDM Bridge',
      body: '<p>For CIOs: Insurance Informatics is Master Data Management applied to healthcare benefits. One golden record per employee. One hub connecting every vendor. One data warehouse with one version of the truth.</p><p>If you\'re a CIO who\'s spent years trying to unify your core business data, imagine a vendor who shows up with the same philosophy for your benefits stack — already built, already running.</p>',
    },
  ],
};
