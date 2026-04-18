# log fetcher

# import module

import numpy as np
import struct
import os

# setting const

rawAcc2g = 4/512
mls2sec = 1e-3
rawSpd2kph = 1.852 / 100

# setting var

class VehicleLog:
    """Class for data"""
    def __init__(self):
        """변수 초기화"""
        self.source_set     = None
        self.CAN_set        = None  # ID 17
        self.key_set        = None

        self.torqueAct_set  = None  # ID 0A, 0D (공유)
        self.currAct_set    = None  # ID 0A
        self.vel_set        = None  # ID 0A
        
        self.ud_set         = None  # ID 0B
        self.uq_set         = None  # ID 0B
        self.Vmod_set       = None  # ID 0B
        self.Vcap_set       = None  # ID 0B
            
        self.L_set          = None  # ID 0C
        self.Vlim_set       = None  # ID 0C
        self.Iflux_set      = None  # ID 0C
        self.Iqmax_set      = None  # ID 0C
            
        self.motorTemp_set  = None  # ID 0D
        self.Ibatt_set      = None  # ID 0D
        self.Tdmd_set       = None  # ID 0D

        self.Vtgt_set       = None  # ID 0E
        self.Idq_set        = None  # ID 0E (Id, Iq)
        self.acc_set        = None  # Source 5
        self.gpsPos_set     = None  # Source 6 Key 0
        self.gpsVec_set     = None  # Source 6 Key 1

        self.cnt_source = 0
        self.cnt_CAN = 0
        self.cnt_key = 0
        self.cnt_torqueAct = 0
        self.cnt_currAct = 0
        self.cnt_vel = 0
        self.cnt_ud = 0
        self.cnt_uq = 0
        self.cnt_Vmod = 0
        self.cnt_Vcap = 0
        self.cnt_L = 0
        self.cnt_Vlim = 0
        self.cnt_Iflux = 0
        self.cnt_Iqmax = 0
        self.cnt_motorTemp = 0
        self.cnt_Ibatt = 0
        self.cnt_Tdmd = 0
        self.cnt_Vtgt = 0
        self.cnt_Idq = 0
        self.cnt_acc = 0
        self.cnt_gpsPos = 0
        self.cnt_gpsVec = 0

    def _read_val(self, fid, fmt, size):
        chunk = fid.read(size)
        if not chunk or len(chunk) < size: return None
        return struct.unpack(fmt, chunk)[0]
    
    def allocate_or_extend(self, n_points, is_first_file):
        """
        n_points: 이번 파일에서 읽을 데이터 개수 (cnt_tot_sub)
        is_first_file: 첫 번째 파일인지 여부 (0이 첫 파일) (True/False)
        """
        new_source      = np.full((1, n_points), np.nan)
        new_CAN         = np.full((8, n_points), np.nan)
        new_key         = np.full((1, n_points), np.nan)

        new_torqueAct   = np.full((2, n_points), np.nan)
        new_currAct     = np.full((2, n_points), np.nan)
        new_vel         = np.full((2, n_points), np.nan)
        
        new_ud          = np.full((2, n_points), np.nan)
        new_uq          = np.full((2, n_points), np.nan)
        new_Vmod        = np.full((2, n_points), np.nan)
        new_Vcap        = np.full((2, n_points), np.nan)
        
        new_L           = np.full((2, n_points), np.nan)
        new_Vlim        = np.full((2, n_points), np.nan)
        new_Iflux       = np.full((2, n_points), np.nan)
        new_Iqmax       = np.full((2, n_points), np.nan)
        
        new_motorTemp   = np.full((2, n_points), np.nan)
        new_Ibatt       = np.full((2, n_points), np.nan)
        new_Tdmd        = np.full((2, n_points), np.nan)
        
        new_Vtgt        = np.full((2, n_points), np.nan)
        new_Idq         = np.full((3, n_points), np.nan)
        new_acc         = np.full((4, n_points), np.nan)
        new_gpsPos      = np.full((3, n_points), np.nan)
        new_gpsVec      = np.full((3, n_points), np.nan)

        if (is_first_file == True):
            self.source_set     = new_source   
            self.CAN_set        = new_CAN
            self.key_set        = new_key
            self.torqueAct_set  = new_torqueAct
            self.currAct_set    = new_currAct
            self.vel_set        = new_vel

            self.ud_set         = new_ud
            self.uq_set         = new_uq
            self.Vmod_set       = new_Vmod
            self.Vcap_set       = new_Vcap

            self.L_set          = new_L
            self.Vlim_set       = new_Vlim
            self.Iflux_set      = new_Iflux
            self.Iqmax_set      = new_Iqmax

            self.motorTemp_set  = new_motorTemp
            self.Ibatt_set      = new_Ibatt
            self.Tdmd_set       = new_Tdmd

            self.Vtgt_set       = new_Vtgt
            self.Idq_set        = new_Idq
            self.acc_set        = new_acc
            self.gpsPos_set     = new_gpsPos
            self.gpsVec_set     = new_gpsVec
        else:
            self.source_set     = np.concatenate((self.source_set, new_source),axis=1)
            self.CAN_set        = np.concatenate((self.CAN_set, new_CAN),axis=1)
            self.key_set        = np.concatenate((self.key_set, new_key),axis=1)
            self.torqueAct_set  = np.concatenate((self.torqueAct_set, new_torqueAct),axis=1)
            self.currAct_set    = np.concatenate((self.currAct_set, new_currAct),axis=1)
            self.vel_set        = np.concatenate((self.vel_set, new_vel),axis=1)

            self.ud_set         = np.concatenate((self.ud_set, new_ud),axis=1)
            self.uq_set         = np.concatenate((self.uq_set, new_uq),axis=1)
            self.Vmod_set       = np.concatenate((self.Vmod_set, new_Vmod),axis=1)
            self.Vcap_set       = np.concatenate((self.Vcap_set, new_Vcap),axis=1)

            self.L_set          = np.concatenate((self.L_set, new_L),axis=1)
            self.Vlim_set       = np.concatenate((self.Vlim_set, new_Vlim),axis=1)
            self.Iflux_set      = np.concatenate((self.Iflux_set, new_Iflux),axis=1)
            self.Iqmax_set      = np.concatenate((self.Iqmax_set, new_Iqmax),axis=1)

            self.motorTemp_set  = np.concatenate((self.motorTemp_set, new_motorTemp),axis=1)
            self.Ibatt_set      = np.concatenate((self.Ibatt_set, new_Ibatt),axis=1)
            self.Tdmd_set       = np.concatenate((self.Tdmd_set, new_Tdmd),axis=1)

            self.Vtgt_set       = np.concatenate((self.Vtgt_set, new_Vtgt),axis=1)
            self.Idq_set        = np.concatenate((self.Idq_set, new_Idq),axis=1)
            self.acc_set        = np.concatenate((self.acc_set, new_acc),axis=1)
            self.gpsPos_set     = np.concatenate((self.gpsPos_set, new_gpsPos),axis=1)
            self.gpsVec_set     = np.concatenate((self.gpsVec_set, new_gpsVec),axis=1)
    
    def parse_file(self, filepath, timestamp_offset=0):
        mls2sec = 0.001
        rawAcc2g = 4.0 / 512.0     # 스케일링 팩터 확인 필요
        rawSpd2kph = 1.0   # 스케일링 팩터 확인 필요

        print(f"DEBUG: Parsing {os.path.basename(filepath)}")
        
        with open(filepath, 'rb') as fid:
            while True:
                # 1. Timestamp (ubit32 -> <I)
                ts_raw = self._read_val(fid, '<I', 4)
                if ts_raw is None: break # EOF
                
                timestamp_tmp = ts_raw * mls2sec + timestamp_offset

                # 2. Headers (ubit8 -> <B)
                level = self._read_val(fid, '<B', 1) # Error / Data / etc..
                src   = self._read_val(fid, '<B', 1) # source
                key   = self._read_val(fid, '<B', 1) # key
                chk   = self._read_val(fid, '<B', 1) # checksum


                # print(f"src: {src}, key: {key}, cnt: {self.cnt_source}")

                # 공통 데이터 저장
                if self.cnt_source < self.source_set.shape[1]:
                    self.source_set[0, self.cnt_source] = src
                    self.cnt_source += 1
                
                if self.cnt_key < self.key_set.shape[1]:
                    self.key_set[0, self.cnt_key] = key
                    self.cnt_key += 1

                # 3. Source별 분기 (Switch-Case)
                if src == 0: # SYS
                    fid.read(8) # Skip 64bit
                
                elif src == 1: # CAN
                    """
                    this is for mk3
                    if key == 17:
                        # ubit16 -> <H (Unsigned Short)
                        busV = self._read_val(fid, '<H', 2)
                        busA = self._read_val(fid, '<H', 2)
                        phA  = self._read_val(fid, '<H', 2)
                        rpm  = self._read_val(fid, '<H', 2)
                        
                        fid.read(8) # ubit64 skip
                        
                        # ubit8 -> <B
                        cntl_T = self._read_val(fid, '<B', 1)
                        mtr_T  = self._read_val(fid, '<B', 1)
                        throt  = self._read_val(fid, '<B', 1)
                        fid.read(5) # ubit40 skip

                        # 데이터 채워넣기 (현재 카운터 위치인 열(Column)에 저장)
                        idx = self.cnt_CAN
                        self.CAN_set[0, idx] = timestamp_tmp
                        self.CAN_set[1, idx] = busV * 0.1
                        self.CAN_set[2, idx] = busA * 0.1 - 3200
                        self.CAN_set[3, idx] = phA * 0.1 - 3200
                        self.CAN_set[4, idx] = rpm
                        self.CAN_set[5, idx] = cntl_T
                        self.CAN_set[6, idx] = mtr_T - 40
                        self.CAN_set[7, idx] = throt
                        
                        self.cnt_CAN += 1
                    """
                    # for mk4
                    if key == 10: # ID 0A
                        # int16 -> <h (Signed Short), int32 -> <i (Signed Int)
                        trq_act  = (1/16) * self._read_val(fid, '<h', 2)
                        curr_act = self._read_val(fid, '<h', 2)
                        vel      = self._read_val(fid, '<i', 4)

                        idx = self.cnt_torqueAct
                        self.torqueAct_set[:, idx] = [timestamp_tmp, trq_act]
                        self.cnt_torqueAct += 1
                        
                        idx = self.cnt_currAct
                        self.currAct_set[:, idx] = [timestamp_tmp, curr_act]
                        self.cnt_currAct += 1

                        idx = self.cnt_vel
                        self.vel_set[:, idx] = [timestamp_tmp, vel]
                        self.cnt_vel += 1

                    elif key == 11: # ID 0B
                        ud   = (1/16) * self._read_val(fid, '<h', 2)
                        uq   = (1/16) * self._read_val(fid, '<h', 2)
                        vmod = (100/256) * self._read_val(fid, '<H', 2) # uint16
                        vcap = (1/16) * self._read_val(fid, '<H', 2)    # uint16

                        idx = self.cnt_ud
                        self.ud_set[:, idx] = [timestamp_tmp, ud]
                        self.cnt_ud += 1

                        idx = self.cnt_uq
                        self.uq_set[:, idx] = [timestamp_tmp, uq]
                        self.cnt_uq += 1

                        idx = self.cnt_Vmod
                        self.Vmod_set[:, idx] = [timestamp_tmp, vmod]
                        self.cnt_Vmod += 1
                        
                        idx = self.cnt_Vcap
                        self.Vcap_set[:, idx] = [timestamp_tmp, vcap]
                        self.cnt_Vcap += 1

                    elif key == 12: # ID 0C
                        L     = self._read_val(fid, '<H', 2) # uint16
                        vlim  = self._read_val(fid, '<h', 2) # int16
                        iflux = self._read_val(fid, '<h', 2)
                        iqmax = self._read_val(fid, '<h', 2)

                        idx = self.cnt_L
                        self.L_set[:, idx] = [timestamp_tmp, L]
                        self.cnt_L += 1

                        idx = self.cnt_Vlim
                        self.Vlim_set[:, idx] = [timestamp_tmp, vlim]
                        self.cnt_Vlim += 1

                        idx = self.cnt_Iflux
                        self.Iflux_set[:, idx] = [timestamp_tmp, iflux]
                        self.cnt_Iflux += 1

                        idx = self.cnt_Iqmax
                        self.Iqmax_set[:, idx] = [timestamp_tmp, iqmax]
                        self.cnt_Iqmax += 1

                    elif key == 13: # ID 0D
                        tmtr  = self._read_val(fid, '<h', 2)
                        ibatt = (1/16) * self._read_val(fid, '<h', 2)
                        tdmd  = (1/16) * self._read_val(fid, '<h', 2)
                        tact  = (1/16) * self._read_val(fid, '<h', 2)

                        idx = self.cnt_motorTemp
                        self.motorTemp_set[:, idx] = [timestamp_tmp, tmtr]
                        self.cnt_motorTemp += 1

                        idx = self.cnt_Ibatt
                        self.Ibatt_set[:, idx] = [timestamp_tmp, ibatt]
                        self.cnt_Ibatt += 1

                        idx = self.cnt_Tdmd
                        self.Tdmd_set[:, idx] = [timestamp_tmp, tdmd]
                        self.cnt_Tdmd += 1

                        # [중요] torqueAct_set을 여기서도 재사용 (MATLAB 로직)
                        idx = self.cnt_torqueAct
                        self.torqueAct_set[:, idx] = [timestamp_tmp, tact]
                        self.cnt_torqueAct += 1

                    elif key == 14: # ID 0E
                        vtgt = self._read_val(fid, '<i', 4) # int32
                        id_val = (1/16) * self._read_val(fid, '<h', 2)
                        iq_val = (1/16) * self._read_val(fid, '<h', 2)

                        idx = self.cnt_Vtgt
                        self.Vtgt_set[:, idx] = [timestamp_tmp, vtgt]
                        self.cnt_Vtgt += 1

                        idx = self.cnt_Idq
                        self.Idq_set[:, idx] = [timestamp_tmp, id_val, iq_val]
                        self.cnt_Idq += 1

                    else:
                        fid.read(8) # Other CAN keys skip

                elif src == 2: # DIGITAL
                    fid.read(8)
                elif src == 3: # ANALOG
                    fid.read(8)
                elif src == 4: # PULSE
                    fid.read(8)

                elif src == 5: # ACCELEROMETER
                    # bit16 -> <h (Signed Short 가정)
                    ax = self._read_val(fid, '<h', 2)
                    ay = self._read_val(fid, '<h', 2)
                    az = self._read_val(fid, '<h', 2)
                    fid.read(2) # skip

                    idx = self.cnt_acc
                    self.acc_set[0, idx] = timestamp_tmp
                    self.acc_set[1, idx] = ax * rawAcc2g
                    self.acc_set[2, idx] = ay * rawAcc2g
                    self.acc_set[3, idx] = az * rawAcc2g
                    self.cnt_acc += 1

                elif src == 6: # GPS
                    if key == 0: # GPS_POS
                        # bit32 -> <i (Signed Int)
                        lat = self._read_val(fid, '<i', 4)
                        lon = self._read_val(fid, '<i', 4)

                        idx = self.cnt_gpsPos
                        self.gpsPos_set[0, idx] = timestamp_tmp
                        self.gpsPos_set[1, idx] = lon / 10000000.0
                        self.gpsPos_set[2, idx] = lat / 10000000.0
                        self.cnt_gpsPos += 1

                    elif key == 1: # GPS_VEC
                        spd = self._read_val(fid, '<i', 4)
                        course = self._read_val(fid, '<i', 4)
                        
                        idx = self.cnt_gpsVec
                        self.gpsVec_set[0, idx] = timestamp_tmp
                        self.gpsVec_set[1, idx] = spd * rawSpd2kph
                        self.gpsVec_set[2, idx] = course
                        self.cnt_gpsVec += 1

                    elif key == 2: # GPS_TIME
                        fid.read(8)
                    else:
                        fid.read(8)

                else:
                    fid.read(8) # Unknown source
    
    def split_laps(self, start_radius_m=1, min_lap_time_sec=30):
        """
        전체 데이터를 랩(Lap) 단위로 쪼개서 반환하는 함수
        - start_radius_m: 스타트 라인 반경 (미터) - GPS 오차 고려 넉넉하게
        - min_lap_time_sec: 최소 랩타임 (이 시간 안에는 다시 카운트 안 함)
        """
        if self.gpsPos_set is None: return []

        # 1. GPS 데이터 준비 (NMEA 변환 포함)
        t_gps = self.gpsPos_set[0, :]
        lon_raw = self.gpsPos_set[1, :]
        lat_raw = self.gpsPos_set[2, :]

        # (NMEA 변환 로직 재사용)
        if np.mean(lon_raw) > 180:
            lon = np.floor(lon_raw/100) + (lon_raw%100)/60
            lat = np.floor(lat_raw/100) + (lat_raw%100)/60
        else:
            lon, lat = lon_raw, lat_raw

        # 2. 스타트 라인 정의 (첫 번째 유효 좌표)
        # (0,0 노이즈 제외하고 첫 지점을 시작점으로)
        valid_idx = np.where(lon > 1.0)[0]
        if len(valid_idx) == 0: return []
        
        start_lon = lon[valid_idx[0]]
        start_lat = lat[valid_idx[0]]
        
        # 3. 랩 분할 루프
        laps = []
        current_lap_start_idx = 0
        last_pass_time = -min_lap_time_sec # 초반 통과 허용

        # 위도/경도 1도 차이는 약 111km (약식 계산)
        # 거리(m) ~= sqrt(dLat^2 + dLon^2) * 111000
        deg_threshold = start_radius_m / 111000.0 

        for i in range(valid_idx[0] + 10, len(t_gps)):
            t_curr = t_gps[i]
            
            # 스타트 라인과의 거리 계산 (유클리드 거리)
            dist_deg = np.sqrt((lon[i] - start_lon)**2 + (lat[i] - start_lat)**2)
            
            # [조건 1] 스타트 라인 반경 안에 들어왔고
            # [조건 2] 마지막 통과 후 최소 시간이 지났다면 -> New Lap!
            if (dist_deg < deg_threshold) and (t_curr - last_pass_time > min_lap_time_sec):
                
                # 이전 랩 저장 (인덱스 슬라이싱)
                lap_data = {
                    'idx_start': current_lap_start_idx,
                    'idx_end': i,
                    'time_duration': t_curr - last_pass_time if len(laps) > 0 else 0
                }
                laps.append(lap_data)
                
                # 상태 업데이트
                current_lap_start_idx = i
                last_pass_time = t_curr
                
                print(f"Lap {len(laps)} Found! Time: {t_curr:.1f}s")

        print(f"총 {len(laps)}개의 랩을 찾았습니다.")
        return laps

# file select

def setfilename(fnametmp, group='2nd Test Week'):
    '''set file path from the Logs directory.'''
    if os.path.isabs(fnametmp):
        return fnametmp

    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, 'Logs', group)
    return os.path.join(log_dir, fnametmp)


#---------------test---------------

if __name__ == "__main__":
    testsett=VehicleLog()


    def exfunc():
        """this function to show docstring
        this is poop"""
    print(exfunc.__doc__)