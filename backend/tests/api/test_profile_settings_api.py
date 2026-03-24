from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.db.models.profile import ThemeKey
from app.schemas.profile import ProfileUpdateRequest
from app.schemas.settings import SettingsUpdateRequest
from app.services.profile.service import ProfileService
from app.services.settings.service import SettingsService

pytestmark = pytest.mark.asyncio(loop_scope="module")


class FakeProfile:
    def __init__(self, user_id):
        self.user_id = user_id
        self.display_name = "Test"
        self.avatar_url = None
        self.bio = None
        self.verified_badge = False
        self.tier_label = None
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


class FakeProfileRepo:
    def __init__(self):
        self.profiles = {uuid4(): FakeProfile(uuid4())}
        self.committed = False

    async def get_profile(self, user_id):
        return self.profiles.get(user_id)

    async def update_profile(self, user_id, **fields):
        p = self.profiles[user_id]
        for k, v in fields.items():
            setattr(p, k, v)
        return p

    async def commit(self):
        self.committed = True


class FakeSettings:
    def __init__(self, user_id):
        self.user_id = user_id
        self.theme_key = ThemeKey.SYSTEM
        self.language_code = "en"
        self.sound_enabled = True
        self.haptic_enabled = True
        self.daily_reminder_enabled = False
        self.leaderboard_scope_default = "global"
        self.updated_at = datetime.now(UTC)


class FakeSettingsRepo:
    def __init__(self):
        self.settings = {uuid4(): FakeSettings(uuid4())}
        self.committed = False

    async def get_settings(self, user_id):
        return self.settings.get(user_id)

    async def update_settings(self, user_id, **fields):
        s = self.settings[user_id]
        for k, v in fields.items():
            setattr(s, k, v)
        return s

    async def commit(self):
        self.committed = True


@pytest.fixture
def profile_service():
    user_id = uuid4()
    repo = FakeProfileRepo()
    repo.profiles = {user_id: FakeProfile(user_id)}
    return ProfileService(repository=repo)


@pytest.fixture
def settings_service():
    user_id = uuid4()
    repo = FakeSettingsRepo()
    repo.settings = {user_id: FakeSettings(user_id)}
    return SettingsService(repository=repo)


async def test_get_profile_returns_data(profile_service):
    repo = profile_service.repository
    user_id = next(iter(repo.profiles.keys()))
    result = await profile_service.get_profile(user_id)
    assert result.display_name == "Test"


async def test_update_profile_updates_fields(profile_service):
    repo = profile_service.repository
    user_id = next(iter(repo.profiles.keys()))
    payload = ProfileUpdateRequest(display_name="New")
    result = await profile_service.update_profile(user_id, payload)
    assert result.display_name == "New"
    assert repo.committed


async def test_get_settings_returns_data(settings_service):
    repo = settings_service.repository
    user_id = next(iter(repo.settings.keys()))
    result = await settings_service.get_settings(user_id)
    assert result.theme_key == ThemeKey.SYSTEM


async def test_update_settings_updates_fields(settings_service):
    repo = settings_service.repository
    user_id = next(iter(repo.settings.keys()))
    payload = SettingsUpdateRequest(theme_key=ThemeKey.DARK)
    result = await settings_service.update_settings(user_id, payload)
    assert result.theme_key == ThemeKey.DARK
    assert repo.committed
