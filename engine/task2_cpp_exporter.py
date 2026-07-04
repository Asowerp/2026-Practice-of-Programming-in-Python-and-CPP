from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent, indent

from engine.task3_log_helper import build_log_text
from engine.warcraft_engine import EventScheduleProfile, WarcraftConfig, WarcraftEngine


WARRIOR_ORDER = ("dragon", "ninja", "iceman", "lion", "wolf")


def export_task2_cpp_project(
    output_dir: str,
    config: WarcraftConfig,
    schedule: EventScheduleProfile,
    include_module_guide: bool = True,
) -> list[str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    config_copy = config.clone()
    schedule_copy = schedule.clone()
    expected_log = _build_expected_log(config_copy, schedule_copy)

    file_map = {
        "task2_solution.cpp": _build_standalone_cpp(config_copy, schedule_copy),
        "README.txt": _build_readme(config_copy, schedule_copy),
        "expected_log.txt": expected_log,
    }
    if include_module_guide:
        file_map["MODULE_DESIGN.md"] = _build_module_design_doc(config_copy, schedule_copy)

    for file_name, content in file_map.items():
        (output_path / file_name).write_text(content, encoding="utf-8")

    return list(file_map)


INCLUDE_BLOCK = dedent(
    """
    #include <algorithm>
    #include <cstddef>
    #include <iomanip>
    #include <iostream>
    #include <map>
    #include <optional>
    #include <sstream>
    #include <string>
    #include <tuple>
    #include <utility>
    #include <vector>
    """
).strip()


def _build_standalone_cpp(config: WarcraftConfig, schedule: EventScheduleProfile) -> str:
    sections = [
        "// Task2 standalone solution generated from the Python reference engine.",
        "// Single translation unit, ready for an online judge submission.",
        "",
        INCLUDE_BLOCK,
        "",
        _build_engine_declarations(),
        "",
        _build_engine_definitions(),
        "",
        _build_generated_case(config, schedule),
        "",
        _build_main(),
    ]
    return "\n".join(sections).strip() + "\n"


def _build_expected_log(config: WarcraftConfig, schedule: EventScheduleProfile) -> str:
    engine = WarcraftEngine(config, schedule)
    engine.initialize_case()
    max_steps = _recommended_max_steps(config, schedule)
    executions = engine.run_until_limit(max_steps=max_steps)
    if executions and not executions[-1].finished:
        raise RuntimeError("Python reference engine did not finish within the export safety step limit.")
    log_text = build_log_text(engine.export_bundle().events)
    return "Case 1:\n" + (log_text + "\n" if log_text else "")


def _recommended_max_steps(config: WarcraftConfig, schedule: EventScheduleProfile) -> int:
    enabled_count = max(1, len(schedule.get_enabled_slots()))
    return max(10, ((config.time_limit // 60) + 2) * enabled_count + 5)


def _build_generated_case(config: WarcraftConfig, schedule: EventScheduleProfile) -> str:
    health_lines = [f'{{{_cpp_string(kind)}, {int(config.warrior_health[kind])}}}' for kind in WARRIOR_ORDER]
    attack_lines = [f'{{{_cpp_string(kind)}, {int(config.warrior_attack[kind])}}}' for kind in WARRIOR_ORDER]
    health_body = indent(",\n".join(health_lines), " " * 12)
    attack_body = indent(",\n".join(attack_lines), " " * 12)
    slot_lines = [
        "{"
        f"{_cpp_string(slot.key)}, "
        f"{_cpp_string(slot.title)}, "
        f"{int(slot.default_minute)}, "
        f"{int(slot.minute)}, "
        f"{_cpp_bool(slot.enabled)}, "
        f"{int(slot.order_index)}"
        "}"
        for slot in schedule.slots
    ]
    config_body = dedent(
        f"""
        config.initial_elements = {int(config.initial_elements)};
        config.city_count = {int(config.city_count)};
        config.arrow_attack = {int(config.arrow_attack)};
        config.lion_loyalty_decay = {int(config.lion_loyalty_decay)};
        config.time_limit = {int(config.time_limit)};
        config.warrior_health = {{
        {health_body}
        }};
        config.warrior_attack = {{
        {attack_body}
        }};
        """
    ).strip()
    slot_body = indent(",\n".join(slot_lines), " " * 12)
    schedule_body = dedent(
        f"""
        profile.name = {_cpp_string(schedule.name)};
        profile.strict_mode = {_cpp_bool(schedule.strict_mode)};
        profile.slots = {{
        {slot_body}
        }};
        """
    ).strip()
    max_steps = _recommended_max_steps(config, schedule)
    return dedent(
        """
        WarcraftConfig buildGeneratedConfig() {
            WarcraftConfig config;
        __CONFIG_BODY__
            return config;
        }

        EventScheduleProfile buildGeneratedSchedule() {
            EventScheduleProfile profile;
        __SCHEDULE_BODY__
            return profile;
        }

        int recommendedMaxSteps() {
            return __MAX_STEPS__;
        }
        """
    ).strip().replace("__CONFIG_BODY__", indent(config_body, " " * 4)).replace(
        "__SCHEDULE_BODY__", indent(schedule_body, " " * 4)
    ).replace("__MAX_STEPS__", str(max_steps))


def _build_main() -> str:
    return dedent(
        """
        int main() {
            const WarcraftConfig config = buildGeneratedConfig();
            const EventScheduleProfile schedule = buildGeneratedSchedule();

            WarcraftEngine engine(config, schedule);
            engine.initializeCase();
            engine.runUntilLimit(recommendedMaxSteps());

            const std::string log_text = buildLogText(engine.exportEvents());
            std::cout << "Case 1:" << std::endl;
            if (!log_text.empty()) {
                std::cout << log_text << std::endl;
            }
            return 0;
        }
        """
    ).strip()


def _build_engine_declarations() -> str:
    return dedent(
        """
        struct EventSlotConfig {
            std::string key;
            std::string title;
            int default_minute = 0;
            int minute = 0;
            bool enabled = true;
            int order_index = 0;
        };

        struct EventScheduleProfile {
            std::string name;
            bool strict_mode = true;
            std::vector<EventSlotConfig> slots;

            std::vector<EventSlotConfig> getEnabledSlots() const;
        };

        struct WarcraftConfig {
            int initial_elements = 20;
            int city_count = 2;
            int arrow_attack = 10;
            int lion_loyalty_decay = 10;
            int time_limit = 240;
            std::map<std::string, int> warrior_health;
            std::map<std::string, int> warrior_attack;
        };

        struct WeaponSet {
            int sword_attack = 0;
            bool bomb = false;
            int arrow_uses = 0;

            bool hasSword() const;
            bool hasBomb() const;
            bool hasArrow() const;
            void useArrow();
            void bluntSword();
            std::string reportText() const;
            void captureFrom(const WeaponSet& other);
        };

        struct WarriorUnit {
            std::string camp;
            std::string kind;
            int warrior_id = 0;
            int hp = 0;
            int attack = 0;
            int position = 0;
            WeaponSet weapons;
            std::optional<double> morale;
            std::optional<int> loyalty;
            int step_count = 0;
            bool reached_enemy_headquarter = false;
            bool alive = true;
            bool removed = false;
            std::string death_reason;
            int death_time = -1;

            std::string displayName() const;
            void moveOneStep(int city_count);
            bool canCounterattack() const;
        };

        struct HeadquarterState {
            std::string camp;
            int elements = 0;
            int next_index = 0;
            int total_warriors = 0;
            int enemy_arrivals = 0;
        };

        struct CityState {
            int city_id = 0;
            int elements = 0;
            std::string flag;
            std::string last_winner;
            int win_streak = 0;
        };

        struct EventRecord {
            int total_minutes = 0;
            std::string stage_key;
            int location_order = 0;
            std::string description;
            bool omit_time = false;

            std::string displayTime() const;
            std::string toLogLine() const;
        };

        struct StageExecution {
            int total_minutes = 0;
            std::string slot_key;
            std::string slot_title;
            std::vector<EventRecord> events;
            std::string summary;
            bool finished = false;
        };

        struct BattleResult {
            int city_id = 0;
            WarriorUnit* winner = nullptr;
            WarriorUnit* loser = nullptr;
            std::vector<std::string> event_descriptions;
            int city_elements_earned = 0;
            std::string flag_raised;
            std::string yell;
            int location_order = 0;
        };

        std::string formatTime(int total_minutes);
        std::string buildLogText(const std::vector<EventRecord>& events);

        class WarcraftEngine {
        public:
            WarcraftEngine(const WarcraftConfig& config, const EventScheduleProfile& schedule);

            void reset();
            std::string initializeCase();
            StageExecution nextStage();
            std::vector<StageExecution> runNextHour(int max_steps = 20);
            std::vector<StageExecution> runUntilLimit(int max_steps = 500);
            std::vector<EventRecord> exportEvents() const;
            std::string buildWorldSummary() const;
            std::string buildCitySummary(int city_id) const;
            std::string buildHeadquarterSummary(const std::string& camp) const;

        private:
            void runStage(const EventSlotConfig& slot, int total_minutes);
            void runSpawnStage(int total_minutes);
            void runLionEscapeStage(int total_minutes);
            void runMarchStage(int total_minutes);
            void runCityProduceStage(int total_minutes);
            void runCollectStage(int total_minutes);
            void runArrowStage(int total_minutes);
            void runBombStage(int total_minutes);
            void runBattleStage(int total_minutes);
            void runHeadquarterReportStage(int total_minutes);
            void runWeaponReportStage(int total_minutes);

            WarriorUnit* spawnNextWarrior(const std::string& camp);
            WeaponSet buildInitialWeapons(const std::string& kind, int warrior_id, int attack) const;
            static void giveWeaponByIndex(WeaponSet& weapons, int index, int attack);
            std::pair<WarriorUnit*, WarriorUnit*> resolveAttacker(int city_id, WarriorUnit* red, WarriorUnit* blue);
            std::pair<bool, bool> predictBattleDeaths(const WarriorUnit& attacker, const WarriorUnit& defender) const;
            BattleResult simulateBattle(int city_id, int total_minutes, WarriorUnit* attacker, WarriorUnit* defender);
            BattleResult buildArrowVictory(int city_id, int total_minutes, WarriorUnit* winner, WarriorUnit* loser);
            void applyBattleRewards(std::vector<BattleResult>& battle_results);
            void collectBattleCityElements(const std::vector<BattleResult>& battle_results);
            std::string updateCityFlag(CityState& city, const std::string& winner_camp);
            std::string formatMarch(const WarriorUnit& unit) const;
            std::string formatHeadquarterReached(const WarriorUnit& unit) const;
            void addEvent(int total_minutes, const std::string& stage_key, int location_order, const std::string& description, bool omit_time = false);
            std::vector<WarriorUnit*> aliveWarriors(const std::optional<std::string>& camp = std::nullopt);
            std::vector<const WarriorUnit*> aliveWarriorsConst(const std::optional<std::string>& camp = std::nullopt) const;
            std::vector<WarriorUnit*> aliveWarriorsAt(int position, const std::string& camp);
            std::vector<const WarriorUnit*> aliveWarriorsAtConst(int position, const std::string& camp) const;
            WarriorUnit* firstAliveWarriorAt(int position, const std::string& camp);
            WarriorUnit* firstAliveEnemyAt(int position, const std::string& shooter_camp);
            WarriorUnit* firstRecentArrowDeadAt(int position, const std::string& camp, int total_minutes);
            static std::string warriorShortName(const WarriorUnit& unit);

            WarcraftConfig config_;
            EventScheduleProfile schedule_;
            std::map<std::string, HeadquarterState> headquarters_;
            std::map<int, CityState> cities_;
            std::vector<WarriorUnit> warriors_;
            std::vector<EventRecord> events_;
            int current_hour_ = 0;
            int current_slot_index_ = 0;
            bool finished_ = false;
            bool war_over_ = false;
            bool case_initialized_ = false;
        };
        """
    ).strip() + "\n"


def _build_engine_definitions() -> str:
    return dedent(
        """
        namespace {
        const std::vector<std::string> kCamps = {"red", "blue"};
        const std::vector<std::string> kRedProductionOrder = {"iceman", "lion", "wolf", "ninja", "dragon"};
        const std::vector<std::string> kBlueProductionOrder = {"lion", "dragon", "ninja", "iceman", "wolf"};

        const std::vector<std::string>& productionOrder(const std::string& camp) {
            return camp == "red" ? kRedProductionOrder : kBlueProductionOrder;
        }

        int campSortOrder(const std::string& camp) {
            return camp == "red" ? 0 : 1;
        }

        std::string joinStrings(const std::vector<std::string>& parts, const std::string& separator) {
            if (parts.empty()) {
                return "";
            }
            std::ostringstream stream;
            for (std::size_t index = 0; index < parts.size(); ++index) {
                if (index > 0) {
                    stream << separator;
                }
                stream << parts[index];
            }
            return stream.str();
        }

        std::string formatMorale(double value) {
            std::ostringstream stream;
            stream << std::fixed << std::setprecision(2) << value;
            return stream.str();
        }
        }  // namespace

        std::vector<EventSlotConfig> EventScheduleProfile::getEnabledSlots() const {
            std::vector<EventSlotConfig> enabled_slots;
            for (const auto& slot : slots) {
                if (slot.enabled) {
                    enabled_slots.push_back(slot);
                }
            }
            std::stable_sort(
                enabled_slots.begin(),
                enabled_slots.end(),
                [](const EventSlotConfig& left, const EventSlotConfig& right) {
                    return std::tie(left.minute, left.order_index) < std::tie(right.minute, right.order_index);
                }
            );
            return enabled_slots;
        }

        bool WeaponSet::hasSword() const {
            return sword_attack > 0;
        }

        bool WeaponSet::hasBomb() const {
            return bomb;
        }

        bool WeaponSet::hasArrow() const {
            return arrow_uses > 0;
        }

        void WeaponSet::useArrow() {
            if (arrow_uses > 0) {
                --arrow_uses;
            }
        }

        void WeaponSet::bluntSword() {
            if (sword_attack <= 0) {
                return;
            }
            sword_attack = static_cast<int>(sword_attack * 0.8);
            if (sword_attack <= 0) {
                sword_attack = 0;
            }
        }

        std::string WeaponSet::reportText() const {
            std::vector<std::string> parts;
            if (arrow_uses > 0) {
                parts.push_back("arrow(" + std::to_string(arrow_uses) + ")");
            }
            if (bomb) {
                parts.push_back("bomb");
            }
            if (sword_attack > 0) {
                parts.push_back("sword(" + std::to_string(sword_attack) + ")");
            }
            if (parts.empty()) {
                return "no weapon";
            }
            return joinStrings(parts, ",");
        }

        void WeaponSet::captureFrom(const WeaponSet& other) {
            if (arrow_uses <= 0 && other.arrow_uses > 0) {
                arrow_uses = other.arrow_uses;
            }
            if (!bomb && other.bomb) {
                bomb = true;
            }
            if (sword_attack <= 0 && other.sword_attack > 0) {
                sword_attack = other.sword_attack;
            }
        }

        std::string WarriorUnit::displayName() const {
            return camp + " " + kind + " " + std::to_string(warrior_id);
        }

        void WarriorUnit::moveOneStep(int city_count) {
            if (!alive || removed || reached_enemy_headquarter) {
                return;
            }
            if (camp == "red") {
                ++position;
                if (position == city_count + 1) {
                    reached_enemy_headquarter = true;
                }
            } else {
                --position;
                if (position == 0) {
                    reached_enemy_headquarter = true;
                }
            }

            if (kind == "iceman") {
                ++step_count;
                if (step_count % 2 == 0) {
                    hp = hp <= 9 ? 1 : hp - 9;
                    attack += 20;
                }
            }
        }

        bool WarriorUnit::canCounterattack() const {
            return kind != "ninja";
        }

        std::string EventRecord::displayTime() const {
            return formatTime(total_minutes);
        }

        std::string EventRecord::toLogLine() const {
            if (omit_time) {
                return description;
            }
            return displayTime() + " " + description;
        }

        std::string formatTime(int total_minutes) {
            total_minutes = std::max(0, total_minutes);
            const int hour = total_minutes / 60;
            const int minute = total_minutes % 60;
            std::ostringstream stream;
            stream << std::setw(3) << std::setfill('0') << hour << ':'
                   << std::setw(2) << std::setfill('0') << minute;
            return stream.str();
        }

        std::string buildLogText(const std::vector<EventRecord>& events) {
            std::vector<EventRecord> sorted_events = events;
            std::stable_sort(
                sorted_events.begin(),
                sorted_events.end(),
                [](const EventRecord& left, const EventRecord& right) {
                    return std::tie(left.total_minutes, left.location_order) < std::tie(right.total_minutes, right.location_order);
                }
            );

            std::vector<std::string> lines;
            lines.reserve(sorted_events.size());
            for (const auto& event : sorted_events) {
                lines.push_back(event.toLogLine());
            }
            return joinStrings(lines, "\\n");
        }

        WarcraftEngine::WarcraftEngine(const WarcraftConfig& config, const EventScheduleProfile& schedule)
            : config_(config), schedule_(schedule) {
            reset();
        }

        void WarcraftEngine::reset() {
            headquarters_.clear();
            headquarters_["red"] = HeadquarterState{"red", config_.initial_elements, 0, 0, 0};
            headquarters_["blue"] = HeadquarterState{"blue", config_.initial_elements, 0, 0, 0};

            cities_.clear();
            for (int city_id = 1; city_id <= config_.city_count; ++city_id) {
                cities_[city_id] = CityState{city_id, 0, "", "", 0};
            }

            warriors_.clear();
            events_.clear();
            current_hour_ = 0;
            current_slot_index_ = 0;
            finished_ = false;
            war_over_ = false;
            case_initialized_ = false;
        }

        std::string WarcraftEngine::initializeCase() {
            reset();
            case_initialized_ = true;
            const auto enabled_slots = schedule_.getEnabledSlots();
            return "Case 初始化完成：M=" + std::to_string(config_.initial_elements)
                + ", N=" + std::to_string(config_.city_count)
                + ", R=" + std::to_string(config_.arrow_attack)
                + ", K=" + std::to_string(config_.lion_loyalty_decay)
                + ", T=" + std::to_string(config_.time_limit)
                + "。 当前启用 " + std::to_string(enabled_slots.size()) + " 个阶段。";
        }

        StageExecution WarcraftEngine::nextStage() {
            if (!case_initialized_) {
                return StageExecution{0, "", "", {}, "请先初始化 Case。", false};
            }

            if (finished_) {
                return StageExecution{config_.time_limit, "", "", {}, "模拟已结束。", true};
            }

            const auto enabled_slots = schedule_.getEnabledSlots();
            if (enabled_slots.empty()) {
                finished_ = true;
                return StageExecution{0, "", "", {}, "当前没有启用任何阶段。", true};
            }

            if (current_slot_index_ >= static_cast<int>(enabled_slots.size())) {
                current_slot_index_ = 0;
                ++current_hour_;
            }

            const EventSlotConfig slot = enabled_slots[static_cast<std::size_t>(current_slot_index_)];
            const int total_minutes = current_hour_ * 60 + slot.minute;
            if (total_minutes > config_.time_limit) {
                finished_ = true;
                return StageExecution{total_minutes, slot.key, slot.title, {}, "已到达时间上限。", true};
            }

            ++current_slot_index_;
            const std::size_t events_before = events_.size();
            runStage(slot, total_minutes);
            std::vector<EventRecord> stage_events(events_.begin() + static_cast<std::ptrdiff_t>(events_before), events_.end());

            std::string summary = "执行 " + slot.title + "，产生 " + std::to_string(stage_events.size()) + " 条事件。";
            if (war_over_) {
                finished_ = true;
                summary += " 战争已结束。";
            }

            return StageExecution{total_minutes, slot.key, slot.title, stage_events, summary, finished_};
        }

        std::vector<StageExecution> WarcraftEngine::runNextHour(int max_steps) {
            std::vector<StageExecution> results;
            if (!case_initialized_) {
                results.push_back(StageExecution{0, "", "", {}, "请先初始化 Case。", false});
                return results;
            }

            const int start_hour = current_hour_;
            for (int step = 0; step < max_steps; ++step) {
                StageExecution execution = nextStage();
                results.push_back(execution);
                if (execution.finished) {
                    break;
                }
                if (execution.total_minutes / 60 > start_hour) {
                    break;
                }
                if (current_slot_index_ == 0 && current_hour_ > start_hour) {
                    break;
                }
            }
            return results;
        }

        std::vector<StageExecution> WarcraftEngine::runUntilLimit(int max_steps) {
            std::vector<StageExecution> results;
            for (int step = 0; step < max_steps; ++step) {
                StageExecution execution = nextStage();
                results.push_back(execution);
                if (execution.finished) {
                    break;
                }
            }
            return results;
        }

        std::vector<EventRecord> WarcraftEngine::exportEvents() const {
            return events_;
        }

        std::string WarcraftEngine::buildWorldSummary() const {
            const auto& red = headquarters_.at("red");
            const auto& blue = headquarters_.at("blue");
            std::vector<std::string> lines = {
                "红方司令部: elements=" + std::to_string(red.elements) + ", 已造=" + std::to_string(red.total_warriors) + ", 敌人到达=" + std::to_string(red.enemy_arrivals),
                "蓝方司令部: elements=" + std::to_string(blue.elements) + ", 已造=" + std::to_string(blue.total_warriors) + ", 敌人到达=" + std::to_string(blue.enemy_arrivals),
            };
            for (int city_id = 1; city_id <= config_.city_count; ++city_id) {
                const auto& city = cities_.at(city_id);
                std::vector<std::string> red_names;
                for (const auto* unit : aliveWarriorsAtConst(city_id, "red")) {
                    red_names.push_back(warriorShortName(*unit));
                }
                std::vector<std::string> blue_names;
                for (const auto* unit : aliveWarriorsAtConst(city_id, "blue")) {
                    blue_names.push_back(warriorShortName(*unit));
                }
                const std::string red_text = red_names.empty() ? "无" : joinStrings(red_names, ", ");
                const std::string blue_text = blue_names.empty() ? "无" : joinStrings(blue_names, ", ");
                const std::string flag = city.flag.empty() ? "无旗" : city.flag;
                lines.push_back(
                    "城市 " + std::to_string(city_id) + ": elements=" + std::to_string(city.elements)
                    + ", flag=" + flag + ", red=[" + red_text + "], blue=[" + blue_text + "]"
                );
            }
            return joinStrings(lines, "\\n");
        }

        std::string WarcraftEngine::buildCitySummary(int city_id) const {
            if (city_id < 1 || city_id > config_.city_count) {
                return "城市 " + std::to_string(city_id) + " 不存在。";
            }
            const auto& city = cities_.at(city_id);
            std::vector<std::string> red_names;
            for (const auto* unit : aliveWarriorsAtConst(city_id, "red")) {
                red_names.push_back(warriorShortName(*unit));
            }
            std::vector<std::string> blue_names;
            for (const auto* unit : aliveWarriorsAtConst(city_id, "blue")) {
                blue_names.push_back(warriorShortName(*unit));
            }
            const std::vector<std::string> lines = {
                "城市 " + std::to_string(city_id),
                "生命元: " + std::to_string(city.elements),
                "旗帜: " + (city.flag.empty() ? std::string("无") : city.flag),
                "连续获胜方: " + (city.last_winner.empty() ? std::string("无") : city.last_winner),
                "连胜计数: " + std::to_string(city.win_streak),
                "红方: " + (red_names.empty() ? std::string("无") : joinStrings(red_names, ", ")),
                "蓝方: " + (blue_names.empty() ? std::string("无") : joinStrings(blue_names, ", ")),
            };
            return joinStrings(lines, "\\n");
        }

        std::string WarcraftEngine::buildHeadquarterSummary(const std::string& camp) const {
            const auto& headquarter = headquarters_.at(camp);
            const auto& order = productionOrder(camp);
            const std::string next_kind = order[static_cast<std::size_t>(headquarter.next_index % static_cast<int>(order.size()))];
            return camp + " headquarter\\n"
                + "elements: " + std::to_string(headquarter.elements) + "\\n"
                + "next warrior: " + next_kind + "\\n"
                + "total warriors: " + std::to_string(headquarter.total_warriors) + "\\n"
                + "enemy arrivals: " + std::to_string(headquarter.enemy_arrivals);
        }

        void WarcraftEngine::runStage(const EventSlotConfig& slot, int total_minutes) {
            if (slot.key == "spawn") {
                runSpawnStage(total_minutes);
            } else if (slot.key == "lion_escape") {
                runLionEscapeStage(total_minutes);
            } else if (slot.key == "march") {
                runMarchStage(total_minutes);
            } else if (slot.key == "city_produce") {
                runCityProduceStage(total_minutes);
            } else if (slot.key == "collect_elements") {
                runCollectStage(total_minutes);
            } else if (slot.key == "arrow") {
                runArrowStage(total_minutes);
            } else if (slot.key == "bomb") {
                runBombStage(total_minutes);
            } else if (slot.key == "battle") {
                runBattleStage(total_minutes);
            } else if (slot.key == "headquarter_report") {
                runHeadquarterReportStage(total_minutes);
            } else if (slot.key == "weapon_report") {
                runWeaponReportStage(total_minutes);
            }
        }

        void WarcraftEngine::runSpawnStage(int total_minutes) {
            for (const auto& camp : kCamps) {
                WarriorUnit* warrior = spawnNextWarrior(camp);
                if (warrior == nullptr) {
                    continue;
                }
                const int location_order = camp == "red" ? 0 : config_.city_count + 1;
                addEvent(total_minutes, "spawn", location_order, camp + " " + warrior->kind + " " + std::to_string(warrior->warrior_id) + " born");
                if (warrior->kind == "dragon" && warrior->morale.has_value()) {
                    addEvent(total_minutes, "spawn", location_order, "Its morale is " + formatMorale(*warrior->morale), true);
                }
                if (warrior->kind == "lion" && warrior->loyalty.has_value()) {
                    addEvent(total_minutes, "spawn", location_order, "Its loyalty is " + std::to_string(*warrior->loyalty), true);
                }
            }
        }

        void WarcraftEngine::runLionEscapeStage(int total_minutes) {
            std::vector<WarriorUnit*> runaways;
            for (auto& unit : warriors_) {
                if (
                    unit.alive
                    && !unit.removed
                    && unit.kind == "lion"
                    && unit.loyalty.value_or(0) <= 0
                    && !unit.reached_enemy_headquarter
                ) {
                    runaways.push_back(&unit);
                }
            }

            std::sort(
                runaways.begin(),
                runaways.end(),
                [](const WarriorUnit* left, const WarriorUnit* right) {
                    return std::make_tuple(left->position, campSortOrder(left->camp), left->warrior_id)
                        < std::make_tuple(right->position, campSortOrder(right->camp), right->warrior_id);
                }
            );

            for (auto* unit : runaways) {
                unit->alive = false;
                unit->removed = true;
                addEvent(total_minutes, "lion_escape", unit->position, unit->camp + " lion " + std::to_string(unit->warrior_id) + " ran away");
            }
        }

        void WarcraftEngine::runMarchStage(int total_minutes) {
            std::vector<WarriorUnit*> movers;
            for (auto& unit : warriors_) {
                if (unit.alive && !unit.removed && !unit.reached_enemy_headquarter) {
                    movers.push_back(&unit);
                }
            }

            for (auto* unit : movers) {
                unit->moveOneStep(config_.city_count);
            }

            std::vector<std::tuple<int, int, std::string>> march_events;
            std::vector<std::pair<int, std::string>> taken_events;
            std::sort(
                movers.begin(),
                movers.end(),
                [](const WarriorUnit* left, const WarriorUnit* right) {
                    return std::make_tuple(left->position, campSortOrder(left->camp), left->warrior_id)
                        < std::make_tuple(right->position, campSortOrder(right->camp), right->warrior_id);
                }
            );

            for (auto* unit : movers) {
                if (unit->reached_enemy_headquarter) {
                    const std::string enemy_camp = unit->camp == "red" ? "blue" : "red";
                    headquarters_[enemy_camp].enemy_arrivals += 1;
                    march_events.emplace_back(unit->position, unit->camp == "red" ? 0 : 1, formatHeadquarterReached(*unit));
                    if (headquarters_[enemy_camp].enemy_arrivals >= 2) {
                        const int location_order = enemy_camp == "red" ? 0 : config_.city_count + 1;
                        taken_events.emplace_back(location_order, enemy_camp + " headquarter was taken");
                    }
                } else {
                    march_events.emplace_back(unit->position, unit->camp == "red" ? 0 : 1, formatMarch(*unit));
                }
            }

            for (const auto& [position, camp_order, description] : march_events) {
                addEvent(total_minutes, "march", position * 10 + camp_order, description);
            }
            for (const auto& [location_order, description] : taken_events) {
                addEvent(total_minutes, "march", location_order * 10 + 9, description);
            }

            if (!taken_events.empty()) {
                war_over_ = true;
            }
        }

        void WarcraftEngine::runCityProduceStage(int total_minutes) {
            (void)total_minutes;
            for (auto& [city_id, city] : cities_) {
                (void)city_id;
                city.elements += 10;
            }
        }

        void WarcraftEngine::runCollectStage(int total_minutes) {
            for (int city_id = 1; city_id <= config_.city_count; ++city_id) {
                auto& city = cities_[city_id];
                if (city.elements <= 0) {
                    continue;
                }
                const auto red_units = aliveWarriorsAt(city_id, "red");
                const auto blue_units = aliveWarriorsAt(city_id, "blue");
                if (static_cast<int>(red_units.size() + blue_units.size()) != 1) {
                    continue;
                }
                WarriorUnit* unit = !red_units.empty() ? red_units.front() : blue_units.front();
                headquarters_[unit->camp].elements += city.elements;
                const int earned = city.elements;
                city.elements = 0;
                addEvent(
                    total_minutes,
                    "collect_elements",
                    city_id,
                    unit->camp + " " + unit->kind + " " + std::to_string(unit->warrior_id)
                        + " earned " + std::to_string(earned) + " elements for his headquarter"
                );
            }
        }

        void WarcraftEngine::runArrowStage(int total_minutes) {
            std::vector<WarriorUnit*> shooters;
            for (auto& unit : warriors_) {
                if (unit.alive && !unit.removed && unit.weapons.hasArrow()) {
                    shooters.push_back(&unit);
                }
            }

            std::sort(
                shooters.begin(),
                shooters.end(),
                [](const WarriorUnit* left, const WarriorUnit* right) {
                    return std::make_tuple(left->position, campSortOrder(left->camp), left->warrior_id)
                        < std::make_tuple(right->position, campSortOrder(right->camp), right->warrior_id);
                }
            );

            std::vector<std::tuple<int, int, std::string>> shots;
            for (auto* shooter : shooters) {
                const int target_position = shooter->camp == "red" ? shooter->position + 1 : shooter->position - 1;
                if (target_position <= 0 || target_position > config_.city_count) {
                    continue;
                }
                WarriorUnit* target = firstAliveEnemyAt(target_position, shooter->camp);
                if (target == nullptr) {
                    continue;
                }

                shooter->weapons.useArrow();
                target->hp -= config_.arrow_attack;
                const bool killed = target->hp <= 0;
                if (killed) {
                    target->hp = 0;
                    target->alive = false;
                    target->death_reason = "arrow";
                    target->death_time = total_minutes;
                    shots.emplace_back(
                        shooter->position,
                        shooter->camp == "red" ? 0 : 1,
                        shooter->camp + " " + shooter->kind + " " + std::to_string(shooter->warrior_id)
                            + " shot and killed " + target->camp + " " + target->kind + " " + std::to_string(target->warrior_id)
                    );
                } else {
                    shots.emplace_back(
                        shooter->position,
                        shooter->camp == "red" ? 0 : 1,
                        shooter->camp + " " + shooter->kind + " " + std::to_string(shooter->warrior_id) + " shot"
                    );
                }
            }

            for (const auto& [position, camp_order, description] : shots) {
                addEvent(total_minutes, "arrow", position * 10 + camp_order, description);
            }
        }

        void WarcraftEngine::runBombStage(int total_minutes) {
            std::vector<std::tuple<int, int, std::string>> bomb_events;
            for (int city_id = 1; city_id <= config_.city_count; ++city_id) {
                WarriorUnit* red = firstAliveWarriorAt(city_id, "red");
                WarriorUnit* blue = firstAliveWarriorAt(city_id, "blue");
                if (red == nullptr || blue == nullptr) {
                    continue;
                }

                auto [attacker, defender] = resolveAttacker(city_id, red, blue);
                if (attacker == nullptr || defender == nullptr) {
                    continue;
                }

                const auto [attacker_dies, defender_dies] = predictBattleDeaths(*attacker, *defender);
                WarriorUnit* user = nullptr;
                WarriorUnit* victim = nullptr;
                if (attacker->weapons.hasBomb() && attacker_dies) {
                    user = attacker;
                    victim = defender;
                } else if (defender->weapons.hasBomb() && defender_dies) {
                    user = defender;
                    victim = attacker;
                }

                if (user == nullptr || victim == nullptr) {
                    continue;
                }

                user->weapons.bomb = false;
                user->alive = false;
                user->death_reason = "bomb";
                user->death_time = total_minutes;
                victim->alive = false;
                victim->death_reason = "bomb";
                victim->death_time = total_minutes;
                bomb_events.emplace_back(
                    city_id,
                    user->camp == "red" ? 0 : 1,
                    user->camp + " " + user->kind + " " + std::to_string(user->warrior_id)
                        + " used a bomb and killed " + victim->camp + " " + victim->kind + " " + std::to_string(victim->warrior_id)
                );
            }

            for (const auto& [city_id, camp_order, description] : bomb_events) {
                addEvent(total_minutes, "bomb", city_id * 10 + camp_order, description);
            }
        }

        void WarcraftEngine::runBattleStage(int total_minutes) {
            std::vector<BattleResult> battle_results;

            for (int city_id = 1; city_id <= config_.city_count; ++city_id) {
                WarriorUnit* red_alive = firstAliveWarriorAt(city_id, "red");
                WarriorUnit* blue_alive = firstAliveWarriorAt(city_id, "blue");
                WarriorUnit* red_arrow_dead = firstRecentArrowDeadAt(city_id, "red", total_minutes);
                WarriorUnit* blue_arrow_dead = firstRecentArrowDeadAt(city_id, "blue", total_minutes);

                if (red_alive == nullptr && blue_alive == nullptr) {
                    continue;
                }

                if (red_alive != nullptr && blue_alive == nullptr && blue_arrow_dead != nullptr) {
                    battle_results.push_back(buildArrowVictory(city_id, total_minutes, red_alive, blue_arrow_dead));
                    continue;
                }
                if (blue_alive != nullptr && red_alive == nullptr && red_arrow_dead != nullptr) {
                    battle_results.push_back(buildArrowVictory(city_id, total_minutes, blue_alive, red_arrow_dead));
                    continue;
                }
                if (red_alive == nullptr || blue_alive == nullptr) {
                    continue;
                }

                auto [attacker, defender] = resolveAttacker(city_id, red_alive, blue_alive);
                if (attacker == nullptr || defender == nullptr) {
                    continue;
                }

                battle_results.push_back(simulateBattle(city_id, total_minutes, attacker, defender));
            }

            applyBattleRewards(battle_results);
            collectBattleCityElements(battle_results);

            for (const auto& result : battle_results) {
                for (const auto& description : result.event_descriptions) {
                    addEvent(total_minutes, "battle", result.location_order, description);
                }
                if (!result.yell.empty()) {
                    addEvent(total_minutes, "battle", result.location_order + 1, result.yell);
                }
                if (result.city_elements_earned > 0 && result.winner != nullptr) {
                    addEvent(
                        total_minutes,
                        "battle",
                        result.location_order + 2,
                        result.winner->camp + " " + result.winner->kind + " " + std::to_string(result.winner->warrior_id)
                            + " earned " + std::to_string(result.city_elements_earned) + " elements for his headquarter"
                    );
                }
                if (!result.flag_raised.empty()) {
                    addEvent(
                        total_minutes,
                        "battle",
                        result.location_order + 3,
                        result.flag_raised + " flag raised in city " + std::to_string(result.city_id)
                    );
                }
            }
        }

        void WarcraftEngine::runHeadquarterReportStage(int total_minutes) {
            addEvent(total_minutes, "headquarter_report", 0, std::to_string(headquarters_["red"].elements) + " elements in red headquarter");
            addEvent(total_minutes, "headquarter_report", (config_.city_count + 1) * 10, std::to_string(headquarters_["blue"].elements) + " elements in blue headquarter");
        }

        void WarcraftEngine::runWeaponReportStage(int total_minutes) {
            auto red_units = aliveWarriorsConst("red");
            auto blue_units = aliveWarriorsConst("blue");
            std::sort(
                red_units.begin(),
                red_units.end(),
                [](const WarriorUnit* left, const WarriorUnit* right) {
                    return std::tie(left->position, left->warrior_id) < std::tie(right->position, right->warrior_id);
                }
            );
            std::sort(
                blue_units.begin(),
                blue_units.end(),
                [](const WarriorUnit* left, const WarriorUnit* right) {
                    return std::tie(left->position, left->warrior_id) < std::tie(right->position, right->warrior_id);
                }
            );

            for (const auto* unit : red_units) {
                addEvent(
                    total_minutes,
                    "weapon_report",
                    unit->position,
                    unit->camp + " " + unit->kind + " " + std::to_string(unit->warrior_id) + " has " + unit->weapons.reportText()
                );
            }
            for (const auto* unit : blue_units) {
                addEvent(
                    total_minutes,
                    "weapon_report",
                    config_.city_count + 2 + unit->position,
                    unit->camp + " " + unit->kind + " " + std::to_string(unit->warrior_id) + " has " + unit->weapons.reportText()
                );
            }
        }

        WarriorUnit* WarcraftEngine::spawnNextWarrior(const std::string& camp) {
            auto& headquarter = headquarters_[camp];
            const auto& order = productionOrder(camp);
            const std::string& kind = order[static_cast<std::size_t>(headquarter.next_index)];
            const int cost = config_.warrior_health.at(kind);
            if (headquarter.elements < cost) {
                return nullptr;
            }

            headquarter.elements -= cost;
            headquarter.total_warriors += 1;
            headquarter.next_index = (headquarter.next_index + 1) % static_cast<int>(order.size());
            const int warrior_id = headquarter.total_warriors;
            const int position = camp == "red" ? 0 : config_.city_count + 1;

            WarriorUnit warrior;
            warrior.camp = camp;
            warrior.kind = kind;
            warrior.warrior_id = warrior_id;
            warrior.hp = cost;
            warrior.attack = config_.warrior_attack.at(kind);
            warrior.position = position;
            warrior.weapons = buildInitialWeapons(kind, warrior_id, warrior.attack);
            if (kind == "dragon") {
                warrior.morale = static_cast<double>(headquarter.elements) / static_cast<double>(cost);
            }
            if (kind == "lion") {
                warrior.loyalty = headquarter.elements;
            }

            warriors_.push_back(warrior);
            return &warriors_.back();
        }

        WeaponSet WarcraftEngine::buildInitialWeapons(const std::string& kind, int warrior_id, int attack) const {
            WeaponSet weapons;
            if (kind == "dragon" || kind == "iceman") {
                giveWeaponByIndex(weapons, warrior_id % 3, attack);
            } else if (kind == "ninja") {
                giveWeaponByIndex(weapons, warrior_id % 3, attack);
                giveWeaponByIndex(weapons, (warrior_id + 1) % 3, attack);
            }
            return weapons;
        }

        void WarcraftEngine::giveWeaponByIndex(WeaponSet& weapons, int index, int attack) {
            if (index == 0) {
                const int sword_attack = attack / 5;
                if (sword_attack > 0) {
                    weapons.sword_attack = sword_attack;
                }
            } else if (index == 1) {
                weapons.bomb = true;
            } else if (index == 2) {
                weapons.arrow_uses = 3;
            }
        }

        std::pair<WarriorUnit*, WarriorUnit*> WarcraftEngine::resolveAttacker(int city_id, WarriorUnit* red, WarriorUnit* blue) {
            auto& city = cities_[city_id];
            if (city.flag == "red") {
                return {red, blue};
            }
            if (city.flag == "blue") {
                return {blue, red};
            }
            return city_id % 2 == 1 ? std::make_pair(red, blue) : std::make_pair(blue, red);
        }

        std::pair<bool, bool> WarcraftEngine::predictBattleDeaths(const WarriorUnit& attacker, const WarriorUnit& defender) const {
            const int defender_hp = defender.hp - attacker.attack - attacker.weapons.sword_attack;
            const bool defender_dies = defender_hp <= 0;
            bool attacker_dies = false;
            if (!defender_dies && defender.canCounterattack()) {
                const int attacker_hp = attacker.hp - defender.attack / 2 - defender.weapons.sword_attack;
                attacker_dies = attacker_hp <= 0;
            }
            return {attacker_dies, defender_dies};
        }

        BattleResult WarcraftEngine::simulateBattle(int city_id, int total_minutes, WarriorUnit* attacker, WarriorUnit* defender) {
            (void)total_minutes;
            auto& city = cities_[city_id];
            BattleResult result;
            result.city_id = city_id;
            result.location_order = city_id * 10;

            const int attacker_pre_hp = attacker->hp;
            const int defender_pre_hp = defender->hp;
            const int attacker_pre_sword = attacker->weapons.sword_attack;
            const int defender_pre_sword = defender->weapons.sword_attack;

            result.event_descriptions.push_back(
                attacker->camp + " " + attacker->kind + " " + std::to_string(attacker->warrior_id)
                    + " attacked " + defender->camp + " " + defender->kind + " " + std::to_string(defender->warrior_id)
                    + " in city " + std::to_string(city_id) + " with " + std::to_string(attacker->hp)
                    + " elements and force " + std::to_string(attacker->attack)
            );

            defender->hp -= attacker->attack + attacker->weapons.sword_attack;
            if (attacker_pre_sword > 0) {
                attacker->weapons.bluntSword();
            }

            if (defender->hp <= 0) {
                defender->hp = 0;
                defender->alive = false;
                defender->death_reason = "battle";
                result.winner = attacker;
                result.loser = defender;
                result.event_descriptions.push_back(
                    defender->camp + " " + defender->kind + " " + std::to_string(defender->warrior_id)
                        + " was killed in city " + std::to_string(city_id)
                );
            } else if (defender->canCounterattack()) {
                result.event_descriptions.push_back(
                    defender->camp + " " + defender->kind + " " + std::to_string(defender->warrior_id)
                        + " fought back against " + attacker->camp + " " + attacker->kind + " " + std::to_string(attacker->warrior_id)
                        + " in city " + std::to_string(city_id)
                );
                attacker->hp -= defender->attack / 2 + defender->weapons.sword_attack;
                if (defender_pre_sword > 0) {
                    defender->weapons.bluntSword();
                }
                if (attacker->hp <= 0) {
                    attacker->hp = 0;
                    attacker->alive = false;
                    attacker->death_reason = "battle";
                    result.winner = defender;
                    result.loser = attacker;
                    result.event_descriptions.push_back(
                        attacker->camp + " " + attacker->kind + " " + std::to_string(attacker->warrior_id)
                            + " was killed in city " + std::to_string(city_id)
                    );
                }
            }

            if (result.winner != nullptr && result.loser != nullptr) {
                if (result.loser->kind == "lion") {
                    result.winner->hp += result.loser == defender ? defender_pre_hp : attacker_pre_hp;
                }

                if (result.winner->kind == "wolf") {
                    result.winner->weapons.captureFrom(result.loser->weapons);
                }

                if (result.winner->kind == "dragon" && result.winner->morale.has_value()) {
                    *result.winner->morale += 0.2;
                }
                if (result.loser->kind == "dragon" && result.loser->morale.has_value()) {
                    *result.loser->morale -= 0.2;
                }
                if (result.loser->kind == "lion" && result.loser->loyalty.has_value()) {
                    *result.loser->loyalty -= config_.lion_loyalty_decay;
                }

                result.city_elements_earned = city.elements;
                result.flag_raised = updateCityFlag(city, result.winner->camp);

                if (attacker->kind == "dragon" && attacker->alive && attacker->morale.has_value() && *attacker->morale > 0.8) {
                    result.yell = attacker->camp + " dragon " + std::to_string(attacker->warrior_id) + " yelled in city " + std::to_string(city_id);
                }
            } else {
                if (attacker->kind == "dragon" && attacker->morale.has_value()) {
                    *attacker->morale -= 0.2;
                    if (attacker->alive && *attacker->morale > 0.8) {
                        result.yell = attacker->camp + " dragon " + std::to_string(attacker->warrior_id) + " yelled in city " + std::to_string(city_id);
                    }
                }
                if (defender->kind == "dragon" && defender->morale.has_value()) {
                    *defender->morale -= 0.2;
                }
                if (attacker->kind == "lion" && attacker->loyalty.has_value()) {
                    *attacker->loyalty -= config_.lion_loyalty_decay;
                }
                if (defender->kind == "lion" && defender->loyalty.has_value()) {
                    *defender->loyalty -= config_.lion_loyalty_decay;
                }
                city.last_winner.clear();
                city.win_streak = 0;
            }

            return result;
        }

        BattleResult WarcraftEngine::buildArrowVictory(int city_id, int total_minutes, WarriorUnit* winner, WarriorUnit* loser) {
            (void)total_minutes;
            auto& city = cities_[city_id];
            BattleResult result;
            result.city_id = city_id;
            result.winner = winner;
            result.loser = loser;
            result.city_elements_earned = city.elements;
            result.location_order = city_id * 10;

            if (winner->kind == "wolf") {
                winner->weapons.captureFrom(loser->weapons);
            }
            if (winner->kind == "dragon" && winner->morale.has_value()) {
                *winner->morale += 0.2;
            }
            if (loser->kind == "dragon" && loser->morale.has_value()) {
                *loser->morale -= 0.2;
            }
            if (loser->kind == "lion" && loser->loyalty.has_value()) {
                *loser->loyalty -= config_.lion_loyalty_decay;
            }

            WarriorUnit* red = winner->camp == "red" ? winner : loser;
            WarriorUnit* blue = winner->camp == "blue" ? winner : loser;
            auto [attacker, ignored_defender] = resolveAttacker(city_id, red, blue);
            (void)ignored_defender;
            if (attacker == winner && winner->kind == "dragon" && winner->morale.has_value() && *winner->morale > 0.8) {
                result.yell = winner->camp + " dragon " + std::to_string(winner->warrior_id) + " yelled in city " + std::to_string(city_id);
            }
            result.flag_raised = updateCityFlag(city, winner->camp);

            return result;
        }

        void WarcraftEngine::applyBattleRewards(std::vector<BattleResult>& battle_results) {
            std::vector<BattleResult*> red_wins;
            std::vector<BattleResult*> blue_wins;

            for (auto& result : battle_results) {
                if (result.winner == nullptr || !result.winner->alive) {
                    continue;
                }
                if (result.winner->camp == "red") {
                    red_wins.push_back(&result);
                } else {
                    blue_wins.push_back(&result);
                }
            }

            std::sort(
                red_wins.begin(),
                red_wins.end(),
                [](const BattleResult* left, const BattleResult* right) { return left->city_id > right->city_id; }
            );
            std::sort(
                blue_wins.begin(),
                blue_wins.end(),
                [](const BattleResult* left, const BattleResult* right) { return left->city_id < right->city_id; }
            );

            for (auto* result : red_wins) {
                auto& headquarter = headquarters_["red"];
                if (headquarter.elements >= 8) {
                    headquarter.elements -= 8;
                    result->winner->hp += 8;
                }
            }
            for (auto* result : blue_wins) {
                auto& headquarter = headquarters_["blue"];
                if (headquarter.elements >= 8) {
                    headquarter.elements -= 8;
                    result->winner->hp += 8;
                }
            }
        }

        void WarcraftEngine::collectBattleCityElements(const std::vector<BattleResult>& battle_results) {
            for (const auto& result : battle_results) {
                if (result.winner == nullptr || result.city_elements_earned <= 0) {
                    continue;
                }
                headquarters_[result.winner->camp].elements += result.city_elements_earned;
                cities_[result.city_id].elements = 0;
            }
        }

        std::string WarcraftEngine::updateCityFlag(CityState& city, const std::string& winner_camp) {
            if (city.last_winner == winner_camp) {
                city.win_streak += 1;
            } else {
                city.last_winner = winner_camp;
                city.win_streak = 1;
            }

            if (city.win_streak >= 2 && city.flag != winner_camp) {
                city.flag = winner_camp;
                return winner_camp;
            }
            return "";
        }

        std::string WarcraftEngine::formatMarch(const WarriorUnit& unit) const {
            return unit.camp + " " + unit.kind + " " + std::to_string(unit.warrior_id)
                + " marched to city " + std::to_string(unit.position)
                + " with " + std::to_string(unit.hp) + " elements and force " + std::to_string(unit.attack);
        }

        std::string WarcraftEngine::formatHeadquarterReached(const WarriorUnit& unit) const {
            const std::string enemy = unit.camp == "red" ? "blue" : "red";
            return unit.camp + " " + unit.kind + " " + std::to_string(unit.warrior_id)
                + " reached " + enemy + " headquarter with " + std::to_string(unit.hp)
                + " elements and force " + std::to_string(unit.attack);
        }

        void WarcraftEngine::addEvent(int total_minutes, const std::string& stage_key, int location_order, const std::string& description, bool omit_time) {
            events_.push_back(EventRecord{total_minutes, stage_key, location_order, description, omit_time});
        }

        std::vector<WarriorUnit*> WarcraftEngine::aliveWarriors(const std::optional<std::string>& camp) {
            std::vector<WarriorUnit*> result;
            for (auto& unit : warriors_) {
                if (!unit.alive || unit.removed) {
                    continue;
                }
                if (camp.has_value() && unit.camp != *camp) {
                    continue;
                }
                result.push_back(&unit);
            }
            return result;
        }

        std::vector<const WarriorUnit*> WarcraftEngine::aliveWarriorsConst(const std::optional<std::string>& camp) const {
            std::vector<const WarriorUnit*> result;
            for (const auto& unit : warriors_) {
                if (!unit.alive || unit.removed) {
                    continue;
                }
                if (camp.has_value() && unit.camp != *camp) {
                    continue;
                }
                result.push_back(&unit);
            }
            return result;
        }

        std::vector<WarriorUnit*> WarcraftEngine::aliveWarriorsAt(int position, const std::string& camp) {
            std::vector<WarriorUnit*> result;
            for (auto* unit : aliveWarriors(camp)) {
                if (unit->position == position) {
                    result.push_back(unit);
                }
            }
            return result;
        }

        std::vector<const WarriorUnit*> WarcraftEngine::aliveWarriorsAtConst(int position, const std::string& camp) const {
            std::vector<const WarriorUnit*> result;
            for (const auto* unit : aliveWarriorsConst(camp)) {
                if (unit->position == position) {
                    result.push_back(unit);
                }
            }
            return result;
        }

        WarriorUnit* WarcraftEngine::firstAliveWarriorAt(int position, const std::string& camp) {
            auto warriors = aliveWarriorsAt(position, camp);
            return warriors.empty() ? nullptr : warriors.front();
        }

        WarriorUnit* WarcraftEngine::firstAliveEnemyAt(int position, const std::string& shooter_camp) {
            return firstAliveWarriorAt(position, shooter_camp == "red" ? "blue" : "red");
        }

        WarriorUnit* WarcraftEngine::firstRecentArrowDeadAt(int position, const std::string& camp, int total_minutes) {
            for (auto& unit : warriors_) {
                if (
                    unit.camp == camp
                    && !unit.alive
                    && !unit.removed
                    && unit.position == position
                    && unit.death_reason == "arrow"
                    && unit.death_time == total_minutes - 5
                ) {
                    return &unit;
                }
            }
            return nullptr;
        }

        std::string WarcraftEngine::warriorShortName(const WarriorUnit& unit) {
            return unit.camp + "-" + unit.kind + "-" + std::to_string(unit.warrior_id);
        }
        """
    ).strip()


def _build_readme(config: WarcraftConfig, schedule: EventScheduleProfile) -> str:
    enabled_slots = schedule.get_enabled_slots()
    stage_lines = [f"- {slot.key}: minute={slot.minute}, enabled={slot.enabled}" for slot in enabled_slots]
    stage_summary = "\n".join(stage_lines) if stage_lines else "- no enabled stages"
    return dedent(
        f"""
        Task2 Standalone C++ Solution

        task2_solution.cpp is a single self-contained translation unit generated
        directly from the current Task2 configuration. It is meant to be submitted
        to an online judge as-is.

        Current case:
        - mode: {'standard' if schedule.strict_mode else 'custom'}
        - profile: {schedule.name}
        - M={config.initial_elements}, N={config.city_count}, R={config.arrow_attack}, K={config.lion_loyalty_decay}, T={config.time_limit}

        Enabled stages:
        {stage_summary}

        Build with g++:
        - g++ -std=c++20 -O2 task2_solution.cpp -o task2_solution.exe

        Run:
        - .\\task2_solution.exe

        Compare output:
        - expected_log.txt is generated from the Python Task2 reference engine using the same case.

        Module design:
        - MODULE_DESIGN.md explains how the standalone solution maps back to the
          intended Game / Headquarter / City / Warrior / Weapon / EventScheduler
          modules used by the teaching UI.
        - The standalone file keeps those boundaries as classes and structs, but
          packages them into one translation unit so it can be submitted directly.
        """
    ).strip() + "\n"


def _build_module_design_doc(config: WarcraftConfig, schedule: EventScheduleProfile) -> str:
    enabled_slots = schedule.get_enabled_slots()
    stage_rows = [
        f"| `{slot.key}` | {slot.minute:02d} | {slot.title} | `{_stage_owner(slot.key)}` |"
        for slot in enabled_slots
    ]
    stage_table = "\n".join(stage_rows) if stage_rows else "| none | - | no enabled stage | - |"
    template = dedent(
        """
        # Task2 Module Design

        This export contains a judge-ready `task2_solution.cpp`, plus this design
        note that explains how the generated single file maps to the modular model
        used by the teaching tool.

        ## Export Scope

        - `task2_solution.cpp` is the complete OJ submission for the current Task2 case.
        - `expected_log.txt` is generated by the Python reference engine with the same inputs.
        - `README.txt` contains build and compare commands.
        - This file is a module map. It is not required by the OJ.

        ## Current Case

        - Profile: `{schedule.name}`
        - Mode: `{'standard' if schedule.strict_mode else 'custom'}`
        - M={config.initial_elements}, N={config.city_count}, R={config.arrow_attack}, K={config.lion_loyalty_decay}, T={config.time_limit}

        ## Logical Modules

        | Module | Responsibility | Generated C++ surface |
        | --- | --- | --- |
        | Model / Schedule | Stores config, enabled stages, minute values, ordering, and normalized event records. | `WarcraftConfig`, `EventScheduleProfile`, `EventSlotConfig`, `EventRecord` |
        | WorldState | Tracks headquarters, cities, warriors, and weapon state as explicit value objects. | `HeadquarterState`, `CityState`, `WarriorUnit`, `WeaponSet` |
        | WarriorFactory | Owns production order, affordability checks, warrior ids, morale/loyalty initialization, and initial weapons. | `spawnNextWarrior`, `buildInitialWeapons`, `giveWeaponByIndex` |
        | StageRunner | Owns the time axis, stop condition, event dispatch, and stage-level orchestration. | `class WarcraftEngine` |
        | MovementSystem | Handles march ordering, headquarter arrivals, iceman step effects, and movement messages. | `runMarchStage`, `formatMarch`, `formatHeadquarterReached` |
        | WeaponSystem | Handles arrow, bomb, sword degradation, weapon capture, and weapon reports. | `runArrowStage`, `runBombStage`, `WeaponSet` |
        | BattleResolver | Handles attacker selection, battle death prediction, combat resolution, rewards, city collection, and flag updates. | `resolveAttacker`, `predictBattleDeaths`, `simulateBattle`, `updateCityFlag` |
        | EventLog / Reporter | Converts normalized events into exact problem output and timeline-friendly records. | `EventRecord`, `buildLogText` |

        ## Enabled Event Stages

        | Stage key | Minute | UI title | Logical owner |
        | --- | ---: | --- | --- |
        __STAGE_TABLE__

        ## Why The OJ Export Is A Single File

        The UI encourages modular design first, but online judges usually expect a
        single translation unit. The exporter therefore preserves module boundaries
        in named classes and structs, then emits them into `task2_solution.cpp`.
        If students want a multi-file learning skeleton, use the class editor's
        "导出工程骨架" command; if they want something to submit, use this Task2
        standalone export.
        """
    ).strip()
    return (
        template.replace("`{schedule.name}`", f"`{schedule.name}`")
        .replace("`{'standard' if schedule.strict_mode else 'custom'}`", f"`{'standard' if schedule.strict_mode else 'custom'}`")
        .replace(
            "M={config.initial_elements}, N={config.city_count}, R={config.arrow_attack}, K={config.lion_loyalty_decay}, T={config.time_limit}",
            f"M={config.initial_elements}, N={config.city_count}, R={config.arrow_attack}, K={config.lion_loyalty_decay}, T={config.time_limit}",
        )
        .replace("__STAGE_TABLE__", stage_table)
        + "\n"
    )


def _stage_owner(stage_key: str) -> str:
    mapping = {
        "spawn": "WarriorFactory / Headquarter",
        "lion_escape": "Warrior",
        "march": "MovementSystem",
        "city_produce": "City",
        "collect": "City / Headquarter",
        "arrow": "WeaponSystem",
        "bomb": "WeaponSystem / BattleResolver",
        "battle": "BattleResolver / City",
        "headquarter_report": "Headquarter / EventLog",
        "weapon_report": "WeaponSystem / EventLog",
    }
    return mapping.get(stage_key, "Game")


def _cpp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _cpp_bool(value: bool) -> str:
    return "true" if value else "false"
