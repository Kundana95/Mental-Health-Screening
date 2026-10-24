import { Link } from '../components/SiteLink.jsx';
import AbstractIllustration from '../components/AbstractIllustration.jsx';
import { screenings } from '../data/screenings.js';

export default function ModulePlaceholder({ slug }) {
  const screening = screenings.find((item) => item.slug === slug);
  if (!screening) {
    return (
      <main className="placeholder-page container">
        <h1>Page not found</h1>
        <Link className="button button--outline" to="/">Back to home</Link>
      </main>
    );
  }

  return (
    <main className="placeholder-page container">
      <AbstractIllustration tone={screening.tone} compact />
      <p className="eyebrow">{screening.eyebrow}</p>
      <h1>{screening.title}</h1>
      <p>{screening.description}</p>
      <p className="placeholder-note">This page is a preview. Assessment forms have not been added yet.</p>
      <Link className="button button--outline" to="/">← Back to home</Link>
    </main>
  );
}
