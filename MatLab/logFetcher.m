

% log fetcher

% 2차 사전테스트
fname = '2025-08-29 08-56-47.log'; flg_cnti = 0; % Laps: 0/0/0, Remarks: 가속/제동
% fname = '2025-08-29 09-01-23.log'; flg_cnti = 0; % Laps: 0/0/0, Remarks: 동적 성능 1
% fname = '2025-08-29 09-04-01.log'; flg_cnti = 1; % Laps: 0/0/0, Remarks: 동적 성능 1(이어짐)
% fname = '2025-08-29 09-05-08.log'; flg_cnti = 1; % Laps: 0/0/0, Remarks: 동적 성능 1(이어짐)
% fname = '2025-08-29 09-09-27.log'; flg_cnti = 0; % Laps: 0/0/0, Remarks: 동적 성능 2
% fname = '2025-08-29 09-11-42.log'; flg_cnti = 1; % Laps: 0/0/0, Remarks: 동적 성능 2(이어짐)
% fname = '.log'; % Laps: 0/0/0, Remarks:

% flg_cnti = 0 : 일반적인 첫 실행
% flg_cnti = 1 : 0으로 한번 돌리고 다른 걸 이어서 돌리고 싶을 때(e.g. 차량이 껐다 켜진 경우)

rawAcc2g = 4/512;
mls2sec = 1e-3;
rawSpd2kph = 1.852 / 100;


fid = fopen(fname, 'r');
fprintf("\nINFO: entering size search loop... \n");
cnt_tot_sub = 0;
while ~feof(fid)
    read_tmp1 = fread(fid, 1, 'bit64');
    if isempty(read_tmp1); break; end
    read_tmp2 = fread(fid, 1, 'bit64');

    cnt_tot_sub = cnt_tot_sub + 1;
end
fprintf("INFO: size search loop finished. \n");
fclose(fid);



if ( flg_cnti ~= 1 )
    timestamp_offset = 0;

    source_set = nan(1, cnt_tot_sub);
    cnt_source = 1;
    
    CAN_set = nan(8, cnt_tot_sub);
    cnt_CAN = 1;
    
    key_set = nan(1, cnt_tot_sub);
    cnt_key = 1;
    
    
    % 물리량별 저장 공간 선언
    torqueAct_set   = nan(2, cnt_tot_sub); cnt_torqueAct = 1;
    currAct_set     = nan(2, cnt_tot_sub); cnt_currAct = 1;
    vel_set         = nan(2, cnt_tot_sub); cnt_vel = 1;
    
    ud_set          = nan(2, cnt_tot_sub); cnt_ud = 1;
    uq_set          = nan(2, cnt_tot_sub); cnt_uq = 1;
    Vmod_set        = nan(2, cnt_tot_sub); cnt_Vmod = 1;
    Vcap_set        = nan(2, cnt_tot_sub); cnt_Vcap = 1;
    
    L_set           = nan(2, cnt_tot_sub); cnt_L = 1;
    Vlim_set        = nan(2, cnt_tot_sub); cnt_Vlim = 1;
    Iflux_set       = nan(2, cnt_tot_sub); cnt_Iflux = 1;
    Iqmax_set       = nan(2, cnt_tot_sub); cnt_Iqmax = 1;
    
    motorTemp_set   = nan(2, cnt_tot_sub); cnt_motorTemp = 1;
    Ibatt_set       = nan(2, cnt_tot_sub); cnt_Ibatt = 1;
    Tdmd_set        = nan(2, cnt_tot_sub); cnt_Tdmd = 1;
    
    Vtgt_set        = nan(2, cnt_tot_sub); cnt_Vtgt = 1;
    Idq_set        = nan(3, cnt_tot_sub); cnt_Idq = 1;
    
    
    acc_set = nan(4, cnt_tot_sub);
    cnt_acc = 1;
    
    gpsPos_set = nan(3, cnt_tot_sub);
    cnt_gpsPos = 1;
    
    gpsVec_set = nan(3, cnt_tot_sub);
    cnt_gpsVec = 1;

