from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


CAMPS = ("red", "blue")
WARRIOR_TYPES = ("dragon", "ninja", "iceman", "lion", "wolf")
WEAPON_TYPES = ("sword", "bomb", "arrow")
RED_PRODUCTION_ORDER = ("iceman", "lion", "wolf", "ninja", "dragon")
BLUE_PRODUCTION_ORDER = ("lion", "dragon", "ninja", "iceman", "wolf")


@dataclass(frozen=True)
class StageDefinition:
    key: str
    title: str
    default_minute: int
    description: str
    order_index: int


STANDARD_STAGE_DEFINITIONS = (
    StageDefinition("spawn", "00 造兵", 0, "双方司令部按固定序列尝试制造一个武士。", 0),
    StageDefinition("lion_escape", "05 Lion 逃跑", 5, "忠诚度不大于 0 的 lion 逃离战场。", 1),
    StageDefinition("march", "10 全体前进", 10, "所有仍在路上的武士同时向敌方司令部前进一步。", 2),
    StageDefinition("city_produce", "20 城市产生命元", 20, "每座城市增加 10 个生命元。", 3),
    StageDefinition("collect_elements", "30 单武士取生命元", 30, "城里只有一个武士时，他取走城市中的全部生命元。", 4),
    StageDefinition("arrow", "35 Arrow 阶段", 35, "拥有 arrow 的武士朝下一座城放箭。", 5),
    StageDefinition("bomb", "38 Bomb 阶段", 38, "拥有 bomb 的武士判断是否应与敌人同归于尽。", 6),
    StageDefinition("battle", "40 战斗阶段", 40, "同城双武士发生战斗，并触发旗帜、奖励和欢呼等后续效果。", 7),
    StageDefinition("headquarter_report", "50 司令部报告", 50, "双方司令部报告当前生命元数量。", 8),
    StageDefinition("weapon_report", "55 武器报告", 55, "所有武士按顺序报告武器情况。", 9),
)

STAGE_DEFINITION_MAP = {definition.key: definition for definition in STANDARD_STAGE_DEFINITIONS}


@dataclass
class EventSlotConfig:
    key: str
    title: str
    default_minute: int
    minute: int
    enabled: bool = True
    order_index: int = 0


@dataclass
class EventScheduleProfile:
    name: str
    strict_mode: bool = True
    slots: list[EventSlotConfig] = field(default_factory=list)

    def clone(self) -> "EventScheduleProfile":
        return deepcopy(self)

    def get_enabled_slots(self) -> list[EventSlotConfig]:
        return sorted(
            [slot for slot in self.slots if slot.enabled],
            key=lambda slot: (slot.minute, slot.order_index),
        )

    def get_slot(self, key: str) -> EventSlotConfig | None:
        for slot in self.slots:
            if slot.key == key:
                return slot
        return None


@dataclass
class WarcraftConfig:
    initial_elements: int = 20
    city_count: int = 2
    arrow_attack: int = 10
    lion_loyalty_decay: int = 10
    time_limit: int = 240
    warrior_health: dict[str, int] = field(default_factory=lambda: {
        "dragon": 20,
        "ninja": 20,
        "iceman": 30,
        "lion": 20,
        "wolf": 20,
    })
    warrior_attack: dict[str, int] = field(default_factory=lambda: {
        "dragon": 5,
        "ninja": 5,
        "iceman": 5,
        "lion": 5,
        "wolf": 5,
    })

    def clone(self) -> "WarcraftConfig":
        return deepcopy(self)


@dataclass
class WeaponSet:
    sword_attack: int = 0
    bomb: bool = False
    arrow_uses: int = 0

    def clone(self) -> "WeaponSet":
        return deepcopy(self)

    def has_sword(self) -> bool:
        return self.sword_attack > 0

    def has_bomb(self) -> bool:
        return self.bomb

    def has_arrow(self) -> bool:
        return self.arrow_uses > 0

    def use_arrow(self) -> None:
        if self.arrow_uses > 0:
            self.arrow_uses -= 1

    def blunt_sword(self) -> None:
        if self.sword_attack <= 0:
            return
        self.sword_attack = int(self.sword_attack * 0.8)
        if self.sword_attack <= 0:
            self.sword_attack = 0

    def report_text(self) -> str:
        parts: list[str] = []
        if self.arrow_uses > 0:
            parts.append(f"arrow({self.arrow_uses})")
        if self.bomb:
            parts.append("bomb")
        if self.sword_attack > 0:
            parts.append(f"sword({self.sword_attack})")
        if not parts:
            return "no weapon"
        return ",".join(parts)

    def capture_from(self, other: "WeaponSet") -> None:
        if self.arrow_uses <= 0 and other.arrow_uses > 0:
            self.arrow_uses = other.arrow_uses
        if not self.bomb and other.bomb:
            self.bomb = True
        if self.sword_attack <= 0 and other.sword_attack > 0:
            self.sword_attack = other.sword_attack


