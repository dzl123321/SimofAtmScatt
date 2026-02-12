from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QWidget, QLabel, QComboBox, QDoubleSpinBox, QSpinBox,
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QProgressBar, QMessageBox, QGroupBox, QCheckBox, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
import numpy as np
from datetime import datetime
import json


class BatchSimulationDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.env_type = getattr(main_window, 'env_type', 'rain')
        self.tasks = []
        self.current_task_index = 0
        self.results = []
        self.worker = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('批处理仿真')
        self.setFixedSize(900, 700)

        layout = QVBoxLayout(self)

        tab_widget = QTabWidget()
        
        tab_widget.addTab(self.create_param_scan_tab(), '参数扫描')
        tab_widget.addTab(self.create_multi_param_tab(), '多参数优化')
        tab_widget.addTab(self.create_task_queue_tab(), '任务队列')
        
        layout.addWidget(tab_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.run_btn = QPushButton('开始执行')
        self.run_btn.setFixedWidth(120)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.run_btn.clicked.connect(self.run_batch_simulation)
        button_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton('停止')
        self.stop_btn.setFixedWidth(120)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_simulation)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        self.export_btn = QPushButton('导出结果')
        self.export_btn.setFixedWidth(120)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)

    def create_param_scan_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scan_group = QGroupBox('参数扫描设置')
        scan_layout = QVBoxLayout(scan_group)
        
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel('扫描参数:'))
        
        self.param_combo = QComboBox()
        self.param_combo.setFixedWidth(200)
        param_layout.addWidget(self.param_combo)
        
        scan_layout.addLayout(param_layout)
        
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel('扫描范围:'))
        
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setFixedWidth(100)
        self.start_spin.setRange(-1000, 1000)
        self.start_spin.setValue(1.0)
        range_layout.addWidget(self.start_spin)
        
        range_layout.addWidget(QLabel('至'))
        
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setFixedWidth(100)
        self.end_spin.setRange(-1000, 1000)
        self.end_spin.setValue(25.0)
        range_layout.addWidget(self.end_spin)
        
        scan_layout.addLayout(range_layout)
        
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel('扫描步长:'))
        
        self.step_spin = QDoubleSpinBox()
        self.step_spin.setFixedWidth(100)
        self.step_spin.setRange(0.01, 100)
        self.step_spin.setValue(1.0)
        self.step_spin.setDecimals(2)
        step_layout.addWidget(self.step_spin)
        
        scan_layout.addLayout(step_layout)
        
        self.generate_btn = QPushButton('生成扫描任务')
        self.generate_btn.clicked.connect(self.generate_scan_tasks)
        scan_layout.addWidget(self.generate_btn)
        
        layout.addWidget(scan_group)
        
        preview_group = QGroupBox('任务预览')
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(['序号', '参数值'])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_table.verticalHeader().setVisible(False)
        preview_layout.addWidget(self.preview_table)
        
        layout.addWidget(preview_group)
        
        self.populate_param_combo()
        self.param_combo.currentIndexChanged.connect(self.update_spin_ranges)
        
        return widget

    def create_multi_param_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        multi_group = QGroupBox('多参数组合设置')
        multi_layout = QVBoxLayout(multi_group)
        
        self.param_checkboxes = []
        self.param_spins = []
        
        params = self.get_available_params()
        for i, (param_key, param_name, param_info) in enumerate(params):
            row_layout = QHBoxLayout()
            
            checkbox = QCheckBox(param_name)
            checkbox.setChecked(False)
            checkbox.stateChanged.connect(self.on_param_checkbox_changed)
            self.param_checkboxes.append((checkbox, param_key))
            row_layout.addWidget(checkbox)
            
            spin = QDoubleSpinBox()
            spin.setFixedWidth(100)
            spin.setRange(param_info['min'], param_info['max'])
            spin.setValue(param_info['default'])
            spin.setEnabled(False)
            spin.setDecimals(param_info.get('decimals', 2))
            self.param_spins.append((spin, param_key))
            row_layout.addWidget(spin)
            
            row_layout.addStretch()
            multi_layout.addLayout(row_layout)
        
        self.generate_multi_btn = QPushButton('生成组合任务')
        self.generate_multi_btn.clicked.connect(self.generate_multi_tasks)
        multi_layout.addWidget(self.generate_multi_btn)
        
        layout.addWidget(multi_group)
        
        preview_group = QGroupBox('组合预览')
        preview_layout = QVBoxLayout(preview_group)
        
        self.multi_preview_table = QTableWidget()
        self.multi_preview_table.setColumnCount(3)
        self.multi_preview_table.setHorizontalHeaderLabels(['序号', '参数名', '参数值'])
        self.multi_preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.multi_preview_table.verticalHeader().setVisible(False)
        preview_layout.addWidget(self.multi_preview_table)
        
        layout.addWidget(preview_group)
        
        return widget

    def create_task_queue_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        progress_group = QGroupBox('执行进度')
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(30)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel('就绪')
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        queue_group = QGroupBox('任务队列')
        queue_layout = QVBoxLayout(queue_group)
        
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(4)
        self.queue_table.setHorizontalHeaderLabels(['序号', '任务类型', '参数', '状态'])
        self.queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.queue_table.verticalHeader().setVisible(False)
        queue_layout.addWidget(self.queue_table)
        
        layout.addWidget(queue_group)
        
        return widget

    def populate_param_combo(self):
        self.param_combo.clear()
        params = self.get_available_params()
        for param_key, param_name, param_info in params:
            self.param_combo.addItem(param_name, param_key)
        
        self.update_spin_ranges()

    def get_available_params(self):
        if self.env_type == 'rain':
            return [
                ('rain_rate', '降雨率', {'min': 1.0, 'max': 25.0, 'default': 15.0, 'decimals': 1}),
                ('temperature', '温度', {'min': 250.0, 'max': 320.0, 'default': 277.0, 'decimals': 1}),
                ('avg_power', '峰值发射功率', {'min': 0.1, 'max': 1000.0, 'default': 0.1, 'decimals': 3}),
                ('frequency', '工作频率', {'min': 1.0, 'max': 100.0, 'default': 10.0, 'decimals': 2}),
                ('pulse_width', '脉宽', {'min': 1, 'max': 10000, 'default': 300, 'decimals': 0}),
                ('system_efficiency', '系统效率', {'min': 0.0, 'max': 1.0, 'default': 0.85, 'decimals': 2}),
                ('max_range', '探测距离', {'min': 1, 'max': 1000, 'default': 1, 'decimals': 0}),
                ('sensitivity', '灵敏度', {'min': -150.0, 'max': 0.0, 'default': -90.0, 'decimals': 1}),
            ]
        else:
            return [
                ('visibility', '能见度', {'min': 0.05, 'max': 20.0, 'default': 1.0, 'decimals': 2}),
                ('ref_real', '折射率实部', {'min': 1.0, 'max': 3.0, 'default': 1.45, 'decimals': 3}),
                ('ref_imag', '折射率虚部', {'min': 0.0, 'max': 1.0, 'default': 0.008, 'decimals': 5}),
                ('avg_power', '峰值发射功率', {'min': 0.1, 'max': 1000.0, 'default': 0.1, 'decimals': 3}),
                ('frequency', '工作频率', {'min': 0.1, 'max': 1000000.0, 'default': 193548.0, 'decimals': 2}),
                ('pulse_width', '脉宽', {'min': 1, 'max': 10000, 'default': 300, 'decimals': 0}),
                ('system_efficiency', '系统效率', {'min': 0.0, 'max': 1.0, 'default': 0.85, 'decimals': 2}),
                ('max_range', '探测距离', {'min': 1, 'max': 1000, 'default': 1, 'decimals': 0}),
                ('sensitivity', '灵敏度', {'min': -150.0, 'max': 0.0, 'default': -90.0, 'decimals': 1}),
            ]

    def update_spin_ranges(self):
        param_key = self.param_combo.currentData()
        params = self.get_available_params()
        for key, name, info in params:
            if key == param_key:
                self.start_spin.setRange(info['min'], info['max'])
                self.start_spin.setValue(info['min'])
                self.end_spin.setRange(info['min'], info['max'])
                self.end_spin.setValue(info['max'])
                self.step_spin.setValue((info['max'] - info['min']) / 10)
                break

    def on_param_checkbox_changed(self):
        for i, (checkbox, param_key) in enumerate(self.param_checkboxes):
            spin, _ = self.param_spins[i]
            spin.setEnabled(checkbox.isChecked())

    def generate_scan_tasks(self):
        param_key = self.param_combo.currentData()
        param_name = self.param_combo.currentText()
        start = self.start_spin.value()
        end = self.end_spin.value()
        step = self.step_spin.value()
        
        if step <= 0:
            QMessageBox.warning(self, '警告', '步长必须大于0')
            return
        
        values = np.arange(start, end + step, step)
        
        self.tasks = []
        for i, value in enumerate(values):
            task = {
                'type': 'scan',
                'param_key': param_key,
                'param_name': param_name,
                'value': value,
                'status': 'pending'
            }
            self.tasks.append(task)
        
        self.update_preview_table(values, param_name)
        self.update_queue_table()
        self.status_label.setText(f'已生成 {len(self.tasks)} 个扫描任务')

    def generate_multi_tasks(self):
        selected_params = []
        for i, (checkbox, param_key) in enumerate(self.param_checkboxes):
            if checkbox.isChecked():
                spin, _ = self.param_spins[i]
                selected_params.append((param_key, checkbox.text(), spin.value()))
        
        if not selected_params:
            QMessageBox.warning(self, '警告', '请至少选择一个参数')
            return
        
        self.tasks = []
        for i, (param_key, param_name, value) in enumerate(selected_params):
            task = {
                'type': 'multi',
                'param_key': param_key,
                'param_name': param_name,
                'value': value,
                'status': 'pending'
            }
            self.tasks.append(task)
        
        self.update_multi_preview_table(selected_params)
        self.update_queue_table()
        self.status_label.setText(f'已生成 {len(self.tasks)} 个组合任务')

    def update_preview_table(self, values, param_name):
        self.preview_table.setRowCount(len(values))
        for i, value in enumerate(values):
            self.preview_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.preview_table.setItem(i, 1, QTableWidgetItem(f'{value:.2f}'))

    def update_multi_preview_table(self, selected_params):
        self.multi_preview_table.setRowCount(len(selected_params))
        for i, (param_key, param_name, value) in enumerate(selected_params):
            self.multi_preview_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.multi_preview_table.setItem(i, 1, QTableWidgetItem(param_name))
            self.multi_preview_table.setItem(i, 2, QTableWidgetItem(f'{value:.2f}'))

    def update_queue_table(self):
        self.queue_table.setRowCount(len(self.tasks))
        for i, task in enumerate(self.tasks):
            self.queue_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            
            type_text = '参数扫描' if task['type'] == 'scan' else '多参数优化'
            self.queue_table.setItem(i, 1, QTableWidgetItem(type_text))
            
            param_text = f"{task['param_name']}: {task['value']:.2f}"
            self.queue_table.setItem(i, 2, QTableWidgetItem(param_text))
            
            status_item = QTableWidgetItem(task['status'])
            if task['status'] == 'pending':
                status_item.setForeground(QColor('#7f8c8d'))
            elif task['status'] == 'running':
                status_item.setForeground(QColor('#f39c12'))
            elif task['status'] == 'completed':
                status_item.setForeground(QColor('#27ae60'))
            elif task['status'] == 'failed':
                status_item.setForeground(QColor('#e74c3c'))
            self.queue_table.setItem(i, 3, status_item)

    def run_batch_simulation(self):
        if not self.tasks:
            QMessageBox.warning(self, '警告', '请先生成任务')
            return
        
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_btn.setEnabled(False)
        
        self.current_task_index = 0
        self.results = []
        
        self.worker = BatchSimulationWorker(self.tasks, self.main_window, self.env_type)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.task_completed.connect(self.on_task_completed)
        self.worker.all_completed.connect(self.on_all_completed)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.start()

    def stop_simulation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.stop_btn.setEnabled(False)
            self.status_label.setText('正在停止...')

    def on_progress_updated(self, current, total):
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f'执行中: {current}/{total}')

    def on_task_completed(self, task_index, result):
        if task_index < len(self.tasks):
            self.tasks[task_index]['status'] = 'completed'
            self.results.append(result)
            self.update_queue_table()

    def on_all_completed(self):
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        self.status_label.setText('所有任务已完成')
        self.progress_bar.setValue(100)
        QMessageBox.information(self, '完成', f'批处理仿真完成，共完成 {len(self.results)} 个任务')

    def on_error_occurred(self, task_index, error_msg):
        if task_index < len(self.tasks):
            self.tasks[task_index]['status'] = 'failed'
            self.update_queue_table()
        QMessageBox.critical(self, '错误', f'任务 {task_index + 1} 执行失败: {error_msg}')

    def export_results(self):
        if not self.results:
            QMessageBox.warning(self, '警告', '没有可导出的结果')
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"batch_simulation_{self.env_type}_{timestamp}.txt"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "保存批处理结果",
            default_filename,
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("批处理仿真结果\n")
                f.write("=" * 80 + "\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"环境类型: {self.env_type}\n")
                f.write(f"任务总数: {len(self.results)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, (task, result) in enumerate(zip(self.tasks, self.results)):
                    f.write(f"任务 {i + 1}:\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"类型: {task['type']}\n")
                    f.write(f"参数: {task['param_name']} = {task['value']:.2f}\n")
                    f.write(f"状态: {task['status']}\n")
                    f.write(f"结果:\n")
                    f.write(f"  有效探测距离: {result.get('eff_range', 0):.2f} m\n")
                    f.write(f"  消光系数: {result.get('alpha', 0) * 1000:.4f} 1/km\n")
                    f.write(f"  后向散射系数: {result.get('beta', 0) * 1000:.4f} 1/km\n")
                    f.write(f"  回波功率: {result.get('echo_power', 0):.6e} W\n")
                    f.write("\n")
            
            QMessageBox.information(self, '导出成功', f'结果已保存到:\n{filepath}')
        except Exception as e:
            QMessageBox.critical(self, '导出失败', f'保存文件失败: {str(e)}')


class BatchSimulationWorker(QThread):
    progress_updated = pyqtSignal(int, int)
    task_completed = pyqtSignal(int, dict)
    all_completed = pyqtSignal()
    error_occurred = pyqtSignal(int, str)

    def __init__(self, tasks, main_window, env_type):
        super().__init__()
        self.tasks = tasks
        self.main_window = main_window
        self.env_type = env_type
        self.running = True

    def run(self):
        for i, task in enumerate(self.tasks):
            if not self.running:
                break
            
            task['status'] = 'running'
            self.progress_updated.emit(i, len(self.tasks))
            
            try:
                result = self.execute_task(task)
                self.task_completed.emit(i, result)
            except Exception as e:
                self.error_occurred.emit(i, str(e))
        
        self.all_completed.emit()

    def execute_task(self, task):
        params = self.main_window.left_panel.get_parameters()
        params[task['param_key']] = task['value']
        
        if self.env_type == 'rain':
            from core.simulation_core import RainLidarSimulationCore
            sim = RainLidarSimulationCore(params)
        else:
            from core.haze_core import HazeLidarSimulationCore
            sim = HazeLidarSimulationCore(params)
        
        result = sim.run_simulation()
        return result

    def stop(self):
        self.running = False