else
    timestamp_offset = timestamp_mem;

    source_set = [source_set, nan(1, cnt_tot_sub)];
    CAN_set    = [CAN_set, nan(8, cnt_tot_sub)];
    key_set    = [key_set, nan(1, cnt_tot_sub)];


    % 물리량별 저장 공간 확장
    torqueAct_set   = [torqueAct_set, nan(2, cnt_tot_sub)];
    currAct_set     = [currAct_set, nan(2, cnt_tot_sub)];
    vel_set         = [vel_set, nan(2, cnt_tot_sub)];

    ud_set          = [ud_set, nan(2, cnt_tot_sub)];
    uq_set          = [uq_set, nan(2, cnt_tot_sub)];
    Vmod_set        = [Vmod_set, nan(2, cnt_tot_sub)];
    Vcap_set        = [Vcap_set, nan(2, cnt_tot_sub)];

    L_set           = [L_set, nan(2, cnt_tot_sub)];
    Vlim_set        = [Vlim_set, nan(2, cnt_tot_sub)];
    Iflux_set       = [Iflux_set, nan(2, cnt_tot_sub)];
    Iqmax_set       = [Iqmax_set, nan(2, cnt_tot_sub)];

    motorTemp_set   = [motorTemp_set, nan(2, cnt_tot_sub)];
    Ibatt_set       = [Ibatt_set, nan(2, cnt_tot_sub)];
    Tdmd_set        = [Tdmd_set, nan(2, cnt_tot_sub)];

    Vtgt_set        = [Vtgt_set, nan(2, cnt_tot_sub)];
    Idq_set         = [Idq_set, nan(3, cnt_tot_sub)];


    acc_set         = [acc_set, nan(4, cnt_tot_sub)];
    gpsPos_set      = [gpsPos_set, nan(3, cnt_tot_sub)];
    gpsVec_set      = [gpsVec_set, nan(3, cnt_tot_sub)];
end



