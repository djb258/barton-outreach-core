import type { WebsitePage } from '../types';

const BOOKING_URL = 'https://calendar.app.google/VT41mpEgTWDexFET8';

export const bookPage: WebsitePage = {
  slug: '/book',
  ctbAltitude: '5K',
  seo: {
    title: 'Book a Meeting | Insurance Informatics Consultation',
    description: 'Zero friction. Four short video briefings. Four 15-minute meetings. Book a free consultation to see how Insurance Informatics can reduce your benefits spend.',
    canonical: 'https://insuranceinformatics.com/book',
  },
  hero: {
    headline: 'See the Math for Yourself',
    subhead: 'Zero friction. Four short video briefings. Four 15-minute meetings. The numbers do the talking.',
    ctaLabel: 'Book 15 Minutes Now',
    ctaHref: BOOKING_URL,
  },
  sections: [
    {
      heading: 'The Four-Step Evaluation',
      body: '<p>No sales pitch. No pressure. Just math. Four meetings, each 15-20 minutes, each building on the last:</p>',
      bullets: [
        'Meeting 1: Fact Finder — "Here\'s what we already know about your company." We bring the data. You bring the bill.',
        'Meeting 2: Education — Self-insured vs. fully-insured explained. Monte Carlo simulation shows two paths diverging over 5 years.',
        'Meeting 3: Service — Five dashboards. Employee page. Ticketing system. What life actually looks like day-to-day.',
        'Meeting 4: Your Numbers — YOUR specific quote, YOUR specific savings. "I encourage you to compete it. Take it to every broker."',
      ],
    },
    {
      heading: 'What You Need to Bring',
      body: '<p>One thing: your current benefits bill. That\'s it. We already have your company data, your carrier, your broker, your renewal date. We stated it all as facts in Meeting 1 — you just confirmed.</p>',
      callout: 'You bring the bill. I\'ll bring the math.',
    },
    {
      heading: 'What You Get',
      bullets: [
        'A clear understanding of self-insured vs. fully-insured mechanics',
        'Your company\'s specific savings projection (Monte Carlo, not a guess)',
        'A side-by-side comparison with your current plan\'s total cost',
        'No BOR letter. No commitment. No pressure. Just numbers.',
      ],
    },
    {
      heading: 'Schedule Your First Meeting',
      body: `<p style="text-align:center;margin:2rem 0"><a href="${BOOKING_URL}" style="display:inline-block;padding:1rem 2.5rem;background:#2b6cb0;color:white;text-decoration:none;border-radius:8px;font-size:1.25rem;font-weight:bold">Book 15 Minutes</a></p><p style="text-align:center;color:#718096">Free. No obligation. The math speaks for itself.</p>`,
    },
  ],
};
