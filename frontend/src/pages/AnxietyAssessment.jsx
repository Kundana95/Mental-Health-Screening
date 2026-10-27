import { useState } from 'react';
import { Link } from '../components/SiteLink.jsx';
import {
  ANXIETY_CHOICES,
  ANXIETY_QUESTIONS,
  analyzeAnxiety,
  validateAnxietyResponses,
} from '../lib/anxiety.js';

export default function AnxietyAssessment() {
  const [responses, setResponses] = useState(() => Array(7).fill(null));
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateResponse(index, value) {
    setResponses((current) => current.map((answer, item) => item === index ? value : answer));
    setResult(null);
    setError(null);
  }

  function retakeScreening() {
    setResponses(Array(7).fill(null));
    setResult(null);
    setError(null);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (isSubmitting) return;
    const validationError = validateAnxietyResponses(responses);
    if (validationError) {
      setError({ kind: 'validation', message: validationError });
      return;
    }

    setError(null);
    setResult(null);
    setIsSubmitting(true);
    try {
      setResult(await analyzeAnxiety(responses));
    } catch (failure) {
      setError({ kind: failure.kind || 'service', message: failure.message });
    } finally {
      setIsSubmitting(false);
    }
  }

  const isComplete = !validateAnxietyResponses(responses);
  return (
    <main className="assessment-page container">
      <Link className="text-classifier-back" to="/">← Back to home</Link>
      {!result && <header className="assessment-heading">
        <h1>Anxiety Screening</h1>
        <p className="screening-quote">“Take a breath. You don't have to figure everything out at once.”</p>
        <p>This experimental screening estimate is not a diagnosis and cannot replace professional assessment. For concerns, speak with a qualified mental-health professional.</p>
      </header>}

      {!result && <form className="assessment-form" onSubmit={handleSubmit} noValidate aria-busy={isSubmitting}>
        {ANXIETY_QUESTIONS.map((question, index) => (
          <fieldset className="assessment-question" key={question.trim()}>
            <legend>{question.trim()}</legend>
            <div className="assessment-options">
              {ANXIETY_CHOICES.map(({ label, value }) => (
                <label className="assessment-option" key={value}>
                  <input
                    type="radio"
                    name={`anxiety-response-${index}`}
                    value={value}
                    checked={responses[index] === value}
                    onChange={() => updateResponse(index, value)}
                    disabled={isSubmitting}
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </fieldset>
        ))}
        <div className="assessment-submit-row">
          <button className="button button--primary" type="submit" disabled={!isComplete || isSubmitting}>
            {isSubmitting ? 'Preparing estimate…' : 'View screening estimate'}
          </button>
          <span className="assessment-submit-note">Your answers are used for this request only.</span>
        </div>
      </form>}

      {error && <p className="assessment-message assessment-message--error" role="alert">{error.message}</p>}
      {result && (
        <section className="screening-results" aria-labelledby="anxiety-result-heading">
          <h2 id="anxiety-result-heading">Screening Results</h2>
          <article className="screening-result-card" role="status">
            <h3>{result.category}</h3>
          </article>
          <p className="screening-results__disclaimer">This experimental result is not a diagnosis and cannot establish or rule out an anxiety disorder. Seek professional assessment for concerns.</p>
          <button className="button button--outline screening-results__retake" type="button" onClick={retakeScreening}>Retake Screening</button>
        </section>
      )}
    </main>
  );
}
