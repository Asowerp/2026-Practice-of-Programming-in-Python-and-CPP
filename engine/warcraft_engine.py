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


class WarcraftEngine:
    def __init__(
        self,
        config: WarcraftConfig | None = None,
        schedule: EventScheduleProfile | None = None,
    ) -> None:
        self.config = (config or build_default_config()).clone()
        self.schedule = (schedule or build_schedule_profile()).clone()
        self.reset()

    def reset(self) -> None:
        self.headquarters = {
            "red": HeadquarterState("red", self.config.initial_elements),
            "blue": HeadquarterState("blue", self.config.initial_elements),
        }
        self.cities = {
            city_id: CityState(city_id)
            for city_id in range(1, self.config.city_count + 1)
        }
        self.warriors: list[WarriorUnit] = []
        self.events: list[EventRecord] = []
        self.current_hour = 0
        self.current_slot_index = 0
        self.finished = False
        self.war_over = False
        self.case_initialized = False
        self.last_stage: StageExecution | None = None

    def initialize_case(self) -> str:
        self.reset()
        self.case_initialized = True
        enabled = self.schedule.get_enabled_slots()
        return (
            f"Case 初始化完成：M={self.config.initial_elements}, N={self.config.city_count}, "
            f"R={self.config.arrow_attack}, K={self.config.lion_loyalty_decay}, T={self.config.time_limit}。"
            f" 当前启用 {len(enabled)} 个阶段。"
        )

    def next_stage(self) -> StageExecution:
        if not self.case_initialized:
            return StageExecution(0, "", "", summary="请先初始化 Case。", finished=False)

        if self.finished:
            return StageExecution(
                self.config.time_limit,
                "",
                "",
                summary="模拟已结束。",
                finished=True,
            )

        enabled_slots = self.schedule.get_enabled_slots()
        if not enabled_slots:
            self.finished = True
            return StageExecution(0, "", "", summary="当前没有启用任何阶段。", finished=True)

        if self.current_slot_index >= len(enabled_slots):
            self.current_slot_index = 0
            self.current_hour += 1

        slot = enabled_slots[self.current_slot_index]
        total_minutes = self.current_hour * 60 + slot.minute
        if total_minutes > self.config.time_limit:
            self.finished = True
            execution = StageExecution(total_minutes, slot.key, slot.title, summary="已到达时间上限。", finished=True)
            self.last_stage = execution
            return execution

        self.current_slot_index += 1
        events_before = len(self.events)
        self._run_stage(slot, total_minutes)
        stage_events = self.events[events_before:]

        summary = f"执行 {slot.title}，产生 {len(stage_events)} 条事件。"
        if self.war_over:
            self.finished = True
            summary += " 战争已结束。"

        execution = StageExecution(
            total_minutes=total_minutes,
            slot_key=slot.key,
            slot_title=slot.title,
            events=stage_events,
            summary=summary,
            finished=self.finished,
        )
        self.last_stage = execution
        return execution

    def run_next_hour(self, max_steps: int = 20) -> list[StageExecution]:
        results: list[StageExecution] = []
        if not self.case_initialized:
            return [StageExecution(0, "", "", summary="请先初始化 Case。")]

        start_hour = self.current_hour
        for _ in range(max_steps):
            execution = self.next_stage()
            results.append(execution)
            if execution.finished:
                break
            if execution.total_minutes // 60 > start_hour:
                break
            if self.current_slot_index == 0 and self.current_hour > start_hour:
                break
        return results

    def run_until_limit(self, max_steps: int = 500) -> list[StageExecution]:
        results: list[StageExecution] = []
        for _ in range(max_steps):
            execution = self.next_stage()
            results.append(execution)
            if execution.finished:
                break
        return results

    def export_bundle(self) -> SimulationBundle:
        mode_label = "标准题面模式" if self.schedule.strict_mode else "自定义教学模式"
        return SimulationBundle(
            mode_label=mode_label,
            config=self.config.clone(),
            schedule=self.schedule.clone(),
            events=list(self.events),
            world_summary=self.build_world_summary(),
        )

    def build_schedule_summary(self) -> str:
        lines = [f"当前日程模板: {self.schedule.name}"]
        lines.append("启用阶段:")
        for slot in self.schedule.get_enabled_slots():
            lines.append(f"- {slot.title}: 第 {slot.minute:02d} 分")
        return "\n".join(lines)

    def build_world_summary(self) -> str:
        red = self.headquarters["red"]
        blue = self.headquarters["blue"]
        lines = [
            f"红方司令部: elements={red.elements}, 已造={red.total_warriors}, 敌人到达={red.enemy_arrivals}",
            f"蓝方司令部: elements={blue.elements}, 已造={blue.total_warriors}, 敌人到达={blue.enemy_arrivals}",
        ]
        for city_id in range(1, self.config.city_count + 1):
            city = self.cities[city_id]
            red_names = ", ".join(self._warrior_short_name(unit) for unit in self._alive_warriors_at(city_id, "red")) or "无"
            blue_names = ", ".join(self._warrior_short_name(unit) for unit in self._alive_warriors_at(city_id, "blue")) or "无"
            flag = city.flag or "无旗"
            lines.append(
                f"城市 {city_id}: elements={city.elements}, flag={flag}, red=[{red_names}], blue=[{blue_names}]"
            )
        return "\n".join(lines)

    def build_city_summary(self, city_id: int) -> str:
        if city_id < 1 or city_id > self.config.city_count:
            return f"城市 {city_id} 不存在。"
        city = self.cities[city_id]
        lines = [
            f"城市 {city_id}",
            f"生命元: {city.elements}",
            f"旗帜: {city.flag or '无'}",
            f"连续获胜方: {city.last_winner or '无'}",
            f"连胜计数: {city.win_streak}",
            f"红方: {', '.join(self._warrior_short_name(unit) for unit in self._alive_warriors_at(city_id, 'red')) or '无'}",
            f"蓝方: {', '.join(self._warrior_short_name(unit) for unit in self._alive_warriors_at(city_id, 'blue')) or '无'}",
        ]
        return "\n".join(lines)

    def build_headquarter_summary(self, camp: str) -> str:
        headquarter = self.headquarters[camp]
        order = RED_PRODUCTION_ORDER if camp == "red" else BLUE_PRODUCTION_ORDER
        next_kind = order[headquarter.next_index]
        return (
            f"{camp} headquarter\n"
            f"elements: {headquarter.elements}\n"
            f"next warrior: {next_kind}\n"
            f"total warriors: {headquarter.total_warriors}\n"
            f"enemy arrivals: {headquarter.enemy_arrivals}"
        )

    def _run_stage(self, slot: EventSlotConfig, total_minutes: int) -> None:
        handlers = {
            "spawn": self._run_spawn_stage,
            "lion_escape": self._run_lion_escape_stage,
            "march": self._run_march_stage,
            "city_produce": self._run_city_produce_stage,
            "collect_elements": self._run_collect_stage,
            "arrow": self._run_arrow_stage,
            "bomb": self._run_bomb_stage,
            "battle": self._run_battle_stage,
            "headquarter_report": self._run_headquarter_report_stage,
            "weapon_report": self._run_weapon_report_stage,
        }
        handler = handlers.get(slot.key)
        if handler is not None:
            handler(total_minutes)

    def _run_spawn_stage(self, total_minutes: int) -> None:
        for camp in CAMPS:
            warrior = self._spawn_next_warrior(camp)
            if warrior is None:
                continue
            location_order = 0 if camp == "red" else self.config.city_count + 1
            self._add_event(
                total_minutes,
                "spawn",
                location_order,
                f"{camp} {warrior.kind} {warrior.warrior_id} born",
            )
            if warrior.kind == "dragon" and warrior.morale is not None:
                self._add_event(
                    total_minutes,
                    "spawn",
                    location_order,
                    f"Its morale is {warrior.morale:.2f}",
                )
            if warrior.kind == "lion" and warrior.loyalty is not None:
                self._add_event(
                    total_minutes,
                    "spawn",
                    location_order,
                    f"Its loyalty is {warrior.loyalty}",
                )

    def _run_lion_escape_stage(self, total_minutes: int) -> None:
        runaways = [
            unit for unit in self.warriors
            if unit.alive
            and not unit.removed
            and unit.kind == "lion"
            and (unit.loyalty or 0) <= 0
            and not unit.reached_enemy_headquarter
        ]
        runaways.sort(key=lambda unit: (unit.position, 0 if unit.camp == "red" else 1, unit.warrior_id))
        for unit in runaways:
            unit.alive = False
            unit.removed = True
            self._add_event(
                total_minutes,
                "lion_escape",
                unit.position,
                f"{unit.camp} lion {unit.warrior_id} ran away",
            )

    def _run_march_stage(self, total_minutes: int) -> None:
        movers = [unit for unit in self.warriors if unit.alive and not unit.removed and not unit.reached_enemy_headquarter]
        for unit in movers:
            unit.move_one_step(self.config.city_count)

        march_events: list[tuple[int, int, str]] = []
        taken_events: list[tuple[int, str]] = []
        for unit in sorted(movers, key=lambda item: (item.position, 0 if item.camp == "red" else 1, item.warrior_id)):
            if unit.reached_enemy_headquarter:
                enemy_camp = "blue" if unit.camp == "red" else "red"
                self.headquarters[enemy_camp].enemy_arrivals += 1
                march_events.append((unit.position, 0 if unit.camp == "red" else 1, self._format_headquarter_reached(unit)))
                if self.headquarters[enemy_camp].enemy_arrivals >= 2:
                    location_order = 0 if enemy_camp == "red" else self.config.city_count + 1
                    taken_events.append((location_order, f"{enemy_camp} headquarter was taken"))
            else:
                march_events.append((unit.position, 0 if unit.camp == "red" else 1, self._format_march(unit)))

        for position, camp_order, description in march_events:
            self._add_event(total_minutes, "march", position * 10 + camp_order, description)
        for location_order, description in taken_events:
            self._add_event(total_minutes, "march", location_order * 10 + 9, description)

        if taken_events:
            self.war_over = True

    def _run_city_produce_stage(self, total_minutes: int) -> None:
        _ = total_minutes
        for city in self.cities.values():
            city.elements += 10

    def _run_collect_stage(self, total_minutes: int) -> None:
        for city_id, city in self.cities.items():
            if city.elements <= 0:
                continue
            red_units = self._alive_warriors_at(city_id, "red")
            blue_units = self._alive_warriors_at(city_id, "blue")
            if len(red_units) + len(blue_units) != 1:
                continue
            unit = red_units[0] if red_units else blue_units[0]
            self.headquarters[unit.camp].elements += city.elements
            earned = city.elements
            city.elements = 0
            self._add_event(
                total_minutes,
                "collect_elements",
                city_id,
                f"{unit.camp} {unit.kind} {unit.warrior_id} earned {earned} elements for his headquarter",
            )

    def _run_arrow_stage(self, total_minutes: int) -> None:
        shots: list[tuple[int, int, str]] = []
        shooters = [unit for unit in self.warriors if unit.alive and not unit.removed and unit.weapons.has_arrow()]
        shooters.sort(key=lambda unit: (unit.position, 0 if unit.camp == "red" else 1, unit.warrior_id))
        for shooter in shooters:
            target_position = shooter.position + 1 if shooter.camp == "red" else shooter.position - 1
            if target_position <= 0 or target_position > self.config.city_count:
                continue
            target = self._first_alive_enemy_at(target_position, shooter.camp)
            if target is None:
                continue
            shooter.weapons.use_arrow()
            target.hp -= self.config.arrow_attack
            killed = target.hp <= 0
            if killed:
                target.hp = 0
                target.alive = False
                target.death_reason = "arrow"
                target.death_time = total_minutes
                shots.append((shooter.position, 0 if shooter.camp == "red" else 1, f"{shooter.camp} {shooter.kind} {shooter.warrior_id} shot and killed {target.camp} {target.kind} {target.warrior_id}"))
            else:
                shots.append((shooter.position, 0 if shooter.camp == "red" else 1, f"{shooter.camp} {shooter.kind} {shooter.warrior_id} shot"))
        for position, camp_order, description in shots:
            self._add_event(total_minutes, "arrow", position * 10 + camp_order, description)

    def _run_bomb_stage(self, total_minutes: int) -> None:
        bomb_events: list[tuple[int, int, str]] = []
        for city_id in range(1, self.config.city_count + 1):
            red = self._first_alive_warrior_at(city_id, "red")
            blue = self._first_alive_warrior_at(city_id, "blue")
            if red is None or blue is None:
                continue
            attacker, defender = self._resolve_attacker(city_id, red, blue)
            if attacker is None or defender is None:
                continue

            attacker_dies, defender_dies = self._predict_battle_deaths(attacker, defender)
            user = None
            victim = None
            if attacker.weapons.has_bomb() and attacker_dies:
                user, victim = attacker, defender
            elif defender.weapons.has_bomb() and defender_dies:
                user, victim = defender, attacker

            if user is None or victim is None:
                continue

            user.weapons.bomb = False
            user.alive = False
            user.death_reason = "bomb"
            user.death_time = total_minutes
            victim.alive = False
            victim.death_reason = "bomb"
            victim.death_time = total_minutes
            bomb_events.append(
                (
                    city_id,
                    0 if user.camp == "red" else 1,
                    f"{user.camp} {user.kind} {user.warrior_id} used a bomb and killed {victim.camp} {victim.kind} {victim.warrior_id}",
                )
            )

        for city_id, camp_order, description in bomb_events:
            self._add_event(total_minutes, "bomb", city_id * 10 + camp_order, description)

    def _run_battle_stage(self, total_minutes: int) -> None:
        battle_results: list[dict[str, Any]] = []

        for city_id in range(1, self.config.city_count + 1):
            red_alive = self._first_alive_warrior_at(city_id, "red")
            blue_alive = self._first_alive_warrior_at(city_id, "blue")
            red_arrow_dead = self._first_recent_arrow_dead_at(city_id, "red", total_minutes)
            blue_arrow_dead = self._first_recent_arrow_dead_at(city_id, "blue", total_minutes)

            if red_alive is None and blue_alive is None:
                continue

            if red_alive is not None and blue_alive is None and blue_arrow_dead is not None:
                battle_results.append(self._build_arrow_victory(city_id, total_minutes, red_alive, blue_arrow_dead))
                continue
            if blue_alive is not None and red_alive is None and red_arrow_dead is not None:
                battle_results.append(self._build_arrow_victory(city_id, total_minutes, blue_alive, red_arrow_dead))
                continue
            if red_alive is None or blue_alive is None:
                continue

            attacker, defender = self._resolve_attacker(city_id, red_alive, blue_alive)
            if attacker is None or defender is None:
                continue

            battle_results.append(self._simulate_battle(city_id, total_minutes, attacker, defender))

        self._apply_battle_rewards(battle_results)
        self._collect_battle_city_elements(battle_results)
        for result in battle_results:
            for description in result.get("event_descriptions", []):
                self._add_event(total_minutes, "battle", result["location_order"], description)
            if result.get("city_elements_earned", 0) > 0:
                self._add_event(
                    total_minutes,
                    "battle",
                    result["location_order"] + 1,
                    f"{result['winner'].camp} {result['winner'].kind} {result['winner'].warrior_id} earned {result['city_elements_earned']} elements for his headquarter",
                )
            if result.get("flag_raised"):
                self._add_event(
                    total_minutes,
                    "battle",
                    result["location_order"] + 2,
                    f"{result['flag_raised']} flag raised in city {result['city_id']}",
                )
            if result.get("yell"):
                self._add_event(
                    total_minutes,
                    "battle",
                    result["location_order"] + 3,
                    result["yell"],
                )

    def _run_headquarter_report_stage(self, total_minutes: int) -> None:
        self._add_event(
            total_minutes,
            "headquarter_report",
            0,
            f"{self.headquarters['red'].elements} elements in red headquarter",
        )
        self._add_event(
            total_minutes,
            "headquarter_report",
            (self.config.city_count + 1) * 10,
            f"{self.headquarters['blue'].elements} elements in blue headquarter",
        )

    def _run_weapon_report_stage(self, total_minutes: int) -> None:
        red_units = sorted(
            self._alive_warriors("red"),
            key=lambda unit: (unit.position, unit.warrior_id),
        )
        blue_units = sorted(
            self._alive_warriors("blue"),
            key=lambda unit: (unit.position, unit.warrior_id),
        )
        for unit in red_units + blue_units:
            self._add_event(
                total_minutes,
                "weapon_report",
                unit.position * 10 + (0 if unit.camp == "red" else 5),
                f"{unit.camp} {unit.kind} {unit.warrior_id} has {unit.weapons.report_text()}",
            )

    def _spawn_next_warrior(self, camp: str) -> WarriorUnit | None:
        headquarter = self.headquarters[camp]
        order = RED_PRODUCTION_ORDER if camp == "red" else BLUE_PRODUCTION_ORDER
        kind = order[headquarter.next_index]
        cost = self.config.warrior_health[kind]
        if headquarter.elements < cost:
            return None

        headquarter.elements -= cost
        headquarter.total_warriors += 1
        headquarter.next_index = (headquarter.next_index + 1) % len(order)
        warrior_id = headquarter.total_warriors
        position = 0 if camp == "red" else self.config.city_count + 1
        warrior = WarriorUnit(
            camp=camp,
            kind=kind,
            warrior_id=warrior_id,
            hp=cost,
            attack=self.config.warrior_attack[kind],
            position=position,
            weapons=self._build_initial_weapons(kind, warrior_id, self.config.warrior_attack[kind]),
        )
        if kind == "dragon":
            warrior.morale = headquarter.elements / cost
        if kind == "lion":
            warrior.loyalty = headquarter.elements
        self.warriors.append(warrior)
        return warrior

    def _build_initial_weapons(self, kind: str, warrior_id: int, attack: int) -> WeaponSet:
        weapons = WeaponSet()
        if kind in {"dragon", "iceman"}:
            self._give_weapon_by_index(weapons, warrior_id % 3, attack)
        elif kind == "ninja":
            self._give_weapon_by_index(weapons, warrior_id % 3, attack)
            self._give_weapon_by_index(weapons, (warrior_id + 1) % 3, attack)
        return weapons

    @staticmethod
    def _give_weapon_by_index(weapons: WeaponSet, index: int, attack: int) -> None:
        if index == 0:
            sword_attack = attack // 5
            if sword_attack > 0:
                weapons.sword_attack = sword_attack
        elif index == 1:
            weapons.bomb = True
        elif index == 2:
            weapons.arrow_uses = 3

    def _resolve_attacker(
        self,
        city_id: int,
        red: WarriorUnit,
        blue: WarriorUnit,
    ) -> tuple[WarriorUnit | None, WarriorUnit | None]:
        city = self.cities[city_id]
        if city.flag == "red":
            return red, blue
        if city.flag == "blue":
            return blue, red
        return (red, blue) if city_id % 2 == 1 else (blue, red)

    def _predict_battle_deaths(self, attacker: WarriorUnit, defender: WarriorUnit) -> tuple[bool, bool]:
        defender_hp = defender.hp - attacker.attack - attacker.weapons.sword_attack
        defender_dies = defender_hp <= 0
        attacker_dies = False
        if not defender_dies and defender.can_counterattack():
            attacker_hp = attacker.hp - defender.attack // 2 - defender.weapons.sword_attack
            attacker_dies = attacker_hp <= 0
        return attacker_dies, defender_dies

    def _simulate_battle(
        self,
        city_id: int,
        total_minutes: int,
        attacker: WarriorUnit,
        defender: WarriorUnit,
    ) -> dict[str, Any]:
        _ = total_minutes
        city = self.cities[city_id]
        location_order = city_id * 10
        event_descriptions: list[str] = []

        attacker_pre_hp = attacker.hp
        defender_pre_hp = defender.hp
        attacker_pre_sword = attacker.weapons.sword_attack
        defender_pre_sword = defender.weapons.sword_attack

        event_descriptions.append(
            f"{attacker.camp} {attacker.kind} {attacker.warrior_id} attacked {defender.camp} {defender.kind} {defender.warrior_id} in city {city_id} with {attacker.hp} elements and force {attacker.attack}"
        )

        defender.hp -= attacker.attack + attacker.weapons.sword_attack
        if attacker_pre_sword > 0:
            attacker.weapons.blunt_sword()

        winner: WarriorUnit | None = None
        loser: WarriorUnit | None = None
        yell_text = ""

        if defender.hp <= 0:
            defender.hp = 0
            defender.alive = False
            defender.death_reason = "battle"
            winner = attacker
            loser = defender
            event_descriptions.append(
                f"{defender.camp} {defender.kind} {defender.warrior_id} was killed in city {city_id}"
            )
        elif defender.can_counterattack():
            event_descriptions.append(
                f"{defender.camp} {defender.kind} {defender.warrior_id} fought back against {attacker.camp} {attacker.kind} {attacker.warrior_id} in city {city_id}"
            )
            attacker.hp -= defender.attack // 2 + defender.weapons.sword_attack
            if defender_pre_sword > 0:
                defender.weapons.blunt_sword()
            if attacker.hp <= 0:
                attacker.hp = 0
                attacker.alive = False
                attacker.death_reason = "battle"
                winner = defender
                loser = attacker
                event_descriptions.append(
                    f"{attacker.camp} {attacker.kind} {attacker.warrior_id} was killed in city {city_id}"
                )

        city_elements_earned = 0
        flag_raised = ""

        if winner is not None and loser is not None:
            if loser.kind == "lion":
                winner.hp += defender_pre_hp if loser is defender else attacker_pre_hp

            if winner.kind == "wolf":
                winner.weapons.capture_from(loser.weapons)

            if winner.kind == "dragon" and winner.morale is not None:
                winner.morale += 0.2
            if loser.kind == "dragon" and loser.morale is not None:
                loser.morale -= 0.2

            if loser.kind == "lion" and loser.loyalty is not None:
                loser.loyalty -= self.config.lion_loyalty_decay

            city_elements_earned = city.elements
            flag_raised = self._update_city_flag(city, winner.camp)

            if attacker.kind == "dragon" and attacker.alive and attacker.morale is not None and attacker.morale > 0.8:
                yell_text = f"{attacker.camp} dragon {attacker.warrior_id} yelled in city {city_id}"
        else:
            if attacker.kind == "dragon" and attacker.morale is not None:
                attacker.morale -= 0.2
                if attacker.alive and attacker.morale > 0.8:
                    yell_text = f"{attacker.camp} dragon {attacker.warrior_id} yelled in city {city_id}"
            if defender.kind == "dragon" and defender.morale is not None:
                defender.morale -= 0.2
            if attacker.kind == "lion" and attacker.loyalty is not None:
                attacker.loyalty -= self.config.lion_loyalty_decay
            if defender.kind == "lion" and defender.loyalty is not None:
                defender.loyalty -= self.config.lion_loyalty_decay
            city.last_winner = ""
            city.win_streak = 0

        return {
            "city_id": city_id,
            "winner": winner,
            "loser": loser,
            "event_descriptions": event_descriptions,
            "city_elements_earned": city_elements_earned,
            "flag_raised": flag_raised,
            "yell": yell_text,
            "location_order": location_order,
        }

    def _build_arrow_victory(
        self,
        city_id: int,
        total_minutes: int,
        winner: WarriorUnit,
        loser: WarriorUnit,
    ) -> dict[str, Any]:
        _ = total_minutes
        city = self.cities[city_id]
        if winner.kind == "wolf":
            winner.weapons.capture_from(loser.weapons)
        if winner.kind == "dragon" and winner.morale is not None:
            winner.morale += 0.2
        if loser.kind == "dragon" and loser.morale is not None:
            loser.morale -= 0.2
        if loser.kind == "lion" and loser.loyalty is not None:
            loser.loyalty -= self.config.lion_loyalty_decay

        city_elements_earned = city.elements
        flag_raised = self._update_city_flag(city, winner.camp)
        yell_text = ""
        red = winner if winner.camp == "red" else loser
        blue = winner if winner.camp == "blue" else loser
        attacker, _ = self._resolve_attacker(city_id, red, blue)
        if attacker is winner and winner.kind == "dragon" and winner.morale is not None and winner.morale > 0.8:
            yell_text = f"{winner.camp} dragon {winner.warrior_id} yelled in city {city_id}"
        return {
            "city_id": city_id,
            "winner": winner,
            "loser": loser,
            "event_descriptions": [],
            "city_elements_earned": city_elements_earned,
            "flag_raised": flag_raised,
            "yell": yell_text,
            "location_order": city_id * 10,
        }

    def _apply_battle_rewards(self, battle_results: list[dict[str, Any]]) -> None:
        winners_by_camp = {"red": [], "blue": []}
        for result in battle_results:
            winner = result.get("winner")
            if isinstance(winner, WarriorUnit) and winner.alive:
                winners_by_camp[winner.camp].append(result)

        winners_by_camp["red"].sort(key=lambda result: result["city_id"], reverse=True)
        winners_by_camp["blue"].sort(key=lambda result: result["city_id"])

        for camp, results in winners_by_camp.items():
            headquarter = self.headquarters[camp]
            for result in results:
                winner = result["winner"]
                if headquarter.elements >= 8:
                    headquarter.elements -= 8
                    winner.hp += 8

    def _collect_battle_city_elements(self, battle_results: list[dict[str, Any]]) -> None:
        for result in battle_results:
            winner = result.get("winner")
            city_id = result.get("city_id")
            earned = int(result.get("city_elements_earned", 0))
            if not isinstance(winner, WarriorUnit) or not earned or not isinstance(city_id, int):
                continue
            self.headquarters[winner.camp].elements += earned
            self.cities[city_id].elements = 0

    def _update_city_flag(self, city: CityState, winner_camp: str) -> str:
        if city.last_winner == winner_camp:
            city.win_streak += 1
        else:
            city.last_winner = winner_camp
            city.win_streak = 1

        if city.win_streak >= 2 and city.flag != winner_camp:
            city.flag = winner_camp
            return winner_camp
        return ""

    def _format_march(self, unit: WarriorUnit) -> str:
        return (
            f"{unit.camp} {unit.kind} {unit.warrior_id} marched to city {unit.position} "
            f"with {unit.hp} elements and force {unit.attack}"
        )

    def _format_headquarter_reached(self, unit: WarriorUnit) -> str:
        enemy = "blue" if unit.camp == "red" else "red"
        return (
            f"{unit.camp} {unit.kind} {unit.warrior_id} reached {enemy} headquarter "
            f"with {unit.hp} elements and force {unit.attack}"
        )

    def _add_event(
        self,
        total_minutes: int,
        stage_key: str,
        location_order: int,
        description: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.events.append(EventRecord(
            total_minutes=total_minutes,
            stage_key=stage_key,
            location_order=location_order,
            description=description,
            payload=payload or {},
        ))

    def _alive_warriors(self, camp: str | None = None) -> list[WarriorUnit]:
        return [
            unit
            for unit in self.warriors
            if unit.alive and not unit.removed and (camp is None or unit.camp == camp)
        ]

    def _alive_warriors_at(self, position: int, camp: str) -> list[WarriorUnit]:
        return [
            unit for unit in self._alive_warriors(camp)
            if unit.position == position
        ]

    def _first_alive_warrior_at(self, position: int, camp: str) -> WarriorUnit | None:
        warriors = self._alive_warriors_at(position, camp)
        return warriors[0] if warriors else None

    def _first_alive_enemy_at(self, position: int, shooter_camp: str) -> WarriorUnit | None:
        enemy_camp = "blue" if shooter_camp == "red" else "red"
        return self._first_alive_warrior_at(position, enemy_camp)

    def _first_recent_arrow_dead_at(
        self,
        position: int,
        camp: str,
        total_minutes: int,
    ) -> WarriorUnit | None:
        for unit in self.warriors:
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

    @staticmethod
    def _warrior_short_name(unit: WarriorUnit) -> str:
        return f"{unit.camp}-{unit.kind}-{unit.warrior_id}"
