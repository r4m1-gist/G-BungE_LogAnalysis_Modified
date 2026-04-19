# main

from logFetcher import *
from logPostProcessor import LogVisualizer

log_data = VehicleLog()

# [2nd Test Week]
#
#     '2000-00-00 13-45-48.log',
#     '2025-08-16 22-56-30.log',
#     '2025-08-17 00-33-28.log',  # Laps: 1/0/0, Remarks: 등 선 빠져서 바로 들어왔음
#     '2025-08-17 00-38-47.log',  # ERR
#     '2025-08-17 00-51-51.log',
#     '2025-08-17 00-54-18.log',
#     '2025-08-17 01-27-27.log',
#     '2025-08-17 02-06-14.log',  # Laps: 1/3/1, Remarks: 최고 기록: 1:20.605, CAN 데이터 끊김
#     '2025-08-17 02-21-45.log',  # 정크데이터
#     '2025-08-17 02-22-57.log',  # 정크데이터
#     '2025-08-17 03-43-11.log',
#     '2025-08-17 03-55-58.log',
#     '2025-08-17 04-32-36.log',
#     '2025-08-17 05-27-32.log',
#
# ------------------ 이 이후로 Iq, Id 파악 가능 ------------------
#
#     '2025-08-17 05-31-36.log',  # Laps: 1/2/1, Remarks: 최고 기록: 1:21.004
#     '2025-08-17 05-44-54.log',  # Laps: 1/0/0, Remarks: 스핀함, 결승선 근처 GPS 튐
#     '2025-08-17 07-08-04.log',
#     '2025-08-17 07-13-44.log',  # 경민-1(+30kg) 세팅 위와 동일
#     '2025-08-17 07-37-33.log',  # 가속@80n.m. -> 60m
#     '2025-08-17 07-44-39.log',  # 가속@120n.m. -> 65m
#     '2025-08-17 07-57-25.log',  # ERR
#     '2025-08-17 08-13-48.log',  # 경민-2(+30kg) 최대 토크 깎기
#     '2025-08-17 08-24-29.log',  # 동적 성능
#     '2025-08-17 11-14-56.log',  # 정크 데이터
#     '2025-08-17 11-16-12.log',  # 동적성능 아닌것 같음
#     '2025-08-18 11-51-28.log',
#     '2025-08-18 11-52-55.log',
#     '2025-08-18 11-55-28.log',
#     '2025-08-18 11-58-29.log',
#     '2025-08-18 12-01-13.log',
#
# [Main Competition]
#
#     '2025-08-29 08-37-35.log',
#     '2025-08-29 08-56-47.log',  # Laps: 0/0/0, Remarks: 가속/제동
#     '2025-08-29 09-01-23.log',  # Laps: 0/0/0, Remarks: 동적 성능 1
#     '2025-08-29 09-04-01.log',  # Laps: 0/0/0, Remarks: 동적 성능 1(이어짐)
#     '2025-08-29 09-05-08.log',  # Laps: 0/0/0, Remarks: 동적 성능 1(이어짐)
#     '2025-08-29 09-09-27.log',  # Laps: 0/0/0, Remarks: 동적 성능 2
#     '2025-08-29 09-11-42.log',  # Laps: 0/0/0, Remarks: 동적 성능 2(이어짐)
#     '2025-08-30 01-58-39.log',  # 2일차 온도 터진거(테스트주행)
#     '2025-08-30 02-03-35.log',
#     '2025-08-30 02-04-07.log',
#     '2025-08-30 06-08-15.log',  # 오토크로스
#     '2025-08-30 06-20-21.log',
#     '2025-08-30 08-32-10.log',  # 예선
#     '2025-08-30 09-18-20.log',
#     '2025-08-31 00-33-04.log',
#     '2025-08-31 01-09-36.log',
#     '2025-08-31 01-11-26.log',
#     '2025-08-31 01-13-33.log',  # 본선1 (충격으로 꺼짐)
#     '2025-08-31 01-33-25.log',  # 본선2 (재시작 후 피트인)
#     '2025-08-31 01-48-43.log',  # 본선3 (김경민 10분)
#     '2025-08-31 02-03-58.log',  # 본선4 (임동윤, 임동윤, 김경민)
#     '2025-08-31 03-07-25.log',

