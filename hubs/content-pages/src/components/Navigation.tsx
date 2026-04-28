import { useState } from 'react';

const NAV_LINKS = [
  { href: '/', label: 'Home' },
  { href: '/what-is-insurance-informatics', label: 'What Is II' },
  { href: '/how-it-works', label: 'How It Works' },
  { href: '/executives', label: 'For Executives' },
  { href: '/hr', label: 'For HR' },
  { href: '/permanent', label: 'Why Permanent' },
  { href: '/vendors', label: 'For Vendors' },
  { href: '/about', label: 'About' },
  { href: '/book', label: 'Book a Meeting' },
];

export function Navigation() {
  const [open, setOpen] = useState(false);
  const current = (window.location.pathname.replace(/\/$/, '') || '/');

  return (
    <nav className="site-nav" role="navigation" aria-label="Main navigation">
      <div className="nav-inner">
        <a href="/" className="nav-brand" aria-label="Insurance Informatics home">
          <img src="/logos/insurance-informatics-horizontal.svg" alt="Insurance Informatics" className="nav-logo" />
        </a>
        <button
          className="nav-toggle"
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          <span className="nav-toggle-bar" />
          <span className="nav-toggle-bar" />
          <span className="nav-toggle-bar" />
        </button>
        <ul className={`nav-links ${open ? 'nav-links--open' : ''}`}>
          {NAV_LINKS.map(link => (
            <li key={link.href}>
              <a
                href={link.href}
                className={`nav-link ${current === link.href ? 'nav-link--active' : ''} ${link.href === '/book' ? 'nav-link--cta' : ''}`}
              >
                {link.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
