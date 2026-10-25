const SEVERITY_LABELS = {
  'PHQ-9': ['Minimal', 'Mild', 'Moderate', 'Moderately severe', 'Severe'],
  'GAD-7': ['Minimal', 'Mild', 'Moderate', 'Severe'],
};

const MAX_SCORES = { 'PHQ-9': 27, 'GAD-7': 21 };

/** Read the existing server-calculated depression screening summaries. */
export function parseDepressionResults(payload) {
  const source = payload?.questionnaire_results;
  const results = {};

  for (const id of ['PHQ-9', 'GAD-7']) {
    const result = source?.[id];
    if (
      !result ||
      !Number.isInteger(result.total_score) ||
      result.total_score < 0 ||
      result.total_score > MAX_SCORES[id] ||
      !SEVERITY_LABELS[id].includes(result.severity)
    ) {
      const error = new Error('The assessment service returned an invalid result.');
      error.kind = 'response';
      throw error;
    }
    results[id] = { total_score: result.total_score, severity: result.severity };
  }

  if (payload?.status !== 'received') {
    const error = new Error('The assessment service returned an invalid result.');
    error.kind = 'response';
    throw error;
  }
  return results;
}

/** Submit answers without retaining them and return only validated score summaries. */
export async function submitDepressionAssessment(payload) {
  let response;
  try {
    response = await fetch('/api/depression/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      cache: 'no-store',
    });
  } catch {
    const error = new Error('The assessment service is unavailable.');
    error.kind = 'network';
    throw error;
  }

  if (!response.ok) {
    const error = new Error('The assessment service could not process the submission.');
    error.kind = response.status === 422 ? 'validation' : 'service';
    throw error;
  }

  let responseBody;
  try {
    responseBody = await response.json();
  } catch {
    const error = new Error('The assessment service returned an invalid result.');
    error.kind = 'response';
    throw error;
  }
  return parseDepressionResults(responseBody);
}