# 여기서 분석할 로그 파일을 선택하면 됨.
# log_group은 아래 두 폴더 이름 중 하나로 맞추면 됨.
# - '2nd Test Week'
# - 'Main Competition'
log_group = '2nd Test Week'
log_files = [
    '2025-08-17 05-31-36.log',
    '2025-08-17 05-44-54.log',
    '2025-08-17 00-33-28.log',
]

# 이어지는 데이터는 같은 리스트에 순서대로 넣을 것.
file_list = [setfilename(fname, group=log_group) for fname in log_files]

for idx, fname in enumerate(file_list):
    # ... (파일 열고 n_points 계산하는 로직) ...
    print(f"\nINFO: entering size search loop{idx}... ")
    cnt_tot_sub = 0 #count total 몇 줄인지
    try:
        with open(fname, 'rb') as fid:
            while True:
                read_tmp1 = fid.read(8) #8 bytes 읽기
                
                if not read_tmp1: #비어있는 경우 false. 따라서 read_tmp1(현재 읽고 있는 줄)이 비어있다면 중단한다는 의미
                    break
                
                read_tmp2 = fid.read(8) 

                cnt_tot_sub += 1

        print(f"INFO: size search loop finished. {cnt_tot_sub}")

    except FileNotFoundError:
        print(f"Error: File {fname} not found.")
        continue # 파일 없으면 다음 파일로 넘어감

    is_first = (idx == 0)
    log_data.allocate_or_extend(cnt_tot_sub, is_first)
    log_data.parse_file(fname)



