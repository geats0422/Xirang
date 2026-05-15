from __future__ import annotations

from dataclasses import dataclass

import httpx


class ResendClientError(RuntimeError):
    pass


@dataclass(slots=True)
class ResendVerificationMailClient:
    api_key: str
    from_email: str
    timeout_seconds: float = 10.0

    async def send_verification_code(
        self, *, email: str, code: str, idempotency_key: str
    ) -> None:
        payload = {
            "from": self.from_email,
            "to": [email],
            "subject": "Your Xirang verification code",
            "text": f"Your Xirang verification code is {code}. It expires in 10 minutes.",
            "html": f"<p>Your Xirang verification code is <strong>{code}</strong>.</p><p>It expires in 10 minutes.</p>",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": idempotency_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise ResendClientError(f"Resend request failed: {exc}") from exc

        if response.status_code >= 400:
            raise ResendClientError(
                f"Resend email failed: status={response.status_code}, body={response.text[:500]}"
            )
