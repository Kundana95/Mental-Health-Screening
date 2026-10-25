import assert from 'node:assert/strict';
import { test } from 'node:test';
import { parseDepressionResults, submitDepressionAssessment } from '../src/lib/depression.js';

const validResponse = {
  status: 'received',
  message: 'Your responses were received.',
  questionnaire_results: {
    'PHQ-9': { total_score: 7, severity: 'Mild' },
    'GAD-7': { total_score: 5, severity: 'Mild' },
  },
};

test('accepts and preserves the actual independent server-calculated results', () => {
  assert.deepEqual(parseDepressionResults(validResponse), {
    'PHQ-9': { total_score: 7, severity: 'Mild' },
    'GAD-7': { total_score: 5, severity: 'Mild' },
  });
});

test('rejects missing, malformed, out-of-range, and unknown severity results', () => {
  const malformed = [
    null,
    {},
    { ...validResponse, questionnaire_results: { 'PHQ-9': validResponse.questionnaire_results['PHQ-9'] } },
    { ...validResponse, questionnaire_results: { ...validResponse.questionnaire_results, 'PHQ-9': { total_score: 28, severity: 'Severe' } } },
    { ...validResponse, questionnaire_results: { ...validResponse.questionnaire_results, 'GAD-7': { total_score: 5, severity: 'unknown' } } },
    { ...validResponse, status: 'error' },
  ];
  for (const payload of malformed) {
    assert.throws(() => parseDepressionResults(payload), { kind: 'response' });
  }
});

test('submits the payload to the depression endpoint and returns parsed scores', async (t) => {
  const payload = { phq9_responses: Array(9).fill(0), gad7_responses: Array(7).fill(0), context_answers: {} };
  const fetch = t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify(validResponse), { status: 200 }));
  assert.deepEqual(await submitDepressionAssessment(payload), parseDepressionResults(validResponse));
  const [url, options] = fetch.mock.calls[0].arguments;
  assert.equal(url, '/api/depression/submit');
  assert.equal(options.method, 'POST');
  assert.equal(options.cache, 'no-store');
  assert.deepEqual(JSON.parse(options.body), payload);
});

test('maps validation, service, malformed response, and network errors safely', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch');
  fetch.mock.mockImplementation(async () => new Response('{"detail":"private-sentinel"}', { status: 422 }));
  await assert.rejects(submitDepressionAssessment({}), (error) => error.kind === 'validation' && !error.message.includes('private-sentinel'));
  fetch.mock.mockImplementation(async () => new Response('{}', { status: 500 }));
  await assert.rejects(submitDepressionAssessment({}), { kind: 'service' });
  fetch.mock.mockImplementation(async () => new Response('not json', { status: 200 }));
  await assert.rejects(submitDepressionAssessment({}), { kind: 'response' });
  fetch.mock.mockImplementation(async () => { throw new Error('private-sentinel'); });
  await assert.rejects(submitDepressionAssessment({}), (error) => error.kind === 'network' && !error.message.includes('private-sentinel'));
});
