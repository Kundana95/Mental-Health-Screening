import { Link } from './SiteLink.jsx';

export default function ScreeningCard({ screening }) {
  return (
    <article className={`screening-card screening-card--${screening.tone}`}>
      <div className="screening-card__top">
        <p className="eyebrow">{screening.eyebrow}</p>
        <div className={`abstract-art abstract-art--${screening.tone} abstract-art--compact`}>
          <img className="screening-card__illustration" src={screening.illustration} alt={screening.illustrationAlt} />
        </div>
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
