export const ANXIETY_QUESTIONS = Object.freeze([
  '1. In a semester, how often you felt nervous, anxious or on edge due to academic pressure? ',
  '2. In a semester, how often have you been unable to stop worrying about your academic affairs? ',
  '3. In a semester, how often have you had trouble relaxing due to academic pressure? ',
  '4. In a semester, how often have you been easily annoyed or irritated because of academic pressure?',
  '5. In a semester, how often have you worried too much about academic affairs? ',
  '6. In a semester, how often have you been so restless due to academic pressure that it is hard to sit still?',
  '7. In a semester, how often have you felt afraid, as if something awful might happen?',
]);

export const ANXIETY_CHOICES = Object.freeze([
  { label: 'Not at all', value: 0 },
  { label: 'Several days', value: 1 },
  { label: 'More than half the days', value: 2 },
  { label: 'Nearly every day', value: 3 },
]);

export const ANXIETY_CATEGORIES = Object.freeze([
  'Minimal Anxiety',
  'Mild Anxiety',
  'Moderate Anxiety',
  'Severe Anxiety',
]);

export function validateAnxietyResponses(responses) {
  if (!Array.isArray(responses) || responses.length !== 7) {
    return 'Please answer all seven questions.';
  }
  if (responses.some((value) => !Number.isInteger(value) || value < 0 || value > 3)) {
    return 'Choose one of the listed answers for each question.';
  }
  return '';
}

export class AnxietyApiError extends Error {
  constructor(kind, message) {
    super(message);
    this.name = 'AnxietyApiError';
    this.kind = kind;
  }
}

export async function analyzeAnxiety(responses, { signal } = {}) {
  const validationError = validateAnxietyResponses(responses);
  if (validationError) throw new AnxietyApiError('validation', validationError);

  let response;
  try {
    response = await fetch('/api/anxiety/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ responses }),
      signal,
      cache: 'no-store',
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new AnxietyApiError('unavailable', 'We could not reach the screening service. Please try again in a moment.');
  }

  if (response.status === 422) {
    throw new AnxietyApiError('validation', 'Some answers could not be validated. Please review your responses.');
  }
  if ([502, 503, 504].includes(response.status)) {
    throw new AnxietyApiError('unavailable', 'Anxiety screening is temporarily unavailable. Please try again later.');
  }
  if (!response.ok) {
    throw new AnxietyApiError('service', 'The screening estimate could not be generated. Please try again.');
  }

  let result;
  try {
    result = await response.json();
  } catch {
    throw new AnxietyApiError('service', 'We could not read the screening result. Please try again.');
  }
  if (!result || !ANXIETY_CATEGORIES.includes(result.category)) {
    throw new AnxietyApiError('service', 'We could not read the screening result. Please try again.');
  }
  return { category: result.category };
}
