import { useEffect, useRef, useState } from 'react';
import AbstractIllustration from '../components/AbstractIllustration.jsx';
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
    <main className="bipolar-page text-classifier-page container">
      <Link className="text-classifier-back" to="/">← Back to home</Link>
      <header className="text-classifier-heading">
        <div>
          <p className="eyebrow">A THOUGHTFUL SPACE TO CHECK IN</p>
          <h1>Bipolar screening prototype</h1>
          <p>Share responses to the model’s input features for an experimental screening result.</p>
          <span className="pill">Experimental · Educational project</span>
        </div>
        <AbstractIllustration tone="blue" compact />
      </header>

      <div className="text-classifier-layout">
        <div className="text-classifier-main">
          <aside className="text-classifier-notice">
            <h2>About this prototype</h2>
            <p>This experimental screening prototype is based on a small dataset. Its prompts are project-defined model inputs, not a clinically validated questionnaire or a diagnosis. A result cannot confirm or rule out bipolar disorder. For concerns, seek assessment from a qualified mental-health professional.</p>
          </aside>

          <form className="assessment-form bipolar-form" onSubmit={handleSubmit} noValidate aria-busy={isAnalyzing}>
            <div className="bipolar-form-intro">
              <h2>Assessment inputs</h2>
              <p>Answer each item to continue. Numeric ratings use the ranges supported by the original training data.</p>
            </div>
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
          </form>

          {error && <div className="assessment-message assessment-message--error" role="alert"><p>{error.message}</p></div>}

          <section
            className={`text-classifier-result${result ? ' text-classifier-result--ready' : ''}`}
            aria-labelledby="bipolar-result-heading"
            ref={resultPanel}
            tabIndex={-1}
          >
            <p className="eyebrow">YOUR SCREENING RESULT</p>
            <h2 id="bipolar-result-heading">{result ? 'A model category' : 'Your result will appear here'}</h2>
            <div role="status" aria-live="polite" aria-atomic="true">
              {result && <p className="text-classifier-category">{BIPOLAR_CATEGORY_COPY[result.category]}</p>}
            </div>
            {!result && <p>Submit all ten responses to see the prototype’s category.</p>}
            {result && <p>The category is not a diagnosis and cannot confirm or rule out bipolar disorder. If you have concerns, speak with a qualified mental-health professional.</p>}
          </section>
        </div>

        <aside className="text-classifier-reminder">
          <p className="eyebrow">BEFORE YOU BEGIN</p>
          <h2>A gentle reminder</h2>
          <p>You can pause or leave at any time. Please avoid entering identifying information; the form only needs the listed responses.</p>
          <hr />
          <h3>About the model</h3>
          <p>This prototype uses a Random Forest trained on a small dataset. Its output may be wrong and is not a substitute for professional assessment.</p>
          <Link className="text-classifier-resource" to="/#resources">Explore support resources ↗</Link>
        </aside>
      </div>
    </main>
  );
}
