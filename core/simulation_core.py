# core/simulation_core.py
import numpy as np
import PyMieScatt as PMS


class RainLidarSimulationCore:
    """核心仿真逻辑类"""

    def __init__(self, params, worker=None):
        self.worker = worker
        self.rain_rate = params['rain_rate']
        self.temperature = params['temperature']  # 温度 (K)
        self.frequency = params['frequency']  # 频率 (GHz)
        self.wavelength = params['wavelength']
        self.avg_power = params['avg_power']
        # self.rep_rate = params['rep_rate'] * 1000  # kHz -> Hz
        self.pulse_width = params['pulse_width'] * 1e-9  # ns -> s
        # self.aperture_dia = params['aperture_dia']
        self.system_efficiency = params['system_efficiency']
        self.max_range = params['max_range'] * 1000  # km -> m
        self.sensitivity_threshold = 10 ** ((params['sensitivity'] - 30) / 10)
        # 根据温度和频率计算复折射率
        self.refractive_index = self.calculate_refractive_index()
        # 根据温度和频率计算复折射率
        self.refractive_index = self.calculate_refractive_index()

    def _report_progress(self, progress, message):
        """报告进度"""
        if self.worker and hasattr(self.worker, 'progress'):
            self.worker.progress.emit(progress, message)

    def calculate_refractive_index(self):
        """根据温度和频率计算雨滴的复折射率
        
        参数:
            temperature: 温度 (K)
            frequency: 频率 (GHz)
            
        返回:
            复折射率 m
        """
        T = self.temperature
        f = self.frequency
        
        # 计算θ
        theta = 1 - 300 / T
        
        # 计算各个参数
        f1 = 20.2 + 146.4 * theta + 316 * theta**2
        f2 = 39.8 * f1
        epsilon_0 = 77.66 - 103.3 * theta
        epsilon_1 = 0.0671 * epsilon_0
        epsilon_2 = 3.52 + 7.52 * theta
        
        # 计算介电常数ε（复数）
        # ε = ε2 + (ε1-ε2)/(1-i(f/f2)) + (ε0-ε1)/(1-i(f/f1))
        term1 = epsilon_2
        term2 = (epsilon_1 - epsilon_2) / (1 - 1j * (f / f2))
        term3 = (epsilon_0 - epsilon_1) / (1 - 1j * (f / f1))
        epsilon = term1 + term2 + term3
        
        # 计算复折射率 m = sqrt(ε)
        m = np.sqrt(epsilon)
        
        return m

    def generate_raindrop_distribution(self):
        N0 = 8000.0
        Lambda = 4.1 * (self.rain_rate ** -0.21)
        d_min, d_max, n_bins = 0.1, 5.0, 200
        diameters_mm = np.linspace(d_min, d_max, n_bins)  # 直径 (mm)
        d_step = diameters_mm[1] - diameters_mm[0]
        nd = N0 * np.exp(-Lambda * diameters_mm)
        diameters_nm = diameters_mm * 1e6  # 转换为nm
        radii_um = diameters_mm * 500  # 转换为半径 (μm)
        return radii_um, diameters_nm, nd, d_step

    def calculate_scattering_properties(self):
        radii_um, diameters_nm, nd_dist, d_step = self.generate_raindrop_distribution()
        q_exts, q_backs = [], []

        for d in diameters_nm:
            q_ext, q_sca, q_abs, g, q_pr, q_back, q_ratio = PMS.AutoMieQ(
                m=self.refractive_index, wavelength=self.wavelength, diameter=d
            )
            q_exts.append(q_ext)
            q_backs.append(q_back)

        q_exts = np.array(q_exts)
        q_backs = np.array(q_backs)
        area_m2 = np.pi * ((diameters_nm * 1e-9) / 2) ** 2
        n_i = nd_dist * d_step

        alpha_ext = np.sum(q_exts * area_m2 * n_i)
        beta_back = np.sum(q_backs * area_m2* n_i)

        return alpha_ext, beta_back, radii_um, n_i

    def calculate_lidar_signal(self, alpha_ext, beta_back):
        r = np.linspace(10, self.max_range, 1000)
        c = 3e8
        pulse_factor = c * self.pulse_width / 2
        transmittance_two_way = np.exp(-2 * alpha_ext * r * 1e-3)  # alpha_ext单位1/m，转换为1/km
        p_received = 1e-21 * (self.avg_power * pulse_factor * self.wavelength ** 2 * self.system_efficiency * c * beta_back *
                      transmittance_two_way) / (32 * np.pi ** 2 * r ** 2)
        return r, p_received, transmittance_two_way

    def calculate_angular_scattering(self):
        rep_diams_mm = [0.5, 1.0, 2.0]
        d_intervals = [0.5, 1.0, 1.0]  # 每个代表性粒径对应的粒径间隔
        Lambda = 4.1 * (self.rain_rate ** -0.21)
        total_su = None
        final_theta = None

        for d_mm, d_step in zip(rep_diams_mm, d_intervals):
            d_nm = d_mm * 1e6
            weight = 8000.0 * np.exp(-Lambda * d_mm) * d_step  # 加上粒径间隔
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
        self._report_progress(10, "计算复折射率...")
        # 已在初始化时计算复折射率

        self._report_progress(30, "计算散射特性...")
        alpha, beta, radii_um, size_dist = self.calculate_scattering_properties()

        self._report_progress(60, "计算雷达信号...")
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
