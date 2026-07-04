import sys

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError as exc:
    if exc.name != "PySide6":
        raise
    implementation_note = ""
    if sys.implementation.name != "cpython":
        implementation_note = (
            "\n当前不是 CPython。PySide6 在 Windows 上通常需要 CPython 解释器；"
            "如果你已经安装过 PySide6，请确认启动程序时用的是同一个 CPython。"
        )
    print(
        "缺少 GUI 依赖 PySide6。\n"
        "请在当前 Python 解释器中执行：python -m pip install -r requirements.txt\n"
        f"当前解释器：{sys.executable}"
        f"{implementation_note}",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

from ui.mainwindow import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
