from __future__ import annotations

import asyncio
import html
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import resend

logger = logging.getLogger(__name__)


class ResendClientError(RuntimeError):
    pass


@dataclass(slots=True)
class ResendMailClient:
    api_key: str
    from_email: str
    timeout_seconds: float = 10.0

    async def _send(
        self,
        params: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> None:
        resend.api_key = self.api_key
        try:
            await asyncio.wait_for(
                asyncio.to_thread(resend.Emails.send, params, options),
                timeout=self.timeout_seconds,
            )
        except Exception as exc:
            logger.warning("resend_email_delivery_failed error_type=%s", type(exc).__name__)
            raise ResendClientError("Resend email delivery failed") from None

    def _trusted_action_url(self, action_url: str | None) -> str | None:
        if not action_url:
            return None
        parsed = urlparse(action_url)
        host = parsed.hostname or ""
        is_xirang_domain = host in {"xiranglearn.quest", "www.xiranglearn.quest"}
        if parsed.scheme == "https" and is_xirang_domain:
            return action_url
        return None

    async def send_verification_code(
        self, *, email: str, code: str, idempotency_key: str
    ) -> None:
        payload = {
            "from": self.from_email,
            "to": [email],
            "subject": "Your Xirang verification code",
            "text": f"Your Xirang verification code is {code}. It expires in 10 minutes.",
            "html": f"<p>Your Xirang verification code is <strong>{html.escape(code)}</strong>.</p><p>It expires in 10 minutes.</p>",
        }
        await self._send(payload, options={"idempotency_key": idempotency_key})

    async def send_notification(
        self,
        *,
        email: str,
        title: str,
        body: str | None = None,
        action_url: str | None = None,
    ) -> None:
        text_parts = [body or title]
        html_parts = [f"<p>{html.escape(body or title)}</p>"]
        trusted_action_url = self._trusted_action_url(action_url)
        if trusted_action_url:
            text_parts.append(f"Open: {trusted_action_url}")
            safe_url = html.escape(trusted_action_url, quote=True)
            html_parts.append(f'<p><a href="{safe_url}">Open in Xirang</a></p>')

        await self._send(
            {
                "from": self.from_email,
                "to": [email],
                "subject": title,
                "text": "\n\n".join(text_parts),
                "html": "".join(html_parts),
            }
        )


ResendVerificationMailClient = ResendMailClient
