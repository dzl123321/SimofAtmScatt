# gui/menu_bar.py
import os
from datetime import datetime
import numpy as np
import json
import urllib.request
import urllib.error
from PyQt5.QtCore import QThread, pyqtSignal

from PyQt5.QtWidgets import (QMenuBar, QMenu, QAction, QActionGroup, QDialog,
                             QVBoxLayout, QLabel, QCheckBox, QPushButton, QHBoxLayout,
                             QButtonGroup, QFileDialog, QMessageBox, QApplication, QProgressDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

import matplotlib.pyplot as plt
import matplotlib
from PyQt5.QtCore import QTimer


class MenuBarManager:
    """菜单栏管理器"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.menubar = None
        self.simulation_results = None
        self.windows = []  # 存储所有打开的窗口
        self.windows.append(main_window)  # 添加当前窗口到列表
        self.update_thread = None  # 更新检查线程

    def create_menu_bar(self):
        """创建完整的菜单栏"""
        self.menubar = QMenuBar(self.main_window)

        # 文件菜单
        self.create_file_menu()

        # 编辑菜单
        self.create_edit_menu()

        # 运行菜单
        self.create_run_menu()

        # 绘图菜单
        self.create_plot_menu()

        # 接口菜单
        self.create_interface_menu()

        # 帮助菜单
        self.create_help_menu()

        return self.menubar

    def create_file_menu(self):
        """创建文件菜单"""
        file_menu = self.menubar.addMenu('文件')

        # 新建项目子菜单
        new_menu = QMenu('新建项目', self.main_window)

        # 降雨环境项目
        new_rain_action = QAction('降雨环境项目', self.main_window)
        new_rain_action.triggered.connect(lambda: self.new_project('rain'))
        new_menu.addAction(new_rain_action)

        # 雾霾环境项目
        new_haze_action = QAction('雾霾环境项目', self.main_window)
        new_haze_action.triggered.connect(lambda: self.new_project('haze'))
        new_menu.addAction(new_haze_action)

        file_menu.addMenu(new_menu)

        # 打开
        open_action = QAction('打开项目', self.main_window)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        # 保存
        save_action = QAction('保存项目', self.main_window)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        # 另存为
        save_as_action = QAction('另存为...', self.main_window)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_as_project)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # 导出子菜单
        export_menu = QMenu('导出', self.main_window)

        export_fig_action = QAction('导出图表', self.main_window)
        export_fig_action.triggered.connect(self.export_figures)
        export_menu.addAction(export_fig_action)

        export_data_action = QAction('导出数据', self.main_window)
        export_data_action.triggered.connect(self.export_data)
        export_menu.addAction(export_data_action)

        file_menu.addMenu(export_menu)
        file_menu.addSeparator()

        # 退出
        exit_action = QAction('退出', self.main_window)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)

    def create_edit_menu(self):
        """创建编辑菜单"""
        edit_menu = self.menubar.addMenu('编辑')

        # 参数操作子菜单
        params_menu = QMenu('参数操作', self.main_window)

        reset_params_action = QAction('重置参数', self.main_window)
        reset_params_action.triggered.connect(self.reset_parameters)
        params_menu.addAction(reset_params_action)

        save_preset_action = QAction('保存预设', self.main_window)
        save_preset_action.triggered.connect(self.save_preset)
        params_menu.addAction(save_preset_action)

        load_preset_action = QAction('加载预设', self.main_window)
        load_preset_action.triggered.connect(self.load_preset)
        params_menu.addAction(load_preset_action)

        edit_menu.addMenu(params_menu)
        edit_menu.addSeparator()

        # 复制
        copy_action = QAction('复制参数', self.main_window)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.copy_parameters)
        edit_menu.addAction(copy_action)

        # 粘贴
        paste_action = QAction('粘贴参数', self.main_window)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.paste_parameters)
        edit_menu.addAction(paste_action)

    def create_run_menu(self):
        """创建运行菜单"""
        run_menu = self.menubar.addMenu('运行')

        # 开始仿真
        run_sim_action = QAction('开始仿真', self.main_window)
        run_sim_action.setShortcut('F5')
        run_sim_action.triggered.connect(self.run_simulation)
        run_menu.addAction(run_sim_action)

        # 停止仿真
        stop_sim_action = QAction('停止仿真', self.main_window)
        stop_sim_action.setShortcut('Esc')
        stop_sim_action.triggered.connect(self.stop_simulation)
        run_menu.addAction(stop_sim_action)

        run_menu.addSeparator()

        # 仿真设置
        sim_settings_action = QAction('仿真设置', self.main_window)
        sim_settings_action.triggered.connect(self.simulation_settings)
        run_menu.addAction(sim_settings_action)

        # 批处理仿真
        batch_sim_action = QAction('批处理仿真', self.main_window)
        batch_sim_action.triggered.connect(self.batch_simulation)
        run_menu.addAction(batch_sim_action)

    def create_plot_menu(self):
        """创建绘图菜单"""
        plot_menu = self.menubar.addMenu('绘图')

        # 图表样式子菜单
        style_menu = QMenu('图表样式', self.main_window)

        style_default_action = QAction('默认样式', self.main_window)
        style_default_action.triggered.connect(lambda: self.set_plot_style('default'))
        style_menu.addAction(style_default_action)

        style_grayscale_action = QAction('灰度样式', self.main_window)
        style_grayscale_action.triggered.connect(lambda: self.set_plot_style('grayscale'))
        style_menu.addAction(style_grayscale_action)

        style_colorful_action = QAction('彩色样式', self.main_window)
        style_colorful_action.triggered.connect(lambda: self.set_plot_style('colorful'))
        style_menu.addAction(style_colorful_action)

        plot_menu.addMenu(style_menu)

        # 网格控制子菜单
        grid_menu = QMenu('网格控制', self.main_window)

        # 创建互斥的QActionGroup
        grid_action_group = QActionGroup(self.main_window)
        grid_action_group.setExclusive(True)

        grid_on_action = QAction('显示网格', self.main_window)
        grid_on_action.setCheckable(True)
        grid_on_action.setChecked(True)
        grid_on_action.triggered.connect(lambda: self.toggle_grid(True))
        grid_menu.addAction(grid_on_action)
        grid_action_group.addAction(grid_on_action)

        grid_off_action = QAction('隐藏网格', self.main_window)
        grid_off_action.setCheckable(True)
        grid_off_action.triggered.connect(lambda: self.toggle_grid(False))
        grid_menu.addAction(grid_off_action)
        grid_action_group.addAction(grid_off_action)

        plot_menu.addMenu(grid_menu)

        # 保存图表
        save_plot_action = QAction('保存当前图表', self.main_window)
        save_plot_action.triggered.connect(self.save_current_plot)
        plot_menu.addAction(save_plot_action)

        # 刷新图表
        refresh_plot_action = QAction('刷新图表', self.main_window)
        refresh_plot_action.triggered.connect(self.refresh_plots)
        plot_menu.addAction(refresh_plot_action)

    def create_interface_menu(self):
        """创建接口菜单"""
        interface_menu = self.menubar.addMenu('接口')

        # 数据接口
        data_interface_action = QAction('数据接口设置', self.main_window)
        data_interface_action.triggered.connect(self.data_interface_settings)
        interface_menu.addAction(data_interface_action)

        # 硬件接口
        hardware_interface_action = QAction('硬件接口', self.main_window)
        hardware_interface_action.triggered.connect(self.hardware_interface)
        interface_menu.addAction(hardware_interface_action)

        # 外部调用
        external_api_action = QAction('外部API', self.main_window)
        external_api_action.triggered.connect(self.external_api)
        interface_menu.addAction(external_api_action)

    def create_help_menu(self):
        """创建帮助菜单"""
        help_menu = self.menubar.addMenu('帮助')

        # 使用说明
        user_manual_action = QAction('使用说明', self.main_window)
        user_manual_action.triggered.connect(self.show_user_manual)
        help_menu.addAction(user_manual_action)

        # 关于软件
        about_action = QAction('关于软件', self.main_window)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        help_menu.addSeparator()

        # 检查更新
        update_action = QAction('检查更新', self.main_window)
        update_action.triggered.connect(self.check_update)
        help_menu.addAction(update_action)

    # ============ 菜单功能实现 ============

    def set_simulation_results(self, results):
        """设置仿真结果"""
        self.simulation_results = results

    def new_project(self, env_type='rain'):
        """新建指定类型的项目"""
        # 使用定时器延迟创建新窗口
        QTimer.singleShot(0, lambda: self._create_new_window_safely(env_type))

    def remove_window(self, window):
        """从窗口列表中移除关闭的窗口"""
        if window in self.windows:
            self.windows.remove(window)

    def _create_new_window_safely(self, env_type):
        """安全创建新窗口"""
        try:
            # 导入窗口类
            if env_type == 'rain':
                from gui.rain_window import RainSimulationWindow
                NewWindowClass = RainSimulationWindow
            else:
                from gui.haze_window import HazeSimulationWindow
                NewWindowClass = HazeSimulationWindow

            # 创建新窗口
            new_window = NewWindowClass()
            
            # 添加新窗口到窗口列表，确保引用不会被垃圾回收
            self.windows.append(new_window)
            
            # 显示新窗口
            new_window.show()

            # 重要：不再隐藏当前窗口，保持所有窗口可见
            # 让用户自由切换窗口，而不是强制隐藏

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            import traceback
            QMessageBox.critical(self.main_window, "错误",
                                 f"创建新窗口失败:\n{str(e)}\n\n{traceback.format_exc()}")

    def open_project(self):
        """打开项目"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "打开项目文件",
            os.path.expanduser("~"),
            "仿真文件 (*.sim);;所有文件 (*.*)"
        )

        if file_path:
            try:
                # 这里可以添加实际的项目文件加载逻辑
                QMessageBox.information(self.main_window, "打开项目", f"已打开项目文件: {file_path}")
                # TODO: 实际加载项目文件的实现
            except Exception as e:
                QMessageBox.critical(self.main_window, "错误", f"打开文件失败: {str(e)}")

    def save_project(self):
        """保存项目"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "保存项目",
            os.path.join(os.path.expanduser("~"), "simulation_project.sim"),
            "仿真文件 (*.sim);;所有文件 (*.*)"
        )

        if file_path:
            try:
                # 这里可以添加实际的项目文件保存逻辑
                QMessageBox.information(self.main_window, "保存项目", f"项目已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self.main_window, "错误", f"保存文件失败: {str(e)}")

    def save_as_project(self):
        """另存为项目"""
        self.save_project()

    def export_figures(self):
        """导出图表"""
        if not self.main_window.simulation_results:
            QMessageBox.warning(self.main_window, "警告", "请先运行仿真后再导出图表")
            return

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("导出图表设置")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout(dialog)

        # 选择图表
        layout.addWidget(QLabel("选择要导出的图表:"))

        # 更新图表列表：去掉方位角散射，新增粒子谱分布
        charts = [
            ("粒子谱分布", "particle_distribution"),
            ("后向散射回波强度", "backscatter"),
            ("双程路径透过率", "transmittance"),
            ("仰角-散射强度 (对数)", "angular_scatter")
            # 移除了方位角散射
        ]

        chart_checkboxes = {}
        chart_group = QVBoxLayout()
        for chart_name, chart_id in charts:
            checkbox = QCheckBox(chart_name)
            checkbox.setChecked(True)
            chart_checkboxes[chart_id] = checkbox
            chart_group.addWidget(checkbox)

        layout.addLayout(chart_group)

        # 格式选择
        layout.addWidget(QLabel("选择图片格式:"))

        format_layout = QHBoxLayout()

        formats = [("PNG", "png"), ("JPEG", "jpg"),
                   ("PDF", "pdf"), ("SVG", "svg")]

        format_buttons = {}
        for format_name, format_ext in formats:
            checkbox = QCheckBox(format_name)
            checkbox.setChecked(format_ext == "png")
            format_buttons[format_ext] = checkbox
            format_layout.addWidget(checkbox)

        layout.addLayout(format_layout)

        # 保存路径
        layout.addWidget(QLabel("保存路径:"))

        path_layout = QHBoxLayout()
        path_label = QLabel("未选择")
        path_layout.addWidget(path_label)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(lambda: self.select_save_directory(dialog, path_label))
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        # 按钮
        button_layout = QHBoxLayout()
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(lambda: self.execute_figure_export(
            dialog, chart_checkboxes, format_buttons, path_label.text()))
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(export_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        dialog.exec_()

    def select_save_directory(self, dialog, path_label):
        """选择保存目录"""
        directory = QFileDialog.getExistingDirectory(
            self.main_window,
            "选择保存目录",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        if directory:
            path_label.setText(directory)

    def execute_figure_export(self, dialog, chart_checkboxes, format_buttons, save_dir):
        """执行图表导出"""
        if save_dir == "未选择" or not save_dir:
            QMessageBox.warning(dialog, "警告", "请选择保存目录")
            return

        # 获取选择的格式
        selected_format = None
        for format_ext, button in format_buttons.items():
            if button.isChecked():
                selected_format = format_ext
                break

        if not selected_format:
            selected_format = "png"

        # 获取选择的图表
        selected_charts = []
        chart_mapping = {
            "backscatter": "后向散射回波强度",
            "transmittance": "双程路径透过率",
            "angular_scatter": "仰角-散射强度 (对数)",
            "azimuth_scatter": "方位角-散射强度"
        }

        for chart_id, checkbox in chart_checkboxes.items():
            if checkbox.isChecked():
                selected_charts.append(chart_id)

        if not selected_charts:
            QMessageBox.warning(dialog, "警告", "请至少选择一个图表")
            return

        # 导出图表
        success_count = 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for chart_id in selected_charts:
            chart_name = chart_mapping[chart_id]
            if hasattr(self.main_window, 'right_panel') and chart_name in self.main_window.right_panel.figures:
                filename = f"chart_{chart_id}_{timestamp}.{selected_format}"
                filepath = os.path.join(save_dir, filename)

                try:
                    self.main_window.right_panel.figures[chart_name].savefig(
                        filepath,
                        dpi=300,
                        bbox_inches='tight',
                        facecolor='white'
                    )
                    success_count += 1
                except Exception as e:
                    print(f"保存图表 {chart_name} 失败: {e}")

        dialog.accept()

        if success_count > 0:
            QMessageBox.information(
                self.main_window,
                "导出成功",
                f"成功导出 {success_count} 个图表到:\n{save_dir}"
            )
        else:
            QMessageBox.warning(self.main_window, "导出失败", "图表导出失败")

    def export_data(self):
        """导出数据"""
        if not self.main_window.simulation_results:
            QMessageBox.warning(self.main_window, "警告", "请先运行仿真后再导出数据")
            return

        # 根据环境类型设置不同的标题
        env_type = getattr(self.main_window, 'env_type', 'rain')
        env_name = "降雨" if env_type == 'rain' else "雾霾"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"lidar_simulation_{env_type}_{timestamp}.txt"

        filepath, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "保存数据文件",
            os.path.join(os.path.expanduser("~"), default_filename),
            "Text Files (*.txt);;All Files (*.*)"
        )

        if not filepath:
            return

        if not filepath.lower().endswith('.txt'):
            filepath += '.txt'

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 写入文件头部信息
                f.write("=" * 60 + "\n")
                f.write(f"{env_name}环境下激光散射-传输建模与仿真数据\n")  # 更新标题
                f.write("=" * 60 + "\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")

                # 1. 写入输入参数
                f.write("一、输入参数\n")
                f.write("-" * 40 + "\n")

                # 获取参数
                params = self.main_window.left_panel.get_parameters()

                # 根据环境类型写入不同的环境参数
                if env_type == 'rain':
                    f.write("[降雨环境]\n")
                    f.write(f"  降雨率: {params['rain_rate']} mm/h\n")
                    f.write(f"  温度: {params['temperature']} K\n")
                    f.write(f"  雨滴谱: Marshall-Palmer\n\n")
                else:
                    f.write("[雾霾环境]\n")
                    f.write(f"  能见度: {params['visibility']} km\n")
                    f.write(f"  折射率: {params['ref_real']} + j{params['ref_imag']}\n")
                    f.write(f"  气溶胶谱: Junge分布\n\n")

                # 系统参数
                f.write("[系统参数]\n")
                params_mapping = {
                    'avg_power': '发射功率',
                    'frequency': '工作频率',
                    'rep_rate': '重复频率',
                    'pulse_width': '脉宽',
                    'aperture_dia': '接收口径',
                    'system_efficiency': '系统效率',
                    'max_range': '探测距离',
                    'sensitivity': '灵敏度'
                }

                for key, display_name in params_mapping.items():
                    value = params.get(key, 'N/A')
                    unit = ""
                    if key == 'avg_power':
                        unit = " W"
                    elif key == 'frequency':
                        unit = " GHz"
                    elif key == 'rep_rate':
                        unit = " kHz"
                    elif key == 'pulse_width':
                        unit = " ns"
                    elif key == 'aperture_dia':
                        unit = " mm"
                    elif key == 'max_range':
                        unit = " km"
                    elif key == 'sensitivity':
                        unit = " dBm"

                    f.write(f"  {display_name}: {value}{unit}\n")

                f.write("\n" + "=" * 60 + "\n\n")

                # 2. 写入输出结果
                f.write("二、仿真结果\n")
                f.write("-" * 40 + "\n")

                output_widgets = self.main_window.left_panel.output_widgets
                f.write(f"有效探测距离: {output_widgets['eff_range'].text()} m\n")
                f.write(f"消光系数: {output_widgets['alpha'].text()} 1/km\n")
                f.write(f"后向散射系数: {output_widgets['beta'].text()} 1/(km\n")
                f.write(f"回波功率: {output_widgets['echo_power'].text()} W\n\n")

                # 3. 写入详细数据
                results = self.main_window.simulation_results
                if results:
                    f.write("三、详细数据\n")
                    f.write("-" * 40 + "\n")

                    f.write("[回波强度数据 - 关键点]\n")
                    r_data = results['r']
                    p_data = results['p_received']

                    f.write("距离(m)     功率(W)\n")
                    f.write("-" * 25 + "\n")

                    # 前5个点
                    for i in range(min(5, len(r_data))):
                        f.write(f"{r_data[i]:<10.2f} {p_data[i]:<10.2e}\n")

                    f.write("...\n")

                    # 最后5个点
                    for i in range(max(0, len(r_data) - 5), len(r_data)):
                        f.write(f"{r_data[i]:<10.2f} {p_data[i]:<10.2e}\n")

                    f.write("\n")

                    # 写入透过率数据
                    f.write("[透过率数据 - 关键点]\n")
                    trans_data = results['trans']
                    f.write("距离(m)     透过率\n")
                    f.write("-" * 25 + "\n")

                    # 均匀采样10个点
                    indices = np.linspace(0, len(r_data) - 1, 10, dtype=int)
                    for idx in indices:
                        f.write(f"{r_data[idx]:<10.2f} {trans_data[idx]:<10.4f}\n")

                f.write("\n" + "=" * 60 + "\n")
                f.write("数据导出完成\n")
                f.write("=" * 60 + "\n")

            QMessageBox.information(
                self.main_window,
                "导出成功",
                f"数据已成功保存到:\n{filepath}"
            )

        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "导出失败",
                f"保存文件时发生错误:\n{str(e)}"
            )

    def reset_parameters(self):
        """重置参数"""
        if hasattr(self.main_window, 'left_panel'):
            # 检查环境类型
            env_type = getattr(self.main_window, 'env_type', 'rain')

            if env_type == 'rain' and hasattr(self.main_window.left_panel, 'rain_rate_spin'):
                # 重置降雨环境参数
                self.main_window.left_panel.rain_rate_spin.setValue(15.0)
                self.main_window.left_panel.temperature_spin.setValue(277.0)  # 4°C
            elif env_type == 'haze' and hasattr(self.main_window.left_panel, 'visibility_spin'):
                # 重置雾霾环境参数
                self.main_window.left_panel.visibility_spin.setValue(1.0)
                self.main_window.left_panel.haze_ref_real_spin.setValue(1.45)
                self.main_window.left_panel.haze_ref_imag_spin.setValue(0.008)

            # 重置系统参数（公共参数）
            defaults = {
                'avg_power': 0.1,
                'frequency': 193548.0 if hasattr(self.main_window.left_panel, 'visibility_spin') else 60.0,
                'rep_rate': 10,
                'pulse_width': 300,
                'aperture_dia': 300,
                'system_efficiency': 0.85,
                'max_range': 1,
                'sensitivity': -90.0
            }

            for key, value in defaults.items():
                if key in self.main_window.left_panel.params_widgets:
                    self.main_window.left_panel.params_widgets[key].setValue(value)

    def save_preset(self):
        """保存预设"""
        if not hasattr(self.main_window, 'left_panel'):
            QMessageBox.warning(self.main_window, "警告", "无法访问参数面板")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "保存预设",
            os.path.join(os.path.expanduser("~"), "simulation_preset.prs"),
            "预设文件 (*.prs);;所有文件 (*.*)"
        )

        if file_path:
            try:
                params = self.main_window.left_panel.get_parameters()
                env_type = getattr(self.main_window, 'env_type', 'rain')
                
                preset_data = {
                    'env_type': env_type,
                    'params': params,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(preset_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self.main_window, "保存预设", f"预设已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self.main_window, "错误", f"保存预设失败: {str(e)}")

    def load_preset(self):
        """加载预设"""
        if not hasattr(self.main_window, 'left_panel'):
            QMessageBox.warning(self.main_window, "警告", "无法访问参数面板")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "加载预设",
            os.path.expanduser("~"),
            "预设文件 (*.prs);;所有文件 (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    preset_data = json.load(f)
                
                env_type = getattr(self.main_window, 'env_type', 'rain')
                
                if preset_data.get('env_type') != env_type:
                    reply = QMessageBox.question(
                        self.main_window,
                        "环境类型不匹配",
                        f"预设的环境类型是 '{preset_data.get('env_type')}'，\n"
                        f"但当前窗口的环境类型是 '{env_type}'。\n\n"
                        "是否仍然加载？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                
                params = preset_data.get('params', {})
                self._apply_parameters(params)
                
                QMessageBox.information(
                    self.main_window,
                    "加载预设",
                    f"已加载预设:\n{file_path}\n\n"
                    f"环境类型: {preset_data.get('env_type')}\n"
                    f"保存时间: {preset_data.get('timestamp')}"
                )
            except Exception as e:
                QMessageBox.critical(self.main_window, "错误", f"加载预设失败: {str(e)}")
    
    def _apply_parameters(self, params):
        """应用参数到界面"""
        left_panel = self.main_window.left_panel
        
        # 应用环境参数
        if hasattr(left_panel, 'rain_rate_spin') and 'rain_rate' in params:
            left_panel.rain_rate_spin.setValue(params['rain_rate'])
        
        if hasattr(left_panel, 'temperature_spin') and 'temperature' in params:
            left_panel.temperature_spin.setValue(params['temperature'])
        
        if hasattr(left_panel, 'visibility_spin') and 'visibility' in params:
            left_panel.visibility_spin.setValue(params['visibility'])
        
        if hasattr(left_panel, 'haze_ref_real_spin') and 'ref_real' in params:
            left_panel.haze_ref_real_spin.setValue(params['ref_real'])
        
        if hasattr(left_panel, 'haze_ref_imag_spin') and 'ref_imag' in params:
            left_panel.haze_ref_imag_spin.setValue(params['ref_imag'])
        
        # 应用系统参数
        for key, widget in left_panel.params_widgets.items():
            if key in params:
                widget.setValue(params[key])

    def copy_parameters(self):
        """复制参数"""
        if not hasattr(self.main_window, 'left_panel'):
            QMessageBox.warning(self.main_window, "警告", "无法访问参数面板")
            return
        
        try:
            params = self.main_window.left_panel.get_parameters()
            env_type = getattr(self.main_window, 'env_type', 'rain')
            
            clipboard_data = {
                'env_type': env_type,
                'params': params
            }
            
            clipboard_text = json.dumps(clipboard_data, indent=2, ensure_ascii=False)
            
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text)
            
            QMessageBox.information(
                self.main_window,
                "复制参数",
                f"参数已复制到剪贴板\n\n"
                f"环境类型: {env_type}\n"
                f"参数数量: {len(params)}"
            )
        except Exception as e:
            QMessageBox.critical(self.main_window, "错误", f"复制参数失败: {str(e)}")

    def paste_parameters(self):
        """粘贴参数"""
        if not hasattr(self.main_window, 'left_panel'):
            QMessageBox.warning(self.main_window, "警告", "无法访问参数面板")
            return
        
        try:
            clipboard = QApplication.clipboard()
            clipboard_text = clipboard.text()
            
            if not clipboard_text:
                QMessageBox.warning(self.main_window, "警告", "剪贴板为空")
                return
            
            clipboard_data = json.loads(clipboard_text)
            
            if 'params' not in clipboard_data:
                QMessageBox.warning(self.main_window, "警告", "剪贴板中的数据格式不正确")
                return
            
            env_type = getattr(self.main_window, 'env_type', 'rain')
            source_env_type = clipboard_data.get('env_type', 'unknown')
            
            if source_env_type != env_type:
                reply = QMessageBox.question(
                    self.main_window,
                    "环境类型不匹配",
                    f"剪贴板中的环境类型是 '{source_env_type}'，\n"
                    f"但当前窗口的环境类型是 '{env_type}'。\n\n"
                    "是否仍然粘贴？",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            params = clipboard_data.get('params', {})
            self._apply_parameters(params)
            
            QMessageBox.information(
                self.main_window,
                "粘贴参数",
                f"已从剪贴板粘贴参数\n\n"
                f"源环境类型: {source_env_type}\n"
                f"参数数量: {len(params)}"
            )
        except json.JSONDecodeError:
            QMessageBox.warning(self.main_window, "警告", "剪贴板中的数据不是有效的JSON格式")
        except Exception as e:
            QMessageBox.critical(self.main_window, "错误", f"粘贴参数失败: {str(e)}")

    def run_simulation(self):
        """运行仿真"""
        if hasattr(self.main_window, 'on_run_clicked'):
            self.main_window.on_run_clicked()

    def stop_simulation(self):
        """停止仿真"""
        if hasattr(self.main_window, 'worker') and self.main_window.worker.isRunning():
            self.main_window.worker.terminate()
            if hasattr(self.main_window, 'left_panel'):
                self.main_window.left_panel.run_btn.setEnabled(True)
                self.main_window.left_panel.run_btn.setText("开始仿真")
            QMessageBox.information(self.main_window, "停止仿真", "仿真已停止")

    def simulation_settings(self):
        """仿真设置"""
        QMessageBox.information(self.main_window, "仿真设置", "仿真参数设置对话框")
        # TODO: 实际仿真设置对话框的实现

    def batch_simulation(self):
        """批处理仿真"""
        from gui.batch_dialog import BatchSimulationDialog
        
        dialog = BatchSimulationDialog(self.main_window)
        dialog.exec_()

    def set_plot_style(self, style):
        """设置图表样式"""
        if style == 'default':
            plt.style.use('default')
        elif style == 'grayscale':
            plt.style.use('grayscale')
        elif style == 'colorful':
            plt.style.use('seaborn-v0_8')

        # 确保中文字体设置生效
        matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial', 'sans-serif']
        matplotlib.rcParams['axes.unicode_minus'] = False

        # 刷新图表
        self.refresh_plots()
        QMessageBox.information(self.main_window, "图表样式", f"已设置为{style}样式")

    def toggle_grid(self, show):
        """切换网格显示"""
        if hasattr(self.main_window, 'right_panel'):
            for ax in self.main_window.right_panel.axes.values():
                ax.grid(show)

            for canvas in self.main_window.right_panel.canvases.values():
                canvas.draw_idle()

    def save_current_plot(self):
        """保存当前图表"""
        if not hasattr(self.main_window, 'right_panel'):
            QMessageBox.warning(self.main_window, "警告", "无法访问图表面板")
            return
        
        if not hasattr(self.main_window.right_panel, 'figures') or not self.main_window.right_panel.figures:
            QMessageBox.warning(self.main_window, "警告", "没有可保存的图表")
            return
        
        # 创建图表选择对话框
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("保存图表")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("选择要保存的图表:"))
        
        # 创建图表选择列表
        chart_checkboxes = {}
        chart_group = QVBoxLayout()
        for title in self.main_window.right_panel.figures.keys():
            checkbox = QCheckBox(title)
            checkbox.setChecked(True)
            chart_checkboxes[title] = checkbox
            chart_group.addWidget(checkbox)
        
        layout.addLayout(chart_group)
        
        # 格式选择
        layout.addWidget(QLabel("选择图片格式:"))
        
        format_layout = QHBoxLayout()
        formats = [("PNG", "png"), ("JPEG", "jpg"),
                   ("PDF", "pdf"), ("SVG", "svg")]
        
        format_radios = {}
        format_group = QButtonGroup(dialog)
        for i, (format_name, format_ext) in enumerate(formats):
            from PyQt5.QtWidgets import QRadioButton
            radio = QRadioButton(format_name)
            radio.setChecked(format_ext == "png")
            format_radios[format_ext] = radio
            format_group.addButton(radio)
            format_layout.addWidget(radio)
        
        layout.addLayout(format_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("保存")
        save_btn.setFixedWidth(80)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedWidth(80)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 获取选择的格式
        def get_selected_format():
            for format_ext, radio in format_radios.items():
                if radio.isChecked():
                    return format_ext
            return "png"
        
        # 保存按钮点击事件
        def on_save_clicked():
            selected_charts = []
            for title, checkbox in chart_checkboxes.items():
                if checkbox.isChecked():
                    selected_charts.append(title)
            
            if not selected_charts:
                QMessageBox.warning(dialog, "警告", "请至少选择一个图表")
                return
            
            selected_format = get_selected_format()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if len(selected_charts) == 1:
                # 单个图表直接保存
                file_path, _ = QFileDialog.getSaveFileName(
                    self.main_window,
                    "保存图表",
                    os.path.join(os.path.expanduser("~"), f"{selected_charts[0]}_{timestamp}.{selected_format}"),
                    f"{selected_format.upper()}文件 (*.{selected_format});;所有文件 (*.*)"
                )
                
                if file_path:
                    try:
                        self.main_window.right_panel.figures[selected_charts[0]].savefig(
                            file_path, dpi=300, bbox_inches='tight', facecolor='white'
                        )
                        QMessageBox.information(
                            self.main_window,
                            "保存成功",
                            f"图表已保存到:\n{file_path}"
                        )
                        dialog.accept()
                    except Exception as e:
                        QMessageBox.critical(self.main_window, "保存失败", f"保存图表失败: {str(e)}")
            else:
                # 多个图表选择目录
                directory = QFileDialog.getExistingDirectory(
                    self.main_window,
                    "选择保存目录",
                    os.path.expanduser("~")
                )
                
                if directory:
                    success_count = 0
                    for title in selected_charts:
                        try:
                            file_path = os.path.join(directory, f"{title}_{timestamp}.{selected_format}")
                            self.main_window.right_panel.figures[title].savefig(
                                file_path, dpi=300, bbox_inches='tight', facecolor='white'
                            )
                            success_count += 1
                        except Exception as e:
                            print(f"保存图表 {title} 失败: {e}")
                    
                    QMessageBox.information(
                        self.main_window,
                        "保存完成",
                        f"成功保存 {success_count}/{len(selected_charts)} 个图表到:\n{directory}"
                    )
                    dialog.accept()
        
        save_btn.clicked.connect(on_save_clicked)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()

    def refresh_plots(self):
        """刷新图表"""
        matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial', 'sans-serif']
        matplotlib.rcParams['axes.unicode_minus'] = False

        if hasattr(self.main_window, 'right_panel'):
            for canvas in self.main_window.right_panel.canvases.values():
                canvas.draw()

    def data_interface_settings(self):
        """数据接口设置"""
        QMessageBox.information(self.main_window, "数据接口", "数据接口设置")
        # TODO: 实际数据接口设置的实现

    def hardware_interface(self):
        """硬件接口"""
        QMessageBox.information(self.main_window, "硬件接口", "硬件接口设置")
        # TODO: 实际硬件接口设置的实现

    def external_api(self):
        """外部API"""
        QMessageBox.information(self.main_window, "外部API", "外部API接口")
        # TODO: 实际外部API设置的实现

    def show_user_manual(self):
        """显示使用说明"""
        QMessageBox.information(self.main_window, "使用说明",
                                "复杂气象条件下大气散射特性建模仿真软件\n\n"
                                "使用步骤:\n"
                                "1. 设置降雨环境参数\n"
                                "2. 设置激光雷达系统参数\n"
                                "3. 点击'开始仿真'按钮\n"
                                "4. 查看仿真结果和图表\n"
                                "5. 使用导出功能保存数据\n\n"
                                "功能说明:\n"
                                "- 左侧面板: 参数设置和结果输出\n"
                                "- 右侧面板: 仿真结果可视化\n"
                                "- 菜单栏: 文件操作、参数管理、图表控制等")

    def show_about(self):
        """显示关于软件"""
        QMessageBox.about(self.main_window, "关于软件",
                          "复杂气象条件下大气散射特性建模仿真软件\n\n"
                          "版本: 2.0 (模块化重构版)\n"
                          "作者: 西安电子科技大学\n"
                          "开发时间: 2024年\n"
                          "功能说明:\n"
                          "- 降雨环境下激光散射特性仿真\n"
                          "- 激光雷达系统性能分析\n"
                          "- 多维度结果可视化\n"
                          "- 数据导出和报告生成\n\n"
                          "版权: Copyright © 2024 西安电子科技大学")

    def check_update(self):
        """检查更新"""
        reply = QMessageBox.question(
            self.main_window,
            "检查更新",
            "是否检查软件更新？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._start_update_check()

    def _start_update_check(self):
        """开始检查更新"""
        from utils import __version__
        
        progress = QProgressDialog("正在检查更新...", "取消", 0, 0, self.main_window)
        progress.setWindowTitle("检查更新")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        update_thread = UpdateCheckThread(__version__)
        self.update_thread = update_thread
        
        update_thread.finished.connect(lambda result: self._handle_update_result(result, progress))
        update_thread.error.connect(lambda error: self._handle_update_error(error, progress))
        update_thread.start()
        
        progress.canceled.connect(self._cancel_update_check)

    def _cancel_update_check(self):
        """取消更新检查"""
        if self.update_thread and self.update_thread.isRunning():
            self.update_thread.terminate()
            self.update_thread.wait()
        self.update_thread = None

    def _handle_update_result(self, result, progress):
        """处理更新检查结果"""
        progress.close()
        self.update_thread = None
        
        if result['status'] == 'latest':
            QMessageBox.information(
                self.main_window,
                "检查更新",
                f"当前已是最新版本\n\n当前版本: {result['current_version']}"
            )
        elif result['status'] == 'update_available':
            reply = QMessageBox.question(
                self.main_window,
                "发现新版本",
                f"发现新版本可用！\n\n"
                f"当前版本: {result['current_version']}\n"
                f"最新版本: {result['remote_version']}\n\n"
                f"更新说明:\n{result['release_notes']}\n\n"
                f"是否查看更新说明？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self._show_update_instructions(result['remote_version'])
        elif result['status'] == 'network_error':
            QMessageBox.warning(
                self.main_window,
                "网络错误",
                f"无法连接到更新服务器\n\n错误信息: {result['error']}\n\n"
                "请检查网络连接或稍后重试。"
            )

    def _handle_update_error(self, error, progress):
        """处理更新检查错误"""
        progress.close()
        self.update_thread = None
        QMessageBox.warning(
            self.main_window,
            "检查更新失败",
            f"检查更新时发生错误:\n\n{error}"
        )

    def _show_update_instructions(self, new_version):
        """显示更新说明"""
        instructions = (
            f"如何更新到版本 {new_version}:\n\n"
            "方法一: 手动下载更新\n"
            "1. 访问项目发布页面下载最新版本\n"
            "2. 解压下载的文件覆盖当前安装目录\n"
            "3. 重新启动程序\n\n"
            "方法二: Git 更新 (如果是 Git 克隆的版本)\n"
            "1. 打开终端，进入项目目录\n"
            "2. 运行: git pull origin main\n"
            "3. 运行: pip install -r requirement.txt --upgrade\n"
            "4. 重新启动程序\n\n"
            "注意: 更新前请备份您的数据和配置文件！"
        )
        QMessageBox.information(
            self.main_window,
            "更新说明",
            instructions
        )


class UpdateCheckThread(QThread):
    """更新检查线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        try:
            result = self._check_update()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def _check_update(self):
        """检查更新"""
        UPDATE_URL = "https://raw.githubusercontent.com/dzl123321/SimofAtmScatt/main/VERSION"
        
        try:
            with urllib.request.urlopen(UPDATE_URL, timeout=10) as response:
                remote_version_info = json.loads(response.read().decode('utf-8'))
                remote_version = remote_version_info.get('version', self.current_version)
                release_notes = remote_version_info.get('release_notes', '暂无更新说明')
                
                from utils import compare_versions
                comparison = compare_versions(self.current_version, remote_version)
                
                if comparison < 0:
                    return {
                        'status': 'update_available',
                        'current_version': self.current_version,
                        'remote_version': remote_version,
                        'release_notes': release_notes
                    }
                else:
                    return {
                        'status': 'latest',
                        'current_version': self.current_version
                    }
                    
        except urllib.error.URLError as e:
            return {
                'status': 'network_error',
                'error': str(e)
            }
        except Exception as e:
            return {
                'status': 'network_error',
                'error': str(e)
            }
    
    def cleanup(self):
        """清理线程资源"""
        if self.isRunning():
            self.terminate()
            self.wait()
        self.deleteLater()
