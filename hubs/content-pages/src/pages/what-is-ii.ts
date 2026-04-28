import type { WebsitePage } from '../types';
import { paradigmShiftDiagram } from '../diagrams';

export const whatIsIIPage: WebsitePage = {
  slug: '/what-is-insurance-informatics',
  ctbAltitude: '50K',
  seo: {
    title: 'What Is Insurance Informatics? | The Named Discipline',
    description: 'Insurance Informatics is the named discipline that merges IT data architecture with insurance operations. Not a brand — a category of one. Learn how it works.',
    canonical: 'https://insuranceinformatics.com/what-is-insurance-informatics',
  },
  hero: {
    headline: 'What Is Insurance Informatics?',
    subhead: 'A named discipline — parallel to medical informatics and clinical informatics. Not a brand. A category of one.',
    ctaLabel: 'See How It Works',
    ctaHref: '/how-it-works',
  },
  sections: [
    {
      heading: 'The Genesis: 25 + 25',
      body: '<p>25 years of IT data architecture. 25 years of insurance operations. Put them together and you get a discipline that didn\'t exist before: <strong>Insurance Informatics</strong>.</p><p>Every other broker is chasing price. We\'re engineering process. They\'re running on spreadsheets. We\'re running on structured data through a 38-node Cloudflare edge network.</p><p>This isn\'t a different product. It\'s a different race entirely.</p>',
    },
    {
      heading: 'Traditional Brokerage vs Insurance Informatics',
      diagram: paradigmShiftDiagram,
    },
    {
      heading: 'Why It Matters',
      body: '<p>The TPA thinks they\'re the hub. They\'re not. They see one pipe — claims. Insurance Informatics sees both pipes (fixed and variable), controls enrollment (the front door), runs the HR communication channel, and aggregates everything into one view.</p>',
      callout: 'Proximity to the client is the moat. Nobody else has this position.',
    },
    {
      heading: 'The Pattern Is Twos',
      bullets: [
        'Two sides: Fixed costs (PEPM vendors) + Variable costs (claims)',
        'Two bills: One from Dave, one from the TPA',
        'Two populations: 90% routine (autopilot) + 10% high-dollar (managed)',
        'Two contacts per vendor: Account manager + customer service',
        'Two claim pipes: TPA (hospitals/doctors) + PBM (pharmacy)',
      ],
      body: '<p>Everything splits into two at every altitude. Structure is the constant. The fill changes — but the pattern doesn\'t.</p>',
    },
    {
      heading: 'Zero Commission. Flat PEPM.',
      body: '<p>Premiums don\'t equal cost. Cost lives in claims, administration, trend, and the friction between the data and the decision.</p><p>We charge a flat Per Employee Per Month fee. No commission. No BOR (Broker of Record letter). No hidden revenue. We sit on the same side of the table as the CFO.</p>',
      callout: 'I encourage you to compete it. Take it to every broker. Their number has commission baked in. Ours doesn\'t.',
    },
  ],
};
