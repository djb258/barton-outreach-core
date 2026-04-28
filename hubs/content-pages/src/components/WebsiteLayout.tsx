import { useEffect } from 'react';
import type { WebsitePage } from '../types';
import { Navigation } from './Navigation';

const LCS_HUB_URL = 'https://lcs-hub.svg-outreach.workers.dev/page-event';
const BOOKING_URL = 'https://calendar.app.google/VT41mpEgTWDexFET8';

function sendEvent(eventType: string, payload: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  const slug = window.location.pathname.replace(/\/$/, '').replace(/^\//, '') || 'home';
  const body = JSON.stringify({
    sovereign_company_id: 'PUBLIC',
    communication_id: `WEB-${slug.toUpperCase()}`,
    event_type: eventType,
    lifecycle_phase: 'WEB',
    page_step: slug,
    signal_set_hash: `WEB-${slug.toUpperCase()}`,
    payload,
  });
  if (navigator.sendBeacon) {
    navigator.sendBeacon(LCS_HUB_URL, new Blob([body], { type: 'application/json' }));
  } else {
    fetch(LCS_HUB_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, keepalive: true }).catch(() => {});
  }
}

function trackCta(label: string) {
  sendEvent('cta_clicked', { cta_label: label, href: BOOKING_URL });
}

export function WebsiteLayout({ page }: { page: WebsitePage }) {
  useEffect(() => {
    document.title = page.seo.title;
    // Update meta tags
    const setMeta = (name: string, content: string, attr = 'name') => {
      let el = document.querySelector(`meta[${attr}="${name}"]`) as HTMLMetaElement | null;
      if (!el) {
        el = document.createElement('meta');
        el.setAttribute(attr, name);
        document.head.appendChild(el);
      }
      el.content = content;
    };
    setMeta('description', page.seo.description);
    setMeta('og:title', page.seo.ogTitle || page.seo.title, 'property');
    setMeta('og:description', page.seo.ogDescription || page.seo.description, 'property');
    setMeta('og:url', page.seo.canonical, 'property');
    // Update canonical
    let canon = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
    if (!canon) {
      canon = document.createElement('link');
      canon.rel = 'canonical';
      document.head.appendChild(canon);
    }
    canon.href = page.seo.canonical;

    sendEvent('page_loaded', { title: page.seo.title, path: window.location.pathname });
  }, [page]);

  return (
    <div className="website">
      <Navigation />

      {/* Hero */}
      <header className="hero">
        <div className="hero-inner">
          <p className="hero-altitude">{page.ctbAltitude} ft</p>
          <h1>{page.hero.headline}</h1>
          <p className="hero-sub">{page.hero.subhead}</p>
          {page.hero.ctaLabel && (
            <a
              className="hero-cta"
              href={page.hero.ctaHref || BOOKING_URL}
              onClick={() => trackCta(page.hero.ctaLabel!)}
            >
              {page.hero.ctaLabel}
            </a>
          )}
        </div>
      </header>

      {/* Sections */}
      <main className="page-sections">
        {page.sections.map((section, i) => (
          <section key={i} className={`page-section ${section.diagram ? 'page-section--has-diagram' : ''}`}>
            <div className="section-inner">
              <h2>{section.heading}</h2>

              {section.body && (
                <div className="section-body" dangerouslySetInnerHTML={{ __html: section.body }} />
              )}

              {section.bullets && (
                <ul className="section-bullets">
                  {section.bullets.map((b, j) => <li key={j}>{b}</li>)}
                </ul>
              )}

              {section.callout && (
                <blockquote className="section-callout">{section.callout}</blockquote>
              )}

              {section.diagram && (
                <div className="section-diagram" dangerouslySetInnerHTML={{ __html: section.diagram }} />
              )}

              {section.video && (
                <div className="section-video">
                  <iframe
                    src={`https://customer-${section.video.streamId}.cloudflarestream.com/iframe`}
                    title={section.video.title}
                    allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture"
                    allowFullScreen
                    style={{ border: 'none', width: '100%', aspectRatio: '16/9' }}
                  />
                </div>
              )}
            </div>
          </section>
        ))}
      </main>

      {/* Bottom CTA */}
      <section className="bottom-cta">
        <div className="bottom-cta-inner">
          <h2>Ready to see the math?</h2>
          <p>15 minutes. Zero fluff. The numbers do the talking.</p>
          <a
            className="hero-cta"
            href={BOOKING_URL}
            onClick={() => trackCta('bottom-cta')}
          >
            Book a Meeting
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <strong>Insurance Informatics</strong>
            <p>A division of SVG Agency</p>
          </div>
          <nav className="footer-links" aria-label="Footer navigation">
            <a href="/what-is-insurance-informatics">What Is II</a>
            <a href="/how-it-works">How It Works</a>
            <a href="/executives">For Executives</a>
            <a href="/hr">For HR</a>
            <a href="/about">About Dave</a>
            <a href="/book">Book a Meeting</a>
          </nav>
          <p className="footer-copy">&copy; {new Date().getFullYear()} Insurance Informatics. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
