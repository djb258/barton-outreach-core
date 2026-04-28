import type { WebsitePage } from '../types';
import { ruleOfTwosDiagram } from '../diagrams';

export const hrPage: WebsitePage = {
  slug: '/hr',
  ctbAltitude: '10K',
  seo: {
    title: 'Insurance Informatics for HR | From Router to Auditor',
    description: 'For HR teams: Insurance Informatics eliminates the benefits bottleneck. 90% of employee questions route directly to vendors. HR goes from router to auditor.',
    canonical: 'https://insuranceinformatics.com/hr',
  },
  hero: {
    headline: 'For HR Teams',
    subhead: 'You stop being the router. You become the auditor. The system handles the routing — you verify it\'s working.',
    ctaLabel: 'Book 15 Minutes',
  },
  sections: [
    {
      heading: 'The 90% — Self-Serve',
      body: '<p>90% of employees have routine needs. Dental question? Vision claim? Life insurance update? Today, every one of those goes through HR. With Insurance Informatics, they go directly to the vendor through a ticketing system.</p>',
      bullets: [
        'Employee submits a ticket — routes directly to the vendor handling that benefit',
        'Dental question → dental vendor. Vision question → vision vendor.',
        'NOT to Dave\'s team. NOT through HR.',
        'Traditional brokers ARE the bottleneck — every question goes through them.',
        'We eliminate the broker from the routine loop entirely.',
      ],
      callout: 'Here\'s your card. Go live your life. That\'s the 90%.',
    },
    {
      heading: 'The 10% — Orchestrated Care',
      body: '<p>When a high-dollar claim fires — cancer, major surgery, specialty drugs — the orchestrator takes over. Not HR. HR gets notified, but the process runs through Dave\'s team.</p>',
      bullets: [
        'HR-branded communication goes out to the employee (they think it\'s from HR)',
        'Orchestrator contacts the employee, collects intake info',
        'Routes to the right waterfall (hospital or drug)',
        'Service rep follows up after the process completes',
        'HR sees it on their dashboard — but doesn\'t have to chase it',
      ],
      diagram: ruleOfTwosDiagram,
    },
    {
      heading: 'Five Dashboards — Including Yours',
      body: '<p>Every stakeholder gets their own view of the same underlying data warehouse:</p>',
      bullets: [
        'HR Dashboard — enrollment, employee status, census, compliance',
        'CFO Dashboard — two bills, total spend, savings, fixed vs variable',
        'Underwriting Dashboard — claims data, loss ratios, risk analysis',
        'Renewal Dashboard — what we spent, what we saved, money back',
        'Service Advisor Dashboard — open cases, process status, satisfaction',
      ],
      callout: 'Same data. Different views. CFO sees dollars. HR sees people. Underwriting sees risk.',
    },
    {
      heading: 'The Employee Page',
      body: '<p>Every employee gets a self-serve page:</p>',
      bullets: [
        'Benefits summary — what they have, how to use it',
        'Ticketing system — submit questions, routes to vendor directly',
        'Self-serve. 90% of employees never need to call anyone.',
      ],
    },
    {
      heading: 'Implementation — No Disruption',
      body: '<p><strong>Year 1:</strong> Census enrollment. Take existing employees, copy them over. New cards issued — same benefits, different plumbing. No re-enrollment, no disruption, no employee confusion. Dave\'s system starts collecting data from day one.</p><p><strong>Year 2:</strong> Full enrollment. Open everything up. Rule of Twos plan design goes live. High-dollar process fully operational. Data from Year 1 drives Year 2 decisions.</p>',
      callout: 'Switching sounds like a nightmare. It\'s not. Year 1 is a soft transition. Year 2 is full optimization.',
    },
  ],
};
