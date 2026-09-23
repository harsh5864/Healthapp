import { Link } from 'react-router-dom';

export default function SiteHeader() {
  return (
    <header className="site-header">
      <Link className="brand" to="/" aria-label="AI Health Companion home">
        <span className="brand__mark" aria-hidden="true">✦</span>
        <span>AI Health <strong>Companion</strong></span>
      </Link>
      <nav aria-label="Main navigation">
        <a href="/#features">Features</a>
        <Link to="/about">About</Link>
        <Link to="/safety">Safety &amp; privacy</Link>
        <Link className="header-login" to="/login">Sign in</Link>
        <Link className="header-signup" to="/register">Get started</Link>
      </nav>
    </header>
  );
}
