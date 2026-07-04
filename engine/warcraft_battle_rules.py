from __future__ import annotations

from engine.warcraft_models import CityState, WarriorUnit


def resolve_attacker(
    city_id: int,
    city: CityState,
    red: WarriorUnit,
    blue: WarriorUnit,
) -> tuple[WarriorUnit | None, WarriorUnit | None]:
    if city.flag == "red":
        return red, blue
    if city.flag == "blue":
        return blue, red
    return (red, blue) if city_id % 2 == 1 else (blue, red)


def predict_battle_deaths(
    attacker: WarriorUnit,
    defender: WarriorUnit,
) -> tuple[bool, bool]:
    defender_hp = defender.hp - attacker.attack - attacker.weapons.sword_attack
    defender_dies = defender_hp <= 0
    attacker_dies = False
    if not defender_dies and defender.can_counterattack():
        attacker_hp = attacker.hp - defender.attack // 2 - defender.weapons.sword_attack
        attacker_dies = attacker_hp <= 0
    return attacker_dies, defender_dies


def update_city_flag(city: CityState, winner_camp: str) -> str:
    if city.last_winner == winner_camp:
        city.win_streak += 1
    else:
        city.last_winner = winner_camp
        city.win_streak = 1

    if city.win_streak >= 2 and city.flag != winner_camp:
        city.flag = winner_camp
        return winner_camp
    return ""
