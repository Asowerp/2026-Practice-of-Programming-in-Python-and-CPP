from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from engine.task3_log_helper import build_log_text
from engine.warcraft_engine import WarcraftConfig, WarcraftEngine, WARRIOR_TYPES, build_schedule_profile


@dataclass(frozen=True)
class Warriors4Case:
    initial_elements: int
    city_count: int
    arrow_attack: int
    lion_loyalty_decay: int
    time_limit: int
    warrior_health: dict[str, int]
    warrior_attack: dict[str, int]

    def to_config(self) -> WarcraftConfig:
        config = WarcraftConfig(
            initial_elements=self.initial_elements,
            city_count=self.city_count,
            arrow_attack=self.arrow_attack,
            lion_loyalty_decay=self.lion_loyalty_decay,
            time_limit=self.time_limit,
        )
        config.warrior_health = dict(self.warrior_health)
        config.warrior_attack = dict(self.warrior_attack)
        return config


def parse_warriors4_input(text: str) -> list[Warriors4Case]:
    values = [int(token) for token in text.split()]
    if not values:
        return []
    iterator = iter(values)
    case_count = next(iterator)
    cases: list[Warriors4Case] = []
    for _ in range(case_count):
        initial_elements, city_count, arrow_attack, lion_loyalty_decay, time_limit = [
            next(iterator) for _ in range(5)
        ]
        health_values = [next(iterator) for _ in range(5)]
        attack_values = [next(iterator) for _ in range(5)]
        cases.append(
            Warriors4Case(
                initial_elements=initial_elements,
                city_count=city_count,
                arrow_attack=arrow_attack,
                lion_loyalty_decay=lion_loyalty_decay,
                time_limit=time_limit,
                warrior_health=dict(zip(WARRIOR_TYPES, health_values)),
                warrior_attack=dict(zip(WARRIOR_TYPES, attack_values)),
            )
        )
    return cases


def render_warriors4_output(cases: list[Warriors4Case], *, max_steps: int = 20000) -> str:
    output_lines: list[str] = []
    for index, case in enumerate(cases, start=1):
        engine = WarcraftEngine(case.to_config(), build_schedule_profile())
        engine.initialize_case()
        executions = engine.run_until_limit(max_steps=max_steps)
        if executions and not executions[-1].finished:
            raise RuntimeError(f"Case {index} did not finish within {max_steps} simulation steps.")
        output_lines.append(f"Case {index}:")
        log_text = build_log_text(engine.export_bundle().events)
        if log_text:
            output_lines.extend(log_text.splitlines())
    return "\n".join(output_lines) + "\n"


def solve_warriors4_file(input_path: str | Path) -> str:
    cases = parse_warriors4_input(Path(input_path).read_text(encoding="utf-8"))
    return render_warriors4_output(cases)
