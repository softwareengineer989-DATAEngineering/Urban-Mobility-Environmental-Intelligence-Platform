from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

USER_AGENT = "urban-mobility-environmental-intelligence-platform/phase1"

RETRY_COUNT = 8
RETRY_BACKOFF_SECONDS = 5
OPENAQ_REQUEST_DELAY_SECONDS = 1.0


class OpenAQRequestError(RuntimeError):
    """OpenAQ API request failure with an HTTP status code."""

    def __init__(
        self,
        status_code: int,
        url: str,
        original_error: Exception,
    ) -> None:
        self.status_code = status_code
        self.url = url
        self.original_error = original_error

        super().__init__(f"OpenAQ API request failed with HTTP {status_code}: {url}")


def api_get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """GET JSON from an API with retry/backoff handling."""

    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            time.sleep(OPENAQ_REQUEST_DELAY_SECONDS)

            request = urllib.request.Request(
                url,
                headers=request_headers,
            )

            with urllib.request.urlopen(request, timeout=120) as response:
                payload = response.read()

            return json.loads(payload.decode("utf-8"))

        except urllib.error.HTTPError as exc:
            last_error = exc

            if exc.code not in {408, 429, 500, 502, 503, 504}:
                raise RuntimeError(
                    f"OpenAQ API request failed with HTTP {exc.code}: {url}"
                ) from exc

            if attempt < RETRY_COUNT:
                retry_after = exc.headers.get("Retry-After")

                if retry_after:
                    try:
                        wait_seconds = float(retry_after)
                    except ValueError:
                        wait_seconds = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))
                else:
                    wait_seconds = RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1))

                wait_seconds = min(wait_seconds, 60.0)

                print(
                    f"  HTTP {exc.code} received. "
                    f"Retrying in {wait_seconds:.1f}s "
                    f"(attempt {attempt}/{RETRY_COUNT})..."
                )

                time.sleep(wait_seconds)
                continue

            raise OpenAQRequestError(
                status_code=exc.code,
                url=url,
                original_error=exc,
            ) from exc

        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as exc:
            last_error = exc

            if attempt < RETRY_COUNT:
                wait_seconds = min(
                    RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)),
                    60.0,
                )

                time.sleep(wait_seconds)
                continue

            raise RuntimeError(
                f"API request failed after {RETRY_COUNT} attempts: {url}; error={last_error}"
            ) from exc

    raise RuntimeError(
        f"API request failed after {RETRY_COUNT} attempts: {url}; error={last_error}"
    )
