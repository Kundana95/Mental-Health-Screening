import { useEffect, useRef, useState } from 'react';
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

  function retakeScreening() {
    setText('');
    setResult(null);
    setError(null);
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
    <main className="assessment-page text-classifier-page container">
      <Link className="text-classifier-back" to="/">← Back to home</Link>
      <header className="assessment-heading">
        <p className="eyebrow">A THOUGHTFUL SPACE TO CHECK IN</p>
        <h1>Schizophrenia-related Text Screening</h1>
        <p className="screening-quote">“Your experiences deserve to be heard with care and understanding.”</p>
      </header>

      <div className="text-classifier-layout">
        <div className="text-classifier-main">
          <aside className="text-classifier-notice">
            <p>This experimental text screening is not a clinical assessment or diagnosis. A category cannot establish or rule out schizophrenia. For concerns, speak with a qualified mental-health professional.</p>
          </aside>

          <form className="assessment-form text-classifier-form" onSubmit={handleSubmit} noValidate aria-busy={isAnalyzing}>
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
              <h3>Privacy</h3>
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

          {result && <section className="screening-results" aria-labelledby="text-result-heading" ref={resultPanel} tabIndex={-1}>
            <h2 id="text-result-heading">Screening Results</h2>
            <article className="screening-result-card" role="status" aria-live="polite" aria-atomic="true">
              <h3>{CLASSIFICATION_COPY[result.category]}</h3>
            </article>
            <p className="screening-results__disclaimer">This experimental text classification is not a clinical diagnosis and does not determine whether you have a mental-health condition. Seek professional assessment for concerns.</p>
            <button className="button button--outline screening-results__retake" type="button" onClick={retakeScreening}>Retake Screening</button>
          </section>}
        </div>

      </div>
    </main>
  );
}
