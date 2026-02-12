import json
import os
import numpy as np
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)


class HistoryManager(QObject):
    def __init__(self):
        super().__init__()
        # 使用绝对路径确保文件路径在不同环境中一致
        self.history_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'simulation_history.json'))
        self.history = []
        self.load_history()

    def add_record(self, params, results, env_type):
        record = {
            'id': len(self.history) + 1,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'env_type': env_type,
            'params': params,
            'results': results
        }
        self.history.append(record)
        self.save_history()
        return record['id']

    def get_record(self, record_id):
        for record in self.history:
            if record['id'] == record_id:
                return record
        return None

    def get_all_records(self):
        return self.history

    def get_records_by_type(self, env_type):
        return [r for r in self.history if r['env_type'] == env_type]

    def delete_record(self, record_id):
        self.history = [r for r in self.history if r['id'] != record_id]
        self.save_history()

    def clear_all(self):
        self.history = []
        self.save_history()

    def save_history(self):
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self.history = []

    def get_summary(self, record):
        params = record['params']
        results = record['results']
        
        if record['env_type'] == 'rain':
            summary = f"降雨率: {params.get('rain_rate', 0):.1f} mm/h"
        else:
            summary = f"能见度: {params.get('visibility', 0):.2f} km"
        
        summary += f" | 有效距离: {results.get('eff_range', 0):.2f} m"
        return summary
