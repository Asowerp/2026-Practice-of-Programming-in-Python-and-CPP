from __future__ import annotations

from controllers.class_manager import ClassManager
from controllers.models import ObjectInstance


COMBAT_STAT_FIELDS = ("hp", "attack", "defense", "weapon_durability")
DEFAULT_COMBAT_STATS = {
    "hp": 100,
    "attack": 30,
    "defense": 5,
    "weapon_durability": 3,
}


def get_warrior_family(manager: ClassManager) -> list[str]:
    return [
        class_name
        for class_name in manager.get_class_names()
        if manager.is_subclass_of(class_name, "Warrior")
    ]


def normalize_combat_stats(stats: dict[str, int] | None = None) -> dict[str, int]:
    normalized = DEFAULT_COMBAT_STATS.copy()
    stats = stats or {}
    for key in COMBAT_STAT_FIELDS:
        normalized[key] = max(0, _to_int(stats.get(key, normalized[key]), normalized[key]))
    normalized["attack"] = max(1, normalized["attack"])
    return normalized


def create_battle_instance(
    manager: ClassManager,
    class_name: str,
    stats: dict[str, int] | None = None,
) -> ObjectInstance:
    normalized = normalize_combat_stats(stats)
    instance = manager.create_instance(class_name, normalized)
    instance.values.update(normalized)
    return instance


def collect_missing_combat_fields(manager: ClassManager, class_name: str) -> list[str]:
    member_names = {member.var_name for member in manager.get_all_members(class_name)}
    return [field_name for field_name in COMBAT_STAT_FIELDS if field_name not in member_names]


def build_fighter_brief(manager: ClassManager, instance: ObjectInstance | None) -> str:
    if instance is None:
        return "尚未设置武士"

    values = normalize_combat_stats(instance.values)
    missing_fields = collect_missing_combat_fields(manager, instance.class_name)
    lines = [
        f"职业: {instance.class_name}",
        f"HP: {values.get('hp')}",
        f"攻击: {values.get('attack')}",
        f"防御: {values.get('defense')}",
        f"武器耐久: {values.get('weapon_durability')}",
        f"特性说明: {describe_warrior_trait(instance.class_name)}",
    ]
    if missing_fields:
        lines.append(
            "类结构提示: 当前类里尚未声明 "
            + ", ".join(missing_fields)
            + "，战斗实验室会用临时战斗值补齐。"
        )
    else:
        lines.append("类结构提示: 该类已经声明了 Task2 常用战斗字段。")
    return "\n".join(lines)


def describe_warrior_trait(class_name: str) -> str:
    trait_map = {
        "Warrior": "基础战士：按标准规则攻击并反击。",
        "Dragon": "Dragon：当前演示中按标准规则战斗，适合观察继承后的基础属性。",
        "Ninja": "Ninja：保留“不反击”的特性，适合测试多态差异。",
        "Iceman": "Iceman：当前演示中按标准规则战斗，适合测试多回合消耗。",
    }
    return trait_map.get(class_name, "Warrior 体系成员：按当前简化规则战斗。")


def _to_int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
