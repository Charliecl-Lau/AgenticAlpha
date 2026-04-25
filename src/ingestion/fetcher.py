import time
import random
import requests

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AgenticAlpha/1.0; research-only)"
}
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0   # seconds; doubles each retry


class PdfSkipError(RuntimeError):
    """Raised when a URL resolves to a PDF — pipeline should log and skip."""


def fetch_page(url: str, timeout: int = 30) -> str:
    if url.lower().endswith(".pdf"):
        raise PdfSkipError(f"PDF URL skipped (no PDF parser in stack): {url}")

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=timeout)
            content_type = resp.headers.get("Content-Type", "")
            if "application/pdf" in content_type:
                raise PdfSkipError(f"PDF content-type at {url} — skipped")
            if resp.status_code == 200:
                return resp.text
            last_exc = RuntimeError(f"HTTP {resp.status_code} fetching {url}")
        except PdfSkipError:
            raise
        except Exception as exc:
            last_exc = exc

        if attempt < _MAX_RETRIES - 1:
            sleep_secs = _BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(sleep_secs)

    raise last_exc  # type: ignore[misc]
