# 魔兽世界大作业辅助工具使用指南

本工具覆盖 C++《魔兽世界》大作业的完整学习流程：类设计、内存查看、事件时间轴、Task1 校验、Task2 整局模拟、Task3 日志对拍与 AI 辅助调错。

## 运行方式

```bash
pip install -r requirements.txt
python main.py
```

如果只需要验证核心逻辑，可以直接运行 Python 模块测试或导入 `engine` 中的纯逻辑模块；GUI 依赖集中在 `ui/` 目录。

如果启动 GUI 时提示缺少 `PySide6`，请先确认 `python -c "import sys; print(sys.executable); print(sys.implementation.name)"` 指向的是安装了 PySide6 的 CPython。Windows 下如果 `python` 指向 PyPy，建议切换到 CPython 后重新执行 `python -m pip install -r requirements.txt`。

也可以先运行环境自检：

```bash
python check_environment.py
```

它会显示当前 Python、PySide6、g++ 状态，并给出下一步建议。

## 1. 类编辑器

可视化设计 C++ 类结构，并实时生成类定义代码。

- 点击“新建类”创建类。
- 填写类名、选择基类、添加成员变量。
- 支持成员拖拽排序、删除类、自动识别已有基类。
- 右侧实时预览生成的 C++ 代码。
- 完成后可通过菜单导出当前类定义。

## 2. 内存视图

可视化查看类对象内存布局。

- 下拉选择对应类，查看对象内存条形图。
- 悬停查看成员类型、偏移、大小和来源类。
- 标识普通成员、虚表指针和对齐填充。
- 用于理解对象大小、内存对齐和继承布局。

## 3. 内置时间轴

时间轴已经整合进 Task2 和 Task3，不再作为单独标签页出现。

- 在 Task2 执行模拟并导出事件后，可直接在右侧时间轴播放、暂停、步进和滑块跳转。
- Task2 时间轴选中某条事件时，会同步显示事件编号、时间、阶段、总分钟、位置顺序和说明。
- Task3 导入 Task2 结果后，也会显示同一条事件流，便于按时间定位日志差异。
- 可复盘造兵、逃跑、行军、射箭、炸弹、战斗、司令部报告、武器报告等节点。

## 4. Task1：武士层级校验

自动校验类继承结构是否符合基础设计要求。

- 设计 `Warrior` 及子类 `Dragon` / `Ninja` / `Iceman`。
- 校验 `hp`、`attack` 等必要成员。
- 校验直接继承关系、成员完整性、构造初始化列表示例和虚函数特性。
- 支持通过积木脚本组合自定义校验规则。

## 5. Task2：整局模拟器

按题面阶段推进整局《魔兽世界》模拟，并导出标准事件流。

- 支持设置 `M N R K T`、生命值表、攻击力表。
- 支持标准题面阶段：`00/05/10/20/30/35/38/40/50/55`。
- 支持教学模式下启用/禁用阶段、调整阶段分钟。
- 可以逐阶段、逐小时或一直运行到时间上限。
- 可以查看司令部、城市、武士、旗帜和生命元变化。
- C++ 导出分为两种模式：
  - `OJ 单文件题解`：导出可直接提交的 `task2_solution.cpp`、`expected_log.txt`、`README.txt` 和 `MODULE_DESIGN.md`。
  - `模块化学习工程骨架`：导出 `Game / Headquarter / City / Warrior / Weapon` 等 `.h/.cpp` 骨架，帮助同学先理解合理模块设计。

Task2 左侧积木表示“模拟配置和事件阶段”，不是 C++ 源文件模块。Python 参考实现已经按更细粒度拆分：`warcraft_models` 管数据模型和时间表，`warcraft_factory` 管造兵和初始武器，`warcraft_queries` 管战场查询，`warcraft_battle_rules` 管先手、死亡预测和旗帜规则，`warcraft_reporting` 管文本格式化，`warcraft_engine` 只负责时间推进和阶段编排。OJ 导出时仍会把这些边界映射到单个 `task2_solution.cpp`，以适配提交环境。

## 6. Task3：日志助手与 AI 调错

对比标准日志和学生程序输出，快速定位格式或逻辑错误。

- 从 Task2 接收统一事件流并生成标准日志。
- 支持按小时、阶段、关键词筛选局部事件。
- 支持逐行对拍并生成 HTML 差异高亮。
- 支持选择 AI 模型并填写 API Key 后辅助调错。
- 内置 DeepSeek、OpenAI GPT-4o mini、OpenAI GPT-4.1 mini，以及 OpenAI 兼容自定义接口。
- API Key 仅用于本次请求，不会保存到本地文件。

AI 调错模块位于 `engine/ai_log_assistant.py`，界面只负责采集模型配置和展示建议；日志比较逻辑仍位于 `engine/task3_log_helper.py`，避免把网络调用塞进模拟器或 UI 核心逻辑。

## 快速上手流程

