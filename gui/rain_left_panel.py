from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox,
                             QLabel, QDoubleSpinBox, QSpinBox, QLineEdit,
                             QPushButton, QHBoxLayout, QToolButton, QFrame)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QCursor


class CollapsibleGroupBox(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header = QFrame()
        self.header.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 5px 5px 0 0;
            }
        """)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 5, 5, 5)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(self.title_label)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.setArrowType(Qt.DownArrow)
        self.toggle_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
            }
            QToolButton:hover {
                background-color: #d5dbdb;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_content)
        header_layout.addWidget(self.toggle_btn)

        self.main_layout.addWidget(self.header)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.addWidget(self.content_widget)

        self.animation = QPropertyAnimation(self.content_widget, b"maximumHeight")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.content_height = 0
        self.is_collapsed = False

    def toggle_content(self):
        if self.toggle_btn.isChecked():
            self.expand()
        else:
            self.collapse()

    def expand(self):
        if self.content_height == 0:
            self.content_height = self.content_widget.sizeHint().height()
        
        self.content_widget.setVisible(True)
        self.content_widget.setMaximumHeight(16777215)
        
        self.animation.stop()
        self.animation.setStartValue(0)
        self.animation.setEndValue(self.content_height)
        try:
            self.animation.finished.disconnect()
        except:
            pass
        self.animation.start()
        
        self.toggle_btn.setArrowType(Qt.DownArrow)
        self.is_collapsed = False

    def collapse(self):
        if self.content_height == 0:
            self.content_height = self.content_widget.sizeHint().height()
        
        self.animation.stop()
        self.animation.setStartValue(self.content_widget.height())
        self.animation.setEndValue(0)
        
        def on_finished():
            self.content_widget.setVisible(False)
            
        try:
            self.animation.finished.disconnect()
        except:
            pass
        self.animation.finished.connect(on_finished)
        self.animation.start()
        
        self.toggle_btn.setArrowType(Qt.RightArrow)
        self.is_collapsed = True

    def setContentLayout(self, layout):
        self.content_layout.addLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        if self.content_height == 0:
            self.content_widget.setVisible(True)
            self.content_height = self.content_widget.sizeHint().height()
            if self.is_collapsed:
                self.content_widget.setVisible(False)


class RainLeftPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.params_widgets = {}
        self.output_widgets = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        rain_group = CollapsibleGroupBox('降雨环境参数')
        r_layout = QGridLayout()
        r_layout.setSpacing(8)

        r_layout.addWidget(QLabel('降雨率 (mm/h)'), 0, 0)
        self.rain_rate_spin = QDoubleSpinBox()
        self.rain_rate_spin.setRange(1.0, 25.0)
        self.rain_rate_spin.setValue(15.0)
        r_layout.addWidget(self.rain_rate_spin, 0, 1)

        r_layout.addWidget(QLabel('雨滴谱'), 1, 0)
        le_spectrum = QLineEdit('Marshall-Palmer')
        le_spectrum.setReadOnly(True)
        le_spectrum.setAlignment(Qt.AlignRight)
        r_layout.addWidget(le_spectrum, 1, 1)

        r_layout.addWidget(QLabel('温度 (K)'), 2, 0)
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(250.0, 320.0)
        self.temperature_spin.setValue(277.0)
        self.temperature_spin.setDecimals(1)
        r_layout.addWidget(self.temperature_spin, 2, 1)

        rain_group.setContentLayout(r_layout)
        layout.addWidget(rain_group)

        sys_group = CollapsibleGroupBox('系统参数')
        s_layout = QGridLayout()
        s_layout.setSpacing(8)

        params_config = [
            ('峰值发射功率 (W)', 'avg_power', QDoubleSpinBox, 0.1, 0, 1000, 3),
            ('工作频率   (GHz)', 'frequency', QDoubleSpinBox, 10.0, 1, 100, 2),
            ('脉宽        (ns)', 'pulse_width', QSpinBox, 300, 1, 10000, 0),
            ('系统效率', 'system_efficiency', QDoubleSpinBox, 0.85, 0, 1, 2),
            ('探测距离    (km)', 'max_range', QSpinBox, 1, 1, 1000, 0),
            ('灵敏度      (dBm)', 'sensitivity', QDoubleSpinBox, -90.0, -150.0, 0.0, 1)
        ]

        for i, (label, key, widget_type, default, min_v, max_v, decimals) in enumerate(params_config):
            s_layout.addWidget(QLabel(label), i, 0)
            widget = widget_type()
            widget.setRange(min_v, max_v)
            widget.setValue(default)
            if isinstance(widget, QDoubleSpinBox):
                widget.setDecimals(decimals)
                widget.setSingleStep(0.1 if decimals > 0 else 1)
            self.params_widgets[key] = widget
            s_layout.addWidget(widget, i, 1)

        sys_group.setContentLayout(s_layout)
        layout.addWidget(sys_group)

        out_group = CollapsibleGroupBox('系统输出')
        o_layout = QGridLayout()
        o_layout.setSpacing(8)

        outputs = ['有效探测距离 (m)', '消光系数 (1/km)', '后向散射系数 (1/km)', '回波功率 (W)']
        keys = ['eff_range', 'alpha', 'beta', 'echo_power']

        for i, (label, key) in enumerate(zip(outputs, keys)):
            o_layout.addWidget(QLabel(label), i, 0)
            le = QLineEdit()
            le.setReadOnly(True)
            le.setAlignment(Qt.AlignRight)
            le.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")
            self.output_widgets[key] = le
            o_layout.addWidget(le, i, 1)

        out_group.setContentLayout(o_layout)
        layout.addWidget(out_group)

        self.run_btn = QPushButton("开始仿真")
        self.run_btn.setFixedHeight(45)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 15px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1a5276;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        layout.addWidget(self.run_btn)

        layout.addStretch(1)

    def get_parameters(self):
        """获取所有输入参数"""
        # 将频率(GHz)转换为波长(nm): λ(nm) = 3e8 / f(GHz)
        frequency_ghz = self.params_widgets['frequency'].value()
        wavelength_nm = 3e8 / frequency_ghz
        
        params = {
            'avg_power': self.params_widgets['avg_power'].value(),
            'frequency': frequency_ghz,  # 频率(GHz)用于计算复折射率
            'wavelength': wavelength_nm,  # 转换后的波长用于Mie散射计算
            # 'rep_rate': self.params_widgets['rep_rate'].value(),
            'pulse_width': self.params_widgets['pulse_width'].value(),
            # 'aperture_dia': self.params_widgets['aperture_dia'].value(),
            'system_efficiency': self.params_widgets['system_efficiency'].value(),
            'max_range': self.params_widgets['max_range'].value(),
            'sensitivity': self.params_widgets['sensitivity'].value(),
            'rain_rate': self.rain_rate_spin.value(),
            'temperature': self.temperature_spin.value(),  # 温度(K)用于计算复折射率
        }

        return params

    def update_outputs(self, results):
        """更新输出显示"""
        self.output_widgets['eff_range'].setText(f"{results['eff_range']:.2f}")
        self.output_widgets['alpha'].setText(f"{results['alpha'] * 1000:.4f}")
        self.output_widgets['beta'].setText(f"{results['beta'] * 1000:.4f}")
        self.output_widgets['echo_power'].setText(f"{results['echo_power']:.6e}")
