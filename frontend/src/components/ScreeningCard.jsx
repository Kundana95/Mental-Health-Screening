import { Link } from './SiteLink.jsx';
import AbstractIllustration from './AbstractIllustration.jsx';

export default function ScreeningCard({ screening }) {
  return (
    <article className={`screening-card screening-card--${screening.tone}`}>
      <div className="screening-card__top">
        <p className="eyebrow">{screening.eyebrow}</p>
        <AbstractIllustration tone={screening.tone} compact />
      </div>
      <h3>{screening.title}</h3>
      <p className="screening-card__description">{screening.description}</p>
      <p className="screening-card__detail">{screening.detail}</p>
      <Link className="button button--outline" to={`/${screening.slug}`}>
        Get started <span aria-hidden="true">→</span>
      </Link>
    </article>
  );
}
