import httpx


def notify(webhook_url: str | None, message: str, timeout: float = 10.0) -> None:
    if webhook_url:
        try:
            httpx.post(webhook_url, json={"content": message[:2000]}, timeout=timeout).raise_for_status()
        except httpx.HTTPError:
            pass