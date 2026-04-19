import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt  # [필수] 신호처리 라이브러리
from sklearn.metrics import r2_score

class LogVisualizer:
    def __init__(self, log_data):
        self.data = log_data

    def plot_gps_only(self):
        """기본 GPS 주행 궤적 그리기 (Path Only)"""
        
        # 1. 데이터 존재 확인
        if self.data.gpsPos_set is None:
            print("GPS 데이터가 없습니다.")
            return

        # 2. 데이터 추출
        # Row 1: Longitude (경도, X축)
        # Row 2: Latitude (위도, Y축)
        lon = self.data.gpsPos_set[1, :]
        lat = self.data.gpsPos_set[2, :]

        # (옵션) GPS 초기화 전 0,0 튀는 값 제거 (필요시 주석 해제)
        # mask = (lon > 1) & (lat > 1) # 0 근처 값 제외
        # lon = lon[mask]
        # lat = lat[mask]

        # 3. 그래프 그리기
        plt.figure(figsize=(10, 10))

        # 궤적 그리기 (파란색 실선)
        plt.plot(lon, lat, 'b-', linewidth=2, label='Vehicle Path')

        # 시작점(Start)과 끝점(End) 표시
        # 주행 방향을 헷갈리지 않게 도와줍니다.
        if len(lon) > 0:
            plt.plot(lon[0], lat[0], 'go', markersize=12, label='Start')
            plt.plot(lon[-1], lat[-1], 'rx', markersize=12, markeredgewidth=3, label='End')

        # 꾸미기
        plt.title('GPS Tracking Path')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        
        # [중요] 지도 비율 고정 (안 하면 찌그러져 보임)
        plt.axis('equal') 
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.show()

    def plot_torque_performance(self):
        """1. 토크 추종성 및 속도 분석 (Torque Tracking)"""
        if self.data.Tdmd_set is None: return

        # 데이터 추출
        t_cmd   = self.data.Tdmd_set[0, :]
        trq_cmd = self.data.Tdmd_set[1, :]   # Demand Torque
        
        t_act   = self.data.torqueAct_set[0, :]
        trq_act = self.data.torqueAct_set[1, :] # Actual Torque
        
        t_vel   = self.data.vel_set[0, :]
        vel     = self.data.vel_set[1, :]       # Velocity (RPM 등)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        # 상단: 토크 비교
        ax1.plot(t_cmd, trq_cmd, 'r--', label='Target (Tdmd)', linewidth=1.5)
        ax1.plot(t_act, trq_act, 'b-',  label='Actual (Tact)', linewidth=1)
        ax1.set_ylabel('Torque (Nm)')
        ax1.set_title('Torque Response Analysis')
        ax1.legend()
        ax1.grid(True)

        # 하단: 속도
        ax2.plot(t_vel, vel, 'k-')
        ax2.set_ylabel('Motor Speed') # 단위(RPM) 확인 필요
        ax2.set_xlabel('Time (sec)')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()

    def plot_vector_control(self):
        """2. 벡터 제어 상태 분석 (Id, Iq Currents) - 가장 전문적인 분석"""
        if self.data.Idq_set is None: return

        # Idq_set 구조: [Time, Id, Iq] 라고 가정 (3행)
        t_dq = self.data.Idq_set[0, :]
        id_curr = self.data.Idq_set[1, :]
        iq_curr = self.data.Idq_set[2, :]
        
        # DC Link Voltage (Vcap)
        t_vcap = self.data.Vcap_set[0, :]
        vcap   = self.data.Vcap_set[1, :]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        # 상단: d-q축 전류
        ax1.plot(t_dq, iq_curr, 'r', label='Iq (Torque)', alpha=0.8)
        ax1.plot(t_dq, id_curr, 'b', label='Id (Flux)', alpha=0.8)
        ax1.set_ylabel('Current (A)')
        ax1.set_title('FOC Vector Control Analysis (Id, Iq)')
        ax1.legend()
        ax1.grid(True)
        # 팁: 고속에서 Id가 음수로 떨어지면 '약계자 제어' 중인 것임

        # 하단: DC Link 전압
        ax2.plot(t_vcap, vcap, 'g-')
        ax2.set_ylabel('DC Link Voltage (V)')
        ax2.set_xlabel('Time (sec)')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()

    def plot_power_flow(self):
        """3. 전력 흐름 및 배터리 전류 분석"""
        if self.data.Ibatt_set is None: return
        
        t_batt = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        
        # 기계적 출력 파워 계산 (P = Torque * w)
        # 시간축을 맞춰야 하므로 간단히 interpolation하거나, 
        # 샘플링이 같다면 인덱스로 접근 (여기서는 길이 체크 후 계산 추천)
        
        # 예시로 배터리 전류만 도시 (파워 계산은 단위 변환 필요)
        plt.figure(figsize=(10, 5))
        plt.plot(t_batt, i_batt, 'm-')
        plt.title('Battery Current Consumption')
        plt.ylabel('Current (A)')
        plt.xlabel('Time (sec)')
        plt.grid(True)
        plt.show()
    
    def plot_field_weakening(self):
        """약계자 제어(Field Weakening) 정밀 분석"""
        # 데이터가 없으면 리턴
        if self.data.Idq_set is None or self.data.Vmod_set is None:
            print("약계자 분석에 필요한 데이터(Idq, Vmod)가 부족합니다.")
            return

        # 1. 데이터 추출
        t_vel = self.data.vel_set[0, :]
        vel   = self.data.vel_set[1, :]       # RPM
        
        t_dq  = self.data.Idq_set[0, :]
        id_curr = self.data.Idq_set[1, :]     # d-axis Current (Flux)
        iq_curr = self.data.Idq_set[2, :]     # q-axis Current (Torque)

        t_vmod = self.data.Vmod_set[0, :]
        vmod   = self.data.Vmod_set[1, :]     # Modulation Voltage
        
        # (옵션) DC Link 전압이 있다면 MI(변조지수) 계산 가능
        if self.data.Vcap_set is not None:
            # 시간축이 다를 수 있으므로 여기서는 단순 비교용으로 따로 그림
            vcap = self.data.Vcap_set[1, :] # DC Link Voltage
        
        # 2. 그래프 그리기 (3단 구성)
        fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

        # [Graph 1] 속도 (RPM)
        axs[0].plot(t_vel, vel, 'k-', linewidth=2)
        axs[0].set_ylabel('Speed (RPM)')
        axs[0].set_title('1. Motor Speed (High Speed Check)')
        axs[0].grid(True)
        
        # [Graph 2] d-q 전류 (핵심!)
        # Id가 음수로 떨어지는지 봐야 하므로 0점 기준선을 그어줌
        axs[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5) 
        axs[1].plot(t_dq, iq_curr, 'r-', label='Iq (Torque)', alpha=0.7)
        axs[1].plot(t_dq, id_curr, 'b-', label='Id (Flux Weakening)', linewidth=2)
        axs[1].set_ylabel('Current (A)')
        axs[1].set_title('2. Vector Currents (Check Negative Id)')
        axs[1].legend(loc='upper right')
        axs[1].grid(True)

        # [Graph 3] 전압 사용률 (Vmod)
        axs[2].plot(t_vmod, vmod, 'g-', label='Vmod (Output Voltage)')
        
        # 만약 Vcap 데이터가 있다면 전압 한계선(Vdc_link)을 같이 그려줌
        if self.data.Vcap_set is not None:
             # 샘플링 개수가 맞다고 가정하고 그림 (다르면 보간 필요)
            axs[2].plot(self.data.Vcap_set[0, :], self.data.Vcap_set[1, :], 
                        'm--', label='Vdc (Limit)', alpha=0.6)
            
        axs[2].set_ylabel('Voltage (V)')
        axs[2].set_xlabel('Time (sec)')
        axs[2].set_title('3. Voltage Utilization (Saturation Check)')
        axs[2].legend()
        axs[2].grid(True)

        plt.tight_layout()
        plt.show()

    def plot_gps_velocity_and_slip(self):
        """GPS 속도와 슬립율(Slip Ratio) 이중축 그래프"""
        
        # 1. 데이터 확인
        if self.data.gpsVec_set is None or self.data.CAN_set is None:
            print("데이터가 부족하여 슬립율 그래프를 그릴 수 없습니다.")
            return

        # 2. 데이터 추출
        # GPS Speed (Time, Speed)
        t_gps = self.data.gpsVec_set[0, :]
        gps_kph = self.data.gpsVec_set[1, :]

        # Motor RPM (Time, RPM) -> Wheel Speed로 변환 필요
        t_rpm = self.data.CAN_set[0, :]
        rpm = self.data.CAN_set[4, :]

        # --- [슬립율 계산 로직] ---
        # 실제 차량 파라미터가 필요합니다. (임의값 적용)
        # Wheel Speed (kph) = RPM * (2*pi/60) * r_tire * 3.6 / Gear_Ratio
        r_tire = 0.3      # 타이어 반지름 (m) 예시
        gear_ratio = 9.0  # 감속비 예시
        
        # RPM 데이터를 GPS 시간축에 맞춰야 정확한 계산이 가능하지만,
        # 여기서는 샘플링이 비슷하다고 가정하고 계산하거나, 
        # 단순히 RPM 자체를 비교용으로 씁니다. (정석은 interp1로 시간 동기화 필요)
        
        # 간단한 변환 (RPM -> KPH)
        wheel_kph = rpm * (2 * np.pi / 60) * r_tire * (1 / gear_ratio) * 3.6
        
        # 슬립율 계산: (Wheel - Vehicle) / Vehicle * 100
        # 분모가 0일 때 에러 방지를 위해 1e-5 더함
        slip_ratio = (wheel_kph - gps_kph) / (np.abs(gps_kph) + 1.0) * 100
        
        # 노이즈가 심할 수 있으므로 범위 제한 (MATLAB의 ylim 역할)
        slip_ratio = np.clip(slip_ratio, -20, 50) 


        # --- [그래프 그리기] ---
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # [Left Axis] GPS Velocity
        # MATLAB: plot(..., 'LineStyle','none','Marker','.','Color','k')
        color_1 = 'black'
        ax1.set_xlabel('Time (sec)')
        ax1.set_ylabel('GPS Speed (km/h)', color=color_1)
        ax1.plot(t_gps, gps_kph, color=color_1, linestyle='none', marker='.', markersize=3, label='GPS Speed')
        ax1.tick_params(axis='y', labelcolor=color_1)
        ax1.grid(True) # 격자는 왼쪽 축 기준

        # [Right Axis] Slip Ratio (핵심: twinx 사용)
        ax2 = ax1.twinx()  # X축을 공유하는 쌍둥이 축 생성
        
        color_2 = 'blue'
        ax2.set_ylabel('Slip Ratio (%)', color=color_2)
        # MATLAB: plot(..., 'LineStyle','-','Marker','none')
        # RPM 시간축(t_rpm)을 사용
        ax2.plot(t_rpm, slip_ratio, color=color_2, linestyle='-', linewidth=1, alpha=0.6, label='Slip Ratio')
        ax2.tick_params(axis='y', labelcolor=color_2)
        
        # MATLAB: yline(0, 'b') -> 수평선 0
        ax2.axhline(0, color='blue', linestyle='--', linewidth=0.8)

        # MATLAB: xline(...) -> 수직선 (예: 이벤트 발생 지점)
        # if ~isempty(tValSeg_LS) 구현 (예시로 10초, 20초에 선 그리기)
        event_times = [10, 20] # 예시 데이터
        for et in event_times:
            ax1.axvline(x=et, color='red', linestyle='--', linewidth=1.5)

        # 제목 및 마무리
        plt.title('GPS Velocity vs Slip Ratio Analysis')
        fig.tight_layout()  # 레이아웃 자동 정렬
        plt.show()

    def plot_torque_vs_rpm(self):
        """RPM에 따른 토크 분포 (Torque Map Analysis)"""
        
        # 1. 데이터 확인
        if self.data.vel_set is None or self.data.Tdmd_set is None:
            print("데이터가 부족하여 토크 맵을 그릴 수 없습니다.")
            return

        # 2. 데이터 추출
        # 기준이 되는 X축 데이터 (Velocity)
        t_vel = self.data.vel_set[0, :]  # 시간 (Time reference)
        rpm   = self.data.vel_set[1, :]  # RPM (X-axis value)

        # Y축 데이터 1 (Demand Torque)
        t_dmd   = self.data.Tdmd_set[0, :]
        val_dmd = self.data.Tdmd_set[1, :]

        # Y축 데이터 2 (Actual Torque)
        t_act   = self.data.torqueAct_set[0, :]
        val_act = self.data.torqueAct_set[1, :]

        # --- [핵심] 데이터 시간 동기화 (Interpolation) ---
        # MATLAB: interp1(x, y, x_new)
        # Python: np.interp(x_new, x, y)  <-- 순서가 다릅니다! 주의!
        
        # "RPM이 측정된 그 시간(t_vel)에 토크는 몇이었니?"를 계산
        dmd_interp = np.interp(t_vel, t_dmd, val_dmd)
        act_interp = np.interp(t_vel, t_act, val_act)

        # 3. 그래프 그리기
        plt.figure(figsize=(10, 8))
        
        # Demand Torque (파란 점)
        # MATLAB: LineStyle='none', Marker='.'
        plt.plot(rpm, dmd_interp, color='blue', linestyle='None', marker='.', 
                 markersize=3, label='Dmd (Target)')
        
        # Actual Torque (주황 점)
        plt.plot(rpm, act_interp, color='orange', linestyle='None', marker='.', 
                 markersize=3, label='Act (Actual)')

        # 꾸미기
        plt.grid(True)
        plt.legend(loc='best')
        plt.xlabel('Speed (RPM)')   # MATLAB: rpm_{CAN}
        plt.ylabel('Torque (Nm)')
        plt.title('Torque vs Speed Distribution')
        
        plt.show()

    def plot_temperature_profile(self):
        """시간에 따른 모터 온도 변화 그래프"""
        
        # 1. 데이터 확인
        if self.data.motorTemp_set is None:
            print("모터 온도 데이터(motorTemp_set)가 없습니다.")
            return

        # 2. 데이터 추출
        # motorTemp_set: [Time, Temperature]
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        # 3. 그래프 그리기
        plt.figure(figsize=(12, 6))
        
        # 메인 온도 그래프
        plt.plot(t_temp, temp_val, color='tab:red', linewidth=2, label='Motor Temp')
        
        # [분석 팁] ME1616 / Sevcon의 일반적인 제한 온도 표시
        # 보통 120도~130도 부근에서 토크 컷이 시작됩니다.
        plt.axhline(y=120, color='orange', linestyle='--', label='Warning (120°C)')
        plt.axhline(y=140, color='red', linestyle='--', label='Limit (140°C)')

        # 꾸미기
        plt.title('Motor Temperature Profile over Time')
        plt.xlabel('Time (sec)')
        plt.ylabel('Temperature (°C)')
        plt.grid(True)
        plt.legend()
        
        # 현재 최고 온도 표시 (텍스트)
        max_temp = np.max(temp_val)
        plt.text(t_temp[-1], max_temp, f' Max: {max_temp:.1f}°C', 
                 verticalalignment='bottom', color='red', fontweight='bold')

        plt.tight_layout()
        plt.show()

    def plot_torque_vs_temperature(self):
        """안전 로직 확인: 온도에 따른 토크 제한(Derating) 확인"""
        if self.data.motorTemp_set is None or self.data.torqueAct_set is None:
            return

        # 데이터 추출 및 시간 동기화
        t_vel = self.data.vel_set[0, :] # 기준 시간축
        
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]
        
        t_trq = self.data.torqueAct_set[0, :]
        trq_val = self.data.torqueAct_set[1, :]
        
        # 인터폴레이션
        temp_interp = np.interp(t_vel, t_temp, temp_val)
        trq_interp = np.interp(t_vel, t_trq, trq_val)

        plt.figure(figsize=(10, 8))
        
        # 산점도 그리기
        plt.scatter(temp_interp, trq_interp, alpha=0.3, s=3, c='orange')
        
        plt.xlabel('Motor Temperature (°C)')
        plt.ylabel('Actual Torque (Nm)')
        plt.title('Thermal Derating Check (Torque vs Temp)')
        plt.grid(True)
        
        # 가이드라인 (예상되는 제한선)
        plt.axvline(x=110, color='r', linestyle='--', label='Derating Start (Expected)')
        plt.legend()
        
        plt.show()

    def plot_current_vs_torque_efficiency(self):
        """효율 분석: 토크 대비 소모 전류량"""
        if self.data.torqueAct_set is None or self.data.Idq_set is None:
            return

        # 데이터 추출
        t_trq = self.data.torqueAct_set[0, :]
        trq = self.data.torqueAct_set[1, :]
        
        t_iq = self.data.Idq_set[0, :]
        iq = self.data.Idq_set[2, :] # 토크 생성에 쓰인 전류
        
        # 시간 동기화
        iq_interp = np.interp(t_trq, t_iq, iq)

        plt.figure(figsize=(10, 6))
        
        # X축: 실제 토크, Y축: 소모 전류 (Iq)
        plt.scatter(trq, iq_interp, alpha=0.1, s=3, c='purple')
        
        plt.xlabel('Actual Torque (Nm)')
        plt.ylabel('Current Iq (A)')
        plt.title('Current Consumption per Torque (Lower is Better)')
        plt.grid(True)
        
        # 이상적인 선 (Reference)
        # ME1616 Kt ~= 0.23 Nm/A  =>  Current = Torque / 0.23
        x_ref = np.linspace(0, 100, 100)
        plt.plot(x_ref, x_ref / 0.23, 'g--', label='Ideal Efficiency Line')
        plt.legend()
        
        plt.show()

    def plot_current_efficiency(self):
        """배터리 전류 vs 모터 상전류 비교 (인버터 효율 확인)"""
        # 데이터 존재 확인
        if self.data.Idq_set is None or self.data.Ibatt_set is None:
            print("전류 분석에 필요한 데이터(Idq, Ibatt)가 없습니다.")
            return

        # 1. 데이터 추출
        # 배터리 전류 (DC)
        t_batt = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        
        # 모터 전류 (Vector Control -> Phase Current Magnitude)
        t_dq = self.data.Idq_set[0, :]
        id_curr = self.data.Idq_set[1, :]
        iq_curr = self.data.Idq_set[2, :]
        
        # 상전류 크기 계산 (Magnitude = sqrt(Id^2 + Iq^2))
        i_phase_calc = np.sqrt(id_curr**2 + iq_curr**2)
        
        # 시간 동기화 (배터리 전류를 모터 전류 시간축에 맞춤)
        i_batt_interp = np.interp(t_dq, t_batt, i_batt)

        # 2. 그래프 그리기
        plt.figure(figsize=(12, 6))
        
        # 모터로 들어가는 전류 (힘)
        plt.plot(t_dq, i_phase_calc, 'm-', label='Phase Current (Motor Force)', alpha=0.8, linewidth=1.5)
        
        # 배터리에서 나가는 전류 (비용)
        plt.plot(t_dq, i_batt_interp, 'k-', label='Battery Current (Energy Cost)', linewidth=2)
        
        plt.ylabel('Current (A)')
        plt.xlabel('Time (sec)')
        plt.title('Inverter Current Multiplication (Phase vs Battery)')
        plt.legend()
        plt.grid(True)
        
        # 3. 뻥튀기 비율 텍스트 표시 (최대 부하 구간)
        max_idx = np.argmax(i_phase_calc)
        max_phase = i_phase_calc[max_idx]
        max_batt = i_batt_interp[max_idx]
        
        if max_batt > 1: # 0으로 나누기 방지
            ratio = max_phase / max_batt
            plt.text(t_dq[max_idx], max_phase, f' Max Ratio: {ratio:.1f}x', 
                     verticalalignment='bottom', color='purple', fontweight='bold')

        plt.show()

    def plot_advanced_id_iq_analysis(self):
        """
        [고급 분석] Id/Iq 데이터를 통한 기어비, 토크맵, 주행전략 분석
        1. Gear Ratio Check: RPM vs Id (약계자 진입 시점 확인)
        2. Saturation Check: Iq vs Torque (자기 포화 확인)
        3. Operating Point: Id vs Iq Circle (주행 전략 확인)
        """
        # 데이터 존재 확인
        if self.data.Idq_set is None or self.data.vel_set is None or self.data.torqueAct_set is None:
            print("데이터 부족: Idq, Vel, TorqueAct가 모두 필요합니다.")
            return

        # --- 1. 데이터 추출 및 동기화 ---
        # 기준 시간축: 속도(Vel) 데이터 사용
        t_ref = self.data.vel_set[0, :]
        rpm   = self.data.vel_set[1, :]

        # Id, Iq 동기화
        t_idq = self.data.Idq_set[0, :]
        id_raw = self.data.Idq_set[1, :]
        iq_raw = self.data.Idq_set[2, :]
        
        id_sync = np.interp(t_ref, t_idq, id_raw)
        iq_sync = np.interp(t_ref, t_idq, iq_raw)

        # Torque 동기화
        t_trq = self.data.torqueAct_set[0, :]
        trq_raw = self.data.torqueAct_set[1, :]
        trq_sync = np.interp(t_ref, t_trq, trq_raw)

        # 노이즈 제거 (정차 중 데이터 제외)
        mask = (np.abs(rpm) > 100) 
        rpm_m = rpm[mask]
        id_m = id_sync[mask]
        iq_m = iq_sync[mask]
        trq_m = trq_sync[mask]

        # --- 2. 그래프 그리기 (1x3 Layout) ---
        fig, axs = plt.subplots(1, 3, figsize=(18, 6))

        # [Graph 1] 기어비 분석: RPM vs Id (Flux Current)
        # 목적: 약계자(Id < 0)가 너무 낮은 RPM에서 시작되는지 확인
        axs[0].scatter(rpm_m, id_m, c='blue', s=3, alpha=0.3)
        axs[0].axhline(0, color='k', linestyle='--', linewidth=1)
        axs[0].set_xlabel('Motor Speed (RPM)')
        axs[0].set_ylabel('Flux Current Id (A)')
        axs[0].set_title('1. Gear Ratio Check\n(RPM vs Id)')
        axs[0].grid(True)
        # 가이드: Id가 음수로 떨어지는 RPM 지점이 "기저속도(Base Speed)"

        # [Graph 2] 토크맵 효율: Iq vs Torque
        # 목적: 전류를 퍼부어도 토크가 안 느는 "포화 구간" 확인
        axs[1].scatter(iq_m, trq_m, c=np.abs(id_m), cmap='coolwarm', s=3, alpha=0.5)
        axs[1].set_xlabel('Torque Current Iq (A)')
        axs[1].set_ylabel('Actual Torque (Nm)')
        axs[1].set_title('2. Saturation Check\n(Iq vs Torque)')
        axs[1].grid(True)
        # 색상(Color)은 Id 전류량 (빨갈수록 약계자 심함)
        
        # 기준선 (Ideal Kt Line, ME1616 approx 0.23)
        x_ref = np.linspace(0, np.max(iq_m), 100)
        axs[1].plot(x_ref, 0.23 * x_ref, 'g--', label='Linear Ref (Kt=0.23)')
        axs[1].legend()

        # [Graph 3] 주행 전략: Id vs Iq (Current Vector Trajectory)
        # 목적: 운전자가 전류원을 어떻게 쓰고 있는지 분포 확인
        sc = axs[2].scatter(id_m, iq_m, c=rpm_m, cmap='viridis', s=3, alpha=0.5)
        axs[2].set_xlabel('Flux Current Id (A)')
        axs[2].set_ylabel('Torque Current Iq (A)')
        axs[2].set_title('3. Driving Strategy\n(Current Vector Trajectory)')
        axs[2].grid(True)
        axs[2].axis('equal') # 원형 유지를 위해 비율 고정
        
        # 전류 제한원(Current Limit Circle) 가이드 (예: 400A)
        theta = np.linspace(0, np.pi, 100)
        axs[2].plot(400*np.cos(theta), 400*np.sin(theta), 'r--', label='400A Limit')
        
        cbar = plt.colorbar(sc, ax=axs[2])
        cbar.set_label('Speed (RPM)')

        plt.tight_layout()
        plt.show()

    def plot_vehicle_dynamics(self):
        """[수정됨] 가속도 센서를 활용한 차량 거동 분석 (센서 누워있음)"""
        if self.data.acc_set is None:
            print("가속도 센서 데이터가 없습니다.")
            return

        # 데이터 추출 (Raw Data)
        t_acc = self.data.acc_set[0, :]
        raw_x = self.data.acc_set[1, :] 
        raw_y = self.data.acc_set[2, :] 
        raw_z = self.data.acc_set[3, :] 

        # --- [축 매핑 수정] ---
        # 사용자 설정: Z=앞뒤, X=위아래
        long_g = raw_z  # 전후 (가속/감속) -> Z축
        lat_g  = raw_y  # 좌우 (코너링)    -> Y축 (기존 유지)
        vert_g = raw_x  # 상하 (진동/점프) -> X축

        fig = plt.figure(figsize=(14, 6))

        # [Graph 1] G-G Diagram (Longitudinal vs Lateral)
        # 이제 Z축(전후)과 Y축(좌우)을 그려야 합니다.
        ax1 = fig.add_subplot(1, 2, 1)
        ax1.plot(lat_g, long_g, 'k.', markersize=2, alpha=0.2)
        
        # 가이드라인 (0.5G, 1.0G)
        theta = np.linspace(0, 2*np.pi, 100)
        ax1.plot(0.5*np.cos(theta), 0.5*np.sin(theta), 'r--', label='0.5G')
        ax1.plot(1.0*np.cos(theta), 1.0*np.sin(theta), 'b--', label='1.0G')
        
        ax1.axhline(0, color='gray', linewidth=0.5)
        ax1.axvline(0, color='gray', linewidth=0.5)
        ax1.set_xlabel('Lateral G (Y-axis: Cornering)')
        ax1.set_ylabel('Longitudinal G (Z-axis: Accel/Brake)')
        ax1.set_title('1. G-G Diagram (Z vs Y)')
        ax1.axis('equal') 
        ax1.legend()
        ax1.grid(True)

        # [Graph 2] 시계열 진동 분석 (Z축 & X축)
        ax2 = fig.add_subplot(1, 2, 2)
        
        # 전후(Z) 가속도: 파란색
        ax2.plot(t_acc, long_g, 'b-', label='Longitudinal (Z: Go/Stop)', alpha=0.6, linewidth=1)
        
        # 상하(X) 가속도: 빨간색 (이제 X축이 충격입니다!)
        ax2.plot(t_acc, vert_g, 'r-', label='Vertical (X: Bump/Jump)', alpha=0.4, linewidth=0.5)
        
        ax2.set_xlabel('Time (sec)')
        ax2.set_ylabel('Acceleration (g)')
        ax2.set_title('2. Vibration & Impact Analysis')
        ax2.legend(loc='upper right')
        ax2.grid(True)
        ax2.set_ylim(-2, 2) # 노이즈 제거용 범위 제한

        plt.tight_layout()
        plt.show()

    def plot_vehicle_dynamics_lpf(self):
        """
        [Bug Fix] NaN 데이터 제거 후 필터링 적용
        """
        if self.data.acc_set is None:
            return

        # 1. 데이터 추출
        t_acc = self.data.acc_set[0, :]
        raw_x = self.data.acc_set[1, :] # 수직
        raw_y = self.data.acc_set[2, :] # 좌우
        raw_z = self.data.acc_set[3, :] # 전후

        # --- [핵심 수정] NaN(빈 값) 제거 ---
        # 하나라도 NaN이 있으면 그 행은 쓰지 않습니다.
        mask = ~np.isnan(raw_x) & ~np.isnan(raw_y) & ~np.isnan(raw_z)
        
        t_acc = t_acc[mask]
        raw_x = raw_x[mask]
        raw_y = raw_y[mask]
        raw_z = raw_z[mask]

        if len(t_acc) == 0:
            print("유효한 가속도 데이터가 없습니다.")
            return
        # ----------------------------------

        # 2. 샘플링 주파수 자동 계산
        if len(t_acc) > 1:
            fs = 1.0 / np.mean(np.diff(t_acc))
        else:
            fs = 100.0

        # 3. 자동 영점 보정 (Calibration)
        # 정차 구간(초반 1초) 평균을 0으로 잡음
        N_cal = min(100, len(raw_x))
        
        offset_x = np.mean(raw_x[:N_cal]) 
        offset_y = np.mean(raw_y[:N_cal])
        offset_z = np.mean(raw_z[:N_cal])

        calib_x = raw_x - offset_x
        calib_y = raw_y - offset_y
        calib_z = raw_z - offset_z

        # 4. 필터링 (LPF)
        def apply_lpf(data, cutoff=1.0, order=2): #필터링 강도. 1.0Hz이상 컷오프.
            nyq = 0.5 * fs
            normal_cutoff = cutoff / nyq
            b, a = butter(order, normal_cutoff, btype='low', analog=False)
            return filtfilt(b, a, data)

        filt_x = apply_lpf(calib_x)
        filt_y = apply_lpf(calib_y)
        filt_z = apply_lpf(calib_z)

        # 5. 축 매핑 (Z=전후, Y=좌우)
        final_long = filt_z
        final_lat  = filt_y
        final_vert = filt_x

        # --- 그래프 그리기 ---
        fig = plt.figure(figsize=(14, 7))

        # [Graph 1] G-G Diagram
        ax1 = fig.add_subplot(1, 2, 1)
        # 배경: 보정된 Raw (회색)
        ax1.plot(calib_y, calib_z, 'k.', markersize=1, alpha=0.05, label='Raw Noise')
        # 전경: 필터링 된 데이터 (빨간색) -> 이제 보일 겁니다!
        ax1.scatter(final_lat, final_long, s=5, c='red', alpha=0.2, label='Vehicle Motion')        
        
        # 중심 표시
        ax1.plot(0, 0, 'g+', markersize=15, linewidth=2)

        theta = np.linspace(0, 2*np.pi, 100)
        ax1.plot(0.5*np.cos(theta), 0.5*np.sin(theta), 'b--', label='0.5G')
        
        ax1.set_xlabel('Lateral G')
        ax1.set_ylabel('Longitudinal G')
        ax1.set_title('1. G-G Diagram (Calibrated & Filtered)')
        ax1.axis('equal')
        ax1.legend()
        ax1.grid(True)

        # [Graph 2] Time Series
        ax2 = fig.add_subplot(1, 2, 2)
        ax2.plot(t_acc, final_long, 'b-', linewidth=1.5, label='Longitudinal (Go/Stop)')
        ax2.plot(t_acc, final_vert, 'r-', linewidth=1, alpha=0.6, label='Vertical (Suspension)')
        
        ax2.set_title('2. Motion Analysis (Filtered)')
        ax2.set_xlabel('Time (sec)')
        ax2.set_ylabel('Acceleration (g)')
        ax2.legend()
        ax2.grid(True)
        ax2.set_ylim(-1.5, 1.5)

        plt.tight_layout()
        plt.show()
    
    def plot_vehicle_dynamics_mv_avg(self):
        """
        [최종 수정 v3] 3초 이동 평균(Moving Average) 적용
        """
        if self.data.acc_set is None:
            return

        # 1. 데이터 추출 & NaN 제거
        t_acc = self.data.acc_set[0, :]
        raw_x = self.data.acc_set[1, :] 
        raw_y = self.data.acc_set[2, :] 
        raw_z = self.data.acc_set[3, :] 

        mask = ~np.isnan(raw_x) & ~np.isnan(raw_y) & ~np.isnan(raw_z)
        t_acc = t_acc[mask]
        raw_x = raw_x[mask]
        raw_y = raw_y[mask]
        raw_z = raw_z[mask]

        if len(t_acc) == 0:
            print("유효한 가속도 데이터가 없습니다.")
            return

        # 2. 샘플링 주파수(fs) 및 윈도우 사이즈 계산
        # fs: 1초에 데이터가 몇 개 찍히는가?
        if len(t_acc) > 1:
            fs = 1.0 / np.mean(np.diff(t_acc))
        else:
            fs = 100.0 # 기본값

        # [핵심] 3초 동안의 데이터 개수 계산
        target_sec = 3.0
        window_size = int(fs * target_sec)
        
        # 윈도우가 너무 작으면 최소 1로 설정
        if window_size < 1: window_size = 1
        
        print(f"INFO: 3초 이동평균 적용 (Window Size: {window_size} samples)")

        # 3. 자동 영점 보정 (Calibration)
        # 정차 구간(초반 1초) 평균을 0으로 잡음
        N_cal = min(int(fs), len(raw_x)) # 1초 분량
        
        calib_x = raw_x - np.mean(raw_x[:N_cal])
        calib_y = raw_y - np.mean(raw_y[:N_cal])
        calib_z = raw_z - np.mean(raw_z[:N_cal])

        # 4. 이동 평균 필터 함수 (Moving Average)
        def apply_moving_average(data, w):
            # np.convolve를 사용하여 'same' 모드로 길이를 유지합니다.
            return np.convolve(data, np.ones(w)/w, mode='same')

        # 필터 적용 (3초 평균)
        avg_x = apply_moving_average(calib_x, window_size)
        avg_y = apply_moving_average(calib_y, window_size)
        avg_z = apply_moving_average(calib_z, window_size)

        # 5. 축 매핑 (Z=전후, Y=좌우, X=상하)
        final_long = avg_z
        final_lat  = avg_y
        final_vert = avg_x

        # --- 그래프 그리기 ---
        fig = plt.figure(figsize=(14, 7))

        # [Graph 1] G-G Diagram
        ax1 = fig.add_subplot(1, 2, 1)
        
        # 배경: 원본 노이즈 (아주 흐리게)
        ax1.plot(calib_y, calib_z, 'k.', markersize=1, alpha=0.02, label='Raw Noise')
        
        # 전경: 3초 평균 데이터 (빨간색 실선)
        # 평균을 냈으므로 점보다는 선(Path)으로 보는 게 더 직관적입니다.
        ax1.plot(final_lat, final_long, 'r-', linewidth=2, alpha=0.9, label='3s Moving Avg')
        
        # 시작점 표시
        ax1.plot(final_lat[0], final_long[0], 'go', label='Start')

        # 가이드라인
        ax1.plot(0, 0, 'g+', markersize=15, linewidth=2)
        theta = np.linspace(0, 2*np.pi, 100)
        ax1.plot(0.5*np.cos(theta), 0.5*np.sin(theta), 'b--', label='0.5G')
        ax1.plot(1.0*np.cos(theta), 1.0*np.sin(theta), 'k--', alpha=0.5, label='1.0G')
        
        ax1.set_xlabel('Lateral G')
        ax1.set_ylabel('Longitudinal G')
        ax1.set_title(f'1. G-G Diagram ({target_sec}s Avg)')
        ax1.axis('equal')
        ax1.legend(loc='upper right')
        ax1.grid(True)
        ax1.set_xlim(-1.0, 1.0) # 범위는 데이터에 맞춰 조절하세요
        ax1.set_ylim(-1.0, 1.0)

        # [Graph 2] Time Series
        ax2 = fig.add_subplot(1, 2, 2)
        ax2.plot(t_acc, final_long, 'b-', linewidth=2, label='Longitudinal (Z)')
        ax2.plot(t_acc, final_vert, 'r-', linewidth=2, alpha=0.7, label='Vertical (X)')
        
        ax2.set_title(f'2. Motion Analysis ({target_sec}s Avg)')
        ax2.set_xlabel('Time (sec)')
        ax2.set_ylabel('Acceleration (g)')
        ax2.legend()
        ax2.grid(True)
        ax2.set_ylim(-0.5, 0.5) # 평균을 내면 값이 작아지므로 범위를 좁혀서 봅니다.

        plt.tight_layout()
        plt.show()

    def plot_gps_gforce_map(self):
        """
        [Final v3] GPS G-Force Heatmap (단순 거리 기반 필터링 적용)
        """
        if self.data.gpsPos_set is None or self.data.acc_set is None:
            return

        # 1. 데이터 추출
        t_gps = self.data.gpsPos_set[0, :]
        lon = self.data.gpsPos_set[1, :]
        lat = self.data.gpsPos_set[2, :]

        # --- [수정됨] 노이즈 제거: Median + Fixed Radius ---
        # 통계(IQR) 대신 물리적인 거리로 자릅니다.
        
        # (1) 0,0 제거
        mask_valid = (np.abs(lon) > 1.0) & (np.abs(lat) > 1.0)
        
        if np.sum(mask_valid) > 0:
            # (2) 트랙의 중심(Median) 찾기 - 튀는 값의 영향을 안 받음
            center_lon = np.median(lon[mask_valid])
            center_lat = np.median(lat[mask_valid])
            
            # (3) 반경 설정 (약 0.02도 ~= 2km)
            # 트랙이 아무리 커도 이 안에는 들어옵니다.
            radius = 0.02 
            
            mask_dist = (np.abs(lon - center_lon) < radius) & \
                        (np.abs(lat - center_lat) < radius)
            
            final_mask = mask_valid & mask_dist
        else:
            final_mask = mask_valid

        # 필터 적용
        t_gps = t_gps[final_mask]
        lon = lon[final_mask]
        lat = lat[final_mask]
        
        print(f"GPS Data Points: {len(lon)} (Filtered)") # 디버깅용 출력

        if len(t_gps) == 0:
            print("유효한 GPS 데이터가 없습니다.")
            return
        # ---------------------------------------------------

        # 2. 가속도 데이터 준비 & 필터링
        t_acc = self.data.acc_set[0, :]
        raw_y = self.data.acc_set[2, :] # Lateral
        raw_z = self.data.acc_set[3, :] # Longitudinal
        
        # (중요) 가속도 데이터도 NaN 제거 안 하면 색깔이 안 나옴
        acc_mask = ~np.isnan(raw_y) & ~np.isnan(raw_z)
        t_acc = t_acc[acc_mask]
        raw_y = raw_y[acc_mask]
        raw_z = raw_z[acc_mask]

        # 영점 보정
        if len(raw_y) > 100:
            calib_y = raw_y - np.mean(raw_y[:100])
            calib_z = raw_z - np.mean(raw_z[:100])
        else:
            calib_y, calib_z = raw_y, raw_z

        # LPF (1Hz) - 부드러운 색상 변화
        fs = 100.0
        if len(t_acc) > 1: fs = 1.0 / np.mean(np.diff(t_acc))
            
        def apply_lpf(data, cutoff=1.0):
            nyq = 0.5 * fs
            b, a = butter(2, cutoff/nyq, btype='low')
            return filtfilt(b, a, data)

        filt_lat = apply_lpf(calib_y)
        filt_long = apply_lpf(calib_z)

        # 3. 데이터 동기화
        # GPS 시간축에 맞춰 가속도 값을 가져옴
        lat_g_sync = np.interp(t_gps, t_acc, filt_lat)
        long_g_sync = np.interp(t_gps, t_acc, filt_long)

        # 4. Total G 계산
        total_g = np.sqrt(lat_g_sync**2 + long_g_sync**2)

        # 5. 그래프 그리기
        plt.figure(figsize=(12, 10))
        
        # s=20 (점 크기를 좀 키움), cmap='turbo' (색상 대비 명확하게)
        sc = plt.scatter(lon, lat, c=total_g, cmap='turbo', s=20, alpha=1.0,
                         vmin=0, vmax=0.6) # Baja니까 0.6G면 빨간색(Max)으로 설정

        cbar = plt.colorbar(sc)
        cbar.set_label('Total G-Force (g)')
        
        plt.title('Vehicle G-Force Heatmap (Fixed Radius Filter)')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.axis('equal')
        plt.grid(True)
        
        # 시작/끝 표시
        plt.plot(lon[0], lat[0], 'gx', markersize=12, markeredgewidth=3, label='Start')
        plt.plot(lon[-1], lat[-1], 'rx', markersize=12, markeredgewidth=3, label='End')
        plt.legend()

        plt.tight_layout()
        plt.show()

    def plot_laps_slideshow(self):
        """
        [Interactive] 키보드 좌우 방향키로 랩을 넘겨보는 기능
        """
        # 1. 랩 분할
        laps = self.data.split_laps(start_radius_m=20, min_lap_time_sec=60)
        if not laps:
            print("감지된 랩이 없습니다.")
            return

        # 2. 전체 데이터 준비 (한 번만 계산)
        # (매번 계산하면 넘길 때 버벅거리므로 미리 다 해둡니다)
        t_gps = self.data.gpsPos_set[0, :]
        lon_raw = self.data.gpsPos_set[1, :]
        lat_raw = self.data.gpsPos_set[2, :]

        # NMEA 변환
        def nmea_to_decimal(nmea_val):
            deg = np.floor(nmea_val / 100.0)
            min = nmea_val - (deg * 100.0)
            return deg + (min / 60.0)

        if np.mean(lon_raw) > 180:
            lon_all = nmea_to_decimal(lon_raw)
            lat_all = nmea_to_decimal(lat_raw)
        else:
            lon_all, lat_all = lon_raw, lat_raw

        # 가속도 & Total G 준비
        t_acc = self.data.acc_set[0, :]
        ay = self.data.acc_set[2, :]
        az = self.data.acc_set[3, :]
        
        # NaN 제거
        mask = ~np.isnan(ay) & ~np.isnan(az)
        t_acc, ay, az = t_acc[mask], ay[mask], az[mask]

        # 필터링 (1Hz)
        from scipy.signal import butter, filtfilt
        fs = 100.0
        if len(t_acc) > 1: fs = 1.0 / np.mean(np.diff(t_acc))
        b, a = butter(2, 1.0/(0.5*fs), btype='low')
        ay_filt = filtfilt(b, a, ay - np.mean(ay[:100]))
        az_filt = filtfilt(b, a, az - np.mean(az[:100]))

        # 동기화
        ay_sync = np.interp(t_gps, t_acc, ay_filt)
        az_sync = np.interp(t_gps, t_acc, az_filt)
        total_g_all = np.sqrt(ay_sync**2 + az_sync**2)

        # 3. 인터랙티브 뷰어 설정
        fig, ax = plt.subplots(figsize=(12, 10))
        plt.subplots_adjust(bottom=0.2) # 아래쪽에 설명 문구 공간 확보

        current_lap_idx = [0] # 리스트로 감싸서 내부 함수에서 접근 가능하게 함

        def update_plot():
            ax.clear() # 이전 그림 지우기
            
            idx = current_lap_idx[0]
            lap_info = laps[idx]
            
            s = lap_info['idx_start']
            e = lap_info['idx_end']
            duration = lap_info['time_duration']

            # 데이터 슬라이싱
            lon_lap = lon_all[s:e]
            lat_lap = lat_all[s:e]
            g_lap = total_g_all[s:e]

            # 그리기
            sc = ax.scatter(lon_lap, lat_lap, c=g_lap, cmap='turbo', s=30, 
                            vmin=0, vmax=0.6) # 스케일 고정
            
            # 시작점
            ax.plot(lon_lap[0], lat_lap[0], 'gx', markersize=15, markeredgewidth=3, label='Start')

            # 꾸미기
            ax.set_title(f"Lap {idx + 1} / {len(laps)}  (Time: {duration:.2f}s)", fontsize=20, fontweight='bold')
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.axis('equal')
            ax.grid(True)
            ax.legend(loc='upper right')

            # 컬러바는 처음에 한 번만 그리거나, 없으면 추가
            if len(fig.axes) > 1: 
                # 이미 컬러바가 있으면 업데이트 안 함 (복잡도 줄임)
                pass 
            else:
                cbar = fig.colorbar(sc, ax=ax)
                cbar.set_label('Total G-Force (g)')

            fig.canvas.draw_idle()

        # 4. 키보드 이벤트 핸들러
        def on_key(event):
            if event.key == 'right':
                current_lap_idx[0] = (current_lap_idx[0] + 1) % len(laps)
                update_plot()
            elif event.key == 'left':
                current_lap_idx[0] = (current_lap_idx[0] - 1) % len(laps)
                update_plot()

        # 이벤트 연결
        fig.canvas.mpl_connect('key_press_event', on_key)

        # 초기 실행
        update_plot()
        
        # 안내 문구
        plt.figtext(0.5, 0.05, "Use [Left] / [Right] Arrow Keys to Switch Laps", 
                    ha="center", fontsize=14, color='blue')
        plt.show()

    def plot_power_and_temp(self):  
        """
        [냉각 성능 분석용] 입력 전력(P = V*I)과 모터 온도 비교 그래프
        """
        # 1. 데이터 확인
        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            print("전압, 전류 또는 온도 데이터가 없습니다.")
            return

        # 2. 데이터 추출
        # 전압 (DC Link Voltage)
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        
        # 전류 (Battery Current)
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        
        # 온도 (Motor Temp)
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        # 3. 데이터 동기화 (시간축 통일)
        # 전압 시간축(t_v)을 기준으로 나머지 데이터를 인터폴레이션
        i_batt_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)

        # 4. 전력(Power) 및 발열량(Heat Loss) 계산
        # 입력 전력 (P_in) = V * I  (단위: kW)
        power_kw = (v_cap * i_batt_sync) / 1000.0
        
        # 예상 발열량 (P_loss) 추정
        # 모터 효율을 약 90%로 가정하면, 나머지 10%가 열로 바뀜
        efficiency = 0.90 
        heat_loss_kw = power_kw * (1 - efficiency)

        # 5. 그래프 그리기 (이중축)
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # [Left Axis] 전력 (입력 파워 & 예상 발열량)
        color = 'tab:blue'
        ax1.set_xlabel('Time (sec)')
        ax1.set_ylabel('Input Power (kW)', color=color)
        
        # 입력 전력 (투명하게 배경에 깔기)
        ax1.fill_between(t_v, 0, power_kw, color=color, alpha=0.2, label='Input Power (Elec)')
        
        # 예상 발열량 (실선)
        # ax1.plot(t_v, heat_loss_kw, color='navy', linewidth=1, linestyle='--', label='Est. Heat Loss (10%)')
        
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.set_ylim(0, max(power_kw)*1.2) # 여유 있게

        # [Right Axis] 온도
        ax2 = ax1.twinx()  
        color = 'tab:red'
        ax2.set_ylabel('Motor Temperature (°C)', color=color)
        
        # 온도 그래프 (굵게)
        ax2.plot(t_v, temp_sync, color=color, linewidth=2.5, label='Motor Temp')
        
        # 위험 온도 라인
        ax2.axhline(115, color='orange', linestyle='--', label='Overheat (115°C)')
        
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim(20, 140) # 온도 범위 고정

        # 제목 및 범례
        plt.title('Thermal Load Analysis: Power Input vs Temperature Rise')
        fig.tight_layout()
        plt.show()

    def analyze_moving_rms(self, window_sec=30):
        """
        [고급 전력 분석] 30초 이동 RMS (Moving RMS) 그래프
        - 순간적인 피크가 아니라, '지속적인 열부하'가 가장 심했던 구간을 찾음
        """
        if self.data.Vcap_set is None or self.data.Ibatt_set is None:
            return

        # 1. 데이터 추출 및 청소
        t_v_raw = self.data.Vcap_set[0, :]
        v_cap_raw = self.data.Vcap_set[1, :]
        t_i_raw = self.data.Ibatt_set[0, :]
        i_batt_raw = self.data.Ibatt_set[1, :]

        # NaN 제거
        mask_v = ~np.isnan(t_v_raw) & ~np.isnan(v_cap_raw)
        t_v = t_v_raw[mask_v]
        v_cap = v_cap_raw[mask_v]

        mask_i = ~np.isnan(t_i_raw) & ~np.isnan(i_batt_raw)
        t_i = t_i_raw[mask_i]
        i_batt = i_batt_raw[mask_i]

        if len(t_v) == 0: return

        # 2. 데이터 동기화 & 순간 전력 계산
        i_sync = np.interp(t_v, t_i, i_batt)
        p_inst = (v_cap * i_sync) / 1000.0 # kW

        # 3. 30초 윈도우 크기 계산
        # 샘플링 주파수(fs) 추정
        if len(t_v) > 1:
            fs = 1.0 / np.mean(np.diff(t_v))
        else:
            fs = 10.0 # 기본값
            
        window_size = int(window_sec * fs)
        if window_size < 1: window_size = 1
        
        print(f"INFO: Calculating {window_sec}s Moving RMS (Window: {window_size} samples)")

        # 4. 이동 RMS 계산 함수
        def calculate_moving_rms(data, w):
            # RMS = sqrt( Mean( Square(Data) ) )
            squared = data ** 2
            # 이동 평균 (Convolution 사용)
            moving_avg_sq = np.convolve(squared, np.ones(w)/w, mode='same')
            # 루트
            return np.sqrt(moving_avg_sq)

        # 전력(Power) RMS & 전류(Current) RMS 계산
        p_moving_rms = calculate_moving_rms(p_inst, window_size)
        i_moving_rms = calculate_moving_rms(i_sync, window_size)

        # 5. 최대 부하 지점 찾기 (Worst Case)
        max_idx = np.argmax(p_moving_rms)
        max_p_rms = p_moving_rms[max_idx]
        max_i_rms = i_moving_rms[max_idx]
        peak_time = t_v[max_idx]

        # 6. 그래프 그리기
        fig, ax1 = plt.subplots(figsize=(12, 7))

        # [Left Axis] 전력 (Power)
        color = 'tab:blue'
        ax1.set_xlabel('Time (sec)')
        ax1.set_ylabel('Power (kW)', color=color)
        
        # 배경: 순간 전력 (흐리게)
        ax1.plot(t_v, p_inst, color='skyblue', alpha=0.3, linewidth=1, label='Instantaneous Power')
        
        # 전경: 30초 이동 RMS (진하게) -> 이게 진짜 열부하!
        ax1.plot(t_v, p_moving_rms, color='blue', linewidth=2.5, label=f'{window_sec}s Moving RMS Power')
        
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.legend(loc='upper left')
        ax1.grid(True)

        # [Right Axis] 전류 (Current) - 발열의 핵심
        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('RMS Current (A)', color=color)
        
        # 30초 이동 RMS 전류
        ax2.plot(t_v, i_moving_rms, color=color, linestyle='--', linewidth=2, label=f'{window_sec}s Moving RMS Current')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.legend(loc='upper right')

        # 최대 부하 지점 표시
        ax1.axvline(peak_time, color='green', linestyle=':', linewidth=2)
        plt.title(f'Thermal Load Analysis: {window_sec}s Moving RMS')
        
        # 텍스트 박스 (결과 요약)
        text_str = (f"Worst {window_sec}s Load:\n"
                    f"Power: {max_p_rms:.1f} kW\n"
                    f"Current: {max_i_rms:.1f} A")
        
        # 그래프 상단에 박스 표시
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax1.text(0.02, 0.95, text_str, transform=ax1.transAxes, fontsize=12,
                verticalalignment='top', bbox=props)

        plt.tight_layout()
        plt.show()

    def plot_temp_rise_vs_power(self):
        """
        [냉각 성능 상관관계 분석]
        X축: 온도 상승률 (degC / 10sec)
        Y축: 소비 전력 (kW)
        - 이 그래프의 기울기나 절편을 통해 냉각 시스템의 한계를 파악할 수 있습니다.
        """
        # 1. 데이터 확인
        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            print("전압, 전류 또는 온도 데이터가 없습니다.")
            return

        # 2. 데이터 추출 및 동기화
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        # 시간축 통일 (전압 기준)
        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)

        # NaN 제거
        mask = ~np.isnan(v_cap) & ~np.isnan(i_sync) & ~np.isnan(temp_sync)
        t_v = t_v[mask]
        v_cap = v_cap[mask]
        i_sync = i_sync[mask]
        temp_sync = temp_sync[mask]

        if len(t_v) == 0: return

        # 3. 데이터 가공 (핵심 로직)
        
        # (1) 소비 전력 (kW)
        power_kw = (v_cap * i_sync) / 1000.0
        
        # (2) 10초 간격 온도 상승률 계산 (Delta T / 10s)
        # 샘플링 주파수(fs) 계산
        fs = 1.0 / np.mean(np.diff(t_v))
        window_10s = int(10 * fs) # 10초에 해당하는 데이터 개수
        
        if window_10s < 1: window_10s = 1

        # 온도 변화율 계산 (현재 온도 - 10초 전 온도)
        # np.roll을 사용하여 배열을 시프트한 뒤 뺄셈
        temp_prev = np.roll(temp_sync, window_10s)
        temp_rise_10s = temp_sync - temp_prev
        
        # 앞부분 10초 데이터는 유효하지 않으므로 마스킹 처리
        valid_idx = slice(window_10s, None)
        
        # (3) 해당 10초 동안의 평균 전력 계산 (반응 지연 고려)
        # 온도가 오르는 건 '지난 10초간 쓴 전력' 때문이므로, 전력도 이동평균을 내줍니다.
        power_smooth = np.convolve(power_kw, np.ones(window_10s)/window_10s, mode='full')
        # convolve 결과 크기가 달라지므로 원본 길이에 맞춤 (앞부분 잘라냄)
        power_smooth = power_smooth[:len(power_kw)]

        # 유효 데이터만 추출
        x_data = temp_rise_10s[valid_idx] # 온도 상승률
        y_data = power_smooth[valid_idx]  # 평균 전력

        # 4. 그래프 그리기
        plt.figure(figsize=(10, 8))
        
        # 산점도 (Scatter) - 밀도 표현을 위해 투명도(alpha) 사용
        # 색상(c)을 온도(temp_sync)로 주어, 고온일 때의 거동을 구분
        sc = plt.scatter(x_data, y_data, c=temp_sync[valid_idx], cmap='inferno', 
                         s=10, alpha=0.5)
        
        # 기준선 (X=0, 온도 변화 없음 = 열 평형 상태)
        plt.axvline(0, color='k', linestyle='--', linewidth=1, label='Thermal Equilibrium (dT=0)')
        
        # 꾸미기
        cbar = plt.colorbar(sc)
        cbar.set_label('Current Motor Temp (°C)')
        
        plt.title('Correlation: Power Input vs Temperature Rise (10s window)')
        plt.xlabel('Temperature Rise per 10 sec (°C / 10s)')
        plt.ylabel('Average Input Power (kW)')
        plt.grid(True)
        plt.legend()

        # [분석 팁] 텍스트 표시
        # X > 0 (오른쪽): 온도가 오르고 있음 (발열 > 냉각)
        # X < 0 (왼쪽): 온도가 식고 있음 (발열 < 냉각)
        plt.text(max(x_data)*0.7, max(y_data)*0.9, "Heating Up ->", color='red', fontweight='bold')
        plt.text(min(x_data)*0.7, max(y_data)*0.9, "<- Cooling Down", color='blue', fontweight='bold')

        plt.tight_layout()
        plt.show()

    def plot_temp_slope_trend(self, window_sec=45.0):
        """
        [정밀 냉각 분석] Rolling Linear Regression (선형 회귀 기울기)
        X축: 온도 상승 기울기 (degC/sec) -> 추세선의 Slope
        Y축: 해당 구간 평균 소비 전력 (kW)
        """
        # 1. 데이터 확인
        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            return

        # 2. 데이터 동기화 (전압 시간축 기준)
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)

        # NaN 제거
        mask = ~np.isnan(v_cap) & ~np.isnan(i_sync) & ~np.isnan(temp_sync)
        t_v = t_v[mask]
        v_cap = v_cap[mask]
        i_sync = i_sync[mask]
        temp_sync = temp_sync[mask]
        
        if len(t_v) == 0: return

        # 전력 계산 (kW)
        power_kw = (v_cap * i_sync) / 1000.0

        # 3. 슬라이딩 윈도우 & 선형 회귀 (핵심 로직)
        # 샘플링 주파수
        fs = 1.0 / np.mean(np.diff(t_v))
        window_len = int(window_sec * fs)
        
        if window_len < 2: window_len = 2
        
        slopes = []
        avg_powers = []
        avg_temps = []
        
        # 데이터를 window_len 만큼씩 잘라서 분석 (Step은 데이터 양에 따라 조절)
        # 데이터가 많으면 step을 늘려서 속도를 높임 (예: 0.5초 단위 이동)
        step = int(fs * 0.5) if int(fs * 0.5) > 1 else 1
        
        print(f"INFO: Calculating Slopes ({window_sec}s window)...")

        for i in range(0, len(t_v) - window_len, step):
            # 구간 데이터 추출
            t_chunk = t_v[i : i + window_len]
            temp_chunk = temp_sync[i : i + window_len]
            power_chunk = power_kw[i : i + window_len]
            
            # [핵심] 1차 함수(선형) 피팅 -> 기울기(Slope) 추출
            # deg=1 : y = ax + b 에서 a(기울기)를 구함
            # 결과: slope (degC/sec)
            fit = np.polyfit(t_chunk, temp_chunk, 1)
            slope = fit[0] 
            
            # 데이터 저장
            slopes.append(slope)
            avg_powers.append(np.mean(power_chunk))
            avg_temps.append(np.mean(temp_chunk))

        # 배열 변환
        slopes = np.array(slopes)
        avg_powers = np.array(avg_powers)
        avg_temps = np.array(avg_temps)

        # 4. 그래프 그리기
        plt.figure(figsize=(11, 9))
        
        # 산점도 (X: 기울기, Y: 전력, Color: 온도)
        # 기울기를 보기 좋게 '10초당 변화량'으로 환산해서 보여줌 (* 10)
        x_axis = slopes * 10.0 
        
        sc = plt.scatter(x_axis, avg_powers, c=avg_temps, cmap='magma', 
                         s=15, alpha=0.6)
        
        # 기준선 (온도 변화 없음 = 열 평형)
        plt.axvline(0, color='k', linestyle='--', linewidth=1.5, label='Equilibrium (Slope=0)')
        
        # 추세선 (데이터 전체의 경향성)
        # X(기울기)와 Y(전력) 사이의 관계를 보여주는 선
        if len(x_axis) > 1:
            trend = np.polyfit(x_axis, avg_powers, 1)
            trend_fn = np.poly1d(trend)
            x_range = np.linspace(min(x_axis), max(x_axis), 100)
            plt.plot(x_range, trend_fn(x_range), 'b:', linewidth=2, label='Trend Line')

        # 꾸미기
        cbar = plt.colorbar(sc)
        cbar.set_label('Motor Temperature (°C)')
        
        plt.title(f'Cooling Performance: Power vs Temp Slope ({window_sec}s Regression)')
        plt.xlabel('Temperature Slope (°C / 10sec)')
        plt.ylabel('Average Input Power (kW)')
        plt.grid(True)
        plt.legend()
        
        # [분석 팁] 텍스트
        plt.text(max(x_axis)*0.6, max(avg_powers)*0.1, "Heating (Insufficient Cooling)", color='red')
        plt.text(min(x_axis)*0.6, max(avg_powers)*0.1, "Cooling (Sufficient)", color='blue')

        plt.tight_layout()
        plt.show()

    def plot_thermal_path(self, window_sec=45.0, min_temp=60.0):
        """
        [Update] 특정 온도(예: 60도) 이상인 '주행 구간' 데이터만 분석
        """
        from matplotlib.collections import LineCollection

        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            return

        # 1. 데이터 추출
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        # 2. 동기화
        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)

        # 3. [핵심] 데이터 필터링 (60도 이상 & NaN 제거)
        # 피트인(저온) 구간을 날려버립니다.
        mask = (~np.isnan(v_cap) & ~np.isnan(i_sync) & ~np.isnan(temp_sync)) & \
               (temp_sync >= min_temp)
        
        t_v = t_v[mask]
        v_cap = v_cap[mask]
        i_sync = i_sync[mask]
        temp_sync = temp_sync[mask]
        
        if len(t_v) == 0:
            print(f"조건을 만족하는 데이터가 없습니다. (Min Temp: {min_temp}°C)")
            return

        power_kw = (v_cap * i_sync) / 1000.0

        # 4. 슬라이딩 윈도우 & 선형 회귀
        fs = 1.0 / np.mean(np.diff(t_v))
        window_len = int(window_sec * fs)
        if window_len < 2: window_len = 2
        
        step = max(1, int(fs * 0.5)) 

        slopes = []
        avg_powers = []
        avg_temps = []

        print(f"INFO: Analyzing Active Driving Data (Temp >= {min_temp}°C)...")

        for i in range(0, len(t_v) - window_len, step):
            t_chunk = t_v[i : i + window_len]
            
            # [중요] 데이터가 시간적으로 연속적인지 체크 (피트인 구간 건너뜀 방지)
            # 데이터 간격이 너무 벌어지면(예: 5초 이상) 회귀 계산에서 제외
            if t_chunk[-1] - t_chunk[0] > window_sec * 2: 
                continue

            temp_chunk = temp_sync[i : i + window_len]
            power_chunk = power_kw[i : i + window_len]
            
            fit = np.polyfit(t_chunk, temp_chunk, 1)
            
            slopes.append(fit[0] * 10.0) # 10초당 변화율
            avg_powers.append(np.mean(power_chunk))
            avg_temps.append(np.mean(temp_chunk))

        # 5. 선 그리기
        x = np.array(slopes)
        y = np.array(avg_powers)
        z = np.array(avg_temps)

        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        fig, ax = plt.subplots(figsize=(12, 10))

        norm = plt.Normalize(z.min(), z.max())
        lc = LineCollection(segments, cmap='magma', norm=norm)
        lc.set_array(z)
        lc.set_linewidth(2)
        lc.set_alpha(0.8)

        line = ax.add_collection(lc)
        
        ax.set_xlim(x.min()-0.5, x.max()+0.5)
        ax.set_ylim(y.min()-1, y.max()+1)

        # 기준선
        ax.axvline(0, color='k', linestyle='--', linewidth=1.5, label='Equilibrium (Slope=0)')
        
        # 추세선 (Trend Line) - 60도 이상 데이터만의 경향성
        if len(x) > 1:
            trend = np.polyfit(x, y, 1)
            
            # 파란 점선 -> 빨간 실선으로 변경 (강조)
            x_range = np.linspace(x.min(), x.max(), 100)
            y_trend = np.poly1d(trend)(x_range)
            
            ax.plot(x_range, y_trend, 'b:', linewidth=3, label=f'Active Trend (>{min_temp}°C)')
            
            # Y절편(냉각 한계) 표시
            y_intercept = np.poly1d(trend)(0)
            ax.plot(0, y_intercept, 'rx', markersize=12, markeredgewidth=3)
            ax.text(0.1, y_intercept, f' Limit: {y_intercept:.1f}kW', color='red', fontweight='bold', fontsize=12)

        cbar = fig.colorbar(line, ax=ax)
        cbar.set_label('Motor Temperature (°C)')
        
        ax.set_title(f'Active Thermal Performance (Temp >= {min_temp}°C)')
        ax.set_xlabel('Temperature Slope (°C / 10sec)')
        ax.set_ylabel('Average Input Power (kW)')
        ax.grid(True)
        ax.legend(loc='upper left')

        plt.tight_layout
        plt.show()

    def plot_thermal_path_v2(self, window_sec=15.0, min_power_kw=2.5):
        """
        [Update v2] 전력(Power) 기반 필터링 적용
        - 2.5kW 미만 데이터(피트인, 탄력주행) 제거
        - 순수 '부하 주행 시'의 열적 특성만 분석
        """
        from matplotlib.collections import LineCollection

        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            return

        # 1. 데이터 추출
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        # 2. 동기화
        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)

        # [중요] 필터링 전에 '전력'을 먼저 계산해야 함
        # (NaN이 포함되어 있어도 계산 후 마스킹으로 처리)
        power_kw_raw = (v_cap * i_sync) / 1000.0

        # 3. [핵심] 데이터 필터링 (Power >= 2.5kW & NaN 제거)
        # 피트인/대기 구간(2.5kW 미만) 삭제
        mask = (~np.isnan(v_cap) & ~np.isnan(i_sync) & ~np.isnan(temp_sync)) & \
               (power_kw_raw >= min_power_kw)
        
        t_v = t_v[mask]
        v_cap = v_cap[mask]
        i_sync = i_sync[mask]
        temp_sync = temp_sync[mask]
        power_kw = power_kw_raw[mask]
        
        if len(t_v) < 10:
            print(f"조건을 만족하는 데이터가 너무 적습니다. (Min Power: {min_power_kw}kW)")
            return

        # 4. 슬라이딩 윈도우 & 선형 회귀
        fs = 1.0 / np.mean(np.diff(t_v))
        window_len = int(window_sec * fs)
        if window_len < 2: window_len = 2
        
        step = max(1, int(fs * 0.5)) 

        slopes = []
        avg_powers = []
        avg_temps = []

        print(f"INFO: Analyzing Active Load Data (Power >= {min_power_kw}kW)...")

        for i in range(0, len(t_v) - window_len, step):
            t_chunk = t_v[i : i + window_len]
            
            # 데이터 연속성 체크 (필터링으로 시간이 끊긴 구간 건너뛰기)
            if t_chunk[-1] - t_chunk[0] > window_sec * 1.5: 
                continue

            temp_chunk = temp_sync[i : i + window_len]
            power_chunk = power_kw[i : i + window_len]
            
            fit = np.polyfit(t_chunk, temp_chunk, 1)
            
            slopes.append(fit[0] * 10.0) # 10초당 변화율
            avg_powers.append(np.mean(power_chunk))
            avg_temps.append(np.mean(temp_chunk))

        # 5. 선 그리기
        x = np.array(slopes)
        y = np.array(avg_powers)
        z = np.array(avg_temps)

        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        fig, ax = plt.subplots(figsize=(12, 10))

        norm = plt.Normalize(z.min(), z.max())
        lc = LineCollection(segments, cmap='magma', norm=norm)
        lc.set_array(z)
        lc.set_linewidth(2)
        lc.set_alpha(0.8)

        line = ax.add_collection(lc)
        
        # 축 범위 설정 (잘린 데이터에 맞춰 자동 조절)
        ax.set_xlim(x.min()-0.5, x.max()+0.5)
        ax.set_ylim(min_power_kw, y.max()+1) # Y축 시작을 컷오프 지점으로

        # 기준선
        ax.axvline(0, color='k', linestyle='--', linewidth=1.5, label='Equilibrium (Slope=0)')
        
        # 추세선 (Trend Line)
        if len(x) > 1:
            trend = np.polyfit(x, y, 1)
            
            x_range = np.linspace(x.min(), x.max(), 100)
            y_trend = np.poly1d(trend)(x_range)
            
            ax.plot(x_range, y_trend, 'b:', linewidth=3, label=f'High Load Trend (>{min_power_kw}kW)')
            
            # Y절편(냉각 한계) 표시
            y_intercept = np.poly1d(trend)(0)
            ax.plot(0, y_intercept, 'rx', markersize=12, markeredgewidth=3)
            ax.text(0.1, y_intercept, f' Limit: {y_intercept:.1f}kW', color='red', fontweight='bold', fontsize=12)

        cbar = fig.colorbar(line, ax=ax)
        cbar.set_label('Motor Temperature (°C)')
        
        ax.set_title(f'Active Thermal Performance (Power >= {min_power_kw}kW)')
        ax.set_xlabel(f'Temperature Slope (°C / 10sec) [Window: {window_sec}s]')
        ax.set_ylabel('Average Input Power (kW)')
        ax.grid(True)
        ax.legend(loc='upper left')

        plt.tight_layout()
        plt.show()

    def plot_power_vs_temp_slope(self, window_sec=15.0, min_power_kw=2.5):
        """
        [Final Analysis] 입력 전력(VI) vs 온도 상승률
        - X축: 온도 변화 기울기 (degC / 10s)
        - Y축: 평균 입력 전력 (kW)
        - Filter: 2.5kW 미만 저부하 구간 제외
        """
        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            return

        # 1. 데이터 추출
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        # 2. 동기화 및 전력 계산
        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)
        
        # 전력 계산 (kW)
        power_kw_raw = (v_cap * i_sync) / 1000.0

        # 3. 필터링 (2.5kW 이상 & NaN 제거)
        mask = (~np.isnan(v_cap) & ~np.isnan(i_sync) & ~np.isnan(temp_sync)) & \
               (power_kw_raw >= min_power_kw)
        
        t_v = t_v[mask]
        temp_sync = temp_sync[mask]
        power_kw = power_kw_raw[mask]
        
        if len(t_v) < 10:
            print("조건을 만족하는 데이터가 부족합니다.")
            return

        # 4. 슬라이딩 윈도우 회귀
        fs = 1.0 / np.mean(np.diff(t_v))
        window_len = int(window_sec * fs)
        if window_len < 2: window_len = 2
        step = max(1, int(fs * 0.5))

        slopes = []
        avg_powers = []
        avg_temps = []

        print(f"INFO: Analyzing Power vs Slope (Window: {window_sec}s)...")

        for i in range(0, len(t_v) - window_len, step):
            # 데이터 끊김 방지
            if t_v[i + window_len - 1] - t_v[i] > window_sec * 1.5:
                continue

            t_chunk = t_v[i : i + window_len]
            temp_chunk = temp_sync[i : i + window_len]
            power_chunk = power_kw[i : i + window_len]
            
            # 선형 회귀 (기울기 추출)
            fit = np.polyfit(t_chunk, temp_chunk, 1)
            
            slopes.append(fit[0] * 10.0) # 10초당 온도 변화
            avg_powers.append(np.mean(power_chunk))
            avg_temps.append(np.mean(temp_chunk))

        # 5. 그래프 그리기
        x = np.array(slopes)
        y = np.array(avg_powers)
        c = np.array(avg_temps)

        plt.figure(figsize=(12, 10))
        
        # 산점도
        sc = plt.scatter(x, y, c=c, cmap='magma', s=20, alpha=0.6)
        
        # 기준선 (열 평형)
        plt.axvline(0, color='k', linestyle='--', linewidth=1.5, label='Thermal Equilibrium')

        # 추세선 (Trend Line)
        if len(x) > 1:
            trend = np.polyfit(x, y, 1)
            x_range = np.linspace(x.min(), x.max(), 100)
            y_trend = np.poly1d(trend)(x_range)
            
            plt.plot(x_range, y_trend, 'b:', linewidth=3, label='Cooling Performance Trend')
            
            # Y절편 (냉각 한계 전력)
            limit_kw = np.poly1d(trend)(0)
            
            plt.plot(0, limit_kw, 'rx', markersize=15, markeredgewidth=3)
            plt.text(0.2, limit_kw, f' Continuous Limit:\n {limit_kw:.1f} kW', 
                     color='red', fontweight='bold', fontsize=14, verticalalignment='center')

        cbar = plt.colorbar(sc)
        cbar.set_label('Motor Temperature (°C)')
        
        plt.title(f'Cooling Capacity Analysis: Input Power vs Temp Slope\n(Filtered: Power >= {min_power_kw}kW)')
        plt.xlabel('Temperature Rise Speed (°C / 10sec)')
        plt.ylabel('Average Input Power (kW)')
        plt.grid(True)
        plt.legend(loc='upper left')

        plt.tight_layout()
        plt.show()

    def plot_cooling_trend_regression(self, window_sec=15.0, max_power_kw=1.0):
        """
        [순수 냉각 성능 정밀 분석]
        - 조건: 전력 소모 1kW 미만 (거의 정차/탄력주행)
        - X축: 현재 모터 온도 (°C)
        - Y축: 온도 변화율 (°C / 10s) -> 식는 속도
        - 추세선: 뉴턴의 냉각 법칙에 따른 냉각 계수(k) 추정
        """
        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            return

        # 1. 데이터 추출
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)
        power_kw = (v_cap * i_sync) / 1000.0

        # 2. 필터링 (Power < 1kW & NaN 제거)
        mask = (~np.isnan(v_cap) & ~np.isnan(i_sync) & ~np.isnan(temp_sync)) & \
               (power_kw < max_power_kw)
        
        t_v = t_v[mask]
        temp_sync = temp_sync[mask]
        
        if len(t_v) < 10:
            print("냉각 분석을 위한 저부하 데이터가 부족합니다.")
            return

        # 3. 슬라이딩 윈도우 & 기울기 계산
        fs = 1.0 / np.mean(np.diff(t_v))
        window_len = int(window_sec * fs)
        if window_len < 2: window_len = 2
        step = max(1, int(fs * 0.5))

        slopes = []     # Y축: 식는 속도
        avg_temps = []  # X축: 현재 온도

        print(f"INFO: Analyzing Cooling Trend (Power < {max_power_kw}kW)...")

        for i in range(0, len(t_v) - window_len, step):
            if t_v[i + window_len - 1] - t_v[i] > window_sec * 1.5:
                continue

            t_chunk = t_v[i : i + window_len]
            temp_chunk = temp_sync[i : i + window_len]
            
            # 선형 회귀로 '순간 기울기' 추출
            fit = np.polyfit(t_chunk, temp_chunk, 1)
            
            slopes.append(fit[0] * 10.0) # 10초당 변화율
            avg_temps.append(np.mean(temp_chunk))

        # 4. 그래프 그리기
        x = np.array(avg_temps) # 온도
        y = np.array(slopes)    # 속도

        plt.figure(figsize=(11, 9))
        
        # 산점도
        plt.scatter(x, y, c='blue', s=15, alpha=0.3, label='Cooling Data Points')
        
        # 기준선 (0 = 변화 없음)
        plt.axhline(0, color='k', linestyle='--', linewidth=1.5, label='Zero Change')

        # --- [핵심] 추세선 (Trend Line) 그리기 ---
        if len(x) > 1:
            # 1차 함수 피팅 (y = ax + b)
            # a (기울기)가 가파를수록 고온에서 냉각 효율이 좋다는 뜻
            trend = np.polyfit(x, y, 1)
            trend_fn = np.poly1d(trend)
            
            x_range = np.linspace(x.min(), x.max(), 100)
            
            # 파란색 점선으로 추세선 표시
            plt.plot(x_range, trend_fn(x_range), 'r:', linewidth=3, label='Cooling Performance Trend')
            
            # 성능 지표 (기울기) 텍스트 표시
            cooling_coeff = trend[0]
            # y값(속도)이 음수이므로, 기울기가 음수여야 정상 (온도가 높을수록 더 빨리 식음 -> y가 더 작아짐)
            
            plt.text(x.min(), trend_fn(x.min()), 
                     f' Cooling Coefficient: {cooling_coeff:.3f}\n (Steeper is Better)', 
                     color='red', fontweight='bold', fontsize=12, verticalalignment='bottom')

        plt.title(f'Passive Cooling Performance: Temp vs Cooling Rate\n(Filtered: Power < {max_power_kw}kW)')
        plt.xlabel('Current Motor Temperature (°C)')
        plt.ylabel('Cooling Speed (°C / 10sec)')
        plt.grid(True)
        plt.legend()
        
        # Y축 반전 (아래로 내려갈수록 빨리 식는 것이므로 직관적으로 보이게)
        # 만약 헷갈리면 이 줄을 주석 처리하세요.
        # plt.gca().invert_yaxis() 

        plt.tight_layout()
        plt.show()        

    def plot_cooling_intercept(self, window_sec=15.0, max_power_kw=1.0):
        """
        [순수 냉각 구간 분석] Power vs Temp Slope (Low Power Only)
        - 조건: 전력 < 1kW (정차/탄력주행)
        - 목적: Y=0(전력 0)일 때의 X절편(냉각 속도) 확인
        """
        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            return

        # 1. 데이터 추출 및 동기화
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)
        power_kw_raw = (v_cap * i_sync) / 1000.0

        # 2. [핵심] 1kW 이상 데이터 제외 (High Power Filter Out)
        mask = (
            np.isfinite(t_v) &
            np.isfinite(v_cap) &
            np.isfinite(i_sync) &
            np.isfinite(temp_sync) &
            np.isfinite(power_kw_raw) &
            (power_kw_raw < max_power_kw)
        )
        
        t_v = t_v[mask]
        temp_sync = temp_sync[mask]
        power_kw = power_kw_raw[mask]

        sort_idx = np.argsort(t_v)
        t_v = t_v[sort_idx]
        temp_sync = temp_sync[sort_idx]
        power_kw = power_kw[sort_idx]

        unique_time = np.concatenate(([True], np.diff(t_v) > 0))
        t_v = t_v[unique_time]
        temp_sync = temp_sync[unique_time]
        power_kw = power_kw[unique_time]
        
        if len(t_v) < 10:
            print(f"조건을 만족하는 저부하 데이터가 부족합니다. (Max Power: {max_power_kw}kW)")
            return

        # 3. 슬라이딩 윈도우 회귀
        dt = np.diff(t_v)
        dt = dt[np.isfinite(dt) & (dt > 0)]
        if len(dt) == 0:
            print("유효한 시간 간격이 없어 냉각 분석을 수행할 수 없습니다.")
            return

        fs = 1.0 / np.median(dt)
        window_len = int(window_sec * fs)
        if window_len < 2: window_len = 2
        step = max(1, int(fs * 0.5))

        slopes = []
        avg_powers = []
        avg_temps = []

        print(f"INFO: Analyzing Cooling Intercept (Power < {max_power_kw}kW)...")

        for i in range(0, len(t_v) - window_len, step):
            if t_v[i + window_len - 1] - t_v[i] > window_sec * 1.5:
                continue

            t_chunk = t_v[i : i + window_len]
            temp_chunk = temp_sync[i : i + window_len]
            power_chunk = power_kw[i : i + window_len]

            chunk_valid = (
                np.isfinite(t_chunk) &
                np.isfinite(temp_chunk) &
                np.isfinite(power_chunk)
            )
            t_chunk = t_chunk[chunk_valid]
            temp_chunk = temp_chunk[chunk_valid]
            power_chunk = power_chunk[chunk_valid]

            if len(t_chunk) < 3 or np.ptp(t_chunk) <= 0:
                continue
            
            try:
                fit = np.polyfit(t_chunk, temp_chunk, 1)
            except np.linalg.LinAlgError:
                continue
            
            slopes.append(fit[0] * 10.0) # 10초당 변화율
            avg_powers.append(np.mean(power_chunk))
            avg_temps.append(np.mean(temp_chunk))

        # 4. 그래프 그리기
        x = np.array(slopes)
        y = np.array(avg_powers)
        c = np.array(avg_temps)

        valid_fit = np.isfinite(x) & np.isfinite(y) & np.isfinite(c)
        x = x[valid_fit]
        y = y[valid_fit]
        c = c[valid_fit]

        if len(x) < 2:
            print("회귀 가능한 냉각 구간이 부족합니다. max_power_kw 또는 window_sec를 조정하세요.")
            return

        plt.figure(figsize=(12, 10))
        
        # 산점도 (Cooling Zone)
        sc = plt.scatter(x, y, c=c, cmap='cool', s=20, alpha=0.5)
        
        # 기준선
        plt.axvline(0, color='k', linestyle='--', linewidth=1, label='Zero Change')
        plt.axhline(0, color='k', linestyle='-', linewidth=1) # Y=0 바닥선

        # 추세선 및 X절편 계산
        if len(x) > 1 and np.ptp(x) > 0:
            try:
                trend = np.polyfit(x, y, 1) # y = ax + b
            except np.linalg.LinAlgError:
                print("추세선 계산 실패: 데이터 분산이 부족하거나 수치적으로 불안정합니다.")
                trend = None
            
            # X절편 구하기 (y=0일 때 x값) => x = -b / a
            if trend is not None:
                slope_a, intercept_b = trend
                if slope_a != 0:
                    x_intercept = -intercept_b / slope_a
                else:
                    x_intercept = 0
                
                # 추세선 그리기
                x_range = np.linspace(min(x.min(), x_intercept-0.5), max(x.max(), 0.5), 100)
                plt.plot(x_range, np.poly1d(trend)(x_range), 'b--', linewidth=2, label='Cooling Trend')
                
                # X절편 표시 (Natural Cooling Rate)
                plt.plot(x_intercept, 0, 'bx', markersize=15, markeredgewidth=3)
                plt.text(x_intercept, 0.1, f' Natural Cooling:\n {x_intercept:.2f} °C/10s', 
                         color='blue', fontweight='bold', fontsize=12, horizontalalignment='center')
        else:
            print("온도 기울기 데이터의 변화폭이 부족하여 추세선을 생략합니다.")

        cbar = plt.colorbar(sc)
        cbar.set_label('Motor Temperature (°C)')
        
        plt.title(f'Natural Cooling Analysis: Power vs Temp Slope\n(Filtered: Power < {max_power_kw}kW)')
        plt.xlabel('Temperature Drop Speed (°C / 10sec)')
        plt.ylabel('Average Input Power (kW)')
        plt.grid(True)
        plt.legend(loc='upper right')
        
        # X축을 반전시키지 않고 그대로 둡니다 (음수 = 식음)
        # 왼쪽으로 갈수록 빨리 식는 것입니다.

        plt.tight_layout()
        plt.show()

    def analyze_thermal_lag(self, window_sec=15.0, min_power_kw=2.5, max_lag_sec=30.0):
        """
        [시스템 식별] 최적의 열 전달 지연 시간(Thermal Lag) 찾기
        - 전력(입력)과 온도상승(출력) 사이의 시간차(phi)를 스캔하여
        - 상관관계(Correlation)가 가장 높은 '진짜 반응 시간'을 찾아냅니다.
        """
  

        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            return

        # 1. 데이터 추출 & 동기화
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        # 전압 시간축 기준 동기화
        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)
        power_kw_raw = (v_cap * i_sync) / 1000.0

        # NaN 제거
        mask = ~np.isnan(v_cap) & ~np.isnan(i_sync) & ~np.isnan(temp_sync)
        t_v = t_v[mask]
        temp_sync = temp_sync[mask]
        power_kw = power_kw_raw[mask]

        if len(t_v) == 0: return

        # 2. 샘플링 정보
        fs = 1.0 / np.mean(np.diff(t_v))
        window_len = int(window_sec * fs)
        if window_len < 2: window_len = 2
        
        # 3. Lag 스윕 (Sweep) 준비
        # 0초부터 max_lag_sec까지 테스트
        lags = np.arange(0, max_lag_sec, 0.5) # 0.5초 단위 검색
        correlations = []
        best_lag = 0
        best_r2 = -999
        best_slopes = []
        best_powers = []
        best_temps = []

        print(f"INFO: Scanning Thermal Lag (0s ~ {max_lag_sec}s)...")

        # 4. Lag별 상관분석 루프
        for lag in lags:
            lag_idx = int(lag * fs)
            
            curr_slopes = []
            curr_powers = []
            curr_temps = []
            
            # 슬라이딩 윈도우
            # 전력은 t 구간, 온도는 t + lag 구간을 매칭
            step = max(1, int(fs * 1.0)) # 속도를 위해 1초 단위 이동

            for i in range(0, len(t_v) - window_len - lag_idx, step):
                # 데이터 끊김 체크
                if t_v[i + window_len - 1] - t_v[i] > window_sec * 1.5: continue

                # 전력: 현재 시점 (원인)
                power_chunk = power_kw[i : i + window_len]
                avg_p = np.mean(power_chunk)
                
                # 필터링 (저부하 제외)
                if avg_p < min_power_kw: continue

                # 온도: Lag만큼 뒤의 시점 (결과)
                idx_temp_start = i + lag_idx
                t_chunk_temp = t_v[idx_temp_start : idx_temp_start + window_len]
                temp_chunk = temp_sync[idx_temp_start : idx_temp_start + window_len]
                
                # 온도 기울기 계산
                fit = np.polyfit(t_chunk_temp, temp_chunk, 1)
                slope = fit[0] * 10.0 # 10초당 변화율

                curr_slopes.append(slope)
                curr_powers.append(avg_p)
                curr_temps.append(np.mean(temp_chunk))

            # 상관계수(R^2) 계산
            if len(curr_slopes) > 10:
                x = np.array(curr_slopes).reshape(-1, 1) # X: 기울기
                y = np.array(curr_powers)                # Y: 전력
                
                # 단순 선형회귀 피팅 후 점수 계산
                model_fit = np.polyfit(curr_slopes, curr_powers, 1)
                model_fn = np.poly1d(model_fit)
                y_pred = model_fn(curr_slopes)
                
                r2 = r2_score(y, y_pred)
                correlations.append(r2)
                
                # 최적값 갱신
                if r2 > best_r2:
                    best_r2 = r2
                    best_lag = lag
                    best_slopes = curr_slopes
                    best_powers = curr_powers
                    best_temps = curr_temps
            else:
                correlations.append(0)

        print(f"RESULT: Optimal Lag = {best_lag} sec (R^2 = {best_r2:.4f})")

        # 5. 그래프 그리기 (2 Subplots)
        fig = plt.figure(figsize=(14, 6))

        # [Graph 1] Lag vs R2 Score
        ax1 = fig.add_subplot(1, 2, 1)
        ax1.plot(lags, correlations, 'b-o')
        ax1.axvline(best_lag, color='r', linestyle='--', label=f'Best Lag: {best_lag}s')
        ax1.set_xlabel('Time Lag (phi) [sec]')
        ax1.set_ylabel('Correlation Score (R²)')
        ax1.set_title('Optimization: Finding Thermal Delay')
        ax1.legend()
        ax1.grid(True)

        # [Graph 2] 최적 Lag 적용 후 성능 곡선
        ax2 = fig.add_subplot(1, 2, 2)
        
        x = np.array(best_slopes)
        y = np.array(best_powers)
        c = np.array(best_temps)
        
        sc = ax2.scatter(x, y, c=c, cmap='magma', s=20, alpha=0.6)
        
        # 추세선
        if len(x) > 1:
            trend = np.polyfit(x, y, 1)
            x_range = np.linspace(x.min(), x.max(), 100)
            ax2.plot(x_range, np.poly1d(trend)(x_range), 'b:', linewidth=3, 
                     label=f'Optimized Trend (Lag={best_lag}s)')
            
            # Y절편 (한계 전력)
            limit_kw = np.poly1d(trend)(0)
            ax2.plot(0, limit_kw, 'rx', markersize=15, markeredgewidth=3)
            ax2.text(0.1, limit_kw, f' Limit: {limit_kw:.1f} kW', color='red', fontweight='bold')

        ax2.axvline(0, color='k', linestyle='--')
        ax2.set_xlabel('Temperature Slope (°C / 10s)')
        ax2.set_ylabel('Avg Input Power (kW)')
        ax2.set_title(f'Corrected Performance Curve (Lag: {best_lag}s)')
        ax2.grid(True)
        ax2.legend()
        
        plt.colorbar(sc, ax=ax2, label='Temp (°C)')
        plt.tight_layout()
        plt.show()

    def plot_cooling_trend_high_temp(self, window_sec=15.0, max_power_kw=1.0, min_temp=60.0):
        """
        [냉각 분석 v2] 고온 구간(60도 이상)에서의 순수 냉각 속도 분석
        - 저온(포화) 영역 데이터 배제 -> 진짜 냉각 성능(기울기) 확인
        """
        if self.data.Vcap_set is None or self.data.Ibatt_set is None or self.data.motorTemp_set is None:
            return

        # 1. 데이터 추출
        t_v = self.data.Vcap_set[0, :]
        v_cap = self.data.Vcap_set[1, :]
        t_i = self.data.Ibatt_set[0, :]
        i_batt = self.data.Ibatt_set[1, :]
        t_temp = self.data.motorTemp_set[0, :]
        temp_val = self.data.motorTemp_set[1, :]

        i_sync = np.interp(t_v, t_i, i_batt)
        temp_sync = np.interp(t_v, t_temp, temp_val)
        power_kw = (v_cap * i_sync) / 1000.0

        # 2. [핵심] 이중 필터링 (Power < 1kW AND Temp > 60도)
        # 이미 식어버린 데이터(Saturation)는 분석에서 뺍니다.
        mask = (~np.isnan(v_cap) & ~np.isnan(i_sync) & ~np.isnan(temp_sync)) & \
               (power_kw < max_power_kw) & \
               (temp_sync >= min_temp)
        
        t_v = t_v[mask]
        temp_sync = temp_sync[mask]
        
        if len(t_v) < 10:
            print(f"조건을 만족하는 데이터가 없습니다. (Temp >= {min_temp}°C)")
            return

        # 3. 슬라이딩 윈도우 회귀
        fs = 1.0 / np.mean(np.diff(t_v))
        window_len = int(window_sec * fs)
        if window_len < 2: window_len = 2
        step = max(1, int(fs * 0.5))

        slopes = []
        avg_temps = []

        print(f"INFO: Analyzing High-Temp Cooling (>{min_temp}°C)...")

        for i in range(0, len(t_v) - window_len, step):
            if t_v[i + window_len - 1] - t_v[i] > window_sec * 1.5:
                continue

            t_chunk = t_v[i : i + window_len]
            temp_chunk = temp_sync[i : i + window_len]
            
            fit = np.polyfit(t_chunk, temp_chunk, 1)
            
            slopes.append(fit[0] * 10.0) 
            avg_temps.append(np.mean(temp_chunk))

        # 4. 그래프 그리기
        x = np.array(avg_temps)
        y = np.array(slopes)

        plt.figure(figsize=(11, 9))
        
        # 산점도 (온도가 높을수록 붉은색)
        plt.scatter(x, y, c=x, cmap='Reds', s=20, alpha=0.6, label='Cooling Data')
        
        plt.axhline(0, color='k', linestyle='--', linewidth=1.5)

        # 추세선
        if len(x) > 1:
            trend = np.polyfit(x, y, 1)
            trend_fn = np.poly1d(trend)
            
            x_range = np.linspace(x.min(), x.max(), 100)
            plt.plot(x_range, trend_fn(x_range), 'b:', linewidth=3, label='High-Temp Cooling Trend')
            
            # 기울기(Cooling Coefficient) 재확인
            k_value = trend[0]
            
            plt.text(x.min(), trend_fn(x.min()), 
                     f' True Cooling Coeff (k): {k_value:.3f}', 
                        color='blue', fontweight='bold', fontsize=14, verticalalignment='bottom')

            plt.xlabel("RPM")
            plt.ylabel("Torque")
            plt.title("Estimated T-N Curve")
            plt.grid()
            plt.show() 

            plt.title(f'Pure Cooling Performance at High Temp (Temp > {min_temp}°C)')
            plt.xlabel('Current Motor Temperature (°C)')
            plt.ylabel('Cooling Speed (°C / 10sec)')
            plt.grid(True)
            plt.legend()
            
            # Y축 반전 (아래가 빠름)
            # plt.gca().invert_yaxis() 

            plt.tight_layout()
            plt.show()

    def plot_tn_curve_envelope(self, rpm_bin_width=100.0, min_samples_per_bin=10, drop_ratio=0.85):
        """
        [T-N Curve Envelope]
        실제 주행 데이터 기준으로 RPM별 토크 상한선을 확인한다.

        - 95% torque: 해당 RPM 구간에서 실제로 자주 도달한 상한선
        - 99% torque: 순간 피크에 가까운 상한선
        - median torque: 일반 주행 분포 확인용
        - sample count: 각 RPM bin의 데이터 신뢰도 확인용
        """
        if self.data.vel_set is None or self.data.torqueAct_set is None:
            print("데이터 부족: vel_set, torqueAct_set이 필요합니다.")
            return

        t_rpm_raw = self.data.vel_set[0, :]
        rpm_raw = self.data.vel_set[1, :]
        t_torque_raw = self.data.torqueAct_set[0, :]
        torque_raw = self.data.torqueAct_set[1, :]

        rpm_valid = np.isfinite(t_rpm_raw) & np.isfinite(rpm_raw)
        torque_valid = np.isfinite(t_torque_raw) & np.isfinite(torque_raw)

        t_rpm = t_rpm_raw[rpm_valid]
        rpm = rpm_raw[rpm_valid]
        t_torque = t_torque_raw[torque_valid]
        torque = torque_raw[torque_valid]

        if len(t_rpm) < 2 or len(t_torque) < 2:
            print("유효한 RPM 또는 Torque 데이터가 부족합니다.")
            return

        rpm_sort = np.argsort(t_rpm)
        t_rpm = t_rpm[rpm_sort]
        rpm = rpm[rpm_sort]

        torque_sort = np.argsort(t_torque)
        t_torque = t_torque[torque_sort]
        torque = torque[torque_sort]

        torque_sync = np.interp(t_rpm, t_torque, torque)

        valid = (
            np.isfinite(rpm) &
            np.isfinite(torque_sync) &
            (rpm >= 0) &
            (rpm <= 6000) &
            (torque_sync >= 0) &
            (torque_sync <= 300)
        )

        rpm = rpm[valid]
        torque = torque_sync[valid]

        if len(rpm) == 0:
            print("유효한 T-N curve 데이터가 없습니다.")
            return

        rpm_max = np.ceil(np.max(rpm) / rpm_bin_width) * rpm_bin_width
        bins = np.arange(0, rpm_max + rpm_bin_width, rpm_bin_width)

        rpm_centers = []
        torque_p50 = []
        torque_p95 = []
        torque_p99 = []
        counts = []

        for i in range(len(bins) - 1):
            mask = (rpm >= bins[i]) & (rpm < bins[i + 1])

            if np.sum(mask) < min_samples_per_bin:
                continue

            rpm_bin = rpm[mask]
            torque_bin = torque[mask]

            rpm_centers.append(np.mean(rpm_bin))
            torque_p50.append(np.percentile(torque_bin, 50))
            torque_p95.append(np.percentile(torque_bin, 95))
            torque_p99.append(np.percentile(torque_bin, 99))
            counts.append(np.sum(mask))

        rpm_centers = np.array(rpm_centers)
        torque_p50 = np.array(torque_p50)
        torque_p95 = np.array(torque_p95)
        torque_p99 = np.array(torque_p99)
        counts = np.array(counts)

        if len(rpm_centers) == 0:
            print("RPM bin별 T-N curve 분석이 불가능합니다. 데이터가 부족합니다.")
            return

        peak_idx = np.argmax(torque_p95)
        peak_rpm = rpm_centers[peak_idx]
        peak_torque = torque_p95[peak_idx]

        drop_rpm = None
        drop_threshold = peak_torque * drop_ratio
        after_peak = np.arange(len(rpm_centers)) > peak_idx
        drop_candidates = np.where(after_peak & (torque_p95 < drop_threshold))[0]
        if len(drop_candidates) > 0:
            drop_rpm = rpm_centers[drop_candidates[0]]

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(12, 8), sharex=True,
            gridspec_kw={'height_ratios': [4, 1]}
        )

        ax1.scatter(rpm[::5], torque[::5], s=5, alpha=0.18, label='Raw Actual Torque')
        ax1.plot(rpm_centers, torque_p50, 'k--', linewidth=1.8, label='Median Torque')
        ax1.plot(rpm_centers, torque_p95, 'r-', linewidth=2.6, label='Torque Envelope (95%)')
        ax1.plot(rpm_centers, torque_p99, 'm:', linewidth=2.2, label='Torque Peak Envelope (99%)')
        ax1.plot(peak_rpm, peak_torque, 'ro', markersize=8, label=f'Peak 95%: {peak_torque:.1f} Nm @ {peak_rpm:.0f} RPM')

        if drop_rpm is not None:
            ax1.axvline(drop_rpm, color='orange', linestyle='--', linewidth=1.8,
                        label=f'Drop below {drop_ratio * 100:.0f}% @ {drop_rpm:.0f} RPM')

        ax1.set_title('T-N Curve Envelope')
        ax1.set_ylabel('Torque (Nm)')
        ax1.grid(True)
        ax1.legend(loc='best')

        ax2.bar(rpm_centers, counts, width=rpm_bin_width * 0.8)
        ax2.set_xlabel('RPM')
        ax2.set_ylabel('Count')
        ax2.set_title('Sample Count per RPM Bin')
        ax2.grid(True)

        plt.tight_layout()
        plt.show()

        print("\n[T-N Curve Envelope Summary]")
        print(f"- Total valid points: {len(rpm)}")
        print(f"- RPM bins analyzed: {len(rpm_centers)}")
        print(f"- Peak 95% torque: {peak_torque:.2f} Nm @ {peak_rpm:.0f} RPM")
        if drop_rpm is not None:
            print(f"- First drop below {drop_ratio * 100:.0f}% of peak: RPM ~ {drop_rpm:.0f}")
        else:
            print(f"- No clear drop below {drop_ratio * 100:.0f}% of peak after peak RPM.")

    def plot_power_vs_rpm(self):
        if self.data.vel_set is None or self.data.torqueAct_set is None:
            print("필요 데이터 없음")
            return

        # -------------------------------
        # 1. 기준 시간축: RPM 데이터
        # -------------------------------
        t_ref = self.data.vel_set[0, :]
        rpm = self.data.vel_set[1, :]

        # -------------------------------
        # 2. Actual Torque 보간
        # -------------------------------
        t_trq = self.data.torqueAct_set[0, :]
        trq_act_raw = self.data.torqueAct_set[1, :]
        trq_act = np.interp(t_ref, t_trq, trq_act_raw)

        # -------------------------------
        # 3. 유효 데이터 필터링
        # -------------------------------
        valid = (
            np.isfinite(rpm) &
            np.isfinite(trq_act) &
            (rpm > 0) &
            (trq_act > 5)
        )

        rpm = rpm[valid]
        trq_act = trq_act[valid]

        if len(rpm) == 0:
            print("유효한 데이터가 없습니다.")
            return

        # -------------------------------
        # 4. Power 계산
        # P(kW) = Torque(Nm) * RPM / 9550
        # -------------------------------
        power_act = trq_act * rpm / 9550.0

        # -------------------------------
        # 5. RPM binning으로 추세선 계산
        # -------------------------------
        bins = np.arange(0, 4000, 100)

        rpm_centers = []
        power_trend = []
        power_env = []

        for i in range(len(bins) - 1):
            mask = (rpm >= bins[i]) & (rpm < bins[i + 1])

            # 샘플이 너무 적으면 제외
            if np.sum(mask) < 20:
                continue

            rpm_bin = rpm[mask]
            power_bin = power_act[mask]

            # 대표 RPM
            rpm_centers.append(np.mean(rpm_bin))

            # 평균 추세선
            power_trend.append(np.mean(power_bin))

            # 상한선 (95 percentile)
            power_env.append(np.percentile(power_bin, 95))

        # -------------------------------
        # 6. 그래프 그리기
        # -------------------------------
        plt.figure(figsize=(9, 6))

        # raw scatter
        plt.scatter(rpm, power_act, s=5, alpha=0.3, label='Actual Power')

        # 평균 추세선
        plt.plot(rpm_centers, power_trend, 'r-', linewidth=3, label='Power Trend')

        # 상한선
        plt.plot(rpm_centers, power_env, 'g--', linewidth=2, label='Power Envelope (95%)')

        plt.xlabel("RPM")
        plt.ylabel("Power (kW)")
        plt.title("Power vs RPM")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def plot_id_iq_vs_rpm(self, rpm_bin_width=100.0, min_samples_per_bin=10, current_limit=None):
        """
        [약계자 기본 확인]
        X축을 RPM으로 두고 Id/Iq 전류가 어떻게 변하는지 확인한다.

        해석 포인트
        - RPM이 올라가면서 Id가 음수 방향으로 내려가면 약계자 진입
        - Iq는 토크 전류이므로, 고RPM에서 Iq가 줄고 Id가 음수로 커지는지 확인
        - current_limit을 넣으면 +/- 기준선을 함께 표시
        """
        if self.data.vel_set is None or self.data.Idq_set is None:
            print("데이터 부족: vel_set, Idq_set이 필요합니다.")
            return

        t_rpm_raw = self.data.vel_set[0, :]
        rpm_raw = self.data.vel_set[1, :]
        t_dq_raw = self.data.Idq_set[0, :]
        id_raw = self.data.Idq_set[1, :]
        iq_raw = self.data.Idq_set[2, :]

        rpm_valid = np.isfinite(t_rpm_raw) & np.isfinite(rpm_raw)
        dq_valid = np.isfinite(t_dq_raw) & np.isfinite(id_raw) & np.isfinite(iq_raw)

        t_rpm = t_rpm_raw[rpm_valid]
        rpm = rpm_raw[rpm_valid]
        t_dq = t_dq_raw[dq_valid]
        id_curr = id_raw[dq_valid]
        iq_curr = iq_raw[dq_valid]

        if len(t_rpm) < 2 or len(t_dq) == 0:
            print("유효한 RPM 또는 Id/Iq 데이터가 부족합니다.")
            return

        rpm_sort = np.argsort(t_rpm)
        t_rpm = t_rpm[rpm_sort]
        rpm = rpm[rpm_sort]

        dq_sort = np.argsort(t_dq)
        t_dq = t_dq[dq_sort]
        id_curr = id_curr[dq_sort]
        iq_curr = iq_curr[dq_sort]

        rpm_sync = np.interp(t_dq, t_rpm, rpm)

        valid = (
            np.isfinite(rpm_sync) &
            np.isfinite(id_curr) &
            np.isfinite(iq_curr) &
            (rpm_sync >= 0) &
            (rpm_sync <= 6000) &
            (id_curr > -1000) & (id_curr < 1000) &
            (iq_curr > -1000) & (iq_curr < 1000)
        )

        rpm_sync = rpm_sync[valid]
        id_curr = id_curr[valid]
        iq_curr = iq_curr[valid]

        if len(rpm_sync) == 0:
            print("유효한 RPM-Id/Iq 데이터가 없습니다.")
            return

        rpm_min = np.floor(np.min(rpm_sync) / rpm_bin_width) * rpm_bin_width
        rpm_max = np.ceil(np.max(rpm_sync) / rpm_bin_width) * rpm_bin_width
        bins = np.arange(rpm_min, rpm_max + rpm_bin_width, rpm_bin_width)

        rpm_centers = []
        id_mean = []
        iq_mean = []
        id_p10 = []
        iq_p90 = []
        counts = []

        for i in range(len(bins) - 1):
            mask = (rpm_sync >= bins[i]) & (rpm_sync < bins[i + 1])
            if np.sum(mask) < min_samples_per_bin:
                continue

            rpm_centers.append(np.mean(rpm_sync[mask]))
            id_mean.append(np.mean(id_curr[mask]))
            iq_mean.append(np.mean(iq_curr[mask]))
            id_p10.append(np.percentile(id_curr[mask], 10))
            iq_p90.append(np.percentile(iq_curr[mask], 90))
            counts.append(np.sum(mask))

        rpm_centers = np.array(rpm_centers)
        id_mean = np.array(id_mean)
        iq_mean = np.array(iq_mean)
        id_p10 = np.array(id_p10)
        iq_p90 = np.array(iq_p90)
        counts = np.array(counts)

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(12, 8), sharex=True,
            gridspec_kw={'height_ratios': [4, 1]}
        )

        ax1.scatter(rpm_sync[::5], id_curr[::5], s=5, alpha=0.15, label='Id Raw')
        ax1.scatter(rpm_sync[::5], iq_curr[::5], s=5, alpha=0.15, label='Iq Raw')
        ax1.axhline(0, color='gray', linestyle='--', linewidth=1)
        if current_limit is not None:
            ax1.axhline(current_limit, color='orange', linestyle='--', linewidth=1.2, label=f'+{current_limit:.0f} A Ref')
            ax1.axhline(-current_limit, color='orange', linestyle='--', linewidth=1.2, label=f'-{current_limit:.0f} A Ref')

        if len(rpm_centers) > 0:
            ax1.plot(rpm_centers, id_mean, 'b-', linewidth=2.5, label='Id Mean')
            ax1.plot(rpm_centers, iq_mean, 'r-', linewidth=2.5, label='Iq Mean')
            ax1.plot(rpm_centers, id_p10, 'b:', linewidth=2, label='Id 10%')
            ax1.plot(rpm_centers, iq_p90, 'r:', linewidth=2, label='Iq 90%')

        ax1.set_title('Id / Iq vs RPM')
        ax1.set_ylabel('Current (A)')
        ax1.grid(True)
        ax1.legend(loc='best')

        if len(rpm_centers) > 0:
            ax2.bar(rpm_centers, counts, width=rpm_bin_width * 0.8)
        ax2.set_xlabel('RPM')
        ax2.set_ylabel('Count')
        ax2.set_title('Sample Count per RPM Bin')
        ax2.grid(True)

        plt.tight_layout()
        plt.show()

        print("\n[Id/Iq vs RPM Summary]")
        print(f"- Total valid points: {len(rpm_sync)}")
        print(f"- RPM bins analyzed: {len(rpm_centers)}")
        if current_limit is not None:
            print(f"- Current reference line: +/-{current_limit:.0f} A")

        fw_mask = (id_curr < -5.0) & (np.abs(iq_curr) > 10.0) & (rpm_sync > 100.0)
        if np.any(fw_mask):
            print(f"- First visible FW point: RPM ~ {np.min(rpm_sync[fw_mask]):.0f}, Id < -5 A, |Iq| > 10 A")
            print(f"- Most negative Id: {np.min(id_curr):.2f} A")
        else:
            print("- 유의미한 약계자 구간(Id < -5 A, |Iq| > 10 A)이 뚜렷하게 보이지 않습니다.")

    def plot_auto_field_weakening_trend(self, fw_current_limit=None, rpm_bin_width=100.0, min_samples_per_bin=10):
        """
        [자동 약계자 / FW current limit 확인]
        약계자 전류를 Iq별로 직접 지정하지 못하고 max current만 설정하는 구조에서,
        컨트롤러가 실제로 어떤 Id/Iq 벡터를 만드는지 확인한다.

        그래프 구성
        1. RPM별 Id/Iq 평균 추세
        2. RPM별 약계자 전류(-Id)와 설정 limit 비교
        3. Id-Iq operating point를 RPM 색상으로 표시
        """
        if self.data.vel_set is None or self.data.Idq_set is None:
            print("데이터 부족: vel_set, Idq_set이 필요합니다.")
            return

        t_rpm_raw = self.data.vel_set[0, :]
        rpm_raw = self.data.vel_set[1, :]
        t_dq_raw = self.data.Idq_set[0, :]
        id_raw = self.data.Idq_set[1, :]
        iq_raw = self.data.Idq_set[2, :]

        rpm_valid = np.isfinite(t_rpm_raw) & np.isfinite(rpm_raw)
        dq_valid = np.isfinite(t_dq_raw) & np.isfinite(id_raw) & np.isfinite(iq_raw)

        t_rpm = t_rpm_raw[rpm_valid]
        rpm = rpm_raw[rpm_valid]
        t_dq = t_dq_raw[dq_valid]
        id_curr = id_raw[dq_valid]
        iq_curr = iq_raw[dq_valid]

        if len(t_rpm) < 2 or len(t_dq) == 0:
            print("유효한 RPM 또는 Id/Iq 데이터가 부족합니다.")
            return

        rpm_sort = np.argsort(t_rpm)
        t_rpm = t_rpm[rpm_sort]
        rpm = rpm[rpm_sort]

        dq_sort = np.argsort(t_dq)
        t_dq = t_dq[dq_sort]
        id_curr = id_curr[dq_sort]
        iq_curr = iq_curr[dq_sort]

        rpm_sync = np.interp(t_dq, t_rpm, rpm)
        current_mag = np.sqrt(id_curr**2 + iq_curr**2)
        fw_current = np.maximum(-id_curr, 0.0)

        valid = (
            np.isfinite(rpm_sync) &
            np.isfinite(id_curr) &
            np.isfinite(iq_curr) &
            np.isfinite(current_mag) &
            np.isfinite(fw_current) &
            (rpm_sync >= 0) &
            (rpm_sync <= 6000) &
            (id_curr > -1000) & (id_curr < 1000) &
            (iq_curr > -1000) & (iq_curr < 1000) &
            (current_mag < 1000)
        )

        rpm_sync = rpm_sync[valid]
        id_curr = id_curr[valid]
        iq_curr = iq_curr[valid]
        current_mag = current_mag[valid]
        fw_current = fw_current[valid]

        if len(rpm_sync) == 0:
            print("유효한 자동 약계자 분석 데이터가 없습니다.")
            return

        rpm_min = np.floor(np.min(rpm_sync) / rpm_bin_width) * rpm_bin_width
        rpm_max = np.ceil(np.max(rpm_sync) / rpm_bin_width) * rpm_bin_width
        bins = np.arange(rpm_min, rpm_max + rpm_bin_width, rpm_bin_width)

        rpm_centers = []
        id_mean = []
        iq_mean = []
        current_mean = []
        current_p95 = []
        fw_current_mean = []
        fw_current_p95 = []
        fw_ratio_median = []

        for i in range(len(bins) - 1):
            mask = (rpm_sync >= bins[i]) & (rpm_sync < bins[i + 1])
            if np.sum(mask) < min_samples_per_bin:
                continue

            iq_bin = iq_curr[mask]
            id_bin = id_curr[mask]
            ratio_valid = np.abs(iq_bin) > 5.0
            ratio = np.full_like(iq_bin, np.nan, dtype=float)
            ratio[ratio_valid] = -id_bin[ratio_valid] / np.abs(iq_bin[ratio_valid])

            rpm_centers.append(np.mean(rpm_sync[mask]))
            id_mean.append(np.mean(id_bin))
            iq_mean.append(np.mean(iq_bin))
            current_mean.append(np.mean(current_mag[mask]))
            current_p95.append(np.percentile(current_mag[mask], 95))
            fw_current_mean.append(np.mean(fw_current[mask]))
            fw_current_p95.append(np.percentile(fw_current[mask], 95))
            fw_ratio_median.append(np.nanmedian(ratio))

        rpm_centers = np.array(rpm_centers)
        id_mean = np.array(id_mean)
        iq_mean = np.array(iq_mean)
        current_mean = np.array(current_mean)
        current_p95 = np.array(current_p95)
        fw_current_mean = np.array(fw_current_mean)
        fw_current_p95 = np.array(fw_current_p95)
        fw_ratio_median = np.array(fw_ratio_median)

        fig, axs = plt.subplots(2, 2, figsize=(14, 10))

        axs[0, 0].scatter(rpm_sync[::5], id_curr[::5], s=5, alpha=0.12, label='Id Raw')
        axs[0, 0].scatter(rpm_sync[::5], iq_curr[::5], s=5, alpha=0.12, label='Iq Raw')
        axs[0, 0].axhline(0, color='gray', linestyle='--', linewidth=1)
        if fw_current_limit is not None:
            axs[0, 0].axhline(-fw_current_limit, color='orange', linestyle='--', linewidth=1.2, label=f'-{fw_current_limit:.0f} A FW Ref')
        if len(rpm_centers) > 0:
            axs[0, 0].plot(rpm_centers, id_mean, 'b-', linewidth=2.5, label='Id Mean')
            axs[0, 0].plot(rpm_centers, iq_mean, 'r-', linewidth=2.5, label='Iq Mean')
        axs[0, 0].set_title('Auto FW Current Split vs RPM')
        axs[0, 0].set_xlabel('RPM')
        axs[0, 0].set_ylabel('Current (A)')
        axs[0, 0].grid(True)
        axs[0, 0].legend()

        axs[0, 1].scatter(rpm_sync[::5], fw_current[::5], s=5, alpha=0.15, label='FW Current Raw (-Id)')
        if fw_current_limit is not None:
            axs[0, 1].axhline(fw_current_limit, color='orange', linestyle='--', linewidth=2, label=f'{fw_current_limit:.0f} A FW Ref')
        if len(rpm_centers) > 0:
            axs[0, 1].plot(rpm_centers, fw_current_mean, 'k-', linewidth=2.5, label='FW Current Mean')
            axs[0, 1].plot(rpm_centers, fw_current_p95, 'm:', linewidth=2.5, label='FW Current 95%')
        axs[0, 1].set_title('Field Weakening Current (-Id) vs RPM')
        axs[0, 1].set_xlabel('RPM')
        axs[0, 1].set_ylabel('-Id when Id < 0 (A)')
        axs[0, 1].grid(True)
        axs[0, 1].legend()

        sc = axs[1, 0].scatter(iq_curr, id_curr, c=rpm_sync, s=8, alpha=0.35, cmap='turbo')
        axs[1, 0].axhline(0, color='gray', linestyle='--', linewidth=1)
        axs[1, 0].axvline(0, color='gray', linestyle='--', linewidth=1)
        if fw_current_limit is not None:
            axs[1, 0].axhline(-fw_current_limit, color='orange', linestyle='--', linewidth=1.5,
                              label=f'-{fw_current_limit:.0f} A FW Ref')
        axs[1, 0].set_title('Id-Iq Operating Points Colored by RPM')
        axs[1, 0].set_xlabel('Iq (A)')
        axs[1, 0].set_ylabel('Id (A)')
        axs[1, 0].axis('equal')
        axs[1, 0].grid(True)
        axs[1, 0].legend()
        cbar = fig.colorbar(sc, ax=axs[1, 0])
        cbar.set_label('RPM')

        if len(rpm_centers) > 0:
            axs[1, 1].plot(rpm_centers, fw_ratio_median, 'g-o', markersize=4, linewidth=2)
        axs[1, 1].axhline(0, color='gray', linestyle='--', linewidth=1)
        axs[1, 1].set_title('Median Field Weakening Ratio (-Id / |Iq|)')
        axs[1, 1].set_xlabel('RPM')
        axs[1, 1].set_ylabel('-Id / |Iq|')
        axs[1, 1].grid(True)

        plt.tight_layout()
        plt.show()

        print("\n[Auto Field Weakening Trend Summary]")
        print(f"- Total valid points: {len(rpm_sync)}")
        if fw_current_limit is not None:
            print(f"- FW current reference line: {fw_current_limit:.0f} A")
        print(f"- Max |I|: {np.max(current_mag):.2f} A")
        print(f"- 95% |I|: {np.percentile(current_mag, 95):.2f} A")
        print(f"- Most negative Id: {np.min(id_curr):.2f} A")
        print(f"- Max FW current (-Id): {np.max(fw_current):.2f} A")

        if fw_current_limit is not None:
            near_limit = fw_current > fw_current_limit * 0.9
            if np.any(near_limit):
                print(f"- First >90% FW current reference point: RPM ~ {np.min(rpm_sync[near_limit]):.0f}")
            else:
                print("- FW current가 reference의 90%를 넘는 구간이 뚜렷하지 않습니다.")

    def plot_torque_vs_iq(self, iq_bin_width=10.0, min_samples_per_bin=8, use_abs_iq=False, min_abs_iq=5.0):
        """
        [Torque vs Iq]
        실제 토크가 Iq에 대해 얼마나 일관되게 나오는지 확인한다.

        해석 포인트
        - 저속/정상 구간에서 Torque/Iq가 크게 흔들리면 토크 환산 또는 전류 스케일 확인 필요
        - 고RPM/약계자 구간에서 같은 Iq 대비 토크가 줄면 전압 제한 또는 Id 영향 가능성
        - RPM 색상을 같이 보면서 토크-Iq 관계가 속도에 따라 갈라지는지 확인
        """
        if self.data.Idq_set is None or self.data.torqueAct_set is None:
            print("데이터 부족: Idq_set, torqueAct_set이 필요합니다.")
            return

        t_dq_raw = self.data.Idq_set[0, :]
        id_raw = self.data.Idq_set[1, :]
        iq_raw = self.data.Idq_set[2, :]

        t_torque_raw = self.data.torqueAct_set[0, :]
        torque_raw = self.data.torqueAct_set[1, :]

        dq_valid = np.isfinite(t_dq_raw) & np.isfinite(id_raw) & np.isfinite(iq_raw)
        torque_valid = np.isfinite(t_torque_raw) & np.isfinite(torque_raw)

        t_dq = t_dq_raw[dq_valid]
        id_curr = id_raw[dq_valid]
        iq_curr = iq_raw[dq_valid]
        t_torque = t_torque_raw[torque_valid]
        torque = torque_raw[torque_valid]

        if len(t_dq) < 2 or len(t_torque) < 2:
            print("유효한 Id/Iq 또는 Torque 데이터가 부족합니다.")
            return

        dq_sort = np.argsort(t_dq)
        t_dq = t_dq[dq_sort]
        id_curr = id_curr[dq_sort]
        iq_curr = iq_curr[dq_sort]

        torque_sort = np.argsort(t_torque)
        t_torque = t_torque[torque_sort]
        torque = torque[torque_sort]

        torque_sync = np.interp(t_dq, t_torque, torque)

        if self.data.vel_set is not None:
            t_rpm_raw = self.data.vel_set[0, :]
            rpm_raw = self.data.vel_set[1, :]
            rpm_valid = np.isfinite(t_rpm_raw) & np.isfinite(rpm_raw)
            t_rpm = t_rpm_raw[rpm_valid]
            rpm = rpm_raw[rpm_valid]
            if len(t_rpm) >= 2:
                rpm_sort = np.argsort(t_rpm)
                rpm_sync = np.interp(t_dq, t_rpm[rpm_sort], rpm[rpm_sort])
            else:
                rpm_sync = np.full_like(t_dq, np.nan, dtype=float)
        else:
            rpm_sync = np.full_like(t_dq, np.nan, dtype=float)

        valid = (
            np.isfinite(iq_curr) &
            np.isfinite(id_curr) &
            np.isfinite(torque_sync) &
            (np.abs(iq_curr) >= min_abs_iq) &
            (iq_curr > -1000) & (iq_curr < 1000) &
            (id_curr > -1000) & (id_curr < 1000) &
            (torque_sync > -100) & (torque_sync < 300)
        )

        iq_curr = iq_curr[valid]
        id_curr = id_curr[valid]
        torque_sync = torque_sync[valid]
        rpm_sync = rpm_sync[valid]

        if len(iq_curr) == 0:
            print("유효한 Torque-Iq 데이터가 없습니다.")
            return

        if use_abs_iq:
            iq_plot = np.abs(iq_curr)
            x_label = '|Iq| (A)'
            kt = torque_sync / np.maximum(iq_plot, 1e-6)
        else:
            iq_plot = iq_curr
            x_label = 'Iq (A)'
            kt = torque_sync / iq_curr

        iq_min = np.floor(np.min(iq_plot) / iq_bin_width) * iq_bin_width
        iq_max = np.ceil(np.max(iq_plot) / iq_bin_width) * iq_bin_width
        bins = np.arange(iq_min, iq_max + iq_bin_width, iq_bin_width)

        iq_centers = []
        torque_mean = []
        torque_p50 = []
        torque_p95 = []
        kt_median = []
        counts = []

        for i in range(len(bins) - 1):
            mask = (iq_plot >= bins[i]) & (iq_plot < bins[i + 1])
            if np.sum(mask) < min_samples_per_bin:
                continue

            iq_centers.append(np.mean(iq_plot[mask]))
            torque_mean.append(np.mean(torque_sync[mask]))
            torque_p50.append(np.percentile(torque_sync[mask], 50))
            torque_p95.append(np.percentile(torque_sync[mask], 95))
            kt_median.append(np.nanmedian(kt[mask]))
            counts.append(np.sum(mask))

        iq_centers = np.array(iq_centers)
        torque_mean = np.array(torque_mean)
        torque_p50 = np.array(torque_p50)
        torque_p95 = np.array(torque_p95)
        kt_median = np.array(kt_median)
        counts = np.array(counts)

        fig, axs = plt.subplots(2, 2, figsize=(14, 10))

        sc = axs[0, 0].scatter(iq_plot, torque_sync, c=rpm_sync, s=8, alpha=0.35, cmap='turbo')
        if len(iq_centers) > 0:
            axs[0, 0].plot(iq_centers, torque_mean, 'k-', linewidth=2.5, label='Mean Torque')
            axs[0, 0].plot(iq_centers, torque_p95, 'r--', linewidth=2, label='95% Torque')
        axs[0, 0].set_title('Torque vs Iq')
        axs[0, 0].set_xlabel(x_label)
        axs[0, 0].set_ylabel('Actual Torque (Nm)')
        axs[0, 0].grid(True)
        axs[0, 0].legend()
        cbar = fig.colorbar(sc, ax=axs[0, 0])
        cbar.set_label('RPM')

        if len(iq_centers) > 0:
            axs[0, 1].plot(iq_centers, kt_median, 'b-o', markersize=4, linewidth=2)
        axs[0, 1].set_title('Median Apparent Torque Constant')
        axs[0, 1].set_xlabel(x_label)
        axs[0, 1].set_ylabel('Torque / Iq (Nm/A)')
        axs[0, 1].grid(True)

        axs[1, 0].scatter(rpm_sync, kt, s=8, alpha=0.25)
        axs[1, 0].set_title('Torque / Iq vs RPM')
        axs[1, 0].set_xlabel('RPM')
        axs[1, 0].set_ylabel('Torque / Iq (Nm/A)')
        axs[1, 0].grid(True)

        if len(iq_centers) > 0:
            axs[1, 1].bar(iq_centers, counts, width=iq_bin_width * 0.8)
        axs[1, 1].set_title('Sample Count per Iq Bin')
        axs[1, 1].set_xlabel(x_label)
        axs[1, 1].set_ylabel('Count')
        axs[1, 1].grid(True)

        plt.tight_layout()
        plt.show()

        print("\n[Torque vs Iq Summary]")
        print(f"- Total valid points: {len(iq_plot)}")
        print(f"- Iq bins analyzed: {len(iq_centers)}")
        print(f"- Median Torque/Iq: {np.nanmedian(kt):.4f} Nm/A")
        print(f"- 95% Torque: {np.percentile(torque_sync, 95):.2f} Nm")

    def plot_motor_control_constraints(
        self,
        current_limit=100.0,
        ld=None,
        lq=None,
        psi_f=None,
        rs=0.0,
        voltage_limit=None,
        rpm_levels=None,
        pole_pairs=1,
    ):
        """
        [Motor Control Constraints]
        Id-Iq operating point 위에 전류 제한원, MTPA 곡선, 전압 제한 타원을 겹쳐 본다.

        Parameters
        ----------
        current_limit : float
            전류 제한원 반지름[A]. 예: 100A ref.
        ld, lq : float
            d/q축 인덕턴스[H]. MTPA와 전압 제한 타원 계산에 필요.
        psi_f : float
            영구자석 flux linkage[Wb]. MTPA와 전압 제한 타원 계산에 필요.
        rs : float
            상저항[ohm]. 모르면 0으로 두고 전압 제한 타원을 근사한다.
        voltage_limit : float
            전압 제한[V]. None이면 Vcap 중앙값 / sqrt(3)으로 근사한다.
        rpm_levels : list[float]
            전압 제한 타원을 그릴 RPM 목록. None이면 로그 RPM 분위수로 자동 선택한다.
        pole_pairs : int
            기계 RPM을 전기 각속도로 바꿀 때 쓰는 pole pair 수.
            만약 vel_set이 이미 electrical RPM이면 1로 둔다.
        """
        if self.data.Idq_set is None:
            print("데이터 부족: Idq_set이 필요합니다.")
            return

        t_dq_raw = self.data.Idq_set[0, :]
        id_raw = self.data.Idq_set[1, :]
        iq_raw = self.data.Idq_set[2, :]

        dq_valid = np.isfinite(t_dq_raw) & np.isfinite(id_raw) & np.isfinite(iq_raw)
        t_dq = t_dq_raw[dq_valid]
        id_curr = id_raw[dq_valid]
        iq_curr = iq_raw[dq_valid]

        if len(t_dq) == 0:
            print("유효한 Id/Iq 데이터가 없습니다.")
            return

        rpm_sync = np.full_like(t_dq, np.nan, dtype=float)
        if self.data.vel_set is not None:
            t_rpm_raw = self.data.vel_set[0, :]
            rpm_raw = self.data.vel_set[1, :]
            rpm_valid = np.isfinite(t_rpm_raw) & np.isfinite(rpm_raw)
            t_rpm = t_rpm_raw[rpm_valid]
            rpm = rpm_raw[rpm_valid]
            if len(t_rpm) >= 2:
                rpm_sort = np.argsort(t_rpm)
                rpm_sync = np.interp(t_dq, t_rpm[rpm_sort], rpm[rpm_sort])

        valid = (
            np.isfinite(id_curr) &
            np.isfinite(iq_curr) &
            (id_curr > -1000) & (id_curr < 1000) &
            (iq_curr > -1000) & (iq_curr < 1000)
        )

        id_curr = id_curr[valid]
        iq_curr = iq_curr[valid]
        rpm_sync = rpm_sync[valid]

        if len(id_curr) == 0:
            print("유효한 Id/Iq operating point가 없습니다.")
            return

        motor_params_ready = (
            ld is not None and
            lq is not None and
            psi_f is not None and
            np.isfinite(ld) and
            np.isfinite(lq) and
            np.isfinite(psi_f)
        )

        if voltage_limit is None and self.data.Vcap_set is not None:
            vcap = self.data.Vcap_set[1, :]
            vcap = vcap[np.isfinite(vcap)]
            if len(vcap) > 0:
                voltage_limit = np.nanmedian(vcap) / np.sqrt(3.0)

        if rpm_levels is None and np.any(np.isfinite(rpm_sync)):
            rpm_for_levels = rpm_sync[np.isfinite(rpm_sync) & (rpm_sync > 0)]
            if len(rpm_for_levels) > 0:
                rpm_levels = np.percentile(rpm_for_levels, [50, 75, 90])

        max_data_current = np.nanpercentile(np.sqrt(id_curr**2 + iq_curr**2), 99)
        plot_limit = max(current_limit * 1.15, max_data_current * 1.15, 10.0)
        axis_min = -plot_limit
        axis_max = plot_limit

        fig, axs = plt.subplots(2, 2, figsize=(14, 11))

        # 1. Id-Iq operating map + constraints
        # Standard motor-control d-q plane: x = Id, y = Iq.
        sc = axs[0, 0].scatter(id_curr, iq_curr, c=rpm_sync, s=8, alpha=0.35, cmap='turbo')
        theta = np.linspace(0, 2 * np.pi, 361)
        axs[0, 0].plot(
            current_limit * np.cos(theta),
            current_limit * np.sin(theta),
            'k--',
            linewidth=1.8,
            label=f'Current Limit {current_limit:.0f} A'
        )

        mtpa_id = None
        mtpa_iq = None
        if motor_params_ready:
            delta_l = ld - lq
            mtpa_id = []
            mtpa_iq = []
            current_grid = np.linspace(1.0, current_limit, 160)

            for current in current_grid:
                if abs(delta_l) < 1e-12:
                    id_candidates = np.array([0.0])
                else:
                    id_candidates = np.linspace(-current, 0.0, 300)

                iq_candidates = np.sqrt(np.maximum(current**2 - id_candidates**2, 0.0))
                torque_score = psi_f * iq_candidates + delta_l * id_candidates * iq_candidates
                best_idx = np.argmax(torque_score)
                mtpa_id.append(id_candidates[best_idx])
                mtpa_iq.append(iq_candidates[best_idx])

            mtpa_id = np.array(mtpa_id)
            mtpa_iq = np.array(mtpa_iq)
            axs[0, 0].plot(mtpa_id, mtpa_iq, 'g-', linewidth=2.5, label='MTPA')

        voltage_ready = motor_params_ready and voltage_limit is not None and rpm_levels is not None
        if voltage_ready:
            id_grid = np.linspace(axis_min, axis_max, 260)
            iq_grid = np.linspace(axis_min, axis_max, 260)
            iq_mesh, id_mesh = np.meshgrid(iq_grid, id_grid)

            for rpm_level in rpm_levels:
                omega_e = 2 * np.pi * rpm_level / 60.0 * pole_pairs
                vd = rs * id_mesh - omega_e * lq * iq_mesh
                vq = rs * iq_mesh + omega_e * (ld * id_mesh + psi_f)
                v_mag = np.sqrt(vd**2 + vq**2)
                contour = axs[0, 0].contour(
                    id_mesh,
                    iq_mesh,
                    v_mag,
                    levels=[voltage_limit],
                    linewidths=1.4,
                    linestyles=':',
                )
                if len(contour.allsegs) > 0 and len(contour.allsegs[0]) > 0:
                    axs[0, 0].plot([], [], linestyle=':', linewidth=1.4,
                                   label=f'Voltage Limit @ {rpm_level:.0f} RPM')

        axs[0, 0].axhline(0, color='gray', linestyle='--', linewidth=1)
        axs[0, 0].axvline(0, color='gray', linestyle='--', linewidth=1)
        axs[0, 0].set_xlim(axis_min, axis_max)
        axs[0, 0].set_ylim(axis_min, axis_max)
        axs[0, 0].set_aspect('equal', adjustable='box')
        axs[0, 0].set_title('Id-Iq Map with Current / Voltage / MTPA Constraints')
        axs[0, 0].set_xlabel('Id (A)')
        axs[0, 0].set_ylabel('Iq (A)')
        axs[0, 0].grid(True)
        axs[0, 0].legend(loc='best')
        cbar = fig.colorbar(sc, ax=axs[0, 0])
        cbar.set_label('RPM')

        # 2. Current magnitude vs RPM
        current_mag = np.sqrt(id_curr**2 + iq_curr**2)
        axs[0, 1].scatter(rpm_sync, current_mag, s=8, alpha=0.25)
        axs[0, 1].axhline(current_limit, color='k', linestyle='--', linewidth=1.8, label=f'{current_limit:.0f} A Limit')
        axs[0, 1].set_title('Current Magnitude vs RPM')
        axs[0, 1].set_xlabel('RPM')
        axs[0, 1].set_ylabel('sqrt(Id^2 + Iq^2) (A)')
        axs[0, 1].grid(True)
        axs[0, 1].legend()

        # 3. Required voltage check
        if voltage_ready:
            omega_e_sync = 2 * np.pi * rpm_sync / 60.0 * pole_pairs
            vd_sync = rs * id_curr - omega_e_sync * lq * iq_curr
            vq_sync = rs * iq_curr + omega_e_sync * (ld * id_curr + psi_f)
            v_req = np.sqrt(vd_sync**2 + vq_sync**2)
            voltage_mask = np.isfinite(rpm_sync) & np.isfinite(v_req)

            axs[1, 0].scatter(rpm_sync[voltage_mask], v_req[voltage_mask], s=8, alpha=0.25)
            axs[1, 0].axhline(voltage_limit, color='orange', linestyle='--', linewidth=1.8,
                              label=f'Voltage Limit {voltage_limit:.1f} V')
            axs[1, 0].set_title('Estimated Voltage Requirement vs RPM')
            axs[1, 0].set_xlabel('RPM')
            axs[1, 0].set_ylabel('Voltage magnitude (V)')
            axs[1, 0].grid(True)
            axs[1, 0].legend()
        else:
            axs[1, 0].axis('off')
            axs[1, 0].text(
                0.05,
                0.5,
                'Voltage ellipse skipped.\nProvide ld, lq, psi_f and voltage_limit\n(or Vcap data for voltage_limit estimate).',
                transform=axs[1, 0].transAxes,
                fontsize=12,
                va='center'
            )

        # 4. MTPA Id command trend
        if mtpa_id is not None and mtpa_iq is not None:
            axs[1, 1].plot(mtpa_id, mtpa_iq, 'g-', linewidth=2.5, label='MTPA')
            axs[1, 1].scatter(id_curr, iq_curr, s=8, alpha=0.15, label='Actual Operating Points')
            axs[1, 1].axhline(0, color='gray', linestyle='--', linewidth=1)
            axs[1, 1].axvline(0, color='gray', linestyle='--', linewidth=1)
            axs[1, 1].set_title('MTPA Curve vs Actual Id-Iq')
            axs[1, 1].set_xlabel('Id (A)')
            axs[1, 1].set_ylabel('Iq (A)')
            axs[1, 1].grid(True)
            axs[1, 1].legend()
        else:
            axs[1, 1].axis('off')
            axs[1, 1].text(
                0.05,
                0.5,
                'MTPA skipped.\nProvide ld, lq, and psi_f.',
                transform=axs[1, 1].transAxes,
                fontsize=12,
                va='center'
            )

        plt.tight_layout()
        plt.show()

        print("\n[Motor Control Constraints Summary]")
        print(f"- Total valid Id/Iq points: {len(id_curr)}")
        print(f"- Current limit reference: {current_limit:.1f} A")
        print(f"- Max current magnitude: {np.nanmax(current_mag):.2f} A")
        if motor_params_ready:
            print(f"- Motor params: Ld={ld}, Lq={lq}, psi_f={psi_f}, Rs={rs}, pole_pairs={pole_pairs}")
        else:
            print("- MTPA/voltage ellipse require motor params: ld, lq, psi_f.")
        if voltage_limit is not None:
            print(f"- Voltage limit reference: {voltage_limit:.2f} V")

    def plot_empirical_mtpa_from_log(
        self,
        current_limit=200.0,
        current_bin_width=10.0,
        min_samples_per_bin=3,
        rpm_max=1500.0,
        rpm_min=0.0,
        min_torque=5.0,
        top_percentile=90.0,
    ):
        """
        [Empirical MTPA-like Analysis]
        모터 파라미터 없이 실제 로그에서 Torque per Ampere가 높은 Id/Iq 운전점을 찾는다.

        이 함수는 이론 MTPA가 아니라 로그 기반 경험적 추세이다.
        전압 제한/약계자 영향을 줄이기 위해 기본값은 저속 영역(rpm <= rpm_max)만 본다.
        """
        if self.data.Idq_set is None or self.data.torqueAct_set is None:
            print("데이터 부족: Idq_set, torqueAct_set이 필요합니다.")
            return

        t_dq_raw = self.data.Idq_set[0, :]
        id_raw = self.data.Idq_set[1, :]
        iq_raw = self.data.Idq_set[2, :]

        t_torque_raw = self.data.torqueAct_set[0, :]
        torque_raw = self.data.torqueAct_set[1, :]

        dq_valid = np.isfinite(t_dq_raw) & np.isfinite(id_raw) & np.isfinite(iq_raw)
        torque_valid = np.isfinite(t_torque_raw) & np.isfinite(torque_raw)

        t_dq = t_dq_raw[dq_valid]
        id_curr = id_raw[dq_valid]
        iq_curr = iq_raw[dq_valid]
        t_torque = t_torque_raw[torque_valid]
        torque = torque_raw[torque_valid]

        if len(t_dq) < 2 or len(t_torque) < 2:
            print("유효한 Id/Iq 또는 Torque 데이터가 부족합니다.")
            return

        dq_sort = np.argsort(t_dq)
        t_dq = t_dq[dq_sort]
        id_curr = id_curr[dq_sort]
        iq_curr = iq_curr[dq_sort]

        torque_sort = np.argsort(t_torque)
        t_torque = t_torque[torque_sort]
        torque = torque[torque_sort]

        torque_sync = np.interp(t_dq, t_torque, torque)

        rpm_sync = np.full_like(t_dq, np.nan, dtype=float)
        if self.data.vel_set is not None:
            t_rpm_raw = self.data.vel_set[0, :]
            rpm_raw = self.data.vel_set[1, :]
            rpm_valid = np.isfinite(t_rpm_raw) & np.isfinite(rpm_raw)
            t_rpm = t_rpm_raw[rpm_valid]
            rpm = rpm_raw[rpm_valid]
            if len(t_rpm) >= 2:
                rpm_sort = np.argsort(t_rpm)
                rpm_sync = np.interp(t_dq, t_rpm[rpm_sort], rpm[rpm_sort])

        current_mag = np.sqrt(id_curr**2 + iq_curr**2)
        torque_per_amp = torque_sync / np.maximum(current_mag, 1e-6)

        valid = (
            np.isfinite(id_curr) &
            np.isfinite(iq_curr) &
            np.isfinite(torque_sync) &
            np.isfinite(current_mag) &
            np.isfinite(torque_per_amp) &
            (current_mag > 1.0) &
            (current_mag <= current_limit * 1.5) &
            (torque_sync >= min_torque) &
            (id_curr > -1000) & (id_curr < 1000) &
            (iq_curr > -1000) & (iq_curr < 1000)
        )

        if np.any(np.isfinite(rpm_sync)):
            valid = valid & np.isfinite(rpm_sync) & (rpm_sync >= rpm_min) & (rpm_sync <= rpm_max)

        id_curr = id_curr[valid]
        iq_curr = iq_curr[valid]
        torque_sync = torque_sync[valid]
        rpm_sync = rpm_sync[valid]
        current_mag = current_mag[valid]
        torque_per_amp = torque_per_amp[valid]

        if len(id_curr) == 0:
            print("유효한 empirical MTPA 분석 데이터가 없습니다.")
            return

        current_max = np.ceil(np.max(current_mag) / current_bin_width) * current_bin_width
        bins = np.arange(0, current_max + current_bin_width, current_bin_width)

        emp_id = []
        emp_iq = []
        emp_current = []
        emp_tpa = []
        emp_torque = []
        counts = []

        for i in range(len(bins) - 1):
            mask = (current_mag >= bins[i]) & (current_mag < bins[i + 1])
            if np.sum(mask) < min_samples_per_bin:
                continue

            tpa_bin = torque_per_amp[mask]
            threshold = np.percentile(tpa_bin, top_percentile)
            top_mask_local = tpa_bin >= threshold

            id_bin = id_curr[mask][top_mask_local]
            iq_bin = iq_curr[mask][top_mask_local]
            current_bin = current_mag[mask][top_mask_local]
            torque_bin = torque_sync[mask][top_mask_local]
            tpa_top = tpa_bin[top_mask_local]

            emp_id.append(np.mean(id_bin))
            emp_iq.append(np.mean(iq_bin))
            emp_current.append(np.mean(current_bin))
            emp_torque.append(np.mean(torque_bin))
            emp_tpa.append(np.mean(tpa_top))
            counts.append(np.sum(mask))

        emp_id = np.array(emp_id)
        emp_iq = np.array(emp_iq)
        emp_current = np.array(emp_current)
        emp_torque = np.array(emp_torque)
        emp_tpa = np.array(emp_tpa)
        counts = np.array(counts)

        fig, axs = plt.subplots(2, 2, figsize=(14, 11))

        sc = axs[0, 0].scatter(id_curr, iq_curr, c=torque_per_amp, s=8, alpha=0.35, cmap='turbo')
        theta = np.linspace(0, 2 * np.pi, 361)
        axs[0, 0].plot(
            current_limit * np.cos(theta),
            current_limit * np.sin(theta),
            'k--',
            linewidth=1.8,
            label=f'Current Limit {current_limit:.0f} A'
        )
        if len(emp_id) > 0:
            axs[0, 0].plot(emp_id, emp_iq, 'r-o', markersize=4, linewidth=2.3,
                           label=f'Empirical MTPA-like ({top_percentile:.0f}% T/A)')
        axs[0, 0].axhline(0, color='gray', linestyle='--', linewidth=1)
        axs[0, 0].axvline(0, color='gray', linestyle='--', linewidth=1)
        axs[0, 0].set_aspect('equal', adjustable='box')
        axs[0, 0].set_title('Empirical Torque per Ampere Map')
        axs[0, 0].set_xlabel('Id (A)')
        axs[0, 0].set_ylabel('Iq (A)')
        axs[0, 0].grid(True)
        axs[0, 0].legend(loc='best')
        cbar = fig.colorbar(sc, ax=axs[0, 0])
        cbar.set_label('Torque / Current (Nm/A)')

        axs[0, 1].scatter(current_mag, torque_per_amp, c=rpm_sync, s=8, alpha=0.35, cmap='viridis')
        if len(emp_current) > 0:
            axs[0, 1].plot(emp_current, emp_tpa, 'r-o', markersize=4, linewidth=2.3,
                           label='Best trend by current bin')
        axs[0, 1].set_title('Torque per Ampere vs Current Magnitude')
        axs[0, 1].set_xlabel('Current magnitude (A)')
        axs[0, 1].set_ylabel('Torque / Current (Nm/A)')
        axs[0, 1].grid(True)
        if len(emp_current) > 0:
            axs[0, 1].legend(loc='best')

        axs[1, 0].scatter(rpm_sync, torque_per_amp, s=8, alpha=0.3)
        axs[1, 0].set_title('Torque per Ampere vs RPM')
        axs[1, 0].set_xlabel('RPM')
        axs[1, 0].set_ylabel('Torque / Current (Nm/A)')
        axs[1, 0].grid(True)

        if len(emp_current) > 0:
            axs[1, 1].bar(emp_current, counts, width=current_bin_width * 0.8)
        axs[1, 1].set_title('Sample Count per Current Bin')
        axs[1, 1].set_xlabel('Current magnitude (A)')
        axs[1, 1].set_ylabel('Count')
        axs[1, 1].grid(True)

        plt.tight_layout()
        plt.show()

        print("\n[Empirical MTPA-like Summary]")
        print(f"- Total valid points: {len(id_curr)}")
        print(f"- RPM filter: {rpm_min:.0f} <= RPM <= {rpm_max:.0f}")
        print(f"- Current bins analyzed: {len(emp_current)}")
        print(f"- Median Torque/Current: {np.nanmedian(torque_per_amp):.4f} Nm/A")
        print(f"- Best observed Torque/Current: {np.nanmax(torque_per_amp):.4f} Nm/A")
        if len(emp_current) > 0:
            best_idx = np.argmax(emp_tpa)
            print(f"- Best empirical point: Id={emp_id[best_idx]:.2f} A, Iq={emp_iq[best_idx]:.2f} A")
            print(f"  Current={emp_current[best_idx]:.2f} A, Torque/Current={emp_tpa[best_idx]:.4f} Nm/A")
        else:
            print("- Not enough samples per current bin. Try a larger current_bin_width or lower min_samples_per_bin.")
