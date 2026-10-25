import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  analyzeBipolar,
  BIPOLAR_CATEGORY_COPY,
  BIPOLAR_QUESTIONS,
  validateBipolarAnswers,
} from '../src/lib/bipolar.js';

function validAnswers() {
  return {
    Sadness: 'Seldom',
    Euphoric: 'Sometimes',
    Exhausted: 'Usually',
    'Sleep dissorder': 'Most-Often',
    'Mood Swing': 'YES',
    'Aggressive Response': 'NO',
    'Admit Mistakes': 'YES',
    Overthinking: 'NO',
    Concentration: 4,
    Optimisim: 5,
  };
}

test('defines ten model inputs and validates a complete supported response set', () => {
  assert.equal(BIPOLAR_QUESTIONS.length, 10);
  assert.equal(validateBipolarAnswers(validAnswers()), '');
});

test('rejects missing, extra, invalid category, and out-of-range numeric answers', () => {
  const incomplete = validAnswers();
  delete incomplete.Sadness;
  assert.ok(validateBipolarAnswers(incomplete));

  assert.ok(validateBipolarAnswers({ ...validAnswers(), unexpected: 'value' }));
  assert.ok(validateBipolarAnswers({ ...validAnswers(), Sadness: 'Rarely' }));
  assert.ok(validateBipolarAnswers({ ...validAnswers(), Concentration: 9 }));
  assert.ok(validateBipolarAnswers({ ...validAnswers(), Optimisim: 10 }));
  assert.ok(validateBipolarAnswers({ ...validAnswers(), Optimisim: 3.5 }));
});

test('valid requests send values unchanged and expose only the supported category', async (t) => {
  const answers = validAnswers();
  const fetch = t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({
    category: 'Bipolar Type 2',
    message: 'private response text',
    limitations: ['screening only'],
    probability: 0.99,
  }), { status: 200 }));
  assert.deepEqual(await analyzeBipolar(answers), { category: 'Bipolar Type 2' });
  const [url, options] = fetch.mock.calls[0].arguments;
  assert.equal(url, '/api/bipolar/analyze');
  assert.equal(options.method, 'POST');
  assert.equal(options.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(options.body), answers);
  assert.equal(options.cache, 'no-store');
});

test('invalid answers never reach the API', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => {
    throw new Error('Should not be called');
  });
  await assert.rejects(analyzeBipolar({}), { kind: 'validation' });
  assert.equal(fetch.mock.callCount(), 0);
});

for (const [status, kind] of [[422, 'validation'], [503, 'unavailable'], [502, 'unavailable'], [504, 'unavailable'], [500, 'service']]) {
  test('maps HTTP ' + status + ' to a safe client error', async (t) => {
    t.mock.method(globalThis, 'fetch', async () => new Response('{"detail":"private-sentinel"}', { status }));
    await assert.rejects(analyzeBipolar(validAnswers()), (error) => {
      assert.equal(error.kind, kind);
      assert.ok(!error.message.includes('private-sentinel'));
      return true;
    });
  });
}

test('unknown categories and malformed JSON do not become a supported result', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch');
  for (const body of ['{}', 'null', '{"category":"unknown"}', 'not JSON']) {
    fetch.mock.mockImplementation(async () => new Response(body, { status: 200 }));
    await assert.rejects(analyzeBipolar(validAnswers()), { kind: 'service' });
  }
  assert.deepEqual(Object.keys(BIPOLAR_CATEGORY_COPY).sort(), [
    'Bipolar Type 1', 'Bipolar Type 2', 'No Bipolar Indication',
  ].sort());
});
