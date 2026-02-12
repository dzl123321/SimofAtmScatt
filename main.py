import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont


def handle_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理"""
    print("Uncaught exception:", exc_type, exc_value)
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    sys.exit(1)


sys.excepthook = handle_exception


class StartupWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('大气散射特性建模仿真系统')
        self.setGeometry(300, 200, 600, 400)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #2c3e50, stop:1 #3498db);
            }
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                border: 2px solid #2980b9;
                border-radius: 10px;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 255);
                border-color: #1abc9c;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)

        # 标题
        title_label = QLabel('大气散射特性建模仿真系统')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Microsoft YaHei', 28, QFont.Bold))
        main_layout.addWidget(title_label)

        # 子标题
        subtitle_label = QLabel('请选择仿真环境类型')
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont('Microsoft YaHei', 16))
        main_layout.addWidget(subtitle_label)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(50)

        # 降雨环境按钮
        rain_btn = QPushButton('降雨环境仿真')
        rain_btn.clicked.connect(self.open_rain_simulation)
        button_layout.addWidget(rain_btn)

        # 雾霾环境按钮
        haze_btn = QPushButton('雾霾环境仿真')
        haze_btn.clicked.connect(self.open_haze_simulation)
        button_layout.addWidget(haze_btn)

        main_layout.addLayout(button_layout)

        # 版权信息
        copyright_label = QLabel('Copyright © 2024 西安电子科技大学')
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setFont(QFont('Microsoft YaHei', 10))
        main_layout.addWidget(copyright_label)

        main_layout.addStretch()

    def open_rain_simulation(self):
        try:
            from gui.rain_window import RainSimulationWindow
            self.rain_window = RainSimulationWindow()
            self.rain_window.show()
            self.hide()  # 隐藏而不是关闭启动窗口
        except Exception as e:
            print(f"打开降雨仿真失败: {e}")
            traceback.print_exc()

    def open_haze_simulation(self):
        try:
            from gui.haze_window import HazeSimulationWindow
            self.haze_window = HazeSimulationWindow()
            self.haze_window.show()
            self.hide()  # 隐藏而不是关闭启动窗口
        except Exception as e:
            print(f"打开雾霾仿真失败: {e}")
            traceback.print_exc()


def main():
    app = QApplication(sys.argv)

    # 设置应用名称
    app.setApplicationName("大气散射特性建模仿真系统")
    app.setOrganizationName("西安电子科技大学")

    app.setStyle('Fusion')

    # 检查更新
    try:
        from utils.update_manager import check_updates_on_start
        check_updates_on_start(app)
    except Exception as e:
        print(f"检查更新失败: {e}")

    # 显示启动窗口
    try:
        startup_window = StartupWindow()
        startup_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
