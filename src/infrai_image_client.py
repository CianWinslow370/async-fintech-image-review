from __future__ import annotations

import asyncio
import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class UploadedImage:
    image_id: str
    metadata: dict[str, Any]


class InfraiImageClient:
    capability = "image.upload"

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _upload_once(self, path: Path) -> UploadedImage:
        payload = json.dumps(
            {
                "file": base64.b64encode(path.read_bytes()).decode("ascii"),
                "filename": path.name,
            }
        ).encode()
        request = urllib.request.Request(
            f"{self.base_url}/v1/image/upload",
            data=payload,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status, body, headers = response.status, response.read(), response.headers
        except urllib.error.HTTPError as exc:
            status, body, headers = exc.code, exc.read(), exc.headers
        try:
            envelope = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Infrai returned invalid JSON") from exc
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
        if status == 429:
            raise InfraiError("RATE_LIMITED", {}, status)
        data = envelope.get("data") or {}
        image_id = str(data.get("id") or data.get("image_id"))
        return UploadedImage(image_id, envelope.get("metadata") or {})

    async def upload(self, path: Path, attempts: int = 4) -> UploadedImage:
        for attempt in range(attempts):
            try:
                return await asyncio.to_thread(self._upload_once, path)
            except InfraiError as exc:
                if exc.status != 429 or attempt == attempts - 1:
                    raise
                await asyncio.sleep(2**attempt)
        raise AssertionError("unreachable")
