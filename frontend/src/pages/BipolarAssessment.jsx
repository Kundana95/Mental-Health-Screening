import { useEffect, useRef, useState } from 'react';
import { Link } from '../components/SiteLink.jsx';
import {
  analyzeBipolar,
  BIPOLAR_CATEGORY_COPY,
  BIPOLAR_QUESTIONS,
  validateBipolarAnswers,
} from '../lib/bipolar.js';

export default function BipolarAssessment() {
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const request = useRef(null);
  const resultPanel = useRef(null);
  const isComplete = validateBipolarAnswers(answers) === '';

  useEffect(() => () => {
    request.current?.abort();
    request.current = null;
  }, []);

  useEffect(() => {
    if (result) resultPanel.current?.focus();
  }, [result]);

  function updateAnswer(key, rawValue, numeric) {
    setAnswers((previous) => ({
      ...previous,
      [key]: numeric ? (rawValue === '' ? '' : Number(rawValue)) : rawValue,
    }));
    setResult(null);
    setError(null);
  }

  function retakeScreening() {
    setAnswers({});
    setResult(null);
    setError(null);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (request.current || !isComplete) return;

    const controller = new AbortController();
    request.current = controller;
    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 30000);

    try {
      const analysis = await analyzeBipolar(answers, { signal: controller.signal });
      if (request.current === controller) setResult(analysis);
    } catch (failure) {
      if (request.current !== controller) return;
      setError(timedOut
        ? { kind: 'unavailable', message: 'Analysis took too long. Please try again in a moment.' }
        : { kind: failure.kind || 'service', message: failure.message });
    } finally {
      clearTimeout(timeout);
      if (request.current === controller) {
        request.current = null;
        setIsAnalyzing(false);
      }
    }
  }

  return (
    <main className="bipolar-page assessment-page text-classifier-page container">
      <Link className="text-classifier-back" to="/">← Back to home</Link>
      {!result && <header className="assessment-heading">
        <p className="eyebrow">A THOUGHTFUL SPACE TO CHECK IN</p>
        <h1>Bipolar Disorder Screening</h1>
        <p className="screening-quote">“Understanding yourself is a journey, not a label.”</p>
      </header>}

      <div className="text-classifier-layout">
        <div className="text-classifier-main">
          {!result && <aside className="text-classifier-notice">
            <p>This experimental screening is not a diagnosis and cannot confirm or rule out bipolar disorder. For concerns, seek assessment from a qualified mental-health professional.</p>
          </aside>}

          {!result && <form className="assessment-form bipolar-form" onSubmit={handleSubmit} noValidate aria-busy={isAnalyzing}>
            {BIPOLAR_QUESTIONS.map((question, index) => {
              const numeric = !question.choices;
              const options = question.choices
                ? question.choices.map((value) => ({ value, label: value }))
                : Array.from({ length: question.max - question.min + 1 }, (_, offset) => {
                    const value = question.min + offset;
                    return { value, label: String(value) };
                  });
              const currentValue = answers[question.key] ?? '';

              return (
                <div className="assessment-context bipolar-question" key={question.key}>
                  <label htmlFor={`bipolar-${index}`}>{index + 1}. {question.label}</label>
                  <select
                    id={`bipolar-${index}`}
                    value={currentValue}
                    onChange={(event) => updateAnswer(question.key, event.target.value, numeric)}
                    required
                    disabled={isAnalyzing}
                    aria-invalid={error?.kind === 'validation' && !currentValue ? true : undefined}
                  >
                    <option value="" disabled>Select an answer</option>
                    {options.map(({ value, label }) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
              );
            })}
            <div className="assessment-submit-row">
              <button className="button button--primary" type="submit" disabled={!isComplete || isAnalyzing}>
                {isAnalyzing ? 'Analyzing…' : 'View screening result'}
              </button>
              <span className="assessment-submit-note">Responses are used for this request only.</span>
            </div>
          </form>}

          {error && <div className="assessment-message assessment-message--error" role="alert"><p>{error.message}</p></div>}

          {result && <section className="screening-results" aria-labelledby="bipolar-result-heading" ref={resultPanel} tabIndex={-1}>
            <h2 id="bipolar-result-heading">Screening Results</h2>
            <article className="screening-result-card" role="status" aria-live="polite" aria-atomic="true">
              <h3>{BIPOLAR_CATEGORY_COPY[result.category]}</h3>
            </article>
            <p className="screening-results__disclaimer">This experimental result is not a diagnosis and cannot confirm or rule out bipolar disorder. Seek professional assessment for concerns.</p>
            <button className="button button--outline screening-results__retake" type="button" onClick={retakeScreening}>Retake Screening</button>
          </section>}
        </div>

      </div>
    </main>
  );
}
