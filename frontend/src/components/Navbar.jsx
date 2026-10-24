import BotanicalMark from './BotanicalMark.jsx';
import { Link } from './SiteLink.jsx';

export default function Navbar() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link to="/" className="brand" aria-label="Mindful home">
          <BotanicalMark small />
          <span>mindful</span>
        </Link>
        <nav className="main-nav" aria-label="Main navigation">
          <Link to="/" className="main-nav__link">Home</Link>
          <a className="main-nav__link" href="/#about">About</a>
          <a className="main-nav__link" href="/#resources">Resources</a>
        </nav>
      </div>
    </header>
  );
}
