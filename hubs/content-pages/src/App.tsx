import { WebsiteLayout } from './components/WebsiteLayout';
import { ContentPage } from './components/ContentPage';
import type { ContentConfig, WebsitePage } from './types';
import './styles.css';

// ── Legacy content pages (kept for backward compat) ──
import { content5500 } from './configs/content5500';
import { contentThe10Orchestrator } from './configs/the-10-orchestrator';
import { contentInformaticsPipeline } from './configs/informatics-pipeline';
import { contentInsuranceInformaticsVendorBriefing } from './configs/insurance-informatics-vendor-briefing';
import { contentDeconstructingTheDuck } from './configs/deconstructing-the-duck';
import { contentInsuranceInformaticsCTB } from './configs/insurance-informatics-ctb';

// ── New website pages (SEO-first) ──
import { homePage } from './pages/home';
import { whatIsIIPage } from './pages/what-is-ii';
import { howItWorksPage } from './pages/how-it-works';
import { executivesPage } from './pages/executives';
import { hrPage } from './pages/hr';
import { permanentPage } from './pages/permanent';
import { vendorsPage } from './pages/vendors';
import { aboutPage } from './pages/about';
import { bookPage } from './pages/book';

// ── Website routes ──
const websiteRoutes: Record<string, WebsitePage> = {
  '/': homePage,
  '/what-is-insurance-informatics': whatIsIIPage,
  '/how-it-works': howItWorksPage,
  '/executives': executivesPage,
  '/hr': hrPage,
  '/permanent': permanentPage,
  '/vendors': vendorsPage,
  '/about': aboutPage,
  '/book': bookPage,
  // Aliases
  '/insurance-informatics': homePage,
};

// ── Legacy routes (content viewer pages) ──
const legacyRoutes: Record<string, ContentConfig> = {
  '/5500': content5500,
  '/the-10-percent-with-orchestrator': contentThe10Orchestrator,
  '/informatics-pipeline': contentInformaticsPipeline,
  '/insurance-informatics-vendor-briefing': contentInsuranceInformaticsVendorBriefing,
  '/deconstructing-the-duck': contentDeconstructingTheDuck,
  '/insurance-informatics-ctb': contentInsuranceInformaticsCTB,
};

export default function App() {
  const raw = window.location.pathname;
  const path = raw.replace(/\/$/, '') || '/';

  // Check website routes first
  const websitePage = websiteRoutes[path];
  if (websitePage) {
    return <WebsiteLayout page={websitePage} />;
  }

  // Fall back to legacy content pages
  const legacyPage = legacyRoutes[path];
  if (legacyPage) {
    return <ContentPage config={legacyPage} />;
  }

  // Default to home
  return <WebsiteLayout page={homePage} />;
}