fid = fopen(fname, 'r');
cnt_tot = 0;
bckSP = 0;
fprintf("\nINFO: entering main search loop... \n");
while ~feof(fid)
    timestamp_tmp = fread(fid, 1, 'ubit32', 'ieee-le');
    if isempty(timestamp_tmp); break; end

    timestamp_tmp = timestamp_tmp * mls2sec + timestamp_offset;
    timestamp_mem = timestamp_tmp;

    level_tmp = fread(fid, 1, 'ubit8', 'ieee-le');
    source_tmp = fread(fid, 1, 'ubit8', 'ieee-le');
    key_tmp = fread(fid, 1, 'ubit8', 'ieee-le');
    checksum_tmp = fread(fid, 1, 'ubit8', 'ieee-le');
    
    
    source_set(cnt_source) = source_tmp;
    cnt_source = cnt_source + 1;

    key_set(cnt_key) = key_tmp;
    cnt_key = cnt_key + 1;
    
    
    switch source_tmp
        case 0  % SYS
            read_tmp = fread(fid, 1, 'ubit64', 'ieee-le');
        
        case 1  % CAN
            switch key_tmp
                case 17
                    busV_tmp = fread(fid, 1, 'ubit16', 'ieee-le'); % BUS Voltage
                    busA_tmp = fread(fid, 1, 'ubit16', 'ieee-le'); % Bus Current
                    phaseA_tmp = fread(fid, 1, 'ubit16', 'ieee-le'); % Phase Current
                    RPM_tmp = fread(fid, 1, 'ubit16', 'ieee-le'); % Rotor RPM

                    fread(fid, 1, 'ubit64', 'ieee-le');
                    cntl_T_tmp = fread(fid, 1, 'ubit8', 'ieee-le'); % Contorller Temperature
                    motor_T_tmp = fread(fid, 1, 'ubit8', 'ieee-le'); % Motor Temperature
                    throttle_tmp = fread(fid, 1, 'ubit8', 'ieee-le'); % Throttle
                    read_tmp = fread(fid, 1, 'ubit40', 'ieee-le');

                    CAN_set(:, cnt_CAN) = [...
                        timestamp_tmp; ...
                        busV_tmp*0.1; ...
                        busA_tmp*0.1 - 3200; ...
                        phaseA_tmp*0.1 - 3200; ...
                        RPM_tmp; ...
                        cntl_T_tmp; ...
                        motor_T_tmp - 40; ...
                        throttle_tmp];
                    cnt_CAN = cnt_CAN + 1;
                    cnt_tot = cnt_tot + 1;

                case 10  % ID 0A
                    % error("ERR");
                    Torq_act_tmp = (1/16) * fread(fid, 1, 'int16', 'ieee-le');
                    Curr_act_tmp = fread(fid, 1, 'int16', 'ieee-le');   % (스케일 필요 시 적용)
                    Vel_tmp      = fread(fid, 1, 'int32', 'ieee-le');
        
                    torqueAct_set(:, cnt_torqueAct) = [timestamp_tmp; Torq_act_tmp]; cnt_torqueAct = cnt_torqueAct+1;
                    currAct_set(:, cnt_currAct)     = [timestamp_tmp; Curr_act_tmp]; cnt_currAct = cnt_currAct+1;
                    vel_set(:, cnt_vel)             = [timestamp_tmp; Vel_tmp];     cnt_vel = cnt_vel+1;
        
                case 11  % ID 0B
                    % error("ERR");
                    ud_tmp   = (1/16) * fread(fid, 1, 'int16', 'ieee-le');
                    uq_tmp   = (1/16) * fread(fid, 1, 'int16', 'ieee-le');
                    Vmod_tmp = (100/256) * fread(fid, 1, 'uint16', 'ieee-le');
                    Vcap_tmp = (1/16) * fread(fid, 1, 'uint16', 'ieee-le');
        
                    ud_set(:, cnt_ud)     = [timestamp_tmp; ud_tmp];   cnt_ud = cnt_ud+1;
                    uq_set(:, cnt_uq)     = [timestamp_tmp; uq_tmp];   cnt_uq = cnt_uq+1;
                    Vmod_set(:, cnt_Vmod) = [timestamp_tmp; Vmod_tmp]; cnt_Vmod = cnt_Vmod+1;
                    Vcap_set(:, cnt_Vcap) = [timestamp_tmp; Vcap_tmp]; cnt_Vcap = cnt_Vcap+1;
        
                case 12  % ID 0C
                    % error("ERR");
                    L_tmp     = fread(fid, 1, 'uint16', 'ieee-le'); % scaling (1e6/2^24) or (1e6/2^20)
                    Vlim_tmp  = fread(fid, 1, 'int16', 'ieee-le');
                    Iflux_tmp = fread(fid, 1, 'int16', 'ieee-le');
                    Iqmax_tmp = fread(fid, 1, 'int16', 'ieee-le');
        
                    L_set(:, cnt_L)         = [timestamp_tmp; L_tmp];     cnt_L = cnt_L+1;
                    Vlim_set(:, cnt_Vlim)   = [timestamp_tmp; Vlim_tmp];  cnt_Vlim = cnt_Vlim+1;
                    Iflux_set(:, cnt_Iflux) = [timestamp_tmp; Iflux_tmp]; cnt_Iflux = cnt_Iflux+1;
                    Iqmax_set(:, cnt_Iqmax) = [timestamp_tmp; Iqmax_tmp]; cnt_Iqmax = cnt_Iqmax+1;
        
                case 13  % ID 0D
                    % error("ERR");
                    Tmtr_tmp  = fread(fid, 1, 'int16', 'ieee-le');
                    Ibatt_tmp = (1/16) * fread(fid, 1, 'int16', 'ieee-le');
                    Tdmd_tmp  = (1/16) * fread(fid, 1, 'int16', 'ieee-le');
                    Tact_tmp  = (1/16) * fread(fid, 1, 'int16', 'ieee-le');
        
                    motorTemp_set(:, cnt_motorTemp) = [timestamp_tmp; Tmtr_tmp]; cnt_motorTemp=cnt_motorTemp+1;
                    Ibatt_set(:, cnt_Ibatt)         = [timestamp_tmp; Ibatt_tmp]; cnt_Ibatt=cnt_Ibatt+1;
                    Tdmd_set(:, cnt_Tdmd)           = [timestamp_tmp; Tdmd_tmp]; cnt_Tdmd=cnt_Tdmd+1;
                    torqueAct_set(:, cnt_torqueAct) = [timestamp_tmp; Tact_tmp]; cnt_torqueAct=cnt_torqueAct+1; % 같은 이름 물리량 재사용
        
                case 14  % ID 0E
                    % error("ERR");
                    Vtgt_tmp = fread(fid, 1, 'int32', 'ieee-le');
                    Id_tmp = (1/16)*fread(fid, 1, 'int16', 'ieee-le');
                    Iq_tmp = (1/16)*fread(fid, 1, 'int16', 'ieee-le');
        
                    Vtgt_set(:, cnt_Vtgt) = [timestamp_tmp; Vtgt_tmp]; cnt_Vtgt=cnt_Vtgt+1;
                    Idq_set(:, cnt_Idq) = [timestamp_tmp; Id_tmp; Iq_tmp]; cnt_Idq=cnt_Idq+1;
        
                otherwise
                    read_tmp = fread(fid, 1, 'bit64', 'ieee-le');
            end

        case 2  % DIGITAL
            read_tmp = fread(fid, 1, 'bit64', 'ieee-le');

        case 3  % ANALOG
            read_tmp = fread(fid, 1, 'bit64', 'ieee-le');

        case 4  % PULSE
            read_tmp = fread(fid, 1, 'bit64', 'ieee-le');

        case 5  % ACCELEROMETER
            accX_tmp = fread(fid, 1, 'bit16', 'ieee-le');
            accY_tmp = fread(fid, 1, 'bit16', 'ieee-le');
            accZ_tmp = fread(fid, 1, 'bit16', 'ieee-le');
            fread(fid, 1, 'bit16', 'ieee-le');
            
            acc_set(:, cnt_acc) = [timestamp_tmp; accX_tmp * rawAcc2g; accY_tmp * rawAcc2g; accZ_tmp * rawAcc2g];
            cnt_acc = cnt_acc + 1;

        case 6  % GPS
            switch key_tmp
                case 0  % GPS_POS
                    latitude_tmp = fread(fid, 1, 'bit32', 'ieee-le');
                    longitude_tmp = fread(fid, 1, 'bit32', 'ieee-le');
                    
                    gpsPos_set(:, cnt_gpsPos) = [timestamp_tmp; longitude_tmp / 10000; latitude_tmp / 10000];
                    cnt_gpsPos = cnt_gpsPos + 1;
                    
                case 1  % GPS_VEC
                    speed_tmp = fread(fid, 1, 'bit32', 'ieee-le');
                    courseAngle_tmp = fread(fid, 1, 'bit32', 'ieee-le');

                    gpsVec_set(:, cnt_gpsVec) = [timestamp_tmp; speed_tmp * rawSpd2kph; courseAngle_tmp];
                    cnt_gpsVec = cnt_gpsVec + 1;
                    
                case 2  % GPS_TIME
                    read_tmp = fread(fid, 1, 'bit64', 'ieee-le');

                otherwise
                    read_tmp = fread(fid, 1, 'bit64', 'ieee-le');
                    fprintf("\nERR: invalid key = %d with source = %d \n", key_tmp, source_tmp); bckSP = 0;
            end

        otherwise
            read_tmp = fread(fid, 1, 'bit64', 'ieee-le');
            fprintf("\nERR: invalid source = %d, Possible values are 0:6 \n", source_tmp); bckSP = 0;
    end
    
    cnt_tot = cnt_tot + 1;
    prg = 100*cnt_tot/cnt_tot_sub;
    
    fprintf(repmat('\b', 1, bckSP));
    if ( bckSP == 0 ); fprintf("progress (%%): "); end
    bckSP = fprintf("%.3f", prg);
