from __future__ import annotations

import re
from dataclasses import dataclass, field

from engine.class_manager import ClassManager


REQUIRED_BASE_FIELDS = ("hp", "attack")
RECOMMENDED_BATTLE_FIELDS = ("defense", "weapon_durability")


@dataclass(frozen=True)
class StandardClassRule:
    class_name: str
    direct_base: str = ""
    own_fields: tuple[str, ...] = ()
    constructor_targets: tuple[str, ...] = ()
    note: str = ""


STANDARD_CLASS_RULES = (
    StandardClassRule(
        class_name="Warrior",
        own_fields=REQUIRED_BASE_FIELDS,
        note="基础战士，建议开启虚函数，便于后续 Task2 讲解多态。",
    ),
    StandardClassRule(
        class_name="Dragon",
        direct_base="Warrior",
        own_fields=("morale",),
        constructor_targets=("Warrior", "morale"),
        note="Dragon 需要额外记录士气 morale。",
    ),
    StandardClassRule(
        class_name="Ninja",
        direct_base="Warrior",
        own_fields=("weaponCount",),
        constructor_targets=("Warrior", "weaponCount"),
        note="Ninja 可以用 weaponCount 之类的字段表示武器数量。",
    ),
    StandardClassRule(
        class_name="Iceman",
        direct_base="Warrior",
        own_fields=("stepCount",),
        constructor_targets=("Warrior", "stepCount"),
        note="Iceman 需要额外状态记录行走或变形阶段。",
    ),
)

STANDARD_RULE_MAP = {rule.class_name: rule for rule in STANDARD_CLASS_RULES}

CONSTRUCTOR_EXAMPLES = {
    "Dragon": "Dragon(int hp, int attack, double morale) : Warrior(hp, attack), morale(morale) {}",
    "Ninja": "Ninja(int hp, int attack, int weaponCount) : Warrior(hp, attack), weaponCount(weaponCount) {}",
    "Iceman": "Iceman(int hp, int attack, int stepCount) : Warrior(hp, attack), stepCount(stepCount) {}",
}


WARCRAFT_ENTITY_RULES = {
    "Headquarter": ("elements", "nextIndex", "totalWarriors"),
    "City": ("elements", "flag", "lastWinner"),
    "Warrior": ("id", "hp", "attack", "position"),
    "Weapon": (),
    "Dragon": ("morale",),
    "Ninja": ("weaponCount",),
    "Iceman": ("stepCount",),
    "Lion": ("loyalty",),
    "Wolf": (),
    "Sword": (),
    "Bomb": (),
    "Arrow": (),
}


@dataclass
class ValidationMessage:
    level: str
    text: str


@dataclass
class ValidationResult:
    messages: list[ValidationMessage] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(message.level != "error" for message in self.messages)

    def add(self, level: str, text: str) -> None:
        self.messages.append(ValidationMessage(level=level, text=text))

    def add_error(self, text: str) -> None:
        self.add("error", text)

    def add_warning(self, text: str) -> None:
        self.add("warning", text)

    def add_success(self, text: str) -> None:
        self.add("success", text)

    def extend(self, lines: list[ValidationMessage]) -> None:
        self.messages.extend(lines)

    def to_text(self) -> str:
        if not self.messages:
            return "尚未执行校验。"

        lines: list[str] = []
        if self.ok:
            lines.append("校验通过：Warrior 体系满足当前 Task1 规则。")
        else:
            lines.append("校验未通过：请根据下列信息修改类结构或初始化列表。")

        prefix_map = {
            "error": "[错误]",
            "warning": "[提示]",
            "success": "[通过]",
        }
        for message in self.messages:
            prefix = prefix_map.get(message.level, "[信息]")
            lines.append(f"{prefix} {message.text}")
        return "\n".join(lines)


def get_recommended_constructor_texts() -> dict[str, str]:
    return dict(CONSTRUCTOR_EXAMPLES)


