export const MAX_TEXT_LENGTH = 4000;

export const CLASSIFICATION_COPY = Object.freeze({
  schizophrenia_community: 'Text resembles the schizophrenia-related Reddit category.',
  general_community: 'Text resembles the general Reddit category.',
});

export class TextAnalysisError extends Error {
  constructor(kind, message) {
    super(message);
    this.name = 'TextAnalysisError';
    this.kind = kind;
  }
}

export function validateText(text) {
  if (typeof text !== 'string' || !text.trim()) {
    return 'Enter a paragraph before analyzing your text.';
  }
  if (Array.from(text).length > MAX_TEXT_LENGTH) {
    return `Use no more than ${MAX_TEXT_LENGTH.toLocaleString('en-US')} characters.`;
  }
  return '';
}

export async function analyzeText(text, { signal } = {}) {
  const validationError = validateText(text);
  if (validationError) throw new TextAnalysisError('validation', validationError);

  let response;
  try {
    response = await fetch('/api/schizophrenia/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
      signal,
      cache: 'no-store',
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new TextAnalysisError('unavailable', 'We could not reach the text analysis service. Please try again in a moment.');
  }

  if (response.status === 422) {
    throw new TextAnalysisError('validation', 'The text could not be classified. Include recognizable words and use no more than 4,000 characters.');
  }
  if (response.status === 413) {
    throw new TextAnalysisError('validation', 'This submission is too large. Shorten your paragraph and try again.');
  }
  if ([502, 503, 504].includes(response.status)) {
    throw new TextAnalysisError('unavailable', 'Text analysis is temporarily unavailable. Please try again later.');
  }
  if (!response.ok) {
    throw new TextAnalysisError('service', 'We could not analyze your text. Please try again in a moment.');
  }

  let result;
  try {
    result = await response.json();
  } catch {
    throw new TextAnalysisError('service', 'We could not read the analysis result. Please try again.');
  }
  if (!result || !Object.hasOwn(CLASSIFICATION_COPY, result.category)) {
    throw new TextAnalysisError('service', 'We could not read the analysis result. Please try again.');
  }
  // Only pass the supported category to the view. Never render arbitrary server
  // messages, clinical scores, or submitted text as part of the result.
  return { category: result.category };
}
