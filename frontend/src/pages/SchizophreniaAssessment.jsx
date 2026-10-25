import { useEffect, useRef, useState } from 'react';
import AbstractIllustration from '../components/AbstractIllustration.jsx';
import { Link } from '../components/SiteLink.jsx';
import { analyzeText, CLASSIFICATION_COPY, MAX_TEXT_LENGTH, validateText } from '../lib/schizophrenia.js';

export default function SchizophreniaAssessment() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const request = useRef(null);
  const textarea = useRef(null);
  const resultPanel = useRef(null);
  const characterCount = Array.from(text).length;

  useEffect(() => () => {
    request.current?.abort();
    request.current = null;
  }, []);

  useEffect(() => {
    if (result) resultPanel.current?.focus();
  }, [result]);

  function updateText(event) {
    setText(event.target.value);
    setResult(null);
    setError(null);
  }

  function clearText() {
    setText('');
    setResult(null);
    setError(null);
    textarea.current?.focus();
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (request.current) return;
    setResult(null);
    const validationError = validateText(text);
    if (validationError) {
      setError({ kind: 'validation', message: validationError });
      textarea.current?.focus();
      return;
    }

    const controller = new AbortController();
    request.current = controller;
    setError(null);
    setIsAnalyzing(true);
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 30000);

    try {
      const analysis = await analyzeText(text, { signal: controller.signal });
      if (request.current === controller) setResult(analysis);
    } catch (failure) {
      if (request.current !== controller) return;
      setError(timedOut
        ? { kind: 'unavailable', message: 'Text analysis took too long. Please try again in a moment.' }
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
    <main className="text-classifier-page container">
      <Link className="text-classifier-back" to="/">← Back to home</Link>
      <header className="text-classifier-heading">
        <div>
          <p className="eyebrow">A SPACE FOR YOUR OWN WORDS</p>
          <h1>Schizophrenia-related text classifier</h1>
          <p>Explore how a paragraph is categorized by a model trained on Reddit posts.</p>
          <span className="pill">Experimental · Educational project</span>
        </div>
        <AbstractIllustration tone="sage" compact />
      </header>

      <div className="text-classifier-layout">
        <div className="text-classifier-main">
          <aside className="text-classifier-notice">
            <h2>Your words are more than a classification</h2>
            <p>This is an experimental Reddit text classifier, not a clinical assessment or diagnosis. A category cannot establish or rule out schizophrenia.</p>
          </aside>

          <form className="assessment-form text-classifier-form" onSubmit={handleSubmit} noValidate aria-busy={isAnalyzing}>
            <p className="eyebrow">AN OPEN SPACE</p>
            <h2>What would you like to share?</h2>
            <p className="text-classifier-intro">Enter a paragraph in your own words. Share only what you feel comfortable sending for analysis.</p>
            <label htmlFor="schizophrenia-text">Your paragraph</label>
            <textarea
              ref={textarea}
              id="schizophrenia-text"
              value={text}
              onChange={updateText}
              placeholder="Write your paragraph here…"
              rows={9}
              required
              disabled={isAnalyzing}
              autoComplete="off"
              spellCheck={false}
              aria-describedby={`text-character-count text-privacy${error?.kind === 'validation' ? ' text-analysis-error' : ''}`}
              aria-invalid={error?.kind === 'validation' || characterCount > MAX_TEXT_LENGTH ? true : undefined}
            />
            <p id="text-character-count" className={`text-character-count${characterCount > MAX_TEXT_LENGTH ? ' text-character-count--invalid' : ''}`}>
              {characterCount.toLocaleString('en-US')} / 4,000 characters
            </p>
            <div className="text-classifier-privacy" id="text-privacy">
              <h3>Before you write</h3>
              <p>Your text is sent to the analysis service when you select Analyze Text. It stays in this page’s memory until you clear it or leave. Mindful does not save it in browser storage or retain submissions in the backend. Avoid names, contact details, and other identifying information.</p>
            </div>
            <div className="text-classifier-actions">
              <button className="button button--primary" type="submit" disabled={isAnalyzing}>
                {isAnalyzing ? 'Analyzing…' : 'Analyze Text'}
              </button>
              <button className="button button--outline" type="button" onClick={clearText} disabled={isAnalyzing || !text}>
                Clear text
              </button>
            </div>
            {isAnalyzing && <p className="text-classifier-progress" role="status">Analyzing your text. This may take a moment.</p>}
          </form>

          {error && (
            <div className="assessment-message assessment-message--error" id="text-analysis-error" role="alert">
              <h2>{error.kind === 'validation' ? 'Please review your text' : error.kind === 'unavailable' ? 'Analysis unavailable' : 'Analysis could not be completed'}</h2>
              <p>{error.message}</p>
            </div>
          )}

          <section className={`text-classifier-result${result ? ' text-classifier-result--ready' : ''}`} aria-labelledby="text-result-heading" ref={resultPanel} tabIndex={-1}>
            <p className="eyebrow">{result ? 'TEXT ANALYSIS COMPLETE' : 'YOUR TEXT CLASSIFICATION'}</p>
            <h2 id="text-result-heading">{result ? 'A category for the text' : 'A space for your result'}</h2>
            <div role="status" aria-live="polite" aria-atomic="true">
              {result && <p className="text-classifier-category">{CLASSIFICATION_COPY[result.category]}</p>}
            </div>
            {!result && <p>Your Reddit text category will appear here after analysis.</p>}
            {result && (
              <>
                <p>This describes a pattern learned from Reddit community posts. It does not determine whether you have a mental-health condition.</p>
                <p className="text-classifier-next-step">If you are concerned about your experiences, consider talking with a qualified mental-health professional.</p>
              </>
            )}
          </section>
        </div>

        <aside className="text-classifier-reminder">
          <p className="eyebrow">BEFORE YOU BEGIN</p>
          <h2>A gentle reminder</h2>
          <p>You do not have to share everything. Take your time, and pause whenever you need to.</p>
          <hr />
          <h3>What the model learned</h3>
          <p>It compares language patterns from schizophrenia-related and general Reddit communities. These community labels are not verified diagnoses.</p>
          <p>Anxiety and addiction topics can be confused with the schizophrenia-related category.</p>
          <Link className="text-classifier-resource" to="/#resources">Explore support resources ↗</Link>
        </aside>
      </div>
    </main>
  );
}
