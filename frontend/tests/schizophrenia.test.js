import assert from 'node:assert/strict';
import { test } from 'node:test';
import { analyzeText, CLASSIFICATION_COPY, validateText } from '../src/lib/schizophrenia.js';

test('blank and over-limit text are rejected, using Python-compatible Unicode character counts', () => {
  for (const text of ['', ' \n\t', null, 42]) assert.ok(validateText(text));
  assert.ok(validateText('a'.repeat(4001)));
  assert.equal(validateText('a'.repeat(4000)), '');
  assert.equal(validateText('🌿'.repeat(4000)), '');
  assert.ok(validateText('🌿'.repeat(4001)));
});

test('invalid text never reaches the network', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch', async () => { throw new Error('Should not be called'); });
  await assert.rejects(analyzeText('  '), { kind: 'validation' });
  assert.equal(fetch.mock.callCount(), 0);
});

for (const category of Object.keys(CLASSIFICATION_COPY)) {
  test(`posts unchanged text and accepts ${category}, exposing only the category`, async (t) => {
    const controller = new AbortController();
    const text = '  Example paragraph with café and 🌿.  ';
    const fetch = t.mock.method(globalThis, 'fetch', async () => new Response(JSON.stringify({
      category, model_id: 'test', limitations: ['test'], unexpected: 'private-sentinel', probability: 0.99,
    }), { status: 200 }));
    assert.deepEqual(await analyzeText(text, { signal: controller.signal }), { category });
    const [url, options] = fetch.mock.calls[0].arguments;
    assert.equal(url, '/api/schizophrenia/analyze');
    assert.equal(options.method, 'POST');
    assert.equal(options.headers['Content-Type'], 'application/json');
    assert.deepEqual(JSON.parse(options.body), { text });
    assert.equal(options.signal, controller.signal);
    assert.equal(options.cache, 'no-store');
  });
}

for (const [status, kind] of [[422, 'validation'], [413, 'validation'], [503, 'unavailable'],
  [502, 'unavailable'], [504, 'unavailable'], [500, 'service']]) {
  test(`handles HTTP ${status} without exposing server details`, async (t) => {
    t.mock.method(globalThis, 'fetch', async () => new Response('{"detail":"private-sentinel"}', { status }));
    await assert.rejects(analyzeText('example text'), (error) => {
      assert.equal(error.kind, kind);
      assert.ok(!error.message.includes('private-sentinel'));
      return true;
    });
  });
}

test('network failures show an unavailable state without exposing internal errors', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new Error('private-sentinel'); });
  await assert.rejects(analyzeText('example text'), (error) => error.kind === 'unavailable' && !error.message.includes('private-sentinel'));
});

test('abort propagates so navigation and timeouts can cancel pending requests', async (t) => {
  const error = new DOMException('Aborted', 'AbortError');
  t.mock.method(globalThis, 'fetch', async () => { throw error; });
  await assert.rejects(analyzeText('example text'), { name: 'AbortError' });
});

test('unknown categories, missing results, and invalid JSON cannot become a general result', async (t) => {
  const fetch = t.mock.method(globalThis, 'fetch');
  for (const body of ['{}', 'null', '{"category":"unknown"}', '{"category":"constructor"}', 'not JSON']) {
    fetch.mock.mockImplementation(async () => new Response(body, { status: 200 }));
    await assert.rejects(analyzeText('example text'), { kind: 'service' });
  }
});
