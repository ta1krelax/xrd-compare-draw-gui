import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    # Fusion 配合样式表渲染更干净：原生 windowsvista 风格会在我们的圆角/配色
    # 上面再叠加一层它自己的渐变描边，两者混在一起就是之前看到的"阴影"感。
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