1. 用类编辑器完成类结构。
2. 用 Task1 校验类设计。
3. 在 Task2 设置 Case 并运行整局模拟。
4. 直接在 Task2 内置时间轴复盘事件顺序和局部状态。
5. 将 Task2 事件导入 Task3，粘贴自己的输出并对拍。
6. 在 Task3 内置时间轴定位差异；如有需要，选择 AI 模型、填写 API Key，点击“AI 分析差异”获取调试建议。

## 项目结构

```text
WOWhelper/
├── main.py                      # 程序入口
├── constants.py                 # 常量与样式
├── README.md                    # 用户文档
├── requirements.txt             # GUI 依赖
├── check_environment.py         # Python / PySide6 / g++ 环境自检
├── run_regressions.py           # 一键回归验证入口
├── run_warriors4.py             # Warriors4 OJ 输入输出验证入口
├── t.txt                        # Warriors4 题面文本
├── warriors4_data/              # Warriors4 样例输入输出
├── engine/                      # 业务逻辑层
│   ├── ai_log_assistant.py      # AI 日志调错接口封装
│   ├── class_manager.py         # 类定义管理器
│   ├── models.py                # 数据模型
│   ├── battle_engine.py         # 简化战斗引擎
│   ├── warcraft_models.py       # Task2 配置、时间表、世界状态和事件数据结构
│   ├── warcraft_factory.py      # Task2 造兵顺序和初始武器工厂
│   ├── warcraft_queries.py      # Task2 战场查询与武士检索
│   ├── warcraft_battle_rules.py # Task2 先手、死亡预测和城市旗帜规则
│   ├── warcraft_reporting.py    # Task2 行军、到达司令部等输出文本格式化
│   ├── warcraft_engine.py       # Task2 整局模拟编排引擎
│   ├── warriors4_runner.py      # Warriors4 OJ 格式解析与渲染
│   ├── task1_validator.py       # Task1 校验逻辑
│   ├── task2_battle.py          # Task2 简化战斗辅助逻辑
│   ├── task2_cpp_exporter.py    # Task2 OJ 单文件导出器与模块设计说明生成
│   └── task3_log_helper.py      # Task3 日志生成与对比
└── ui/                          # 界面层
    ├── mainwindow.py            # 主窗口
    ├── class_editor_widget.py   # 类编辑器界面
    ├── memory_view_widget.py    # 内存视图界面
    ├── task1_widget.py          # Task1 界面
    ├── task2_widget.py          # Task2 界面与内置时间轴
    ├── task3_widget.py          # Task3 界面、内置时间轴与 AI 调错入口
    ├── timeline_panel.py        # 可复用时间轴面板
    ├── timeline_controller.py   # 时间轴播放控制器
    ├── block_workspace.py       # 积木工作区
    ├── ui_form.py               # Qt Designer 生成的 UI
    ├── ui_dialog.py             # 介绍对话框
    └── resources_rc.py          # 资源文件
```

## 核心功能

- 解析题目设计需求。
- 校验类结构设计正确性。
- 模拟标准题面事件流。
- 验证程序输出结果。
- 借助 AI 快速定位日志差异原因。
- 保持模拟器、日志处理、AI 接口和界面层的模块化边界。

## 开发验证

推荐在提交前运行：

```bash
python run_regressions.py
```

该命令会一次性检查：

- Python 语法编译。
- GUI 模块导入状态；如果当前解释器没有安装 PySide6，会清晰标记为跳过。
- 默认模块化类设计是否覆盖题面对象集合。
- 模块化 C++ 学习工程骨架是否能用 `g++ -std=c++20` 编译并运行出教学事件流。
- Task3 日志筛选、逐行对拍和 AI 调错配置的本地确定性行为。
- Warriors4 两组样例回归。
- Task2 C++ 导出包是否包含 `MODULE_DESIGN.md`，并在有 `g++` 时编译运行 `task2_solution.cpp` 与 `expected_log.txt` 对拍。

如果想把 GUI 依赖也作为硬性验收条件，可以运行：

```bash
python run_regressions.py --strict-gui
```

该模式会在当前 Python 缺少 PySide6 时直接失败，适合安装好 CPython + PySide6 后做完整 GUI 导入验收。

也可以分项运行：

```bash
python -m compileall .
python -c "from engine.warcraft_engine import WarcraftEngine, build_default_config, build_schedule_profile; cfg=build_default_config(); e=WarcraftEngine(cfg, build_schedule_profile()); print(e.initialize_case()); e.run_until_limit(); print(len(e.export_bundle().events))"
```

如果要直接验证 Warriors4 的 OJ 样例：

```bash
python run_warriors4.py warriors4_data/extra.in --compare warriors4_data/extra.out
python run_warriors4.py warriors4_data/Warcraft.in --compare warriors4_data/Warcraft.out
```

这两个命令会使用 `engine/warriors4_runner.py` 解析题面输入格式，调用 Task2 参考模拟器生成 `Case n:` 格式输出，并逐行对比标准答案。
