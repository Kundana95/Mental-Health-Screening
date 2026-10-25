export const BIPOLAR_QUESTIONS = Object.freeze([
  { key: 'Sadness', label: 'How often do you experience sadness?', choices: ['Seldom', 'Sometimes', 'Usually', 'Most-Often'] },
  { key: 'Euphoric', label: 'How often do you experience euphoric mood?', choices: ['Seldom', 'Sometimes', 'Usually', 'Most-Often'] },
  { key: 'Exhausted', label: 'How often do you feel exhausted?', choices: ['Seldom', 'Sometimes', 'Usually', 'Most-Often'] },
  { key: 'Sleep dissorder', label: 'How often do you experience sleep difficulties?', choices: ['Seldom', 'Sometimes', 'Usually', 'Most-Often'] },
  { key: 'Mood Swing', label: 'Do you experience mood swings?', choices: ['YES', 'NO'] },
  { key: 'Aggressive Response', label: 'Do you have aggressive responses?', choices: ['YES', 'NO'] },
  { key: 'Admit Mistakes', label: 'Do you admit when you make mistakes?', choices: ['YES', 'NO'] },
  { key: 'Overthinking', label: 'Do you tend to overthink?', choices: ['YES', 'NO'] },
  { key: 'Concentration', label: 'Choose your concentration rating (1–8).', min: 1, max: 8 },
  { key: 'Optimisim', label: 'Choose your optimism rating (1–9).', min: 1, max: 9 },
]);

export const BIPOLAR_CATEGORY_COPY = Object.freeze({
  'Bipolar Type 1': 'The experimental model returned the Bipolar Type 1 category for these inputs.',
  'Bipolar Type 2': 'The experimental model returned the Bipolar Type 2 category for these inputs.',
  'No Bipolar Indication': 'The experimental model returned No Bipolar Indication for these inputs. This result cannot rule out bipolar disorder.',
});

export class BipolarApiError extends Error {
  constructor(kind, message) {
    super(message);
    this.name = 'BipolarApiError';
    this.kind = kind;
  }
}

export function validateBipolarAnswers(answers) {
  if (!answers || typeof answers !== 'object' || Array.isArray(answers)) {
    return 'Please answer all ten items.';
  }

  const expectedKeys = new Set(BIPOLAR_QUESTIONS.map(({ key }) => key));
  if (Object.keys(answers).some((key) => !expectedKeys.has(key))) {
    return 'Please use only the listed screening items.';
  }

  for (const question of BIPOLAR_QUESTIONS) {
    const value = answers[question.key];
    if (question.choices) {
      if (!question.choices.includes(value)) return 'Please answer all ten items using the listed choices.';
    } else if (!Number.isInteger(value) || value < question.min || value > question.max) {
      return `Please choose a ${question.min}–${question.max} rating for each numeric item.`;
    }
  }
  return '';
}

export async function analyzeBipolar(answers, { signal } = {}) {
  const validationError = validateBipolarAnswers(answers);
  if (validationError) throw new BipolarApiError('validation', validationError);

  let response;
  try {
    response = await fetch('/api/bipolar/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(answers),
      signal,
      cache: 'no-store',
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new BipolarApiError('unavailable', 'We could not reach the screening service. Please try again in a moment.');
  }

  if (response.status === 422) {
    throw new BipolarApiError('validation', 'Some responses could not be validated. Please review your answers.');
  }
  if ([502, 503, 504].includes(response.status)) {
    throw new BipolarApiError('unavailable', 'Bipolar screening is temporarily unavailable. Please try again later.');
  }
  if (!response.ok) {
    throw new BipolarApiError('service', 'We could not analyze these responses. Please try again in a moment.');
  }

  let result;
  try {
    result = await response.json();
  } catch {
    throw new BipolarApiError('service', 'We could not read the screening result. Please try again.');
  }
  if (!result || !Object.hasOwn(BIPOLAR_CATEGORY_COPY, result.category)) {
    throw new BipolarApiError('service', 'We could not read the screening result. Please try again.');
  }
  return { category: result.category };
}
