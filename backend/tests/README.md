# Tests

Your acceptance criteria are the specification, and CI runs them.

## Write your first test in under two minutes

Everything you need is a fixture. No Qdrant, no Postgres, no network.

```python
def test_the_threshold_question_finds_the_right_policy(loaded_store, model):
    query = model.embed(["What is the approval threshold?"])[0]
    hits = loaded_store.search(query, limit=1)

    assert hits[0].document_id == "travel-expense-policy"
```

## The fixtures

| | |
|---|---|
| `client` | the API, loaded, for asserting on real responses |
| `store` | an empty in-memory vector store |
| `loaded_store` | the same, with three passages already in it |
| `model` | a model that never touches the network |
| `failing_model` | a model that is always unreachable |
| `passages` | three embedded passages about different things |
| `sample_corpus` | three tiny policy documents on disk |

## The two that matter most

**A refusal must not call the model.**

```python
def test_refusal(loaded_store, model):
    # ... your code decides there is nothing good enough ...
    assert not model.was_called
```

`model.was_called` is the whole assertion. If retrieval found nothing and the
model was still called, the product will invent an answer — which is the exact
failure it exists to prevent.

**Degraded mode, without unplugging anything.**

```python
def test_degraded(loaded_store, failing_model):
    # ... your code catches ProviderError and returns passages, no answer ...
```

Use `failing_model`. A degraded mode nobody can test is a degraded mode nobody
has tested.

## Running them

```bash
pytest -q                          # all of them
pytest -q tests/test_ingest.py     # one file
pytest -q -k refusal               # anything matching
```

CI runs `pytest -q`, `ruff check`, `bandit -r app/ -ll` and the licence check.
All four must pass before your pull request can merge.
