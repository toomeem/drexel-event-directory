import { NavLink } from "react-router-dom";

const LOGO_URL = "https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/logos/logo_v4.png";

interface SiteHeaderProps {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  aiEnabled: boolean;
  onToggleAi: () => void;
}

export function SiteHeader({
  theme,
  onToggleTheme,
  aiEnabled,
  onToggleAi,
}: SiteHeaderProps) {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <NavLink to="/" className="site-header__brand">
          <img src={LOGO_URL} alt="Drexel Logo" className="site-header__logo" />

        </NavLink>
        <nav className="site-header__nav">
          <button
            type="button"
            className={"ai-toggle" + (aiEnabled ? " ai-toggle--on" : "")}
            onClick={onToggleAi}
            role="switch"
            aria-checked={aiEnabled}
            aria-label={
              aiEnabled ? "Disable AI features" : "Enable AI features"
            }
            title={aiEnabled ? "Disable AI features" : "Enable AI features"}
          >
            <span className="ai-toggle__label">AI</span>
            {!aiEnabled && (
              <span className="ai-toggle__no" aria-hidden="true" />
            )}
          </button>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              "site-header__nav-link" + (isActive ? " active" : "")
            }
          >
            Events
          </NavLink>
          <NavLink
            to="/about"
            className={({ isActive }) =>
              "site-header__nav-link" + (isActive ? " active" : "")
            }
          >
            About
          </NavLink>
          <button
            className="theme-toggle"
            onClick={onToggleTheme}
            aria-label={
              theme === "light" ? "Switch to dark theme" : "Switch to light theme"
            }
          >
            {theme === "light" ? <MoonIcon /> : <SunIcon />}
          </button>
        </nav>
      </div>
    </header>
  );
}

function SunIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}
