# gui/right_panel.py
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter
import numpy as np

from PyQt5.QtWidgets import QWidget, QGridLayout, QFrame, QVBoxLayout, QSizePolicy, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor


class RightPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.figures = {}
        self.canvases = {}
        self.axes = {}
        self.toolbars = {}
        self.tooltips = {}
        self.initUI()

    def initUI(self):
        layout = QGridLayout(self)
        layout.setSpacing(10)

        titles = [
            ('粒子谱分布', 0, 0),
            ('后向散射回波强度', 0, 1),
            ('双程路径透过率', 1, 0),
            ('仰角-散射强度 (对数)', 1, 1)
        ]

        for title, row, col in titles:
            fig = Figure(figsize=(5, 4), dpi=100)
            canvas = FigureCanvas(fig)
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            ax = fig.add_subplot(111)

            ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
            ax.grid(True, linestyle='--', alpha=0.7)

            # 添加导航工具栏
            toolbar = NavigationToolbar(canvas, self)
            toolbar.setStyleSheet("""
                QToolBar {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                }
                QToolButton {
                    padding: 3px;
                    margin: 1px;
                }
            """)

            frame = QFrame()
            frame.setFrameStyle(QFrame.Box | QFrame.Plain)
            frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 2px solid #bdc3c7;
                    border-radius: 5px;
                }
            """)
            f_layout = QVBoxLayout(frame)
            f_layout.setContentsMargins(5, 5, 5, 5)
            f_layout.addWidget(toolbar)
            f_layout.addWidget(canvas)

            layout.addWidget(frame, row, col)

            self.figures[title] = fig
            self.canvases[title] = canvas
            self.axes[title] = ax
            self.toolbars[title] = toolbar

            # 启用交互功能
            canvas.mpl_connect('motion_notify_event', lambda event, t=title: self.on_motion(event, t))

        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 1)

    def update_plots(self, results, sensitivity_watts):
        ax1 = self.axes['粒子谱分布']
        ax1.clear()
        if 'size_distribution' in results and 'radii' in results:
            radii = results['radii']
            size_dist = results['size_distribution']
            # 保存数据以便在on_motion中使用
            self.radii_data = radii
            self.size_dist_data = size_dist
            ax1.semilogy(radii, size_dist, 'b-', linewidth=1.5, marker='o', markersize=1)
            ax1.set_title('粒子谱分布', fontsize=11, fontweight='bold', pad=10)
            ax1.set_xlabel('粒子半径 (μm)', fontsize=9)
            ax1.set_ylabel('相对数量密度', fontsize=9)
            ax1.tick_params(labelsize=8)
        else:
            ax1.text(0.5, 0.5, '粒子谱数据\n未提供',
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax1.transAxes, fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        self.canvases['粒子谱分布'].draw()

        ax2 = self.axes['后向散射回波强度']
        ax2.clear()
        distance = results['r']
        power = results['p_received']
        # 保存数据以便在on_motion中使用
        self.distance_data = distance
        self.power_data = power
        ax2.semilogy(distance, power, 'b-', linewidth=1.5, marker='s', markersize=1)
        ax2.axhline(y=sensitivity_watts, color='r', linestyle='--', linewidth=1.5, label='噪声阈值')
        ax2.set_title('后向散射回波强度', fontsize=11, fontweight='bold', pad=10)
        ax2.set_xlabel('距离 (m)', fontsize=9)
        ax2.set_ylabel('功率 (W)', fontsize=9)
        ax2.tick_params(labelsize=8)
        ax2.legend(fontsize=8, loc='upper right')
        ax2.grid(True, linestyle='--', alpha=0.7)
        self.canvases['后向散射回波强度'].draw()

        ax3 = self.axes['双程路径透过率']
        ax3.clear()
        trans = results['trans']
        # 保存数据以便在on_motion中使用
        self.trans_data = trans
        ax3.plot(distance, trans, 'g-', linewidth=1.5, marker='^', markersize=1)
        ax3.set_title('双程路径透过率', fontsize=11, fontweight='bold', pad=10)
        ax3.set_xlabel('距离 (m)', fontsize=9)
        ax3.set_ylabel('透过率', fontsize=9)
        ax3.tick_params(labelsize=8)
        ax3.grid(True, linestyle='--', alpha=0.7)
        self.canvases['双程路径透过率'].draw()

        ax4 = self.axes['仰角-散射强度 (对数)']
        ax4.clear()
        theta = results['theta']
        phase_func = results['phase_func']
        # 保存数据以便在on_motion中使用
        self.theta_data = theta
        self.phase_func_data = phase_func
        ax4.semilogy(theta, phase_func, 'r-', linewidth=1.5, marker='d', markersize=1)
        ax4.set_title('仰角-散射强度', fontsize=11, fontweight='bold', pad=10)
        ax4.set_xlabel('散射角 (度)', fontsize=9)
        ax4.set_ylabel('归一化强度', fontsize=9)
        ax4.tick_params(labelsize=8)
        ax4.grid(True, linestyle='--', alpha=0.7)
        self.canvases['仰角-散射强度 (对数)'].draw()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for title, canvas in self.canvases.items():
            canvas.draw()

    def on_motion(self, event, title):
        """处理鼠标移动事件，显示数据提示"""
        if event.inaxes is None:
            return

        ax = event.inaxes
        x, y = event.xdata, event.ydata

        # 获取当前图表的数据
        if title == '粒子谱分布':
            if hasattr(self, 'radii_data') and hasattr(self, 'size_dist_data'):
                radii = self.radii_data
                size_dist = self.size_dist_data
                # 找到最近的数据点
                if radii.size > 0:
                    idx = np.argmin(np.abs(radii - x))
                    x_val = radii[idx]
                    y_val = size_dist[idx]
                    self.show_tooltip(event, ax, f'半径: {x_val:.3f} μm\n密度: {y_val:.2e}')
        elif title == '后向散射回波强度':
            if hasattr(self, 'distance_data') and hasattr(self, 'power_data'):
                distance = self.distance_data
                power = self.power_data
                if distance.size > 0:
                    idx = np.argmin(np.abs(distance - x))
                    x_val = distance[idx]
                    y_val = power[idx]
                    self.show_tooltip(event, ax, f'距离: {x_val:.0f} m\n功率: {y_val:.2e} W')
        elif title == '双程路径透过率':
            if hasattr(self, 'distance_data') and hasattr(self, 'trans_data'):
                distance = self.distance_data
                trans = self.trans_data
                if distance.size > 0:
                    idx = np.argmin(np.abs(distance - x))
                    x_val = distance[idx]
                    y_val = trans[idx]
                    self.show_tooltip(event, ax, f'距离: {x_val:.0f} m\n透过率: {y_val:.4f}')
        elif title == '仰角-散射强度 (对数)':
            if hasattr(self, 'theta_data') and hasattr(self, 'phase_func_data'):
                theta = self.theta_data
                phase_func = self.phase_func_data
                if theta.size > 0:
                    idx = np.argmin(np.abs(theta - x))
                    x_val = theta[idx]
                    y_val = phase_func[idx]
                    self.show_tooltip(event, ax, f'散射角: {x_val:.1f}°\n强度: {y_val:.2e}')

    def show_tooltip(self, event, ax, text):
        """显示数据提示"""
        # 清除之前的提示
        if hasattr(self, 'tooltip'):
            self.tooltip.remove()

        # 创建新的提示
        self.tooltip = ax.annotate(text, xy=(event.xdata, event.ydata),
                                  xytext=(10, 10), textcoords='offset points',
                                  bbox=dict(boxstyle='round', fc='w', ec='gray', alpha=0.8),
                                  fontsize=9)
        self.canvases[ax.get_title()].draw()

    def compare_plots(self, records):
        colors = ['#3498db', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6', '#1abc9c']
        markers = ['o', 's', '^', 'd', 'v', 'p']

        ax1 = self.axes['粒子谱分布']
        ax1.clear()
        for i, record in enumerate(records):
            if 'size_distribution' in record['results'] and 'radii' in record['results']:
                radii = record['results']['radii']
                size_dist = record['results']['size_distribution']
                color = colors[i % len(colors)]
                marker = markers[i % len(markers)]
                ax1.semilogy(radii, size_dist, color=color, linewidth=1.5, 
                             marker=marker, markersize=1, 
                             label=f"记录#{record['id']}")
        ax1.set_title('粒子谱分布（对比）', fontsize=11, fontweight='bold', pad=10)
        ax1.set_xlabel('粒子半径 (μm)', fontsize=9)
        ax1.set_ylabel('相对数量密度', fontsize=9)
        ax1.tick_params(labelsize=8)
        ax1.legend(fontsize=7, loc='upper right')
        ax1.grid(True, linestyle='--', alpha=0.7)
        self.canvases['粒子谱分布'].draw()

        ax2 = self.axes['后向散射回波强度']
        ax2.clear()
        for i, record in enumerate(records):
            color = colors[i % len(colors)]
            marker = markers[i % len(markers)]
            ax2.semilogy(record['results']['r'], record['results']['p_received'], 
                         color=color, linewidth=1.5, marker=marker, markersize=1,
                         label=f"记录#{record['id']}")
        ax2.set_title('后向散射回波强度（对比）', fontsize=11, fontweight='bold', pad=10)
        ax2.set_xlabel('距离 (m)', fontsize=9)
        ax2.set_ylabel('功率 (W)', fontsize=9)
        ax2.tick_params(labelsize=8)
        ax2.legend(fontsize=7, loc='upper right')
        ax2.grid(True, linestyle='--', alpha=0.7)
        self.canvases['后向散射回波强度'].draw()

        ax3 = self.axes['双程路径透过率']
        ax3.clear()
        for i, record in enumerate(records):
            color = colors[i % len(colors)]
            marker = markers[i % len(markers)]
            ax3.plot(record['results']['r'], record['results']['trans'], 
                     color=color, linewidth=1.5, marker=marker, markersize=1,
                     label=f"记录#{record['id']}")
        ax3.set_title('双程路径透过率（对比）', fontsize=11, fontweight='bold', pad=10)
        ax3.set_xlabel('距离 (m)', fontsize=9)
        ax3.set_ylabel('透过率', fontsize=9)
        ax3.tick_params(labelsize=8)
        ax3.legend(fontsize=7, loc='upper right')
        ax3.grid(True, linestyle='--', alpha=0.7)
        self.canvases['双程路径透过率'].draw()

        ax4 = self.axes['仰角-散射强度 (对数)']
        ax4.clear()
        for i, record in enumerate(records):
            color = colors[i % len(colors)]
            marker = markers[i % len(markers)]
            ax4.semilogy(record['results']['theta'], record['results']['phase_func'], 
                         color=color, linewidth=1.5, marker=marker, markersize=1,
                         label=f"记录#{record['id']}")
        ax4.set_title('仰角-散射强度（对比）', fontsize=11, fontweight='bold', pad=10)
        ax4.set_xlabel('散射角 (度)', fontsize=9)
        ax4.set_ylabel('归一化强度', fontsize=9)
        ax4.tick_params(labelsize=8)
        ax4.legend(fontsize=7, loc='upper right')
        ax4.grid(True, linestyle='--', alpha=0.7)
        self.canvases['仰角-散射强度 (对数)'].draw()
