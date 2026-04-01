from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import enum_values


class ThemeKey(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class LeaderboardScope(StrEnum):
    GLOBAL = "global"
    FRIENDS = "friends"


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(Text())
    bio: Mapped[str | None] = mapped_column(Text())
    verified_badge: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    tier_label: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )


class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    theme_key: Mapped[ThemeKey] = mapped_column(
        Enum(ThemeKey, native_enum=False, create_constraint=True, values_callable=enum_values),
        nullable=False,
        default=ThemeKey.SYSTEM,
        server_default=ThemeKey.SYSTEM.value,
    )
    language_code: Mapped[str] = mapped_column(
        String(20), nullable=False, default="en", server_default="en"
    )
    sound_enabled: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )
    haptic_enabled: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default=text("true")
    )
    daily_reminder_enabled: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    leaderboard_scope_default: Mapped[LeaderboardScope] = mapped_column(
        Enum(
            LeaderboardScope, native_enum=False, create_constraint=True, values_callable=enum_values
        ),
        nullable=False,
        default=LeaderboardScope.GLOBAL,
        server_default=LeaderboardScope.GLOBAL.value,
    )
    selected_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        server_default=None,
        comment="User's selected LLM model for question generation",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
