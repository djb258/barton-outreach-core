import type { ContentConfig } from '../types';

// 5500 Education — preserved from the original single-config App.tsx.
// Route: / and /5500
export const content5500: ContentConfig = {
  brand: 'svg',
  title: '5500 Education',
  subtitle: 'Form 5500 Compliance Training',
  description:
    'Everything you need to know about Form 5500 filing — from the basics to Schedule C service provider reporting, audit requirements, and the 80-120 rule.',

  video: {
    streamId: 'dae7d03656b5ce0718b0e6be7d14c259',
    title: 'Pull vs. Push: The Form 5500 Data Showdown',
  },

  audio: {
    src: '/content/5500/podcast.m4a',
    title: 'The Invisible Machinery of Employee Benefits',
  },
  slides: {
    src: '/content/5500/slides.pdf',
    title: 'Health & Welfare Compliance Blueprint',
  },
  infographic: {
    src: '/content/5500/infographic.png',
    title: 'Health and Welfare Compliance Guide',
  },
};
