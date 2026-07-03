from __future__ import annotations

from engine.warcraft_models import WarriorUnit


def format_march(unit: WarriorUnit) -> str:
    return (
        f"{unit.camp} {unit.kind} {unit.warrior_id} marched to city {unit.position} "
        f"with {unit.hp} elements and force {unit.attack}"
    )


def format_headquarter_reached(unit: WarriorUnit) -> str:
    enemy = "blue" if unit.camp == "red" else "red"
    return (
        f"{unit.camp} {unit.kind} {unit.warrior_id} reached {enemy} headquarter "
        f"with {unit.hp} elements and force {unit.attack}"
    )
