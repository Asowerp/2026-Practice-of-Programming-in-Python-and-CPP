from __future__ import annotations

from engine.warcraft_models import WarriorUnit


def alive_warriors(
    warriors: list[WarriorUnit],
    camp: str | None = None,
) -> list[WarriorUnit]:
    return [
        unit
        for unit in warriors
        if unit.alive and not unit.removed and (camp is None or unit.camp == camp)
    ]


def alive_warriors_at(
    warriors: list[WarriorUnit],
    position: int,
    camp: str,
) -> list[WarriorUnit]:
    return [
        unit
        for unit in alive_warriors(warriors, camp)
        if unit.position == position
    ]


def first_alive_warrior_at(
    warriors: list[WarriorUnit],
    position: int,
    camp: str,
) -> WarriorUnit | None:
    units = alive_warriors_at(warriors, position, camp)
    return units[0] if units else None


def first_alive_enemy_at(
    warriors: list[WarriorUnit],
    position: int,
    shooter_camp: str,
) -> WarriorUnit | None:
    enemy_camp = "blue" if shooter_camp == "red" else "red"
    return first_alive_warrior_at(warriors, position, enemy_camp)


def first_recent_arrow_dead_at(
    warriors: list[WarriorUnit],
    position: int,
    camp: str,
    total_minutes: int,
) -> WarriorUnit | None:
    for unit in warriors:
        if (
            unit.camp == camp
            and not unit.alive
            and not unit.removed
            and unit.position == position
            and unit.death_reason == "arrow"
            and unit.death_time == total_minutes - 5
        ):
            return unit
    return None


def warrior_short_name(unit: WarriorUnit) -> str:
    return f"{unit.camp}-{unit.kind}-{unit.warrior_id}"
