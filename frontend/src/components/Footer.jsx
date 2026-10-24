import { Link } from './SiteLink.jsx';

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container">
        <Link to="/" className="footer-brand">mindful</Link>
        <p className="footer-tagline">A little space to check in with yourself.</p>
        <nav className="footer-nav" aria-label="Footer navigation">
          <Link to="/">Home</Link>
          <a href="/#about">About the project</a>
          <a href="/#resources">Mental-health resources</a>
        </nav>
        <div className="footer-rule" />
        <p className="footer-note">Mindful · College computer-science mini-project. Screening scores use fixed rules; no diagnosis or generated analysis is provided.</p>
      </div>
    </footer>
  );
}
