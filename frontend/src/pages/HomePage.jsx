import { screenings } from '../data/screenings.js';
import AbstractIllustration from '../components/AbstractIllustration.jsx';
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
    <>
      <main>
        <section className="hero container" aria-labelledby="hero-title">
          <div className="hero__copy">
            <span className="pill">A thoughtful space to check in</span>
            <h1 id="hero-title">A small step towards understanding yourself.</h1>
            <p className="hero__text">You don’t have to have it all figured out. Explore a gentle starting point for reflecting on your mental well-being, at your own pace.</p>
            <a className="button button--primary" href="#screenings">Explore screenings <span aria-hidden="true">↓</span></a>
            <p className="hero__note">Academic prototype. Not a diagnosis. No generated interpretation is shown.</p>
          </div>
          <AbstractIllustration />
        </section>

        <div className="values-strip" aria-label="Our approach">
          <div className="container values-strip__inner">
            <span><i aria-hidden="true">✧</i> Your pace, always</span>
            <span><i aria-hidden="true">✧</i> A starting point, not a label</span>
            <span><i aria-hidden="true">✧</i> Support beyond a screen</span>
          </div>
        </div>

        <section className="screenings-section container" id="screenings" aria-labelledby="screenings-title">
          <p className="eyebrow">FOUR PATHWAYS. EQUAL CARE.</p>
          <h2 id="screenings-title">Start where you feel comfortable.</h2>
          <p className="section-intro">Each pathway offers a different way to reflect. Choose one to explore its assessment preview.</p>
          <div className="screening-grid">
            {screenings.map((screening) => <ScreeningCard key={screening.slug} screening={screening} />)}
          </div>
        </section>

        <section className="how-section" aria-labelledby="how-title">
          <div className="container">
            <p className="eyebrow">HOW IT IS INTENDED TO WORK</p>
            <h2 id="how-title">From reflection to a next step.</h2>
            <p className="section-intro">A planned academic workflow, not a working screening service. The AI analysis and report stages are not active.</p>
            <div className="steps-grid">
              <article className="step-card">
                <p className="step-number">01 <span>—</span></p>
                <h3>Assessment</h3>
                <p>Reflect through a form or your own words. The input format depends on the module.</p>
              </article>
              <article className="step-card">
                <p className="step-number">02 <span>—</span></p>
                <h3>AI analysis</h3>
                <p>Planned only. Future teammate models would process confirmed module inputs.</p>
              </article>
              <article className="step-card">
                <p className="step-number">03 <span>—</span></p>
                <h3>Report</h3>
                <p>Planned only. A shared layout would organize future output and supportive next steps.</p>
              </article>
            </div>
          </div>
        </section>

        <section className="about-section container" id="about" aria-labelledby="about-title">
          <p className="eyebrow">ABOUT THE PROJECT</p>
          <h2 id="about-title">Built with curiosity.<br />Designed with care.</h2>
          <p className="about-copy">Mindful is a college computer-science mini-project exploring AI-assisted mental-health screening. This design brings four teammate modules into one welcoming experience, while keeping their different input needs clear.</p>
          <p className="about-copy about-copy--small">What is here: assessment layouts, transparent placeholders and a future report preview. What is not here: clinical predictions, working models or generated results. Some dataset details still need project confirmation.</p>
          <aside className="support-notice">
            <h3>Support comes before screening</h3>
            <p>This is not a diagnosis or an emergency service. If you feel unsafe or may hurt yourself, contact local emergency services or a crisis line now. In the U.S. or Canada, call or text 988. Elsewhere, visit <a href="https://findahelpline.com/" target="_blank" rel="noreferrer">findahelpline.com</a> for local support.</p>
          </aside>
        </section>

        <section className="resources-section container" id="resources" aria-labelledby="resources-title">
          <p className="eyebrow">YOU ARE NOT ALONE</p>
          <h2 id="resources-title">Support beyond this screen.</h2>
          <p className="section-intro">Reliable places to learn more or connect with a person who can help.</p>
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

        <section className="closing-cta" aria-labelledby="closing-title">
          <div className="container">
            <h2 id="closing-title">You deserve understanding, not a label.</h2>
            <p>Screening can only be a starting point. A qualified professional can help you explore what comes next.</p>
            <a className="button button--primary" href="#screenings">Explore screenings <span aria-hidden="true">↑</span></a>
          </div>
        </section>
      </main>
    </>
  );
}
