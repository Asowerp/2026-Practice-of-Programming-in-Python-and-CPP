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
            lines.append("    virtual void act();")
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
        else:
            lines.append("    :")
        lines.append("{")
        lines.append("}")
        return "\n".join(lines)

    # 将当前所有类统一导出到指定头文件中，便于集中查看或保存生成结果。
    def export_all_cpp(self, file_path: str) -> None:
        content_parts = ["#pragma once", "", "#include <string>", ""]
        for cls_def in self.get_all_classes():
            content_parts.append(self.generate_cpp_code(cls_def.name))
            content_parts.append("")
        Path(file_path).write_text("\n".join(content_parts), encoding="utf-8")

    def export_cpp_skeleton(self, output_dir: str) -> None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        class_header_lines = ["#pragma once", "", "#include <string>", ""]
        for cls_def in self.get_all_classes():
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
        return """#include <iostream>
#include \"game.h\"

int main() {
    // TODO: 读取输入，构造 Game，并输出事件日志。
    std::cout << \"Warcraft skeleton project\" << std::endl;
    return 0;
}
"""

    @staticmethod
    def _build_game_h() -> str:
        return """#pragma once

#include <vector>
#include <string>

class Game {
public:
    Game();
    void initializeCase(int M, int N, int R, int K, int T);
    void run();
    std::vector<std::string> getLogs() const;

private:
    // TODO: 维护时间轴、司令部、城市和武士集合。
};
"""

    @staticmethod
    def _build_game_cpp() -> str:
        return """#include \"game.h\"

Game::Game() = default;

void Game::initializeCase(int M, int N, int R, int K, int T) {
    // TODO: 初始化题面参数和地图状态。
}

void Game::run() {
    // TODO: 按 00/05/10/20/30/35/38/40/50/55 的分钟点推进整局模拟。
}

std::vector<std::string> Game::getLogs() const {
    // TODO: 返回完整标准输出。
    return {};
}
"""

    @staticmethod
    def _build_headquarter_h() -> str:
        return """#pragma once

#include <string>

class Headquarter {
public:
    Headquarter(std::string camp, int elements);
    void tryProduceWarrior();
    void reportElements() const;

private:
    std::string camp_;
    int elements_;
    int nextIndex_;
    int totalWarriors_;
};
"""

    @staticmethod
    def _build_headquarter_cpp() -> str:
        return """#include \"headquarter.h\"

Headquarter::Headquarter(std::string camp, int elements)
    : camp_(std::move(camp)), elements_(elements), nextIndex_(0), totalWarriors_(0) {
}

void Headquarter::tryProduceWarrior() {
    // TODO: 按红蓝固定序列尝试造兵，若生命元不足则等待下一个整点。
}

void Headquarter::reportElements() const {
    // TODO: 输出 50 分司令部生命元报告。
}
"""

    @staticmethod
    def _build_city_h() -> str:
        return """#pragma once

#include <string>

class City {
public:
    explicit City(int id);
    void produceElements();
    void resolveBattle();

private:
    int id_;
    int elements_;
    std::string flag_;
    std::string lastWinner_;
};
"""

    @staticmethod
    def _build_city_cpp() -> str:
        return """#include \"city.h\"

City::City(int id)
    : id_(id), elements_(0) {
}

void City::produceElements() {
    // TODO: 20 分产出 10 个生命元。
}

void City::resolveBattle() {
    // TODO: 40 分处理主动攻击、反击、旗帜和战后生命元结算。
}
"""

    @staticmethod
    def _build_warrior_h() -> str:
        return """#pragma once

#include <string>

class Warrior {
public:
    Warrior(int id, int hp, int attack, std::string camp);
    virtual ~Warrior() = default;

    virtual void march();
    virtual void reportWeapons() const;
    virtual bool canCounterattack() const;

protected:
    int id_;
    int hp_;
    int attack_;
    int position_;
    std::string camp_;
};
"""

    @staticmethod
    def _build_warrior_cpp() -> str:
        return """#include \"warrior.h\"

Warrior::Warrior(int id, int hp, int attack, std::string camp)
    : id_(id), hp_(hp), attack_(attack), position_(0), camp_(std::move(camp)) {
}

void Warrior::march() {
    // TODO: 10 分行军；Iceman 需要在每两步后修改 hp 和 attack。
}

void Warrior::reportWeapons() const {
    // TODO: 55 分按 arrow,bomb,sword 顺序报告武器。
}

bool Warrior::canCounterattack() const {
    return true;
}
"""

    @staticmethod
    def _build_weapon_h() -> str:
        return """#pragma once

class Weapon {
public:
    virtual ~Weapon() = default;
};

class Sword : public Weapon {
public:
    explicit Sword(int attack);

private:
    int attack_;
};

class Bomb : public Weapon {
public:
    Bomb() = default;
};

class Arrow : public Weapon {
public:
    explicit Arrow(int attack);

private:
    int attack_;
    int uses_;
};
"""

    @staticmethod
    def _build_weapon_cpp() -> str:
        return """#include \"weapon.h\"

Sword::Sword(int attack)
    : attack_(attack) {
}

Arrow::Arrow(int attack)
    : attack_(attack), uses_(3) {
}
"""

    @staticmethod
    def _build_skeleton_readme() -> str:
        return """Warcraft C++ Skeleton

1. classes.h 来自图形化类编辑器导出的当前类定义。
2. 其余 .h / .cpp 文件是根据 warcraft.txt 题面准备的工程骨架。
3. 这些文件主要提供类划分、方法签名和 TODO 提示，不保证已经实现完整题解。
4. 建议从 Game::run() 开始，把时间轴规则逐步补全。
"""

    # 在管理器为空时填充一组演示类数据，便于界面初次打开即可直接体验功能。
    def seed_demo_classes(self) -> None:
        if self._classes:
            return
        self.add_class(
            ClassDef(
                name="Warrior",
                members=[MemberDef("int", "hp"), MemberDef("int", "attack")],
                has_virtual=True,
            )
        )
        self.add_class(ClassDef(name="Dragon", base_class="Warrior", members=[MemberDef("double", "morale")]))
        self.add_class(ClassDef(name="Ninja", base_class="Warrior", members=[MemberDef("int", "weaponCount")]))
        self.add_class(ClassDef(name="Iceman", base_class="Warrior", members=[MemberDef("int", "stepCount")]))