@dataclass
class WarriorUnit:
    camp: str
    kind: str
    warrior_id: int
    hp: int
    attack: int
    position: int
    weapons: WeaponSet = field(default_factory=WeaponSet)
    morale: float | None = None
    loyalty: int | None = None
    step_count: int = 0
    reached_enemy_headquarter: bool = False
    alive: bool = True
    removed: bool = False
    death_reason: str = ""
    death_time: int = -1

    def display_name(self) -> str:
        return f"{self.camp} {self.kind} {self.warrior_id}"

    def is_in_city(self) -> bool:
        return self.position > 0 and not self.reached_enemy_headquarter

    def is_enemy_headquarter_position(self, city_count: int) -> bool:
        return (self.camp == "red" and self.position == city_count + 1) or (
            self.camp == "blue" and self.position == 0
        )

    def move_one_step(self, city_count: int) -> None:
        if not self.alive or self.removed or self.reached_enemy_headquarter:
            return
        if self.camp == "red":
            self.position += 1
            if self.position == city_count + 1:
                self.reached_enemy_headquarter = True
        else:
            self.position -= 1
            if self.position == 0:
                self.reached_enemy_headquarter = True

        if self.kind == "iceman":
            self.step_count += 1
            if self.step_count % 2 == 0:
                self.hp = 1 if self.hp <= 9 else self.hp - 9
                self.attack += 20

    def can_counterattack(self) -> bool:
        return self.kind != "ninja"


@dataclass
class HeadquarterState:
    camp: str
    elements: int
    next_index: int = 0
    total_warriors: int = 0
    enemy_arrivals: int = 0


@dataclass
class CityState:
    city_id: int
    elements: int = 0
    flag: str = ""
    last_winner: str = ""
    win_streak: int = 0


@dataclass
class EventRecord:
    total_minutes: int
    stage_key: str
    location_order: int
    description: str
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def display_time(self) -> str:
        return format_time(self.total_minutes)

    def to_log_line(self) -> str:
        if self.payload.get("omit_time"):
            return self.description
        return f"{self.display_time} {self.description}"


@dataclass
class StageExecution:
    total_minutes: int
    slot_key: str
    slot_title: str
    events: list[EventRecord] = field(default_factory=list)
    summary: str = ""
    finished: bool = False


@dataclass
class SimulationBundle:
    mode_label: str
    config: WarcraftConfig
    schedule: EventScheduleProfile
    events: list[EventRecord]
    world_summary: str


def format_time(total_minutes: int) -> str:
    total_minutes = max(0, int(total_minutes))
    hour = total_minutes // 60
    minute = total_minutes % 60
    return f"{hour:03d}:{minute:02d}"


def build_schedule_profile(profile_name: str = "标准题面") -> EventScheduleProfile:
    slots = [
        EventSlotConfig(
            key=definition.key,
            title=definition.title,
            default_minute=definition.default_minute,
            minute=definition.default_minute,
            enabled=True,
            order_index=definition.order_index,
        )
        for definition in STANDARD_STAGE_DEFINITIONS
    ]

    profile = EventScheduleProfile(name=profile_name, strict_mode=True, slots=slots)
    if profile_name == "基础行军版":
        _apply_stage_subset(profile, {"spawn", "march", "headquarter_report"}, strict_mode=False)
    elif profile_name == "资源流版":
        _apply_stage_subset(profile, {"spawn", "march", "city_produce", "collect_elements", "headquarter_report"}, strict_mode=False)
    elif profile_name == "战斗讲解版":
        _apply_stage_subset(profile, {"spawn", "march", "arrow", "bomb", "battle", "weapon_report"}, strict_mode=False)
    elif profile_name == "自定义版":
        profile.strict_mode = False
    return profile


def get_schedule_profile_names() -> list[str]:
    return ["标准题面", "基础行军版", "资源流版", "战斗讲解版", "自定义版"]


def get_stage_keys() -> list[str]:
    return [definition.key for definition in STANDARD_STAGE_DEFINITIONS]


def get_stage_labels() -> list[str]:
    return [f"{definition.title} [{definition.key}]" for definition in STANDARD_STAGE_DEFINITIONS]


def get_stage_label_map() -> dict[str, str]:
    return {definition.key: f"{definition.title} [{definition.key}]" for definition in STANDARD_STAGE_DEFINITIONS}


def build_default_config() -> WarcraftConfig:
    return WarcraftConfig()


def _apply_stage_subset(
    profile: EventScheduleProfile,
    enabled_keys: set[str],
    *,
    strict_mode: bool,
) -> None:
    profile.strict_mode = strict_mode
    for slot in profile.slots:
        slot.enabled = slot.key in enabled_keys



