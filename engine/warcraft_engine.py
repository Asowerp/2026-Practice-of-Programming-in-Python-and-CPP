from __future__ import annotations

from typing import Any

from engine.warcraft_battle_rules import (
    predict_battle_deaths,
    resolve_attacker,
    update_city_flag,
)
from engine.warcraft_factory import (
    build_initial_weapons,
    create_next_warrior,
    give_weapon_by_index,
)
from engine.warcraft_queries import (
    alive_warriors,
    alive_warriors_at,
    first_alive_enemy_at,
    first_alive_warrior_at,
    first_recent_arrow_dead_at,
    warrior_short_name,
)
from engine.warcraft_reporting import (
    format_headquarter_reached,
    format_march,
)

from engine.warcraft_models import (
    BLUE_PRODUCTION_ORDER,
    CAMPS,
    RED_PRODUCTION_ORDER,
    STANDARD_STAGE_DEFINITIONS,
    STAGE_DEFINITION_MAP,
    WEAPON_TYPES,
    WARRIOR_TYPES,
    CityState,
    EventRecord,
    EventScheduleProfile,
    EventSlotConfig,
    HeadquarterState,
    SimulationBundle,
    StageDefinition,
    StageExecution,
    WarcraftConfig,
    WarriorUnit,
    WeaponSet,
    build_default_config,
    build_schedule_profile,
    format_time,
    get_schedule_profile_names,
    get_stage_keys,
    get_stage_label_map,
    get_stage_labels,
)
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
                    {"omit_time": True},
                )
            if warrior.kind == "lion" and warrior.loyalty is not None:
                self._add_event(
                    total_minutes,
                    "spawn",
                    location_order,
                    f"Its loyalty is {warrior.loyalty}",
                    {"omit_time": True},
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
            if result.get("yell"):
                self._add_event(
                    total_minutes,
                    "battle",
                    result["location_order"] + 1,
                    result["yell"],
                )
            if result.get("city_elements_earned", 0) > 0:
                self._add_event(
                    total_minutes,
                    "battle",
                    result["location_order"] + 2,
                    f"{result['winner'].camp} {result['winner'].kind} {result['winner'].warrior_id} earned {result['city_elements_earned']} elements for his headquarter",
                )
            if result.get("flag_raised"):
                self._add_event(
                    total_minutes,
                    "battle",
                    result["location_order"] + 3,
                    f"{result['flag_raised']} flag raised in city {result['city_id']}",
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
            report_order = unit.position if unit.camp == "red" else self.config.city_count + 2 + unit.position
            self._add_event(
                total_minutes,
                "weapon_report",
                report_order,
                f"{unit.camp} {unit.kind} {unit.warrior_id} has {unit.weapons.report_text()}",
            )

    def _spawn_next_warrior(self, camp: str) -> WarriorUnit | None:
        warrior = create_next_warrior(camp, self.headquarters[camp], self.config)
        if warrior is None:
            return None
        self.warriors.append(warrior)
        return warrior

    def _build_initial_weapons(self, kind: str, warrior_id: int, attack: int) -> WeaponSet:
        return build_initial_weapons(kind, warrior_id, attack)

    @staticmethod
    def _give_weapon_by_index(weapons: WeaponSet, index: int, attack: int) -> None:
        give_weapon_by_index(weapons, index, attack)

    def _resolve_attacker(
        self,
        city_id: int,
        red: WarriorUnit,
        blue: WarriorUnit,
    ) -> tuple[WarriorUnit | None, WarriorUnit | None]:
        return resolve_attacker(city_id, self.cities[city_id], red, blue)

    def _predict_battle_deaths(self, attacker: WarriorUnit, defender: WarriorUnit) -> tuple[bool, bool]:
        return predict_battle_deaths(attacker, defender)

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
        yell_text = ""
        red = winner if winner.camp == "red" else loser
        blue = winner if winner.camp == "blue" else loser
        attacker, _ = self._resolve_attacker(city_id, red, blue)
        if attacker is winner and winner.kind == "dragon" and winner.morale is not None and winner.morale > 0.8:
            yell_text = f"{winner.camp} dragon {winner.warrior_id} yelled in city {city_id}"
        flag_raised = self._update_city_flag(city, winner.camp)
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
        return update_city_flag(city, winner_camp)

    def _format_march(self, unit: WarriorUnit) -> str:
        return format_march(unit)

    def _format_headquarter_reached(self, unit: WarriorUnit) -> str:
        return format_headquarter_reached(unit)

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
        return alive_warriors(self.warriors, camp)

    def _alive_warriors_at(self, position: int, camp: str) -> list[WarriorUnit]:
        return alive_warriors_at(self.warriors, position, camp)

    def _first_alive_warrior_at(self, position: int, camp: str) -> WarriorUnit | None:
        return first_alive_warrior_at(self.warriors, position, camp)

    def _first_alive_enemy_at(self, position: int, shooter_camp: str) -> WarriorUnit | None:
        return first_alive_enemy_at(self.warriors, position, shooter_camp)

    def _first_recent_arrow_dead_at(
        self,
        position: int,
        camp: str,
        total_minutes: int,
    ) -> WarriorUnit | None:
        return first_recent_arrow_dead_at(self.warriors, position, camp, total_minutes)

    @staticmethod
    def _warrior_short_name(unit: WarriorUnit) -> str:
        return warrior_short_name(unit)

