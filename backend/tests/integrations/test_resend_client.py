from __future__ import annotations

from typing import ClassVar

import pytest

from app.integrations.resend.client import ResendClientError, ResendMailClient


class FakeEmails:
    sent: ClassVar[list[dict[str, object]]] = []

    @classmethod
    def send(
        cls,
        params: dict[str, object],
        options: dict[str, object] | None = None,
    ) -> dict[str, str]:
        cls.sent.append({"params": params, "options": options})
        return {"id": "email_123"}


class FailingEmails:
    @classmethod
    def send(
        cls,
        params: dict[str, object],
        options: dict[str, object] | None = None,
    ) -> dict[str, str]:
        _ = params
        _ = options
        raise RuntimeError("upstream leaked payload")


@pytest.fixture(autouse=True)
def reset_fake_emails() -> None:
    FakeEmails.sent = []


@pytest.mark.asyncio
async def test_send_verification_code_uses_verified_xirang_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations.resend import client as resend_client_module

    monkeypatch.setattr(resend_client_module.resend, "Emails", FakeEmails)
    client = ResendMailClient(
        api_key="test-key",
        from_email="Xirang <noreply@xiranglearn.quest>",
        timeout_seconds=10,
    )

    await client.send_verification_code(
        email="student@example.com",
        code="123456",
        idempotency_key="verify-1",
    )

    assert FakeEmails.sent == [
        {
            "params": {
                "from": "Xirang <noreply@xiranglearn.quest>",
                "to": ["student@example.com"],
                "subject": "Your Xirang verification code",
                "text": "Your Xirang verification code is 123456. It expires in 10 minutes.",
                "html": "<p>Your Xirang verification code is <strong>123456</strong>.</p><p>It expires in 10 minutes.</p>",
            },
            "options": {"idempotency_key": "verify-1"},
        }
    ]


@pytest.mark.asyncio
async def test_send_notification_email_uses_application_message_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations.resend import client as resend_client_module

    monkeypatch.setattr(resend_client_module.resend, "Emails", FakeEmails)
    client = ResendMailClient(
        api_key="test-key",
        from_email="Xirang <notifications@xiranglearn.quest>",
        timeout_seconds=10,
    )

    await client.send_notification(
        email="student@example.com",
        title="New quest available",
        body="Check your daily quest reward.",
        action_url="https://www.xiranglearn.quest/quests",
    )

    assert FakeEmails.sent == [
        {
            "params": {
                "from": "Xirang <notifications@xiranglearn.quest>",
                "to": ["student@example.com"],
                "subject": "New quest available",
                "text": "Check your daily quest reward.\n\nOpen: https://www.xiranglearn.quest/quests",
                "html": '<p>Check your daily quest reward.</p><p><a href="https://www.xiranglearn.quest/quests">Open in Xirang</a></p>',
            },
            "options": None,
        }
    ]


@pytest.mark.asyncio
async def test_send_notification_omits_untrusted_action_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.integrations.resend import client as resend_client_module

    monkeypatch.setattr(resend_client_module.resend, "Emails", FakeEmails)
    client = ResendMailClient(
        api_key="test-key",
        from_email="Xirang <notifications@xiranglearn.quest>",
        timeout_seconds=10,
    )

    await client.send_notification(
        email="student@example.com",
        title="New quest available",
        body="Open this safely.",
        action_url="https://evil.example/login",
    )

    params = FakeEmails.sent[0]["params"]
    assert isinstance(params, dict)
    assert params["text"] == "Open this safely."
    assert params["html"] == "<p>Open this safely.</p>"


@pytest.mark.asyncio
async def test_send_failure_uses_generic_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations.resend import client as resend_client_module

    monkeypatch.setattr(resend_client_module.resend, "Emails", FailingEmails)
    client = ResendMailClient(
        api_key="test-key",
        from_email="Xirang <noreply@xiranglearn.quest>",
        timeout_seconds=10,
    )

    with pytest.raises(ResendClientError) as exc_info:
        await client.send_verification_code(
            email="student@example.com",
            code="123456",
            idempotency_key="verify-1",
        )

    assert str(exc_info.value) == "Resend email delivery failed"
