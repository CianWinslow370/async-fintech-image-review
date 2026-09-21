from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from .infrai_image_client import InfraiImageClient


@dataclass(frozen=True)
class PaymentImage:
    path: Path
    merchant: str
    amount_cents: int


@dataclass(frozen=True)
class AuditRecord:
    filename: str
    image_id: str
    decision: str
    reason: str


def decide(amount_cents: int, review_limit_cents: int = 100_000) -> tuple[str, str]:
    if amount_cents >= review_limit_cents:
        return "manual_review", "amount meets the review threshold"
    return "accepted", "amount is below the review threshold"


async def process_one(item: PaymentImage, client: InfraiImageClient) -> AuditRecord:
    uploaded = await client.upload(item.path)
    decision, reason = decide(item.amount_cents)
    return AuditRecord(item.path.name, uploaded.image_id, decision, reason)


async def run(directory: Path) -> list[AuditRecord]:
    client = InfraiImageClient()
    items = [PaymentImage(path, path.stem.split("-")[0], int(path.stem.split("-")[-1])) for path in sorted(directory.iterdir()) if path.is_file()]
    return await asyncio.gather(*(process_one(item, client) for item in items))


def main() -> None:
    records = asyncio.run(run(Path(sys.argv[1] if len(sys.argv) > 1 else "receipts")))
    for record in records:
        print(json.dumps(asdict(record), sort_keys=True))


if __name__ == "__main__":
    main()
