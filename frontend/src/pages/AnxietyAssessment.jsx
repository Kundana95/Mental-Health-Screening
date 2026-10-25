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
      <header className="assessment-heading">
        <p className="eyebrow">THE STUDENT EXPERIENCE</p>
        <h1>Anxiety Screening</h1>
        <p>This is an experimental screening estimate, not a clinical diagnosis.</p>
      </header>

      <aside className="text-classifier-notice anxiety-notice">
        <h2>A model-based estimate</h2>
        <p>This prototype uses a trained model and these seven academic-context questions. It has not been established as a clinical assessment and cannot diagnose or rule out an anxiety disorder. For concerns, seek a qualified mental-health professional.</p>
      </aside>

      <form className="assessment-form" onSubmit={handleSubmit} noValidate aria-busy={isSubmitting}>
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
      </form>

      {error && <p className="assessment-message assessment-message--error" role="alert">{error.message}</p>}
      {result && (
        <section className="anxiety-result" role="status" aria-labelledby="anxiety-result-heading">
          <p className="eyebrow">EXPERIMENTAL MODEL ESTIMATE</p>
          <h2 id="anxiety-result-heading">{result.category}</h2>
          <p>This is an experimental estimate, not a diagnosis. A result cannot establish or rule out an anxiety disorder.</p>
        </section>
      )}
    </main>
  );
}