if __name__ == "__main__":    
    # 보고 싶은 그래프 함수의 주석을 해제하면 됨.

    visualizer = LogVisualizer(log_data)
    
    '''
    아래부터 #visualizer. 로 시작하는 함수의 주석 해제를 하면 아래 주석의 설명하는 그래프 그림을 받을 수 있음.
    '''

    # visualizer.plot_gps_only()
    
    # visualizer.plot_torque_performance()
    # 토크 응답성 확인
    
    # visualizer.plot_vector_control()
    # 벡터 제어(Id/Iq) 상태 확인

    # visualizer.plot_field_weakening()
    # 약계자 제어

    # visualizer.plot_gps_velocity_and_slip()
    # gps 속도 slip ratio

    # visualizer.plot_torque_vs_rpm()
    # rpm 변화에 따른 토크 변화

    # visualizer.plot_temperature_profile()
    # 시간에 따른 모터 온도 변화 그래프

    # visualizer.plot_torque_vs_temperature()
    # 온도 변화에 따른 토크 변화

    # visualizer.plot_current_vs_torque_efficiency()
    # 효율 분석: 토크 대비 소모 전류량

    # visualizer.plot_current_efficiency()
    # 배터리 전류 vs 모터 상전류 비교 (인버터 효율 확인)

    # visualizer.plot_advanced_id_iq_analysis()
    # [고급 분석] Id/Iq 데이터를 통한 기어비, 토크맵, 주행전략 분석
    '''
    1. Gear Ratio Check: RPM vs Id (약계자 진입 시점 확인)
    2. Saturation Check: Iq vs Torque (자기 포화 확인)
    3. Operating Point: Id vs Iq Circle (주행 전략 확인)
    '''

    # visualizer.plot_vehicle_dynamics()
    # 가속도 센서를 활용한 차량 거동 분석

    # visualizer.plot_vehicle_dynamics_lpf()
    # [수정] NaN 데이터 제거 후 필터링 적용
    
    # visualizer.plot_vehicle_dynamics_mv_avg()
    # [수정] 3초 이동 평균(Moving Average) 적용

    # log_data.split_laps()
    # 데이터 랩 분할 

    # visualizer.plot_gps_gforce_map()   
    # GPS G-Force Heatmap

    # visualizer.plot_laps_slideshow()
    # 키보드 좌우 방향키로 랩을 넘겨보는 기능 

    # ================= Cooling Validation Set =================
    # 냉각 성능, 열부하, 저부하 냉각 추세를 확인할 때 아래 묶음을 순서대로 켜면 됨.

    # visualizer.plot_power_and_temp()
    # [냉각 성능 분석용] 입력 전력(P = V*I)과 모터 온도 비교 그래프
    
    # visualizer.analyze_moving_rms()
    # 고급 전력 분석 30초 이동 RMS (Moving RMS) 그래프 순간적인 피크가 아니라, '지속적인 열부하'가 가장 심했던 구간을 찾음

    # visualizer.plot_temp_rise_vs_power()
    # 냉각 성능 상관관계 분석
    '''
    X축: 온도 상승률 (degC / 10sec), Y축: 소비 전력 (kW)
    이 그래프의 기울기나 절편을 통해 냉각 시스템의 한계를 파악할 수 있습니다.
    '''

    # visualizer.plot_temp_slope_trend()
    # [정밀 냉각 분석] Rolling Linear Regression (선형 회귀 기울기)
    '''
    X축: 온도 상승 기울기 (degC/sec) -> 추세선의 Slope, Y축: 해당 구간 평균 소비 전력 (kW)
    '''

    # visualizer.plot_thermal_path()
    # 특정 온도(예: 60도) 이상인 '주행 구간' 데이터만 분석

    # visualizer.plot_thermal_path_v2()
    '''
    [Update v2] 전력(Power) 기반 필터링 적용
    - 2.5kW 미만 데이터(피트인, 탄력주행) 제거
    - 순수 '부하 주행 시'의 열적 특성만 분석
    '''

    # visualizer.plot_power_vs_temp_slope()
    # [Final Analysis] 입력 전력(VI) vs 온도 상승률
    '''
    - X축: 온도 변화 기울기 (degC / 10s)
    - Y축: 평균 입력 전력 (kW)
    - Filter: 2.5kW 미만 저부하 구간 제외
    '''

    # visualizer.plot_cooling_trend_regression()
    # [순수 냉각 성능 정밀 분석]
    '''
    - 조건: 전력 소모 1kW 미만 (거의 정차/탄력주행)
    - X축: 현재 모터 온도 (°C)
    - Y축: 온도 변화율 (°C / 10s) -> 식는 속도
    - 추세선: 뉴턴의 냉각 법칙에 따른 냉각 계수(k) 추정
    '''

    # visualizer.plot_cooling_intercept()
    # [순수 냉각 구간 분석] Power vs Temp Slope (Low Power Only)
    '''
    - 조건: 전력 < 1kW (정차/탄력주행)
    - 목적: Y=0(전력 0)일 때의 X절편(냉각 속도) 확인
    '''

    # visualizer.analyze_thermal_lag()
    # [시스템 식별] 최적의 열 전달 지연 시간(Thermal Lag) 찾기
    '''
    - 전력(입력)과 온도상승(출력) 사이의 시간차(phi)를 스캔하여
    - 상관관계(Correlation)가 가장 높은 '진짜 반응 시간'을 찾아냅니다.
    '''

    # visualizer.plot_cooling_trend_high_temp()
    '''
    [냉각 분석 v2] 고온 구간(60도 이상)에서의 순수 냉각 속도 분석
    저온(포화) 영역 데이터 배제 -> 진짜 냉각 성능(기울기) 확인
    '''

    # ===========================================================

    # ================= Torque Map Validation Set =================

    # visualizer.plot_power_vs_rpm()

    # visualizer.plot_tn_curve_envelope() 
    # T-N Curve Envelope (토크-속도 곡선 봉우리)
    '''
    대표 토크값은 상위 95%값 사용
    대표 RPM값은 그 구간 평균 RPM 사용
    '''

    # visualizer.plot_id_iq_vs_rpm(rpm_bin_width=100.0, min_samples_per_bin=10)
    # RPM 기준 Id/Iq 전류 추세 확인

    # visualizer.plot_auto_field_weakening_trend(fw_current_limit=150.0, rpm_bin_width=100.0, min_samples_per_bin=10)
    # 약계자 max current 설정값 예시를 넣고, 컨트롤러가 자동 분배한 Id/Iq operating point 확인

    # visualizer.plot_torque_vs_iq(iq_bin_width=10.0, min_samples_per_bin=8, use_abs_iq=False)
    # 실제 토크와 Iq 관계 및 Torque/Iq 추세 확인

    # visualizer.plot_motor_control_constraints(current_limit=200.0)
    # Id-Iq operating point, 전류 제한원, MTPA, 전압 제한 타원 시각화
    # MTPA/전압 타원은 ld, lq, psi_f, voltage_limit 값을 넣어야 정확히 표시됨

    # visualizer.plot_empirical_mtpa_from_log(current_limit=200.0, current_bin_width=10.0, min_samples_per_bin=3, rpm_max=1500.0)
    # 모터 파라미터 없이 저속 로그에서 Torque/Current가 높은 Id-Iq 운전점 추세 확인
    
    # =============================================================
