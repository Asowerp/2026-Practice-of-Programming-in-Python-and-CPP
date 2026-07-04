from __future__ import annotations

from engine.warcraft_models import (
    BLUE_PRODUCTION_ORDER,
    RED_PRODUCTION_ORDER,
    HeadquarterState,
    WarcraftConfig,
    WarriorUnit,
    WeaponSet,
)


def get_production_order(camp: str) -> tuple[str, ...]:
    return RED_PRODUCTION_ORDER if camp == "red" else BLUE_PRODUCTION_ORDER


def create_next_warrior(
    camp: str,
    headquarter: HeadquarterState,
    config: WarcraftConfig,
) -> WarriorUnit | None:
    order = get_production_order(camp)
    kind = order[headquarter.next_index]
    cost = config.warrior_health[kind]
    if headquarter.elements < cost:
        return None

    headquarter.elements -= cost
    headquarter.total_warriors += 1
    headquarter.next_index = (headquarter.next_index + 1) % len(order)
    warrior_id = headquarter.total_warriors
    attack = config.warrior_attack[kind]
    position = 0 if camp == "red" else config.city_count + 1
    warrior = WarriorUnit(
        camp=camp,
        kind=kind,
        warrior_id=warrior_id,
        hp=cost,
        attack=attack,
        position=position,
        weapons=build_initial_weapons(kind, warrior_id, attack),
    )
    if kind == "dragon":
        warrior.morale = headquarter.elements / cost
    if kind == "lion":
        warrior.loyalty = headquarter.elements
    return warrior


def build_initial_weapons(kind: str, warrior_id: int, attack: int) -> WeaponSet:
    weapons = WeaponSet()
    if kind in {"dragon", "iceman"}:
        give_weapon_by_index(weapons, warrior_id % 3, attack)
    elif kind == "ninja":
        give_weapon_by_index(weapons, warrior_id % 3, attack)
        give_weapon_by_index(weapons, (warrior_id + 1) % 3, attack)
    return weapons


def give_weapon_by_index(weapons: WeaponSet, index: int, attack: int) -> None:
    if index == 0:
        sword_attack = attack // 5
        if sword_attack > 0:
            weapons.sword_attack = sword_attack
    elif index == 1:
        weapons.bomb = True
    elif index == 2:
        weapons.arrow_uses = 3
