import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  ANXIETY_CATEGORIES,
  ANXIETY_CHOICES,
  ANXIETY_QUESTIONS,
  analyzeAnxiety,
  validateAnxietyResponses,
} from '../src/lib/anxiety.js';

test('defines seven feature questions and a 0–3 response mapping', () => {
  assert.equal(ANXIETY_QUESTIONS.length, 7);
  assert.deepEqual(ANXIETY_CHOICES.map(({ value }) => value), [0, 1, 2, 3]);
  assert.equal(validateAnxietyResponses([0, 1, 2, 3, 0, 1, 2]), '');
});

test('rejects incomplete and invalid response arrays', () => {
  for (const answers of [null, [0, 1, 2, 3, 0, 1], [0, 1, 2, 3, 0, 1, 4], [0, 1, 2, 3, 0, 1, true], [0, 1, 2, 3, 0, 1, '2']]) {
    assert.ok(validateAnxietyResponses(answers));
  }
});

test('submits seven unchanged responses and accepts an available category', async (t) => {
  const responses = [0, 1, 2, 3, 0, 1, 2];
  const fetch = t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({ category: 'Moderate Anxiety', limitations: ['not displayed'] }), { status: 200 }));
  assert.deepEqual(await analyzeAnxiety(responses), { category: 'Moderate Anxiety' });
  const [url, options] = fetch.mock.calls[0].arguments;
  assert.equal(url, '/api/anxiety/analyze');
  assert.equal(options.method, 'POST');
  assert.equal(options.cache, 'no-store');
  assert.deepEqual(JSON.parse(options.body), { responses });
});

test('invalid answers never reach the API and service errors stay generic', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch');
  await assert.rejects(analyzeAnxiety([0]), { kind: 'validation' });
  assert.equal(fetch.mock.callCount(), 0);

  for (const body of [
    new Response('{"detail":"private-sentinel"}', { status: 422 }),
    new Response('{"detail":"private-sentinel"}', { status: 503 }),
    new Response('{"category":"unknown"}', { status: 200 }),
    new Response('not json', { status: 200 }),
  ]) {
    fetch.mock.mockImplementation(async () => body);
    await assert.rejects(analyzeAnxiety([0, 1, 2, 3, 0, 1, 2]), (error) => {
      assert.ok(!error.message.includes('private-sentinel'));
      return true;
    });
  }
  assert.deepEqual(ANXIETY_CATEGORIES, ['Minimal Anxiety', 'Mild Anxiety', 'Moderate Anxiety', 'Severe Anxiety']);
});
