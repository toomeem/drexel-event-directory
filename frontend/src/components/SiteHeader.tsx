import { NavLink } from "react-router-dom";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <NavLink to="/" className="site-header__brand">
          <span className="site-header__brand-mark" aria-hidden="true" />
          <span className="site-header__brand-text">Drexel Events</span>
        </NavLink>
        <nav className="site-header__nav">
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
        </nav>
      </div>
    </header>
  );
}
