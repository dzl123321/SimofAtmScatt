# core/haze_core.py
import numpy as np
import PyMieScatt as PMS


class HazeLidarSimulationCore:
    """核心仿真逻辑类 - 雾霾环境"""

    def __init__(self, params, worker=None):
        self.worker = worker
        self.visibility = params['visibility'] * 1000  # km -> m
        self.refractive_index = complex(params['ref_real'], params['ref_imag'])
        self.wavelength = params['wavelength']
        self.avg_power = params['avg_power']
        # self.rep_rate = params['rep_rate'] * 1000  # kHz -> Hz
        self.pulse_width = params['pulse_width'] * 1e-9  # ns -> s
        # self.aperture_dia = params['aperture_dia']
        self.system_efficiency = params['system_efficiency']
        self.max_range = params['max_range'] * 1000  # km -> m
        self.sensitivity_threshold = 10 ** ((params['sensitivity'] - 30) / 10)

    def _report_progress(self, progress, message):
        """报告进度"""
        if self.worker and hasattr(self.worker, 'progress'):
            self.worker.progress.emit(progress, message)

    def generate_aerosol_distribution(self):
        """生成Junge气溶胶粒子分布"""
        # Junge分布参数
        v = 3.0  # Junge指数，典型值3-4
        r_min, r_max, n_bins = 0.01, 10.0, 100  # 半径范围 (μm)
        radii_um = np.linspace(r_min, r_max, n_bins)
        r_step = radii_um[1] - radii_um[0]

        # Junge分布: dn/dr ∝ r^(-v)
        # 使用能见度估算粒子浓度
        beta_ext_target = 3.912 / self.visibility  # 1/m

        # Junge分布的归一化形式
        n_r = radii_um ** (-v)

        # 转换为nm用于PyMieScatt计算
        diameters_nm = radii_um * 2000  # μm -> nm

        return radii_um, diameters_nm, n_r, r_step, beta_ext_target  # 返回radii_um用于绘图

    def calculate_scattering_properties(self):
        radii_um, diameters_nm, n_r_dist, r_step, beta_ext_target = self.generate_aerosol_distribution()
        q_exts, q_backs = [], []

        for d in diameters_nm:
            try:
                q_ext, q_sca, q_abs, g, q_pr, q_back, q_ratio = PMS.AutoMieQ(
                    m=self.refractive_index, wavelength=self.wavelength, diameter=d
                )
                q_exts.append(q_ext)
                q_backs.append(q_back)
            except:
                q_exts.append(0.0)
                q_backs.append(0.0)

        q_exts = np.array(q_exts)
        q_backs = np.array(q_backs)
        area_m2 = np.pi * ((diameters_nm * 1e-9) / 2) ** 2

        # 归一化粒子数密度分布
        n_r_normalized = n_r_dist / np.sum(n_r_dist * r_step)

        # 计算单位浓度下的消光系数
        alpha_per_particle = np.sum(q_exts * area_m2 * n_r_normalized * r_step)

        # 根据能见度调整粒子总浓度
        N_total = beta_ext_target / alpha_per_particle if alpha_per_particle > 0 else 1e6

        # 实际粒子数密度
        n_i = n_r_normalized * N_total * r_step

        # 计算消光系数和后向散射系数
        alpha_ext = np.sum(q_exts * area_m2 * n_i)
        beta_back = np.sum((q_backs * area_m2 / (4 * np.pi)) * n_i)

        # 返回粒子谱分布数据
        return alpha_ext, beta_back, radii_um, n_i

    def calculate_lidar_signal(self, alpha_ext, beta_back):
        r = np.linspace(10, self.max_range, 1000)
        c = 3e8
        pulse_factor = c * self.pulse_width / 2
        transmittance_two_way = np.exp(-2 * alpha_ext * r)
        p_received = (self.avg_power * pulse_factor * self.wavelength ** 2 * self.system_efficiency *
                      transmittance_two_way * (4 * np.pi * beta_back) ** 3)/(256 * np.log(2) * r ** 2)
        return r, p_received, transmittance_two_way

    def calculate_angular_scattering(self):
        """计算角度散射函数"""
        rep_radii_um = [0.1, 0.5, 2.0]  # 代表性粒子半径
        v = 3.0  # Junge指数
        total_su = None
        final_theta = None

        for r_um in rep_radii_um:
            d_nm = r_um * 2000  # μm -> nm
            weight = r_um ** (-v)
            try:
                measure = PMS.ScatteringFunction(self.refractive_index,
                                                 self.wavelength, d_nm,
                                                 angularResolution=1.0)
                theta_rad, sl, sr, su = measure
                if total_su is None:
                    total_su = su * weight
                    final_theta = theta_rad
                else:
                    if len(su) == len(total_su):
                        total_su += su * weight
            except:
                continue

        if total_su is None:
            return np.linspace(0, 180, 181), np.ones(181)

        theta_deg = np.rad2deg(final_theta)
        if np.max(total_su) > 0:
            total_su /= np.max(total_su)
        return theta_deg, total_su

    def run_simulation(self):
        self._report_progress(20, "生成气溶胶分布...")
        alpha, beta, radii_um, size_dist = self.calculate_scattering_properties()  # 获取新增数据

        self._report_progress(50, "计算雷达信号...")
        r, p_received, trans = self.calculate_lidar_signal(alpha, beta)

        valid_indices = np.where(p_received > self.sensitivity_threshold)[0]
        eff_range = r[valid_indices[-1]] if len(valid_indices) > 0 else 0.0
        echo_power = p_received[-1]

        self._report_progress(80, "计算角度散射...")
        theta, phase_func = self.calculate_angular_scattering()

        self._report_progress(100, "完成仿真计算...")

        return {
            'alpha': alpha,
            'beta': beta,
            'r': r,
            'p_received': p_received,
            'trans': trans,
            'eff_range': eff_range,
            'echo_power': echo_power,
            'theta': theta,
            'phase_func': phase_func,
            # 新增粒子谱分布数据
            'radii': radii_um,  # 粒子半径 (μm)
            'size_distribution': size_dist  # 粒子数密度分布
        }
