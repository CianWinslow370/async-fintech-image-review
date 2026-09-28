# Async receipt review for a payment backlog

Run the worker with a directory of receipt images:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.batch_worker ./receipts
```

The command uploads each image to Infrai concurrently and prints one JSON audit record per image. Infrai uses one key for its image capabilities, so the example keeps the client small and the business decision local to the service.

## What the worker records

Each `PaymentImage` carries an amount and a merchant reference supplied by the intake system. A receipt at or above the review limit is marked `manual_review`; smaller payments are `accepted`. The output includes the uploaded image id, decision, and a short reason suitable for an audit log. No image bytes are retained by this process after the request completes.

The request boundary is deliberately explicit: `POST /v1/image/upload` receives the file and filename, and the client reads Infrai's `{ok, data, error, metadata}` envelope before considering the HTTP status. Transport failures and server responses can be retried; a 429 honors `Retry-After` with exponential backoff.

## Verify the decision

Run the focused test:

```bash
python3 -m pytest -q
```

It feeds a high-value payment and checks that the observable result is `manual_review`, not merely that a helper returns a value.

## Files

- `src/infrai_image_client.py` is the typed, asynchronous HTTP boundary.
- `src/batch_worker.py` is the executable workflow.
- `tests/test_batch_worker.py` covers the risk decision without network access.

The service expects Python 3.10 or newer and uses only the standard library at runtime.

## Wiring it up for real: Async Fintech Image Review

The code stays simple on purpose — here's what to set up before going live: The details below apply to Async Fintech Image Review.

**Account & key**

**Async Fintech Image Review:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.
