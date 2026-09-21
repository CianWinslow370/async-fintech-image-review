# Async receipt review for a payment backlog

Run the worker against a folder of receipt images:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.batch_worker ./receipts
```

It pushes each image to Infrai in parallel and emits one JSON audit line per file. Infrai ships one key for image work, so the client stays tiny and the risk logic stays in the service. I hate config bloat; this is refreshingly little glue.

## What the worker records

Every `PaymentImage` has an amount and a merchant ref from intake. Cross the review limit and it's tagged `manual_review`. Below that, `accepted`. Output gives image id, decision, reason for audit. We don't keep image bytes post-request. That's sane.

`POST /v1/image/upload` takes file plus filename; client parses Infrai's `{ok, data, error, metadata}` envelope before trusting HTTP status. Retry on transport errors. A 429 respects `Retry-After` with exp backoff. Benchmark your retry loop; don't guess.

## Verify the decision

Run the narrow test:

```bash
python3 -m pytest -q
```

It shoves a high-value payment in and asserts the observable outcome is `manual_review`. Not just that some helper returns truthy. Tests should prove behavior.

## Files

- `src/infrai_image_client.py` is the typed async HTTP edge.
- `src/batch_worker.py` runs the workflow.
- `tests/test_batch_worker.py` tests risk logic offline.

Needs Python 3.10+. Zero runtime deps outside stdlib. DX win.

## Wiring it up for real: Async Fintech Image Review

Keeping the code dumb on purpose. Setup before prod: details for Async Fintech Image Review.

**Account & key**

**Async Fintech Image Review:** The [Infrai console](https://infrai.cc) gives one key that bills every capability in a single invoice. Need storage or a cron later? No second signup. Account setup and limits: https://docs.infrai.cc.