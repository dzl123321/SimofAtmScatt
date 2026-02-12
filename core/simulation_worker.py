# core/simulation_worker.py
from PyQt5.QtCore import QThread, pyqtSignal
from core.simulation_core import RainLidarSimulationCore

class SimulationWorker(QThread):
    """后台计算线程，防止界面卡死"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)  # 进度信号 (进度百分比, 状态信息)

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            # 预先计算 Watts 阈值方便绘图使用
            self.params['sensitivity_watts'] = 10 ** ((self.params['sensitivity'] - 30) / 10)
            sim = RainLidarSimulationCore(self.params, self)
            results = sim.run_simulation()
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
