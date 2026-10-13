from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from engine.predicates.palace import get_shishen
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    Shishen,
    Zhi,
    ZHI_CANGGAN_TABLE,
)


class SignalSource(str, Enum):
    NATAL = "原局"
    DAYUN = "大运"
    LIUNIAN = "流年"


@dataclass(frozen=True, slots=True)
class TenGodSignal:
    role: Shishen
    gan: Gan
    location: str
    score: float
    source: SignalSource
    visible: bool
    branch: Zhi | None


@dataclass(frozen=True, slots=True)
class TenGodProfile:
    signals: tuple[TenGodSignal, ...]

    def total(self, *roles: Shishen) -> float:
        return sum(signal.score for signal in self.signals if signal.role in roles)

    def source_total(self, source: SignalSource, *roles: Shishen) -> float:
        return sum(
            signal.score
            for signal in self.signals
            if signal.source is source and signal.role in roles
        )

    def signals_for(
        self,
        role: Shishen,
        *,
        source: SignalSource | None = None,
    ) -> tuple[TenGodSignal, ...]:
        return tuple(
            signal
            for signal in self.signals
            if signal.role == role and (source is None or signal.source is source)
        )


def natal_ten_god_profile(bazi: Bazi) -> TenGodProfile:
    signals: list[TenGodSignal] = []
    for location, gan in bazi.all_gans():
        if location == "日柱":
            continue
        signals.append(
            TenGodSignal(
                role=get_shishen(gan, bazi.day_master),
                gan=gan,
                location=location,
                score=1.0,
                source=SignalSource.NATAL,
                visible=True,
                branch=None,
            )
        )

    for location, zhi in bazi.all_zhis():
        month_multiplier = 1.5 if location == "月支" else 1.0
        canggans = bazi.藏干.get(location) or ZHI_CANGGAN_TABLE.get(zhi, [])
        for canggan in canggans:
            if isinstance(canggan, tuple):
                gan, _, strength = canggan
            else:
                gan, strength = canggan.gan, canggan.li_liang
            signals.append(
                TenGodSignal(
                    role=get_shishen(gan, bazi.day_master),
                    gan=gan,
                    location=location,
                    score=strength * month_multiplier,
                    source=SignalSource.NATAL,
                    visible=False,
                    branch=zhi,
                )
            )
    return TenGodProfile(signals=tuple(signals))


def cycle_ten_god_profile(
    ganzhi: GanZhi,
    day_master: Gan,
    source: SignalSource,
) -> TenGodProfile:
    stem_location = f"{source.value}干"
    branch_location = f"{source.value}支"
    signals = [
        TenGodSignal(
            role=get_shishen(ganzhi.gan, day_master),
            gan=ganzhi.gan,
            location=stem_location,
            score=1.0,
            source=source,
            visible=True,
            branch=None,
        )
    ]
    signals.extend(
        TenGodSignal(
            role=get_shishen(gan, day_master),
            gan=gan,
            location=branch_location,
            score=strength,
            source=source,
            visible=False,
            branch=ganzhi.zhi,
        )
        for gan, _, strength in ZHI_CANGGAN_TABLE.get(ganzhi.zhi, [])
    )
    return TenGodProfile(signals=tuple(signals))


def combine_ten_god_profiles(*profiles: TenGodProfile) -> TenGodProfile:
    return TenGodProfile(
        signals=tuple(signal for profile in profiles for signal in profile.signals)
    )
