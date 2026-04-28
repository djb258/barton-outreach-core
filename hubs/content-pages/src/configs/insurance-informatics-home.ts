import type { ContentConfig } from '../types';
import { VOICE_SPEC } from '../voice-spec.generated';

const bookingUrl = 'https://calendar.app.google/VT41mpEgTWDexFET8';
const requiredPhrases = VOICE_SPEC.voice_constants.required_phrases;
const websiteRules = VOICE_SPEC.channel_rules.website.required_elements;
const brandName = VOICE_SPEC.brand.name;

const reportHtml = `
  <h1>Here's how it works.</h1>
  <p>${brandName} is the named discipline. The website exists to explain the machine, not to decorate it.</p>
  <p><strong>The math is simple.</strong> Premiums don't equal cost. Cost lives in claims, administration, trend, and the friction between a visitor and a booked meeting.</p>
  <p>You can't stop claims. You can only measure them, price them, and route them through a system that does not blink.</p>

  <h2>FCE-007 website performance constants</h2>
  <table>
    <thead>
      <tr>
        <th>Column</th>
        <th>Primitive</th>
        <th>Question</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Valuation</td>
        <td>Thing</td>
        <td>Does the site exist with speed, mobile behavior, crawlability, SSL, and schema in place?</td>
      </tr>
      <tr>
        <td>Concentration</td>
        <td>Flow</td>
        <td>Which keywords, backlinks, and channels send the right visitors?</td>
      </tr>
      <tr>
        <td>Trend</td>
        <td>Change</td>
        <td>Are authority and rankings improving while content stays fresh?</td>
      </tr>
      <tr>
        <td>Liquidity</td>
        <td>Connection</td>
        <td>Can a visitor move from interest to booked meeting without friction?</td>
      </tr>
    </tbody>
  </table>

  <h2>What the page does</h2>
  <ul>
    <li>Names the category first: Insurance Informatics.</li>
    <li>Explains the operating model in direct language.</li>
    <li>Gives the visitor one next step.</li>
    <li>Logs page and CTA events back to LCS Hub.</li>
  </ul>

  <h2>Voice spec phrases</h2>
  <ul>
    ${requiredPhrases.map((phrase) => `<li>${phrase}</li>`).join('\n    ')}
  </ul>

  <h2>Website rules</h2>
  <ul>
    ${websiteRules.map((rule) => `<li>${rule}</li>`).join('\n    ')}
  </ul>

  <blockquote>I encourage you to compete it.</blockquote>

  <p>Compare the math. Compare the structure. Compare the cost of doing nothing against the cost of a disciplined system.</p>
`;

export const contentInsuranceInformaticsHome: ContentConfig = {
  brand: 'insuranceinformatics',
  title: brandName,
  subtitle: `${brandName} performance for the named discipline`,
  description:
    `${brandName} is the merger of insurance discipline and IT discipline under one named field. The site speaks plainly, moves fast, and pushes one next step.`,
  primaryCta: {
    label: 'Book 15 minutes',
    href: bookingUrl,
    note: 'Zero fluff. One conversation. The math does the talking.',
  },
  video: {
    streamId: 'f5290faa8da6e1d67410697ae2bd5c89',
    title: 'Insurance Informatics - The Pipeline Behind Your Next 100 Clients',
  },
  report: {
    title: 'Website Positioning',
    html: reportHtml,
  },
  infographic: {
    src: '/content/insurance-informatics/performance-pillars.svg',
    title: 'FCE-007 performance pillars',
  },
  slides: {
    src: '/content/insurance-informatics/site-map.svg',
    title: 'Insurance Informatics website map',
  },
  mindmap: {
    src: '/content/insurance-informatics/lead-flow.svg',
    title: 'Lead flow and conversion path',
  },
  datatable: {
    title: 'Conversion and SEO constants',
    data: {
      headers: ['Signal', 'What it means', 'What the site must do'],
      rows: [
        ['Technical SEO', 'Valuation foundation', 'Load fast, read clean, stay crawlable'],
        ['Content strategy', 'Concentration flow', 'Answer the right query in the right tone'],
        ['Freshness', 'Trend change', 'Update proof, examples, and links'],
        ['CTA path', 'Liquidity connection', 'Make the booking path obvious'],
      ],
    },
  },
  quiz: {
    title: 'Website performance check',
    questions: [
      {
        question: 'Which FCE-007 column covers speed, crawlability, SSL, and schema?',
        options: ['Valuation', 'Trend', 'Liquidity'],
        correct: 0,
        explanation: 'Valuation is the technical foundation. If the thing is broken, nothing else matters.',
      },
      {
        question: 'What does Liquidity measure?',
        options: ['Backlink volume', 'Conversion friction', 'Keyword density'],
        correct: 1,
        explanation: 'Liquidity is the connection path. If booking is hard, traffic leaks out.',
      },
      {
        question: 'What is the one clear CTA on the site?',
        options: ['Book 15 minutes', 'Request a proposal', 'Contact us for more info'],
        correct: 0,
        explanation: 'The voice spec wants one clear next step. The site uses the booking link.',
      },
    ],
  },
  flashcards: {
    title: 'Voice and performance memory',
    cards: [
      { front: 'Here\'s how it works.', back: 'Open with the mechanism, not a sales lead-in.' },
      { front: 'The math is simple.', back: 'Tie the site to measurable performance, not vibes.' },
      { front: 'Premiums don\'t equal cost.', back: 'Separate price from actual claims and operating cost.' },
      { front: 'You can\'t stop claims.', back: 'The site explains the machine that manages them.' },
    ],
  },
};
