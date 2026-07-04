from __future__ import annotations

from pathlib import Path

from constants import DEFAULT_MEMBER_NAMES, TYPE_SIZES
from engine.models import ClassDef, MemberDef, MemoryBlock, ObjectInstance

# 类定义管理器：统一维护项目中的所有类结构，并提供代码生成、内存布局计算等核心能力。
# 该类采用单例模式，便于多个界面和业务模块共享同一份类定义数据。
class ClassManager:
    _instance: "ClassManager | None" = None

    # 初始化内部类定义表，键为类名，值为对应的 ClassDef 对象。
    def __init__(self) -> None:
        self._classes: dict[str, ClassDef] = {}

    # 获取全局唯一的 ClassManager 实例，确保项目中所有模块共享同一份数据。
    @classmethod
    def get_instance(cls) -> "ClassManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # 向管理器中新增一个类定义；添加前会先进行合法性校验。
    def add_class(self, cls_def: ClassDef) -> None:
        self._validate_class_def(cls_def)
        self._classes[cls_def.name] = cls_def

    # 更新已有类定义，并支持类名重命名；若类名变化，会同步修正其子类的基类名称引用。
    def update_class(self, old_name: str, cls_def: ClassDef) -> None:
        self._validate_class_def(cls_def, old_name=old_name)
        if old_name != cls_def.name and old_name in self._classes:
            del self._classes[old_name]
            for child_def in self._classes.values():
                if child_def.base_class == old_name:
                    child_def.base_class = cls_def.name
        self._classes[cls_def.name] = cls_def

    # 删除指定类；若其他类原本继承它，则将这些类的 base_class 清空。
    def remove_class(self, name: str) -> None:
        if name in self._classes:
            del self._classes[name]
        for cls_def in self._classes.values():
            if cls_def.base_class == name:
                cls_def.base_class = ""

    # 根据类名获取单个类定义；若不存在则返回 None。
    def get_class(self, name: str) -> ClassDef | None:
        return self._classes.get(name)

    # 获取全部类定义，并按类名不区分大小写排序，便于界面稳定展示。
    def get_all_classes(self) -> list[ClassDef]:
        return sorted(self._classes.values(), key=lambda c: c.name.lower())

    # 获取全部类名列表，常用于下拉框、列表框等界面控件填充。
    def get_class_names(self) -> list[str]:
        return [cls_def.name for cls_def in self.get_all_classes()]

    # 判断一个类是否为另一个类的子类或其本身，沿继承链向上逐级查找。
    # 通过 visited 集合避免异常数据导致的重复回溯或死循环。
    def is_subclass_of(self, class_name: str, base_name: str) -> bool:
        if class_name == base_name:
            return True
        current = self.get_class(class_name)
        visited: set[str] = set()
        while current and current.base_class and current.name not in visited:
            visited.add(current.name)
            if current.base_class == base_name:
                return True
            current = self.get_class(current.base_class)
        return False

    # 获取一个类“包含继承而来的成员”在内的完整成员列表，顺序为先基类后派生类。
    def get_all_members(self, class_name: str) -> list[MemberDef]:
        cls_def = self.get_class(class_name)
        if cls_def is None:
            return []
        members: list[MemberDef] = []
        if cls_def.base_class:
            members.extend(self.get_all_members(cls_def.base_class))
        members.extend(cls_def.members)
        return members

    # 判断指定类或其任意祖先类是否声明了虚函数，用于决定对象是否应包含 vptr。
    def class_has_virtual(self, class_name: str) -> bool:
        cls_def = self.get_class(class_name)
        if cls_def is None:
            return False
        if cls_def.has_virtual:
            return True
        if cls_def.base_class:
            return self.class_has_virtual(cls_def.base_class)
        return False

    # 根据类定义生成对应的 C++ 类声明与内联默认构造函数代码。
    def generate_cpp_code(self, class_name: str) -> str:
        cls_def = self.get_class(class_name)
        if cls_def is None:
            return "// 未找到该类"

        inherit_part = f" : public {cls_def.base_class}" if cls_def.base_class else ""
        lines = [f"class {cls_def.name}{inherit_part}", "{", "public:"]
        lines.append(f"    {cls_def.name}();")
        if cls_def.has_virtual:
            lines.append(f"    virtual ~{cls_def.name}() = default;")
            lines.append("    virtual void act() {}")
        lines.append("")
        lines.append("private:")
        if cls_def.members:
            for member in cls_def.members:
                cpp_type = self._to_cpp_type(member.type_name)
                lines.append(f"    {cpp_type} {member.var_name};")
        else:
            lines.append("    // 暂无成员变量")
        lines.append("};")
        lines.append("")
        lines.append(f"inline {cls_def.name}::{cls_def.name}()")
        if cls_def.base_class:
            lines.append(f"    : {cls_def.base_class}()")
        lines.append("{")
        lines.append("}")
        return "\n".join(lines)

    # 将当前所有类统一导出到指定头文件中，便于集中查看或保存生成结果。
    def export_all_cpp(self, file_path: str) -> None:
        content_parts = ["#pragma once", "", "#include <string>", ""]
        for cls_def in self._get_cpp_export_order():
            content_parts.append(self.generate_cpp_code(cls_def.name))
            content_parts.append("")
        Path(file_path).write_text("\n".join(content_parts), encoding="utf-8")

    def export_cpp_skeleton(self, output_dir: str) -> None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        class_header_lines = ["#pragma once", "", "#include <string>", ""]
        for cls_def in self._get_cpp_export_order():
            class_header_lines.append(self.generate_cpp_code(cls_def.name))
            class_header_lines.append("")
        (output_path / "classes.h").write_text("\n".join(class_header_lines), encoding="utf-8")

        file_map = {
            "main.cpp": self._build_main_cpp(),
            "game.h": self._build_game_h(),
            "game.cpp": self._build_game_cpp(),
            "headquarter.h": self._build_headquarter_h(),
            "headquarter.cpp": self._build_headquarter_cpp(),
            "city.h": self._build_city_h(),
            "city.cpp": self._build_city_cpp(),
            "warrior.h": self._build_warrior_h(),
            "warrior.cpp": self._build_warrior_cpp(),
            "weapon.h": self._build_weapon_h(),
            "weapon.cpp": self._build_weapon_cpp(),
            "README.txt": self._build_skeleton_readme(),
        }
        for file_name, content in file_map.items():
            (output_path / file_name).write_text(content, encoding="utf-8")

    # 计算指定类的教学化内存布局，输出各内存块及对象总大小。
    # 每个 MemoryBlock 均携带 source_class 字段，标明该块由继承链中的哪一个类定义。
    def compute_memory_layout(self, class_name: str) -> tuple[list[MemoryBlock], int]:
        cls_def = self.get_class(class_name)
        if cls_def is None:
            return [], 0

        blocks: list[MemoryBlock] = []
        offset = 0
        max_align = 1

        vptr_source = self._find_virtual_source(class_name)
        if vptr_source:
            blocks.append(MemoryBlock(
                offset=0, size=8, name="vptr", type_name="pointer",
                block_type="vptr", source_class=vptr_source,
            ))
            offset = 8
            max_align = 8

        for member, source_class in self._get_members_with_source(class_name):
            size = TYPE_SIZES.get(member.type_name, 4)
            align = min(size, 8) if size > 0 else 1
            max_align = max(max_align, align)

            padding = self._calc_padding(offset, align)
            if padding > 0:
                blocks.append(MemoryBlock(
                    offset=offset, size=padding, name="padding",
                    type_name="padding", block_type="padding",
                    source_class=source_class,
                ))
                offset += padding

            blocks.append(MemoryBlock(
                offset=offset, size=size, name=member.var_name,
                type_name=member.type_name, block_type="member",
                source_class=source_class,
            ))
            offset += size

        tail_padding = self._calc_padding(offset, max_align)
        if tail_padding > 0:
            blocks.append(MemoryBlock(
                offset=offset, size=tail_padding, name="tail_padding",
                type_name="padding", block_type="padding",
                source_class=class_name,
            ))
            offset += tail_padding

        return blocks, offset

    # 沿继承链向上追溯，找到第一个声明了虚函数的基类；若无则返回空字符串。
    def _find_virtual_source(self, class_name: str) -> str:
        current_name = class_name
        last_virtual_class = ""
        while current_name:
            cls_def = self.get_class(current_name)
            if cls_def is None:
                break
            if cls_def.has_virtual:
                last_virtual_class = current_name
            current_name = cls_def.base_class
        return last_virtual_class

    # 获取指定类的完整成员列表（含继承），每个成员附上其原始定义所在的类名。
    def _get_members_with_source(self, class_name: str) -> list[tuple[MemberDef, str]]:
        cls_def = self.get_class(class_name)
        if cls_def is None:
            return []
        result: list[tuple[MemberDef, str]] = []
        if cls_def.base_class:
            result.extend(self._get_members_with_source(cls_def.base_class))
        for member in cls_def.members:
            result.append((member, class_name))
        return result

    # C++ 导出必须保证基类先于派生类出现，否则 `class Derived : public Base` 无法编译。
    def _get_cpp_export_order(self) -> list[ClassDef]:
        ordered: list[ClassDef] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(class_name: str) -> None:
            if class_name in visited:
                return
            if class_name in visiting:
                raise ValueError(f"类继承关系存在循环，无法导出 C++：{class_name}")
            cls_def = self.get_class(class_name)
            if cls_def is None:
                return

            visiting.add(class_name)
            if cls_def.base_class:
                visit(cls_def.base_class)
            visiting.remove(class_name)
            visited.add(class_name)
            ordered.append(cls_def)

        for cls_def in self.get_all_classes():
            visit(cls_def.name)
        return ordered

    # 为指定类创建一个对象实例数据，并为未显式传入的成员补上按类型推断的默认值。
    def create_instance(self, class_name: str, init_values: dict | None = None) -> ObjectInstance:
        init_values = init_values or {}
        values = {}
        for member in self.get_all_members(class_name):
            values[member.var_name] = init_values.get(member.var_name, self._default_value_for_type(member.type_name))
        return ObjectInstance(class_name=class_name, values=values)

    # 校验类定义是否合法，包括类名、基类、成员名唯一性以及继承关系是否形成环。
    def _validate_class_def(self, cls_def: ClassDef, old_name: str | None = None) -> None:
        if not cls_def.name.strip():
            raise ValueError("类名不能为空")
        if " " in cls_def.name:
            raise ValueError("类名不能包含空格")
        if cls_def.name != old_name and cls_def.name in self._classes:
            raise ValueError("类名已存在")
        if cls_def.base_class == cls_def.name:
            raise ValueError("类不能继承自己")
        if cls_def.base_class and cls_def.base_class not in self._classes and cls_def.base_class != old_name:
            raise ValueError("基类不存在")

        member_names: set[str] = set()
        for member in cls_def.members:
            if not member.var_name.strip():
                raise ValueError("成员变量名不能为空")
            if member.var_name in member_names:
                raise ValueError("同一个类中成员变量名不能重复")
            member_names.add(member.var_name)

        if self._would_create_cycle(cls_def, old_name):
            raise ValueError("该继承关系会形成循环继承")

    # 预判当前修改后的继承关系是否会形成循环继承，避免保存非法类结构。
    def _would_create_cycle(self, cls_def: ClassDef, old_name: str | None) -> bool:
        if not cls_def.base_class:
            return False
        current_name = cls_def.name
        parent_name = cls_def.base_class
        visited: set[str] = {current_name}
        while parent_name:
            if parent_name in visited:
                return True
            visited.add(parent_name)
            parent = self.get_class(parent_name)
            if parent is None:
                if parent_name == old_name:
                    return True
                break
            parent_name = parent.base_class
        return False

    @staticmethod
    # 根据当前位置和目标对齐值计算所需补位字节数；若已对齐则返回 0。
    def _calc_padding(offset: int, align: int) -> int:
        if align <= 0:
            return 0
        remainder = offset % align
        return 0 if remainder == 0 else align - remainder

    @staticmethod
    # 将内部简化类型名映射为更符合 C++ 输出习惯的实际类型名称。
    def _to_cpp_type(type_name: str) -> str:
        mapping = {
            "string": "std::string",
            "pointer": "void*",
        }
        return mapping.get(type_name, type_name)

    @staticmethod
    # 按成员类型返回默认初始值，供创建对象实例时自动补全未提供的字段。
    def _default_value_for_type(type_name: str):
        defaults = {
            "bool": False,
            "char": "\\0",
            "int": 0,
            "float": 0.0,
            "double": 0.0,
            "string": "",
            "pointer": None,
        }
        return defaults.get(type_name, DEFAULT_MEMBER_NAMES.get(type_name, None))

    @staticmethod
    def _build_main_cpp() -> str:
        return """#include <cstddef>
#include <iostream>
#include <string>
#include <vector>

#include "game.h"

int main() {
    int M = 20;
    int N = 3;
    int R = 10;
    int K = 5;
    int T = 120;

    int first = 0;
    if (std::cin >> first) {
        std::vector<int> values;
        int value = 0;
        while (std::cin >> value) {
            values.push_back(value);
        }

        if (first > 0 && values.size() >= static_cast<std::size_t>(15 * first)) {
            M = values[0];
            N = values[1];
            R = values[2];
            K = values[3];
            T = values[4];
        } else if (values.size() >= 4) {
            M = first;
            N = values[0];
            R = values[1];
            K = values[2];
            T = values[3];
        }
    }

    Game game;
    game.initializeCase(M, N, R, K, T);
    game.run();
    for (const std::string& line : game.getLogs()) {
        std::cout << line << '\\n';
    }
    return 0;
}
"""

    @staticmethod
    def _build_game_h() -> str:
        return """#pragma once

#include "city.h"
#include "headquarter.h"
#include "warrior.h"

#include <string>
#include <vector>

class Game {
public:
    Game();
    void initializeCase(int M, int N, int R, int K, int T);
    void run();
    std::vector<std::string> getLogs() const;

private:
    int M_;
    int N_;
    int R_;
    int K_;
    int T_;
    Headquarter red_;
    Headquarter blue_;
    std::vector<City> cities_;
    std::vector<Warrior> warriors_;
    std::vector<std::string> logs_;

    void addLog(const std::string& message);
    void createWarriorFrom(const Headquarter& headquarter);
};
"""

    @staticmethod
    def _build_game_cpp() -> str:
        return """#include "game.h"

#include <string>
#include <vector>

Game::Game()
    : M_(0), N_(0), R_(0), K_(0), T_(0), red_("red", 0), blue_("blue", 0) {
}

void Game::initializeCase(int M, int N, int R, int K, int T) {
    M_ = M;
    N_ = N;
    R_ = R;
    K_ = K;
    T_ = T;
    red_ = Headquarter("red", M_);
    blue_ = Headquarter("blue", M_);
    cities_.clear();
    warriors_.clear();
    logs_.clear();

    for (int id = 1; id <= N_; ++id) {
        cities_.emplace_back(id);
    }

    addLog("Case 1:");
    addLog("config M=" + std::to_string(M_) + " N=" + std::to_string(N_) +
           " R=" + std::to_string(R_) + " K=" + std::to_string(K_) +
           " T=" + std::to_string(T_));
}

void Game::run() {
    const std::vector<std::string> red_order = {"iceman", "lion", "wolf", "ninja", "dragon"};
    const std::vector<std::string> blue_order = {"lion", "dragon", "ninja", "iceman", "wolf"};
    const std::vector<int> warrior_costs = {20, 20, 30, 10, 15};

    for (int hour = 0; hour * 60 <= T_; ++hour) {
        const int base = hour * 60;
        addLog(red_.tryProduceWarrior(base, red_order, warrior_costs));
        addLog(blue_.tryProduceWarrior(base, blue_order, warrior_costs));
        createWarriorFrom(red_);
        createWarriorFrom(blue_);

        if (base + 10 <= T_) {
            for (Warrior& warrior : warriors_) {
                if (warrior.alive()) {
                    addLog(warrior.march(base + 10, N_));
                }
            }
        }

        if (base + 20 <= T_) {
            for (City& city : cities_) {
                addLog(city.produceElements(base + 20));
            }
        }

        if (base + 40 <= T_) {
            for (City& city : cities_) {
                addLog(city.resolveBattle(base + 40));
            }
        }

        if (base + 50 <= T_) {
            addLog(red_.reportElements(base + 50));
            addLog(blue_.reportElements(base + 50));
        }

        if (base + 55 <= T_) {
            for (const Warrior& warrior : warriors_) {
                if (warrior.alive()) {
                    addLog(warrior.reportWeapons(base + 55));
                }
            }
        }
    }
}

std::vector<std::string> Game::getLogs() const {
    return logs_;
}

void Game::addLog(const std::string& message) {
    logs_.push_back(message);
}

void Game::createWarriorFrom(const Headquarter& headquarter) {
    if (!headquarter.producedThisTurn()) {
        return;
    }
    const int start_position = headquarter.camp() == "red" ? 0 : N_ + 1;
    warriors_.emplace_back(
        headquarter.totalWarriors(),
        20,
        K_,
        headquarter.camp(),
        headquarter.lastProducedKind(),
        start_position
    );
}
"""

    @staticmethod
    def _build_headquarter_h() -> str:
        return """#pragma once

#include <string>
#include <vector>

class Headquarter {
public:
    Headquarter(std::string camp = "red", int elements = 0);
    std::string tryProduceWarrior(int minute, const std::vector<std::string>& order, const std::vector<int>& costs);
    std::string reportElements(int minute) const;
    bool producedThisTurn() const;
    const std::string& lastProducedKind() const;
    const std::string& camp() const;
    int totalWarriors() const;

private:
    std::string camp_;
    int elements_;
    int nextIndex_;
    int totalWarriors_;
    bool producedThisTurn_;
    std::string lastProducedKind_;

    static std::string formatTime(int minute);
};
"""

    @staticmethod
    def _build_headquarter_cpp() -> str:
        return """#include "headquarter.h"

#include <iomanip>
#include <sstream>
#include <utility>

Headquarter::Headquarter(std::string camp, int elements)
    : camp_(std::move(camp)),
      elements_(elements),
      nextIndex_(0),
      totalWarriors_(0),
      producedThisTurn_(false),
      lastProducedKind_() {
}

std::string Headquarter::tryProduceWarrior(int minute, const std::vector<std::string>& order, const std::vector<int>& costs) {
    producedThisTurn_ = false;
    if (order.empty() || costs.empty()) {
        return formatTime(minute) + " " + camp_ + " headquarter has no production rule";
    }

    const int attempts = static_cast<int>(order.size());
    for (int offset = 0; offset < attempts; ++offset) {
        const int index = (nextIndex_ + offset) % attempts;
        const int cost = costs[index % static_cast<int>(costs.size())];
        if (elements_ >= cost) {
            elements_ -= cost;
            nextIndex_ = (index + 1) % attempts;
            ++totalWarriors_;
            producedThisTurn_ = true;
            lastProducedKind_ = order[index];
            return formatTime(minute) + " " + camp_ + " " + lastProducedKind_ + " " +
                   std::to_string(totalWarriors_) + " born";
        }
    }
    return formatTime(minute) + " " + camp_ + " headquarter waits";
}

std::string Headquarter::reportElements(int minute) const {
    return formatTime(minute) + " " + std::to_string(elements_) + " elements in " + camp_ + " headquarter";
}

bool Headquarter::producedThisTurn() const {
    return producedThisTurn_;
}

const std::string& Headquarter::lastProducedKind() const {
    return lastProducedKind_;
}

const std::string& Headquarter::camp() const {
    return camp_;
}

int Headquarter::totalWarriors() const {
    return totalWarriors_;
}

std::string Headquarter::formatTime(int minute) {
    std::ostringstream out;
    out << std::setw(3) << std::setfill('0') << minute / 60
        << ':' << std::setw(2) << std::setfill('0') << minute % 60;
    return out.str();
}
"""

    @staticmethod
    def _build_city_h() -> str:
        return """#pragma once

#include <string>

class City {
public:
    explicit City(int id);
    std::string produceElements(int minute);
    std::string resolveBattle(int minute) const;
    int id() const;
    int elements() const;

private:
    int id_;
    int elements_;
    std::string flag_;
    std::string lastWinner_;

    static std::string formatTime(int minute);
};
"""

    @staticmethod
    def _build_city_cpp() -> str:
        return """#include "city.h"

#include <iomanip>
#include <sstream>

City::City(int id)
    : id_(id), elements_(0) {
}

std::string City::produceElements(int minute) {
    elements_ += 10;
    return formatTime(minute) + " city " + std::to_string(id_) +
           " produced 10 elements, total " + std::to_string(elements_);
}

std::string City::resolveBattle(int minute) const {
    return formatTime(minute) + " city " + std::to_string(id_) +
           " checks battle state, flag=" + (flag_.empty() ? "none" : flag_);
}

int City::id() const {
    return id_;
}

int City::elements() const {
    return elements_;
}

std::string City::formatTime(int minute) {
    std::ostringstream out;
    out << std::setw(3) << std::setfill('0') << minute / 60
        << ':' << std::setw(2) << std::setfill('0') << minute % 60;
    return out.str();
}
"""

    @staticmethod
    def _build_warrior_h() -> str:
        return """#pragma once

#include <string>

class Warrior {
public:
    Warrior(int id, int hp, int attack, std::string camp, std::string kind, int position);
    virtual ~Warrior() = default;

    virtual std::string march(int minute, int cityCount);
    virtual std::string reportWeapons(int minute) const;
    virtual bool canCounterattack() const;
    bool alive() const;
    const std::string& camp() const;
    const std::string& kind() const;

protected:
    int id_;
    int hp_;
    int attack_;
    int position_;
    int steps_;
    std::string camp_;
    std::string kind_;

    static std::string formatTime(int minute);
};
"""

    @staticmethod
    def _build_warrior_cpp() -> str:
        return """#include "warrior.h"

#include <algorithm>
#include <iomanip>
#include <sstream>
#include <utility>

Warrior::Warrior(int id, int hp, int attack, std::string camp, std::string kind, int position)
    : id_(id),
      hp_(hp),
      attack_(attack),
      position_(position),
      steps_(0),
      camp_(std::move(camp)),
      kind_(std::move(kind)) {
}

std::string Warrior::march(int minute, int cityCount) {
    position_ += camp_ == "red" ? 1 : -1;
    ++steps_;
    if (kind_ == "iceman" && steps_ % 2 == 0) {
        hp_ = std::max(1, hp_ - 9);
        attack_ += 20;
    }

    std::string place = "city " + std::to_string(position_);
    if (position_ <= 0) {
        place = "red headquarter";
    } else if (position_ > cityCount) {
        place = "blue headquarter";
    }
    return formatTime(minute) + " " + camp_ + " " + kind_ + " " +
           std::to_string(id_) + " marched to " + place;
}

std::string Warrior::reportWeapons(int minute) const {
    const int weaponIndex = id_ % 3;
    std::string weapon = "sword(" + std::to_string(std::max(1, attack_ / 5)) + ")";
    if (weaponIndex == 1) {
        weapon = "bomb";
    } else if (weaponIndex == 2) {
        weapon = "arrow(3)";
    }
    return formatTime(minute) + " " + camp_ + " " + kind_ + " " +
           std::to_string(id_) + " has " + weapon;
}

bool Warrior::canCounterattack() const {
    return kind_ != "ninja";
}

bool Warrior::alive() const {
    return hp_ > 0;
}

const std::string& Warrior::camp() const {
    return camp_;
}

const std::string& Warrior::kind() const {
    return kind_;
}

std::string Warrior::formatTime(int minute) {
    std::ostringstream out;
    out << std::setw(3) << std::setfill('0') << minute / 60
        << ':' << std::setw(2) << std::setfill('0') << minute % 60;
    return out.str();
}
"""

    @staticmethod
    def _build_weapon_h() -> str:
        return """#pragma once

#include <string>

class Weapon {
public:
    explicit Weapon(std::string name);
    virtual ~Weapon() = default;
    virtual std::string report() const;

private:
    std::string name_;
};

class Sword : public Weapon {
public:
    explicit Sword(int attack);
    std::string report() const override;

private:
    int attack_;
};

class Bomb : public Weapon {
public:
    Bomb();
};

class Arrow : public Weapon {
public:
    explicit Arrow(int attack);
    std::string report() const override;

private:
    int attack_;
    int uses_;
};
"""

    @staticmethod
    def _build_weapon_cpp() -> str:
        return """#include "weapon.h"

#include <string>
#include <utility>

Weapon::Weapon(std::string name)
    : name_(std::move(name)) {
}

std::string Weapon::report() const {
    return name_;
}

Sword::Sword(int attack)
    : Weapon("sword"), attack_(attack) {
}

std::string Sword::report() const {
    return "sword(" + std::to_string(attack_) + ")";
}

Bomb::Bomb()
    : Weapon("bomb") {
}

Arrow::Arrow(int attack)
    : Weapon("arrow"), attack_(attack), uses_(3) {
}

std::string Arrow::report() const {
    return "arrow(" + std::to_string(uses_) + ")";
}
"""

    @staticmethod
    def _build_skeleton_readme() -> str:
        return """Warcraft C++ Skeleton

1. classes.h comes from the current visual class editor model.
2. The other .h/.cpp files form a runnable modular teaching project.
3. main.cpp reads either Warriors4-style input or a short M N R K T input; without input it runs a small built-in case.
4. Module boundaries are explicit: Game owns the timeline, Headquarter owns production, City owns city state, Warrior owns movement and reports, and Weapon owns weapon reports.
5. This skeleton is for learning and extension. For judge submission, export the OJ single-file solution from Task2.
"""

    # 在管理器为空时填充一组题面导向的默认类数据，便于界面初次打开即可体验完整模块化设计。
    def seed_demo_classes(self) -> None:
        if self._classes:
            return
        default_classes = [
            ClassDef(
                name="Headquarter",
                members=[
                    MemberDef("string", "camp"),
                    MemberDef("int", "elements"),
                    MemberDef("int", "nextIndex"),
                    MemberDef("int", "totalWarriors"),
                ],
            ),
            ClassDef(
                name="City",
                members=[
                    MemberDef("int", "id"),
                    MemberDef("int", "elements"),
                    MemberDef("string", "flag"),
                    MemberDef("string", "lastWinner"),
                ],
            ),
            ClassDef(
                name="Weapon",
                members=[MemberDef("string", "name")],
                has_virtual=True,
            ),
            ClassDef(
                name="Sword",
                base_class="Weapon",
                members=[MemberDef("int", "attack")],
            ),
            ClassDef(
                name="Bomb",
                base_class="Weapon",
                members=[MemberDef("bool", "available")],
            ),
            ClassDef(
                name="Arrow",
                base_class="Weapon",
                members=[MemberDef("int", "attack"), MemberDef("int", "uses")],
            ),
            ClassDef(
                name="Warrior",
                members=[
                    MemberDef("int", "id"),
                    MemberDef("int", "hp"),
                    MemberDef("int", "attack"),
                    MemberDef("int", "position"),
                    MemberDef("string", "camp"),
                    MemberDef("int", "weaponCount"),
                ],
                has_virtual=True,
            ),
            ClassDef(name="Dragon", base_class="Warrior", members=[MemberDef("double", "morale")]),
            ClassDef(name="Ninja", base_class="Warrior", members=[MemberDef("int", "secondWeaponIndex")]),
            ClassDef(name="Iceman", base_class="Warrior", members=[MemberDef("int", "stepCount")]),
            ClassDef(name="Lion", base_class="Warrior", members=[MemberDef("int", "loyalty")]),
            ClassDef(name="Wolf", base_class="Warrior", members=[MemberDef("int", "capturedWeaponCount")]),
        ]
        for cls_def in default_classes:
            self.add_class(cls_def)