end
fprintf("\nINFO: main search loop finished. \n");
fclose(fid);



torqueAct_set = rmmissing(torqueAct_set, 2);
currAct_set   = rmmissing(currAct_set, 2);
vel_set       = rmmissing(vel_set, 2);

ud_set        = rmmissing(ud_set, 2);
uq_set        = rmmissing(uq_set, 2);
Vmod_set      = rmmissing(Vmod_set, 2);
Vcap_set      = rmmissing(Vcap_set, 2);

L_set         = rmmissing(L_set, 2);
Vlim_set      = rmmissing(Vlim_set, 2);
Iflux_set     = rmmissing(Iflux_set, 2);
Iqmax_set     = rmmissing(Iqmax_set, 2);

motorTemp_set = rmmissing(motorTemp_set, 2);
Ibatt_set     = rmmissing(Ibatt_set, 2);
Tdmd_set      = rmmissing(Tdmd_set, 2);

Vtgt_set      = rmmissing(Vtgt_set, 2);
Idq_set      = rmmissing(Idq_set, 2);

CAN_set = rmmissing(CAN_set, 2);
acc_set = rmmissing(acc_set, 2);
gpsPos_set = rmmissing(gpsPos_set, 2);
gpsVec_set = rmmissing(gpsVec_set, 2);



