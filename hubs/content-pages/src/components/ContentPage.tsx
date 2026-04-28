import { useEffect } from 'react';
import type { ContentConfig } from '../types';
import {
  VideoSlot, AudioSlot, SlidesSlot, ReportSlot,
  InfographicSlot, QuizSlot, FlashcardsSlot, MindMapSlot, DataTableSlot,
} from './slots';

const LOGOS = {
  svg: '/logos/svg-agency.bmp',
  weewee: '/logos/weewee-me.jpg',
  insuranceinformatics: '/logos/insurance-informatics-horizontal.svg',
};

const LCS_HUB_URL = 'https://lcs-hub.svg-outreach.workers.dev/page-event';

function slugify(pathname: string): string {
  const raw = pathname.replace(/\/+$/g, '').replace(/^\//, '') || 'home';
  return raw.replace(/[^a-z0-9]+/gi, '-').replace(/^-+|-+$/g, '').toUpperCase();
}

function sendPageEvent(eventType: string, payload: Record<string, unknown>) {
  if (typeof window === 'undefined') return;

  const body = JSON.stringify({
    sovereign_company_id: 'PUBLIC',
    communication_id: `WEB-${slugify(window.location.pathname)}`,
    event_type: eventType,
    lifecycle_phase: 'WEB',
    page_step: payload.page_step ?? 'home',
    signal_set_hash: payload.signal_set_hash ?? `WEB-${slugify(window.location.pathname)}`,
    payload,
  });

  if (navigator.sendBeacon) {
    navigator.sendBeacon(LCS_HUB_URL, new Blob([body], { type: 'application/json' }));
    return;
  }

  fetch(LCS_HUB_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    keepalive: true,
  }).catch(() => {});
}

export function ContentPage({ config }: { config: ContentConfig }) {
  useEffect(() => {
    sendPageEvent('page_loaded', {
      page_step: 'page_loaded',
      title: config.title,
      brand: config.brand,
      path: typeof window === 'undefined' ? '/' : window.location.pathname,
    });
  }, [config.brand, config.title]);

  const brandLabel = config.brand === 'svg'
    ? 'SVG Agency'
    : config.brand === 'weewee'
      ? 'WeeWee.Me'
      : 'Insurance Informatics';

  return (
    <div className={`content-page brand-${config.brand}`}>
      <header className="page-header">
        <img src={LOGOS[config.brand]} alt={brandLabel} className="brand-logo" />
        <div className="header-text">
          <div className="eyebrow">{brandLabel}</div>
          <h1>{config.title}</h1>
          {config.subtitle && <h2>{config.subtitle}</h2>}
          {config.description && <p className="description">{config.description}</p>}
          {config.primaryCta && (
            <div className="cta-row">
              <a
                className="primary-cta"
                href={config.primaryCta.href}
                onClick={() => {
                  sendPageEvent('cta_clicked', {
                    page_step: 'cta',
                    cta_label: config.primaryCta?.label,
                    href: config.primaryCta?.href,
                    title: config.title,
                  });
                }}
              >
                {config.primaryCta.label}
              </a>
              {config.primaryCta.note && <p className="cta-note">{config.primaryCta.note}</p>}
            </div>
          )}
        </div>
      </header>

      <main className="slots-grid">
        {config.video && <VideoSlot {...config.video} />}
        {config.audio && <AudioSlot {...config.audio} />}
        {config.slides && <SlidesSlot {...config.slides} />}
        {config.report && <ReportSlot {...config.report} />}
        {config.infographic && <InfographicSlot {...config.infographic} />}
        {config.quiz && <QuizSlot {...config.quiz} />}
        {config.flashcards && <FlashcardsSlot {...config.flashcards} />}
        {config.mindmap && <MindMapSlot {...config.mindmap} />}
        {config.datatable && <DataTableSlot {...config.datatable} />}
      </main>

      <footer className="page-footer">
        <p>&copy; {new Date().getFullYear()} {brandLabel}</p>
      </footer>
    </div>
  );
}
