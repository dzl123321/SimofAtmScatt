# utils/export_utils.py
import os
import numpy as np
from datetime import datetime


def export_data_to_txt(simulation_results, parameters, output_widgets, filepath):
    """导出数据到TXT文件"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # 写入文件头部信息
            f.write("=" * 60 + "\n")
            f.write("降雨环境下激光散射-传输建模与仿真数据\n")
            f.write("=" * 60 + "\n")
            f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            # 1. 写入输入参数
            f.write("一、输入参数\n")
            f.write("-" * 40 + "\n")

            # 降雨环境参数
            f.write("[降雨环境]\n")
            f.write(f"  降雨率: {parameters['rain_rate']} mm/h\n")
            f.write(f"  温度: {parameters['temperature']} K\n")
            f.write(f"  雨滴谱: Marshall-Palmer\n\n")

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
                value = parameters.get(key, 'N/A')
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

            for key, widget in output_widgets.items():
                if key == 'eff_range':
                    f.write(f"有效探测距离: {widget.text()} m\n")
                elif key == 'alpha':
                    f.write(f"消光系数: {widget.text()} 1/km\n")
                elif key == 'beta':
                    f.write(f"后向散射系数: {widget.text()} 1/(km·)\n")

            f.write("\n")

            # 3. 写入详细数据
            if simulation_results:
                f.write("三、详细数据\n")
                f.write("-" * 40 + "\n")

                # 回波强度数据
                f.write("[回波强度数据 - 关键点]\n")
                r_data = simulation_results['r']
                p_data = simulation_results['p_received']

                f.write("距离(m)     功率(W)\n")
                f.write("-" * 25 + "\n")

                # 均匀采样20个点
                indices = np.linspace(0, len(r_data) - 1, 20, dtype=int)
                for idx in indices:
                    f.write(f"{r_data[idx]:<10.2f} {p_data[idx]:<10.2e}\n")

                f.write("\n" + "=" * 60 + "\n")
                f.write("数据导出完成\n")
                f.write("=" * 60 + "\n")

        return True
    except Exception as e:
        raise e