torqueAct_set = makeUnique(torqueAct_set);
currAct_set   = makeUnique(currAct_set);
vel_set       = makeUnique(vel_set);

ud_set   = makeUnique(ud_set);
uq_set   = makeUnique(uq_set);
Vmod_set = makeUnique(Vmod_set);
Vcap_set = makeUnique(Vcap_set);

L_set     = makeUnique(L_set);
Vlim_set  = makeUnique(Vlim_set);
Iflux_set = makeUnique(Iflux_set);
Iqmax_set = makeUnique(Iqmax_set);

motorTemp_set = makeUnique(motorTemp_set);
Ibatt_set     = makeUnique(Ibatt_set);
Tdmd_set      = makeUnique(Tdmd_set);

Vtgt_set = makeUnique(Vtgt_set);
Idq_set   = makeUnique(Idq_set);

CAN_set = makeUnique(CAN_set);
acc_set   = makeUnique(acc_set);
gpsPos_set = makeUnique(gpsPos_set);
gpsVec_set = makeUnique(gpsVec_set);

% [gpsPos_set(2:3, :), idx_gpsPos_filled] = filloutliers( gpsPos_set(2:3, :), 'linear', 2 );

if ( size(Vcap_set, 2) >= size(Ibatt_set, 2) ) && ( size(Ibatt_set, 2) >= 2 )
    Pbatt_set = Vcap_set;
    Pbatt_set(2, :) = Vcap_set(2, :) .* interp1(Ibatt_set(1, :), Ibatt_set(2, :), Vcap_set(1, :));
elseif ( size(Vcap_set, 2) < size(Ibatt_set, 2) ) && ( size(Vcap_set, 2) >= 2 )
    Pbatt_set = Ibatt_set;
    Pbatt_set(2, :) = Ibatt_set(2, :) .* interp1(Vcap_set(1, :), Vcap_set(2, :), Ibatt_set(1, :));
else
    disp("ERR: Vcap_set and Ibatt_set have not been sampled enough.");
end



function Xout = makeUnique(Xin)
    if isempty(Xin), Xout = Xin; return; end
    [x_unq, ia] = unique(Xin(1,:), 'stable');
    n = size(Xin, 1);
    Xout = [x_unq; Xin(2:n, ia)];
end
