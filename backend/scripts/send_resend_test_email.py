from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.integrations.resend.client import ResendClientError, ResendMailClient


TEST_RECIPIENT = "jixianchuansuo@126.com"


async def main() -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    client = ResendMailClient(
        api_key=settings.resend_api_key,
        from_email=settings.resend_from_email,
        timeout_seconds=settings.resend_timeout_seconds,
    )
    await client.send_notification(
        email=TEST_RECIPIENT,
        title="Xirang Resend test",
        body="This is a test email from Xirang local backend via Resend.",
        action_url="https://www.xiranglearn.quest",
    )
    print(f"Sent Resend test email to {TEST_RECIPIENT} from {settings.resend_from_email}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ResendClientError as exc:
        raise SystemExit(str(exc)) from None
