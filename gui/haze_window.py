import matplotlib
import numpy as np

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QSplitter, QTabWidget, QMessageBox, QScrollArea,
                             QProgressBar, QStatusBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from gui.haze_left_panel import HazeLeftPanel
from gui.right_panel import RightPanel
from gui.history_panel import HistoryPanel
from gui.menu_bar import MenuBarManager
from core.haze_worker import HazeSimulationWorker
from utils.style_utils import setup_chinese_font
from utils.history_manager import HistoryManager
from main import StartupWindow


class HazeSimulationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.simulation_results = None
        self.env_type = 'haze'
        self.history_manager = HistoryManager()

        setup_chinese_font()

        self.initUI()
        try:
            self.setWindowIcon(QIcon('resources/icons/haze_cloud.png'))
        except:
            pass

    def initUI(self):
        self.setWindowTitle('雾霾环境下大气散射特性建模仿真')
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(900, 600)

        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QMenuBar {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
            }
            QMenuBar::item {
                background: transparent;
                padding: 5px 15px;
            }
            QMenuBar::item:selected {
                background: #3498db;
            }
            QMenu {
                background-color: white;
                border: 1px solid #bdc3c7;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
            }
            QSplitter::handle {
                background-color: #95a5a6;
                width: 10px;
                border-left: 2px solid #7f8c8d;
                border-right: 2px solid #7f8c8d;
            }
            QSplitter::handle:hover {
                background-color: #3498db;
                border-left: 2px solid #2980b9;
                border-right: 2px solid #2980b9;
            }
            QSplitter::handle:pressed {
                background-color: #2980b9;
                border-left: 2px solid #1a5276;
                border-right: 2px solid #1a5276;
            }
            QSplitter::handle:horizontal {
                image: none;
            }
            QProgressBar {
                border: 2px solid #2c3e50;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
                border-radius: 3px;
            }
            QStatusBar {
                background-color: #ecf0f1;
                border-top: 1px solid #bdc3c7;
            }
        """)

        self.menu_manager = MenuBarManager(self)
        menubar = self.menu_manager.create_menu_bar()
        self.setMenuBar(menubar)

        # 添加状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # 添加进度条到状态栏
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        # 添加状态标签
        self.status_label = QLabel('就绪')
        self.status_label.setMinimumWidth(200)
        
        self.statusBar.addPermanentWidget(self.status_label)
        self.statusBar.addPermanentWidget(self.progress_bar)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        content_splitter = QSplitter(Qt.Horizontal)

        left_tab_widget = QTabWidget()
        left_tab_widget.setTabPosition(QTabWidget.North)
        left_tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 8px 20px;
                border: 1px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
        """)

        self.left_panel = HazeLeftPanel()
        self.left_panel.run_btn.clicked.connect(self.on_run_clicked)
        
        # 添加滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.left_panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        left_tab_widget.addTab(scroll_area, "参数设置")

        self.history_panel = HistoryPanel(self.history_manager, self.env_type)
        self.history_panel.record_selected.connect(self.on_history_record_selected)
        self.history_panel.compare_selected.connect(self.on_compare_records)
        
        # 为历史记录面板添加滚动区域
        history_scroll_area = QScrollArea()
        history_scroll_area.setWidget(self.history_panel)
        history_scroll_area.setWidgetResizable(True)
        history_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        history_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        left_tab_widget.addTab(history_scroll_area, "历史记录")
        self.history_panel.refresh_list()

        content_splitter.addWidget(left_tab_widget)

        self.right_panel = RightPanel()
        content_splitter.addWidget(self.right_panel)

        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 3)
        content_splitter.setSizes([300, 900])

        main_layout.addWidget(content_splitter)

        copyright_label = QLabel('Copyright：西安电子科技大学')
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        main_layout.addWidget(copyright_label)

    def on_run_clicked(self):
        params = self.left_panel.get_parameters()
        params['env_type'] = self.env_type

        self.left_panel.run_btn.setEnabled(False)
        self.left_panel.run_btn.setText("正在计算...")

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("开始仿真计算...")

        self.worker = HazeSimulationWorker(params)
        self.worker.finished.connect(self.on_simulation_finished)
        self.worker.error.connect(self.on_simulation_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()

    def on_progress_update(self, progress, message):
        """处理进度更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        QApplication.processEvents()  # 确保界面更新

    def on_simulation_finished(self, results):
        self.left_panel.run_btn.setEnabled(True)
        self.left_panel.run_btn.setText("开始仿真")

        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.status_label.setText("仿真计算完成")

        self.simulation_results = results
        self.menu_manager.set_simulation_results(results)

        self.left_panel.update_outputs(results)

        if 'radii' not in results or 'size_distribution' not in results:
            results['radii'] = np.linspace(0.1, 6.0, 50)
            results['size_distribution'] = 8000.0 * np.exp(-4.1 * np.power(100, -0.21) * results['radii'])

        self.right_panel.update_plots(results, self.worker.params['sensitivity_watts'])

        self.history_manager.add_record(self.worker.params, results, self.env_type)
        self.history_panel.refresh_list(self.env_type)

    def on_history_record_selected(self, record):
        self.left_panel.update_outputs(record['results'])
        
        if 'radii' in record['results'] and 'size_distribution' in record['results']:
            self.right_panel.update_plots(record['results'], 
                                      record['params'].get('sensitivity_watts', 1e-12))
        else:
            record['results']['radii'] = np.linspace(0.1, 6.0, 50)
            record['results']['size_distribution'] = 8000.0 * np.exp(-4.1 * np.power(100, -0.21) * record['results']['radii'])
            self.right_panel.update_plots(record['results'], 
                                      record['params'].get('sensitivity_watts', 1e-12))

    def on_compare_records(self, records):
        self.right_panel.compare_plots(records)

    def on_simulation_error(self, error_msg):
        self.left_panel.run_btn.setEnabled(True)
        self.left_panel.run_btn.setText("开始仿真")
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.status_label.setText("仿真计算出错")
        
        QMessageBox.critical(self, "仿真错误", f"计算过程中发生错误:\n{error_msg}")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '确认退出',
                                     '确定要退出仿真吗？',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            if hasattr(self, 'menu_manager') and hasattr(self.menu_manager, 'remove_window'):
                self.menu_manager.remove_window(self)
            app = QApplication.instance()
            for widget in app.topLevelWidgets():
                if isinstance(widget, StartupWindow):
                    widget.show()
                    break
        else:
            event.ignore()
