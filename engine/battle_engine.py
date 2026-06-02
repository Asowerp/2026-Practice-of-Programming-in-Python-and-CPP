from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from models import ObjectInstance


@dataclass
class FighterState:
    class_name: str
    display_name: str
    hp: int
    attack: int
    defense: int
    weapon_durability: int
    can_counterattack: bool = True
    broken_penalty: int = 5

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def effective_attack(self, counter: bool = False) -> int:
        attack_value = self.attack
        if self.weapon_durability <= 0:
            attack_value = max(1, attack_value - self.broken_penalty)
        if counter:
            attack_value = max(1, attack_value // 2)
        return max(1, attack_value)


class BattleEngine:
    def __init__(
        self,
        obj1: ObjectInstance,
        obj2: ObjectInstance,
        *,
        label1: str = "",
        label2: str = "",
        max_rounds: int = 12,
    ) -> None:
        self._source_obj1 = deepcopy(obj1)
        self._source_obj2 = deepcopy(obj2)
        self._source_label1 = label1 or f"红方 {obj1.class_name}"
        self._source_label2 = label2 or f"蓝方 {obj2.class_name}"
        self.max_rounds = max(1, int(max_rounds))

        self.fighters = [
            self._build_fighter(self._source_obj1, self._source_label1),
            self._build_fighter(self._source_obj2, self._source_label2),
        ]
        self.round_no = 1
        self.attacker_index = 0
        self.finished = False
        self._stage = "intro"
        self._events: list[tuple[int, str]] = []
        self._event_cursor = 0

    def next_step(self) -> tuple[bool, str]:
        if self.finished and self._stage == "done":
            return True, "战斗已结束。"

        if self._stage == "intro":
            left, right = self.fighters
            self._stage = "attack"
            log = (
                f"战斗开始：{left.display_name} 对阵 {right.display_name}。"
                f" 初始属性分别为 {left.hp}/{left.attack}/{left.defense} 和"
                f" {right.hp}/{right.attack}/{right.defense}。"
            )
            return self._record_event(False, log)

        if self.round_no > self.max_rounds:
            self.finished = True
            self._stage = "done"
            return self._record_event(True, f"达到最大回合数 {self.max_rounds}，本场战斗判定为平局。")

        if self._stage == "attack":
            return self._run_attack_step()
        if self._stage == "counter":
            return self._run_counter_step()
        if self._stage == "summary":
            return self._run_summary_step()

        self.finished = True
        self._stage = "done"
        return self._record_event(True, "战斗状态异常，已停止。")

    def get_all_events(self) -> list[tuple[int, str]]:
        replay = BattleEngine(
            deepcopy(self._source_obj1),
            deepcopy(self._source_obj2),
            label1=self._source_label1,
            label2=self._source_label2,
            max_rounds=self.max_rounds,
        )
        while True:
            finished, _ = replay.next_step()
            if finished:
                break
        return replay.get_recorded_events()

    def get_recorded_events(self) -> list[tuple[int, str]]:
        return list(self._events)

    def get_state_snapshot(self) -> list[dict[str, object]]:
        snapshots: list[dict[str, object]] = []
        for fighter in self.fighters:
            snapshots.append({
                "class_name": fighter.class_name,
                "display_name": fighter.display_name,
                "hp": fighter.hp,
                "attack": fighter.attack,
                "effective_attack": fighter.effective_attack(),
                "defense": fighter.defense,
                "weapon_durability": fighter.weapon_durability,
                "alive": fighter.alive,
                "can_counterattack": fighter.can_counterattack,
            })
        return snapshots

    def _run_attack_step(self) -> tuple[bool, str]:
        attacker = self.fighters[self.attacker_index]
        defender = self.fighters[1 - self.attacker_index]
        damage, broke_now = self._deal_damage(attacker, defender, counter=False)

        log = (
            f"第 {self.round_no} 回合：{attacker.display_name} 主动攻击 {defender.display_name}，"
            f"造成 {damage} 点伤害。{defender.display_name} 剩余 {defender.hp} HP。"
        )
        if broke_now:
            log += " 武器耐久已耗尽，后续攻击力下降。"

        if not defender.alive:
            self.finished = True
            self._stage = "done"
            log += f" {defender.display_name} 被击败，{attacker.display_name} 获胜。"
            return self._record_event(True, log)

        if not defender.can_counterattack:
            self._stage = "summary"
            log += f" {defender.display_name} 不会反击。"
            return self._record_event(False, log)

        self._stage = "counter"
        return self._record_event(False, log)

    def _run_counter_step(self) -> tuple[bool, str]:
        defender = self.fighters[1 - self.attacker_index]
        attacker = self.fighters[self.attacker_index]
        damage, broke_now = self._deal_damage(defender, attacker, counter=True)

        log = (
            f"第 {self.round_no} 回合：{defender.display_name} 发起反击，"
            f"造成 {damage} 点伤害。{attacker.display_name} 剩余 {attacker.hp} HP。"
        )
        if broke_now:
            log += " 反击后武器耐久耗尽，后续攻击力下降。"

        if not attacker.alive:
            self.finished = True
            self._stage = "done"
            log += f" {attacker.display_name} 被击败，{defender.display_name} 获胜。"
            return self._record_event(True, log)

        self._stage = "summary"
        return self._record_event(False, log)

    def _run_summary_step(self) -> tuple[bool, str]:
        left, right = self.fighters
        next_attacker = self.fighters[1 - self.attacker_index]
        log = (
            f"第 {self.round_no} 回合结束：{left.display_name} 为 {left.hp} HP，"
            f"{right.display_name} 为 {right.hp} HP。"
            f" 下一回合由 {next_attacker.display_name} 先手。"
        )

        self.round_no += 1
        self.attacker_index = 1 - self.attacker_index
        self._stage = "attack"
        return self._record_event(False, log)

    def _deal_damage(
        self,
        attacker: FighterState,
        defender: FighterState,
        *,
        counter: bool,
    ) -> tuple[int, bool]:
        attack_value = attacker.effective_attack(counter=counter)
        damage = max(1, attack_value - defender.defense)
        defender.hp = max(0, defender.hp - damage)

        broke_now = False
        if attacker.weapon_durability > 0:
            attacker.weapon_durability -= 1
            if attacker.weapon_durability == 0:
                broke_now = True

        return damage, broke_now

    def _record_event(self, finished: bool, log: str) -> tuple[bool, str]:
        self._events.append((self._event_cursor, log))
        self._event_cursor += 1
        return finished, log

    @staticmethod
    def _build_fighter(obj: ObjectInstance, label: str) -> FighterState:
        values = obj.values or {}
        class_name = obj.class_name or "Warrior"
        return FighterState(
            class_name=class_name,
            display_name=label or class_name,
            hp=max(0, BattleEngine._to_int(values.get("hp"), 100)),
            attack=max(1, BattleEngine._to_int(values.get("attack"), 30)),
            defense=max(0, BattleEngine._to_int(values.get("defense"), 5)),
            weapon_durability=max(0, BattleEngine._to_int(values.get("weapon_durability"), 3)),
            can_counterattack=class_name.lower() != "ninja",
        )

    @staticmethod
    def _to_int(value: object, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
