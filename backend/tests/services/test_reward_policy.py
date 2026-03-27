from __future__ import annotations

from datetime import UTC, datetime

from app.services.learning_paths.reward_policy import DailyCapUsage, RewardPolicy


def test_legend_reward_rate_steps_follow_expected_decay() -> None:
    assert RewardPolicy.compute_legend_rate(is_legend_review=True, historical_round_count=0) == 0.5
    assert RewardPolicy.compute_legend_rate(is_legend_review=True, historical_round_count=1) == 0.3
    assert RewardPolicy.compute_legend_rate(is_legend_review=True, historical_round_count=2) == 0.2
    assert RewardPolicy.compute_legend_rate(is_legend_review=True, historical_round_count=3) == 0.1
    assert RewardPolicy.compute_legend_rate(is_legend_review=True, historical_round_count=9) == 0.1
    assert RewardPolicy.compute_legend_rate(is_legend_review=False, historical_round_count=99) == 1.0


def test_old_version_discount_is_applied() -> None:
    assert RewardPolicy.compute_version_discount(is_latest_ready_version=True) == 1.0
    assert RewardPolicy.compute_version_discount(is_latest_ready_version=None) == 1.0
    assert RewardPolicy.compute_version_discount(is_latest_ready_version=False) == 0.7


def test_free_daily_cap_limits_rewards() -> None:
    result = RewardPolicy.apply_free_daily_cap(
        xp=120,
        coins=40,
        usage=DailyCapUsage(xp_earned=260, coin_earned=50),
    )
    assert result.xp == 40
    assert result.coins == 10
    assert result.applied is True


def test_subscription_user_is_not_capped() -> None:
    reward = RewardPolicy.build_reward(
        base_xp=200,
        base_coins=80,
        is_legend_review=False,
        historical_legend_round_count=0,
        is_latest_ready_version=True,
        subscription_active=True,
        daily_usage=DailyCapUsage(xp_earned=290, coin_earned=59),
    )
    assert reward.xp == 200
    assert reward.coins == 80
    assert reward.free_cap_applied is False


def test_utc8_date_key_uses_utc_plus_8_boundary() -> None:
    now = datetime(2026, 3, 27, 17, 30, tzinfo=UTC)
    assert str(RewardPolicy.utc8_date_key(now)) == "2026-03-28"
