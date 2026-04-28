// Content configuration - one per topic/notebook (legacy — kept for backwards compat)
export interface ContentConfig {
  brand: 'svg' | 'weewee' | 'insuranceinformatics';
  title: string;
  subtitle?: string;
  description?: string;
  primaryCta?: {
    label: string;
    href: string;
    note?: string;
  };
  video?: { streamId: string; title: string };
  audio?: { src: string; title: string };
  slides?: { src: string; title: string };
  report?: { html: string; title: string };
  infographic?: { src: string; title: string };
  quiz?: { questions: { question: string; options: string[]; correct: number; explanation?: string }[]; title: string };
  flashcards?: { cards: { front: string; back: string }[]; title: string };
  mindmap?: { src: string; title: string };
  datatable?: { data: { headers: string[]; rows: string[][] }; title: string };
}

// ── Website page (SEO-first, diagram-heavy) ──

export interface PageSection {
  heading: string;
  body?: string; // HTML string
  diagram?: string; // inline SVG string
  bullets?: string[];
  callout?: string; // blockquote-style highlight
  video?: { streamId: string; title: string };
}

export interface WebsitePage {
  slug: string; // route path, e.g. '/how-it-works'
  seo: {
    title: string;
    description: string;
    canonical: string;
    ogTitle?: string;
    ogDescription?: string;
  };
  hero: {
    headline: string;
    subhead: string;
    ctaLabel?: string;
    ctaHref?: string;
  };
  sections: PageSection[];
  ctbAltitude: string; // e.g. '50K', '40K-30K'
}
