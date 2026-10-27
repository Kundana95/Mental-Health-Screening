import { Link } from './SiteLink.jsx';

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container">
        <Link to="/" className="footer-brand">mindful</Link>
        <p className="footer-tagline">A little space to check in with yourself.</p>
        <nav className="footer-nav" aria-label="Footer navigation">
          <Link to="/">Home</Link>
          <a href="/#about">About Mindful</a>
          <a href="/#resources">Mental-health resources</a>
        </nav>
        <div className="footer-rule" />
        <p className="footer-note">Screening results are experimental and are not a diagnosis or a substitute for professional care.</p>
      </div>
    </footer>
  );
}
