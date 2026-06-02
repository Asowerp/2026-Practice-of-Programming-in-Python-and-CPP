from dataclasses import dataclass, field
from typing import Any, List


# 表示单个成员变量的定义信息，包含类型名与变量名。
@dataclass
class MemberDef:
    type_name: str
    var_name: str


# 表示一个类的结构定义，记录类名、继承关系、成员列表和虚函数标记。
@dataclass
class ClassDef:
    name: str
    base_class: str = ""
    members: List[MemberDef] = field(default_factory=list)
    has_virtual: bool = False
    description: str = ""


# 表示内存布局中的一个连续块，可用于描述成员、vptr 或对齐补位。
# source_class 记录该块的"定义来源"类名，用于教学展示继承关系。
@dataclass
class MemoryBlock:
    offset: int
    size: int
    name: str
    type_name: str
    block_type: str = "member"
    source_class: str = ""


# 表示一个轻量级对象实例，保存类名及其成员当前值。
@dataclass
class ObjectInstance:
    class_name: str
    values: dict[str, Any] = field(default_factory=dict)