def build_reference_hierarchy_text() -> str:
    lines = [
        "标准层级参考",
        "",
        "1. Warrior",
        "   - 不继承其他类",
        "   - 必备成员: hp, attack",
        "   - 建议成员: defense, weapon_durability",
        "   - 建议打开虚函数特性，便于 Task2 演示多态",
        "",
        "2. Dragon : public Warrior",
        "   - 新增成员: morale",
        "   - 初始化列表示例中应看到 Warrior(...) 与 morale(...)",
        "",
        "3. Ninja : public Warrior",
        "   - 新增成员: weaponCount",
        "   - 初始化列表示例中应看到 Warrior(...) 与 weaponCount(...)",
        "",
        "4. Iceman : public Warrior",
        "   - 新增成员: stepCount",
        "   - 初始化列表示例中应看到 Warrior(...) 与 stepCount(...)",
    ]
    return "\n".join(lines)


def build_warcraft_entity_reference_text() -> str:
    lines = [
        "题面对象参考",
        "",
        "1. Headquarter",
        "   - 建议成员: elements, nextIndex, totalWarriors",
        "   - 建议负责: 造兵顺序、生命元管理、编号分配",
        "",
        "2. City",
        "   - 建议成员: elements, flag, lastWinner",
        "   - 建议负责: 产生命元、旗帜、战斗结果记录",
        "",
        "3. Warrior",
        "   - 建议成员: id, hp, attack, position",
        "   - 建议负责: 行军、战斗、武器报告",
        "",
        "4. 五种武士",
        "   - Dragon: morale",
        "   - Ninja: 双武器 / 不反击",
        "   - Iceman: stepCount / 两步变形",
        "   - Lion: loyalty / 逃跑",
        "   - Wolf: 缴获武器",
        "",
        "5. Weapon / Sword / Bomb / Arrow",
        "   - Sword: 攻击衰减",
        "   - Bomb: 战前同归于尽判断",
        "   - Arrow: 最多使用 3 次",
    ]
    return "\n".join(lines)


def validate_warcraft_entities(manager: ClassManager) -> ValidationResult:
    result = ValidationResult()
    for class_name, required_fields in WARCRAFT_ENTITY_RULES.items():
        cls_def = manager.get_class(class_name)
        if cls_def is None:
            result.add_warning(f"当前还没有定义 {class_name}。")
            continue
        all_members = {member.var_name for member in manager.get_all_members(class_name)}
        missing_fields = [field for field in required_fields if field not in all_members]
        if missing_fields:
            result.add_warning(f"{class_name} 建议补充字段：{', '.join(missing_fields)}。")
        else:
            if required_fields:
                result.add_success(f"{class_name} 已覆盖建议字段：{', '.join(required_fields)}。")
            else:
                result.add_success(f"{class_name} 已建立，可在后续继续补细节。")

    if manager.get_class("Dragon") and not manager.is_subclass_of("Dragon", "Warrior"):
        result.add_error("Dragon 应继承 Warrior。")
    if manager.get_class("Ninja") and not manager.is_subclass_of("Ninja", "Warrior"):
        result.add_error("Ninja 应继承 Warrior。")
    if manager.get_class("Iceman") and not manager.is_subclass_of("Iceman", "Warrior"):
        result.add_error("Iceman 应继承 Warrior。")
    if manager.get_class("Lion") and not manager.is_subclass_of("Lion", "Warrior"):
        result.add_error("Lion 应继承 Warrior。")
    if manager.get_class("Wolf") and not manager.is_subclass_of("Wolf", "Warrior"):
        result.add_error("Wolf 应继承 Warrior。")

    if manager.get_class("Sword") and manager.get_class("Weapon") and not manager.is_subclass_of("Sword", "Weapon"):
        result.add_error("Sword 应继承 Weapon。")
    if manager.get_class("Bomb") and manager.get_class("Weapon") and not manager.is_subclass_of("Bomb", "Weapon"):
        result.add_error("Bomb 应继承 Weapon。")
    if manager.get_class("Arrow") and manager.get_class("Weapon") and not manager.is_subclass_of("Arrow", "Weapon"):
        result.add_error("Arrow 应继承 Weapon。")

    return result


