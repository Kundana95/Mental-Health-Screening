import { screenings } from '../data/screenings.js';
import ScreeningCard from '../components/ScreeningCard.jsx';

const resources = [
  {
    title: 'Find a Helpline',
    description: 'Explore support by country.',
    link: 'https://findahelpline.com/',
    label: 'findahelpline.com ↗',
  },
  {
    title: '988 Lifeline',
    description: 'U.S. and Canada · Call or text 988.',
    link: 'https://988lifeline.org/',
    label: '988 · Crisis support ↗',
  },
  {
    title: 'NIMH',
    description: 'Mental-health information and guidance.',
    link: 'https://www.nimh.nih.gov/health',
    label: 'nimh.nih.gov ↗',
  },
];

export default function HomePage() {
  return (
    <main className="dashboard">
      <header className="dashboard-intro container">
        <div className="dashboard-intro__copy">
          <p className="eyebrow">MENTAL HEALTH SCREENING</p>
          <h1>Mindful</h1>
          <p className="dashboard-intro__tagline">Explore four screening and text-classification modules in one place.</p>
          <a className="button button--primary dashboard-intro__button" href="#screenings">Explore screenings ↓</a>
        </div>
      </header>

      <section className="screenings-section container" id="screenings" aria-labelledby="screenings-title">
        <div className="dashboard-section-heading">
          <div>
            <p className="eyebrow">FOUR MODULES</p>
            <h2 id="screenings-title">Explore screenings</h2>
          </div>
          <p className="section-intro">Choose a module to open its questionnaire or text-classification page.</p>
        </div>
        <div className="screening-grid">
          {screenings.map((screening) => <ScreeningCard key={screening.slug} screening={screening} />)}
        </div>
        <aside className="dashboard-disclaimer" aria-label="Mental-health safety disclaimer">
          <strong>Safety note</strong>
          <span>Results are experimental and are not diagnoses. They are not a substitute for professional assessment or care.</span>
        </aside>
      </section>

      <section className="dashboard-about container" id="about" aria-labelledby="about-title">
        <div className="dashboard-about__inner">
          <h2 id="about-title">About Mindful</h2>
          <p>Mindful brings four mental-health screening and text-classification modules together in one place. It offers a simple, welcoming space for reflection through questionnaires and text-based input, with results presented carefully and responsibly. Each module is designed to be easy to explore while keeping clear that screening results are not a diagnosis or a substitute for professional care.</p>
        </div>
      </section>

      <section className="resources-section container" id="resources" aria-labelledby="resources-title">
        <p className="eyebrow">SUPPORT AND INFORMATION</p>
        <h2 id="resources-title">Mental-health resources</h2>
        <p className="section-intro">For reliable information or support from a person.</p>
        <div className="resources-grid">
          {resources.map((resource) => (
            <article className="resource-card" key={resource.title}>
              <h3>{resource.title}</h3>
              <p>{resource.description}</p>
              <a href={resource.link} target="_blank" rel="noreferrer">{resource.label}</a>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
