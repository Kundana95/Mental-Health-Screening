# Schizophrenia route: experimental Reddit community classifier

This backend classifies text into Reddit community categories. It is not a
clinical questionnaire, diagnosis, risk estimate, probability, or crisis detector.
Neither category establishes or rules out schizophrenia. Anxiety, addiction,
and other mental-health text may be misclassified.

## Setup

Use Python 3.13 and an isolated environment. From the repository root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ml.txt
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

`requirements-ml.txt` includes the API and test dependencies. Gensim 4.4.0 and
scikit-learn 1.6.1 match the saved metadata. The remaining pinned ML versions are
a compatible local environment, not a recovered original Colab environment.
The original Word2Vec metadata records Python 3.13.16 on Linux; local parity is
checked on Windows Python 3.13. Do not use the default Python 3.14 environment
with a different scikit-learn version to deserialize this pipeline.

## Trusted local artifacts

The owner explicitly confirmed that these exports came from their own Colab
session. Keep them at the fixed repository-relative paths:

- `local_models/word2vec_zenodo.model`
- `local_models/svm_word2vec_classifier.pkl`

Both Word2Vec loading and joblib loading use pickle-based serialization. The
loader verifies both files against the inspected SHA-256 hashes in
`classifier.py` before deserialization and checks the Gensim/scikit-learn
versions. These hashes identify the reviewed exports; hashes do not establish
the safety of arbitrary files. Do not update the allowlist for untrusted files.
The API accepts no artifact paths or uploads. Keep the local files controlled by
the owner. New exports require review and a deliberate hash update.

Models load lazily on the first valid request and are cached once per worker.
Failed loads are not cached, allowing a later request to retry after dependencies
or files are restored. Missing ML dependencies do not prevent the depression API
from importing or operating. Restart workers after intentionally replacing models.

`local_models/` and `modules/sctizo.ipynb` are excluded from Git. No model or
notebook contents are copied into tracked fixtures.

## HTTP contract

`POST /api/schizophrenia/analyze`, `Content-Type: application/json`:

```json
{"text": "I am planning my budget and saving money for rent."}
```

`text` is a strict string, nonblank, at most 4,000 characters. Unexpected fields
are rejected. The API's existing 16 KiB request-body and trusted-host limits also
apply. Input text is not intentionally persisted, logged, or echoed in results.

Successful response (the category below is illustrative):

```json
{
  "category": "general_community",
  "model_id": "reddit-word2vec-linearsvc-2026-10-24",
  "limitations": [
    "Experimental Reddit community text classification; not a diagnosis or clinical screening result.",
    "Anxiety, addiction, and other mental-health text may be misclassified.",
    "Neither category establishes or rules out schizophrenia; no clinical risk or probability is estimated."
  ]
}
```

- `general_community`: original model label 0, from personalfinance,
  relationships, meditation, and teaching community posts.
- `schizophrenia_community`: original model label 1, from schizophrenia
  community posts. Community membership is not a verified diagnosis.
- No score, severity, probability, submitted text, or user identifiers are returned.
- `422`: missing/invalid text, malformed JSON, unexpected fields, or no recognized
  tokens. Validation errors do not echo supplied values.
- `413`: request body exceeds the existing API limit.
- `503`: absent, changed, incompatible, or unreadable models/dependencies.
- `500`: unexpected inference/output error, with a generic message.

## Exact inference method

1. `gensim.utils.simple_preprocess(str(text))`, with unmodified defaults:
   lowercase, `deacc=False`, `min_len=2`, `max_len=15`; no custom stopwords,
   stemming, lemmatization, or URL cleaning.
2. Keep raw `model.wv[token]` vectors for known tokens, including repeated tokens.
3. `np.mean(vectors, axis=0)` gives 100 features; no weighting or normalization.
4. `pipeline.predict(vector.reshape(1, -1))`, using the saved fitted
   `StandardScaler` followed by fitted `LinearSVC`. Never add another scaler.

The intentional deviation from the notebook is rejecting empty/no-vocabulary
input instead of sending a zero vector to the classifier. There is no fitting,
training, score calibration, or adjustment of outputs in the backend.

## Verification

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
$env:RUN_LOCAL_MODEL_TESTS = '1'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
Remove-Item Env:RUN_LOCAL_MODEL_TESTS
```

The default suite uses synthetic vectors and mocked API inference; the two
local reference tests are skipped unless explicitly enabled. Enabling them
loads only the trusted, hash-checked artifacts and reads notebook JSON without
executing its cells. It compares exact vectors and predictions for six synthetic
examples, checks actual HTTP responses, verifies no-vocabulary rejection, and
reproduces the historical prediction saved with the notebook's original
single-model input example. Private example text is never printed or committed.

These checks establish implementation parity, not clinical validity or general
classification performance. The notebook reports 93.84% held-out accuracy, but
that evaluation used general-community negatives rather than a dedicated
anxiety/addiction challenge set. The original split datasets, full environment
export, and independent false-positive evaluation remain needed before deciding
whether broader user-facing use is appropriate. No frontend is integrated in
this stage.

## Stage 1 verification results

On 2026-10-25, all 62 backend tests passed with `RUN_LOCAL_MODEL_TESTS=1`
(43 existing tests and 19 new tests, including both local reference tests).
Exact vectors and categories matched the notebook calculation for six synthetic
inputs; the original saved Colab example reproduced its historical label 1.
An additional unmocked TestClient smoke check exercised the actual lazy loader:
the budget example returned `general_community`; the psychiatrist, anxiety, and
alcohol-support examples returned `schizophrenia_community`. The latter two
illustrate topic confusion, not evidence of a person's diagnosis. Empty,
whitespace, numeric-only, and unknown-vocabulary inputs returned 422.

`pip check` found no broken requirements. The original artifacts' hashes were
unchanged, Git exclusions were verified, and `git diff --check` passed. Neither
frontend files nor depression scoring files changed. These checks do not replace
the missing dataset-level false-positive evaluation. Starlette's TestClient emits
an httpx deprecation notice in this environment; all HTTP assertions pass.
