from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

FREE_DAILY_XP_CAP = 300
FREE_DAILY_COIN_CAP = 60
LEGEND_REWARD_RATE_STEPS: tuple[float, ...] = (0.5, 0.3, 0.2, 0.1)
OLD_VERSION_DISCOUNT = 0.7
LATEST_VERSION_DISCOUNT = 1.0


@dataclass(slots=True)
class RewardComputation:
    xp: int
    coins: int
    legend_rate: float
    version_discount: float
    free_cap_applied: bool


@dataclass(slots=True)
class DailyCapUsage:
    xp_earned: int
    coin_earned: int


@dataclass(slots=True)
class DailyCapResult:
    xp: int
    coins: int
    applied: bool


class RewardPolicy:
    @staticmethod
    def compute_legend_rate(*, is_legend_review: bool, historical_round_count: int) -> float:
        if not is_legend_review:
            return 1.0
        idx = max(0, min(historical_round_count, len(LEGEND_REWARD_RATE_STEPS) - 1))
        return LEGEND_REWARD_RATE_STEPS[idx]

    @staticmethod
    def compute_version_discount(*, is_latest_ready_version: bool | None) -> float:
        if is_latest_ready_version is False:
            return OLD_VERSION_DISCOUNT
        return LATEST_VERSION_DISCOUNT

    @staticmethod
    def apply_rates(*, base_xp: int, base_coins: int, legend_rate: float, version_discount: float) -> tuple[int, int]:
        factor = legend_rate * version_discount
        return max(0, int(base_xp * factor)), max(0, int(base_coins * factor))

    @staticmethod
    def utc8_date_key(now_utc: datetime) -> date:
        return (now_utc.astimezone(UTC) + timedelta(hours=8)).date()

    @staticmethod
    def apply_free_daily_cap(
        *,
        xp: int,
        coins: int,
        usage: DailyCapUsage,
        xp_cap: int = FREE_DAILY_XP_CAP,
        coin_cap: int = FREE_DAILY_COIN_CAP,
    ) -> DailyCapResult:
        xp_left = max(0, xp_cap - usage.xp_earned)
        coin_left = max(0, coin_cap - usage.coin_earned)
        capped_xp = min(max(0, xp), xp_left)
        capped_coins = min(max(0, coins), coin_left)
        return DailyCapResult(
            xp=capped_xp,
            coins=capped_coins,
            applied=(capped_xp != xp or capped_coins != coins),
        )

    @staticmethod
    def build_reward(
        *,
        base_xp: int,
        base_coins: int,
        is_legend_review: bool,
        historical_legend_round_count: int,
        is_latest_ready_version: bool | None,
        subscription_active: bool,
        daily_usage: DailyCapUsage,
    ) -> RewardComputation:
        legend_rate = RewardPolicy.compute_legend_rate(
            is_legend_review=is_legend_review,
            historical_round_count=historical_legend_round_count,
        )
        version_discount = RewardPolicy.compute_version_discount(
            is_latest_ready_version=is_latest_ready_version,
        )
        xp_after_rates, coins_after_rates = RewardPolicy.apply_rates(
            base_xp=base_xp,
            base_coins=base_coins,
            legend_rate=legend_rate,
            version_discount=version_discount,
        )

        if subscription_active:
            return RewardComputation(
                xp=xp_after_rates,
                coins=coins_after_rates,
                legend_rate=legend_rate,
                version_discount=version_discount,
                free_cap_applied=False,
            )

        cap_result = RewardPolicy.apply_free_daily_cap(
            xp=xp_after_rates,
            coins=coins_after_rates,
            usage=daily_usage,
        )
        return RewardComputation(
            xp=cap_result.xp,
            coins=cap_result.coins,
            legend_rate=legend_rate,
            version_discount=version_discount,
            free_cap_applied=cap_result.applied,
        )
