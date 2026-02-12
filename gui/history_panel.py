from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QListWidgetItem, QPushButton, QLabel, QFrame, QMessageBox,
                             QToolTip, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont


class HistoryPanel(QWidget):
    record_selected = pyqtSignal(dict)
    compare_selected = pyqtSignal(list)

    def __init__(self, history_manager, env_type=None, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.env_type = env_type
        self.selected_records = []
        self.tooltip_widget = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        header = QLabel('历史记录')
        header.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; padding: 5px;")
        layout.addWidget(header)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        self.list_widget.setMouseTracking(True)
        self.list_widget.viewport().installEventFilter(self)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
                font-size: 9px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #d5dbdb;
            }
        """)
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()

        self.view_btn = QPushButton('查看')
        self.view_btn.setFixedHeight(30)
        self.view_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.view_btn.clicked.connect(self.on_view_clicked)
        self.view_btn.setEnabled(False)
        button_layout.addWidget(self.view_btn)

        self.compare_btn = QPushButton('对比')
        self.compare_btn.setFixedHeight(30)
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.compare_btn.clicked.connect(self.on_compare_clicked)
        self.compare_btn.setEnabled(False)
        button_layout.addWidget(self.compare_btn)

        self.delete_btn = QPushButton('删除')
        self.delete_btn.setFixedHeight(30)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        layout.addLayout(button_layout)

        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)

    def refresh_list(self, env_type=None):
        self.list_widget.clear()
        records = self.history_manager.get_all_records()
        
        current_env_type = env_type or self.env_type
        if current_env_type:
            records = [r for r in records if r['env_type'] == current_env_type]

        for record in reversed(records):
            summary = self.history_manager.get_summary(record)
            item = QListWidgetItem(f"#{record['id']} - {record['timestamp']}\n{summary}")
            item.setData(Qt.UserRole, record)
            self.list_widget.addItem(item)

    def on_selection_changed(self):
        selected_items = self.list_widget.selectedItems()
        self.selected_records = [item.data(Qt.UserRole) for item in selected_items]
        
        has_selection = len(selected_items) > 0
        self.view_btn.setEnabled(len(selected_items) == 1)
        self.compare_btn.setEnabled(len(selected_items) >= 2)
        self.delete_btn.setEnabled(has_selection)

    def on_view_clicked(self):
        if self.selected_records:
            self.record_selected.emit(self.selected_records[0])

    def on_compare_clicked(self):
        if len(self.selected_records) >= 2:
            self.compare_selected.emit(self.selected_records)

    def on_delete_clicked(self):
        if not self.selected_records:
            return

        reply = QMessageBox.question(
            self, 
            '确认删除',
            f'确定要删除选中的 {len(self.selected_records)} 条记录吗？',
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for record in self.selected_records:
                self.history_manager.delete_record(record['id'])
            self.refresh_list()

    def eventFilter(self, obj, event):
        if obj == self.list_widget.viewport():
            if event.type() == event.MouseMove:
                self.on_mouse_move(event)
            elif event.type() == event.Leave:
                self.hide_tooltip()
        return super().eventFilter(obj, event)

    def on_mouse_move(self, event):
        item = self.list_widget.itemAt(event.pos())
        if item:
            record = item.data(Qt.UserRole)
            if record:
                self.show_tooltip(event.globalPos(), record)
            else:
                self.hide_tooltip()
        else:
            self.hide_tooltip()

    def show_tooltip(self, pos, record):
        if self.tooltip_widget:
            self.tooltip_widget.hide()
            self.tooltip_widget.deleteLater()

        self.tooltip_widget = RecordTooltip(record, self)
        self.tooltip_widget.move(pos.x() + 15, pos.y() + 15)
        self.tooltip_widget.show()

    def hide_tooltip(self):
        if self.tooltip_widget:
            self.tooltip_widget.hide()
            self.tooltip_widget = None


class RecordTooltip(QLabel):
    def __init__(self, record, parent=None):
        super().__init__(parent)
        self.record = record
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.setStyleSheet("""
            QLabel {
                background-color: rgb(44, 62, 80);
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 10px;
            }
        """)

        content = self._build_tooltip_content()
        self.setText(content)
        self.adjustSize()

    def _build_tooltip_content(self):
        record = self.record
        html = f"<div style='font-weight: bold; margin-bottom: 8px;'>记录 #{record['id']} - {record['timestamp']}</div>"
        
        # 环境参数
        html += "<div style='margin-top: 10px; font-weight: bold;'>环境参数:</div>"
        html += "<div style='margin-left: 10px;'>"
        
        if 'params' in record:
            params = record['params']
            if record['env_type'] == 'rain':
                if 'rain_rate' in params:
                    html += f"<div><span style='color: #3498db;'>降雨率:</span> {params['rain_rate']} mm/h</div>"
                html += f"<div><span style='color: #3498db;'>雨滴谱:</span> Marshall-Palmer</div>"
                if 'temperature' in params:
                    html += f"<div><span style='color: #3498db;'>温度:</span> {params['temperature']} K</div>"
            elif record['env_type'] == 'haze':
                if 'visibility' in params:
                    html += f"<div><span style='color: #3498db;'>能见度:</span> {params['visibility']} km</div>"
                html += f"<div><span style='color: #3498db;'>粒子谱:</span> Junge</div>"
                if 'ref_real' in params and 'ref_imag' in params:
                    html += f"<div><span style='color: #3498db;'>折射率:</span> {params['ref_real']:.3f} + j{params['ref_imag']:.5f}</div>"
        
        html += "</div>"

        # 系统参数
        if 'params' in record:
            params = record['params']
            html += "<div style='margin-top: 10px; font-weight: bold;'>系统参数:</div>"
            html += self._format_system_params(params)

        # 系统输出
        if 'results' in record:
            results = record['results']
            html += "<div style='margin-top: 10px; font-weight: bold;'>系统输出:</div>"
            html += self._format_system_output(results)

        return html

    def _format_system_params(self, params):
        html = "<div style='margin-left: 10px;'>"
        
        # 系统参数（与参数设置界面中的标签对应）
        if 'avg_power' in params:
            html += f"<div><span style='color: #f39c12;'>峰值发射功率:</span> {params['avg_power']} W</div>"
        
        if 'frequency' in params:
            html += f"<div><span style='color: #f39c12;'>工作频率:</span> {params['frequency']} GHz</div>"
        
        if 'wavelength' in params:
            html += f"<div><span style='color: #f39c12;'>波长:</span> {params['wavelength']:.2f} nm</div>"
        
        if 'pulse_width' in params:
            html += f"<div><span style='color: #f39c12;'>脉宽:</span> {params['pulse_width']} ns</div>"
        
        if 'system_efficiency' in params:
            html += f"<div><span style='color: #f39c12;'>系统效率:</span> {params['system_efficiency']}</div>"
        
        if 'max_range' in params:
            html += f"<div><span style='color: #f39c12;'>探测距离:</span> {params['max_range']} km</div>"
        
        if 'sensitivity' in params:
            html += f"<div><span style='color: #f39c12;'>灵敏度:</span> {params['sensitivity']} dBm</div>"
        
        html += "</div>"
        return html

    def _format_system_output(self, results):
        html = "<div style='margin-left: 10px;'>"
        
        # 系统输出参数（与参数设置界面中的标签对应）
        if 'eff_range' in results:
            html += f"<div><span style='color: #27ae60;'>有效探测距离:</span> {results['eff_range']:.2f} m</div>"
        
        if 'alpha' in results:
            html += f"<div><span style='color: #27ae60;'>消光系数:</span> {results['alpha'] * 1000:.4f} 1/km</div>"
        
        if 'beta' in results:
            html += f"<div><span style='color: #27ae60;'>后向散射系数:</span> {results['beta'] * 1000:.4f} 1/km</div>"
        
        if 'echo_power' in results:
            html += f"<div><span style='color: #27ae60;'>回波功率:</span> {results['echo_power']:.6e} W</div>"
        
        html += "</div>"
        return html