def validate_warrior_hierarchy(
    manager: ClassManager,
    constructor_texts: dict[str, str] | None = None,
) -> ValidationResult:
    constructor_texts = constructor_texts or {}
    result = ValidationResult()

    warrior = manager.get_class("Warrior")
    if warrior is None:
        result.add_error("缺少 Warrior 类。")
    else:
        if warrior.base_class:
            result.add_error(f"Warrior 不应再继承其他类，当前基类为 {warrior.base_class}。")

        warrior_members = {member.var_name for member in warrior.members}
        missing_base_fields = [field for field in REQUIRED_BASE_FIELDS if field not in warrior_members]
        if missing_base_fields:
            result.add_error(
                f"Warrior 缺少基础成员：{', '.join(missing_base_fields)}。"
            )
        else:
            result.add_success("Warrior 的基础成员 hp / attack 齐全。")

        missing_battle_fields = [field for field in RECOMMENDED_BATTLE_FIELDS if field not in warrior_members]
        if missing_battle_fields:
            result.add_warning(
                "Warrior 还没有补齐 Task2 常用战斗字段："
                f"{', '.join(missing_battle_fields)}。"
            )
        else:
            result.add_success("Warrior 已包含 Task2 常用战斗字段 defense / weapon_durability。")

        if manager.class_has_virtual("Warrior"):
            result.add_success("Warrior 保留了虚函数特性，后续可用于演示多态。")
        else:
            result.add_warning("Warrior 当前没有虚函数特性，Task2 的多态演示会弱一些。")

    for rule in STANDARD_CLASS_RULES[1:]:
        cls_def = manager.get_class(rule.class_name)
        if cls_def is None:
            result.add_error(f"缺少 {rule.class_name} 类。")
            continue

        if cls_def.base_class != rule.direct_base:
            current_base = cls_def.base_class or "<空>"
            result.add_error(
                f"{rule.class_name} 的直接基类应为 {rule.direct_base}，当前为 {current_base}。"
            )

        all_members = {member.var_name for member in manager.get_all_members(rule.class_name)}
        required_fields = (*REQUIRED_BASE_FIELDS, *rule.own_fields)
        missing_fields = [field for field in required_fields if field not in all_members]
        if missing_fields:
            result.add_error(
                f"{rule.class_name} 最终成员中缺少 {', '.join(missing_fields)}。"
            )
        else:
            result.add_success(
                f"{rule.class_name} 的继承后成员齐全，已保留 hp / attack 并新增了 {', '.join(rule.own_fields)}。"
            )

    for rule in STANDARD_CLASS_RULES[1:]:
        if manager.get_class(rule.class_name) is None:
            continue

        constructor_text = constructor_texts.get(rule.class_name, "").strip()
        if not constructor_text:
            result.add_warning(
                f"未填写 {rule.class_name} 的构造函数初始化列表示例，已跳过这一项。"
            )
            continue

        initializer_targets = extract_initializer_targets(constructor_text)
        missing_targets = [
            target_name
            for target_name in rule.constructor_targets
            if target_name not in initializer_targets
        ]
        if missing_targets:
            result.add_error(
                f"{rule.class_name} 的初始化列表缺少：{', '.join(name + '(...)' for name in missing_targets)}。"
            )
        else:
            result.add_success(
                f"{rule.class_name} 的初始化列表已覆盖 {', '.join(name + '(...)' for name in rule.constructor_targets)}。"
            )

    return result


def extract_initializer_targets(constructor_text: str) -> set[str]:
    if ":" not in constructor_text:
        return set()

    initializer_part = constructor_text.split(":", 1)[1]
    initializer_part = initializer_part.split("{", 1)[0]
    return {
        match.group(1)
        for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", initializer_part)
    }
