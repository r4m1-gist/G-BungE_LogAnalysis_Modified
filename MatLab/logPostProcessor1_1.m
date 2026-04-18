


// circuit settings
pREFauto = 0; pUpr_FLautoAdd = [0.25; 0.5]; pLwr_FLautoAdd = [0.0; -0.5];
pUpr_FL = [126354.475; 35568.275];    % pUwr_FL(2) > (y coordinates of intersection points)
pLwr_FL = [126354.50; 35568.00];    % pLwr_FL(2) < (y coordinates of intersection points)
dst_CRT_FL = 0.075;
tDiff_CRT = 30;
NoStI = 1000;

// plotting settings
PLTtRNG_ENB = 0;    % 시간 범위 지정 할지 말지
PLTtRNG = [115, 180];    % 시간 범위
% PLTtRNG = [210, 295];    % 시간 범위

PLTrngAcc = 5;

PLTrngGpsPosLng = 2.0; PLToffGpsPosLng = 0.2;
PLTrngGpsPosLat = 1.0; PLToffGpsPosLat = -0.4;

PLTgpsRNG = [0, 100];
PLTratCAN = 1.2;


% ||| -------------------- post-processing -------------------- |||
% [~, indrm_lng] = rmoutliers(gpsPos_set(2, :), 2);
% [~, indrm_lat] = rmoutliers(gpsPos_set(3, :), 2);
% induse_gps = (~indrm_lng) | (~indrm_lat);
% gpsPos_set = gpsPos_set(:, induse_gps);

r_wheel = 0.553/2;
v_car_lwb = 1;
v_wheel_lwb = 1;
if ( size(gpsVec_set, 2) >= size(vel_set, 2) )
    omega_wheel = (1 / 4.652) * (2*pi/60) * interp1(vel_set(1, :), vel_set(2, :), gpsVec_set(1, :));
    v_car = (1000/3600) * gpsVec_set(2, :);
    t_slip = gpsVec_set(1, :);
else
    omega_wheel = (1 / 4.652) * (2*pi/60) * vel_set(2, :);
    v_car = (1000/3600) * interp1(gpsVec_set(1, :), gpsVec_set(2, :), vel_set(1, :));
    t_slip = vel_set(1, :);
end
slip_rat = [t_slip; ( max(omega_wheel*r_wheel, v_wheel_lwb) ./ max(v_car, v_car_lwb) - 1 )*100];

if ( pREFauto == 1 )
    pUpr_FL = mean(gpsPos_set(2:3, :), 2) + pUpr_FLautoAdd;
    pLwr_FL = mean(gpsPos_set(2:3, :), 2) + pLwr_FLautoAdd;
end

% lap segmentation
dlt_FL = pUpr_FL - pLwr_FL;
a_FL = dlt_FL(2);
b_FL = (-1)*dlt_FL(1);
c_FL = dlt_FL(1)*pLwr_FL(2) - dlt_FL(2)*pLwr_FL(1);

t_LS = gpsPos_set(1, :);
xPos_LS = gpsPos_set(2, :);
yPos_LS = gpsPos_set(3, :);
dst_LS = abs( a_FL.*xPos_LS + b_FL.*yPos_LS + c_FL ) ./ sqrt( a_FL^2 + b_FL^2 );

idx_dstVal = zeros(1, length(dst_LS));
for i = 1:length(dst_LS)
    if ( dst_LS(i) <= dst_CRT_FL ) && ( yPos_LS(i) > pLwr_FL(2) ) && ( yPos_LS(i) < pUpr_FL(2) )
        idx_dstVal(i) = 1;
    end
end
idx_dstVal = logical(idx_dstVal);

idx_dstVal_fnd = find(idx_dstVal);
tVal_LS = gpsPos_set(1, idx_dstVal);
strtRem = 1;
crntSeg_LS = 1;
idx_ValSeg_LS = nan(1, NoStI);
tValSeg_LS = nan(1, NoStI);
for i = 2:length(tVal_LS)
    tDiff = abs( tVal_LS(i) - tVal_LS(i-1) );
    if ( tDiff > tDiff_CRT ) || ( i == length(tVal_LS) )
        [~, idx_tmp1] = min(dst_LS( idx_dstVal_fnd( strtRem:(i-1) ) ));
        idx_ValSeg_LS(crntSeg_LS) = idx_dstVal_fnd(idx_tmp1 + strtRem - 1);
        tValSeg_LS(crntSeg_LS) = t_LS(idx_ValSeg_LS(crntSeg_LS));

        strtRem = i;
        crntSeg_LS = crntSeg_LS + 1;
    end
end
idx_ValSeg_LS = rmmissing(idx_ValSeg_LS);
tValSeg_LS = rmmissing(tValSeg_LS);

NoL = length(tValSeg_LS) - 1;

CMB.source = source_set;
CMB.CAN = CAN_set;
CMB.acc = acc_set;
CMB.pos = gpsPos_set;
CMB.vel = gpsVec_set;
CMB.idx_tSeg = idx_ValSeg_LS;
CMB.tSeg = tValSeg_LS;

Ibatt_mean = nan(1, NoL);
fprintf("\n");
fprintf("  Number of detected laps: %d \n", NoL);
if ( NoL >= 1 )
    for i = 2:(NoL+1)
        t_tmp = tValSeg_LS(i) - tValSeg_LS(i-1);
        fprintf("  Lap %d: %d min %.3f sec, ", i-1, fix(t_tmp/60), rem(t_tmp, 60));

        Ibatt_set_tmp = ext_rng(Ibatt_set, [tValSeg_LS(i-1), tValSeg_LS(i)]);
        if any(isempty(Ibatt_set_tmp)); Ibatt_mean(i-1) = nan;
        else
            Ibatt_mean(i-1) = tMean(Ibatt_set_tmp(1, :), Ibatt_set_tmp(2, :));
        end

        fprintf("I_mean: %.3f A \n", Ibatt_mean(i-1));
    end
end

function Xout = ext_rng(Xin, tRNG)
    dim1 = size(Xin, 1);
    t = Xin(1, :);
    I = Xin(2:dim1, :);
    
    mask = ( t >= tRNG(1) ) & ( t <= tRNG(2) );
    Xout = [t(mask); I(mask)];
end

function arr_mean = tMean(t, arr)
    n = length(t);
    if ( n ~= length(arr) ); error("ERR: input arrays have different lengths."); end
    
    sum = 0;
    for i = 2:n
        sum = sum + ( t(i) - t(i-1) ) * ( arr(i-1) + arr(i) ) / 2;
    end
    arr_mean = sum / ( t(end) - t(1) );
end


% ||| -------------------- plotting -------------------- |||
figure('units','normalized','outerposition', [0.0 0.1 1.0 0.9]);

PLT_r = 3;  PLT_c = 2;  PLT_cntr = 0;

% % acc.
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(acc_set(1, :), acc_set(2, :), 'LineStyle','none','Marker','.','Color','r');
% hold on;
% plot(acc_set(1, :), acc_set(3, :), 'LineStyle','none','Marker','.','Color','g');
% plot(acc_set(1, :), acc_set(4, :), 'LineStyle','none','Marker','.','Color','b');
% hold off;
% grid on;
% accMean = mean(acc_set(2:4, :), 'all');
% ylim( [ accMean - PLTrngAcc, accMean + PLTrngAcc ] );
% xlabel('t (sec)');
% ylabel('acc (g)');

% GPS pos.
PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
plot([pUpr_FL(1), pLwr_FL(1)], [pUpr_FL(2), pLwr_FL(2)], 'LineStyle','--','Marker','*','Color','b');
hold on;
plot(gpsPos_set(2, 1), gpsPos_set(3, 1), 'LineStyle','none','Marker','o','Color','r');
plot(gpsPos_set(2, end), gpsPos_set(3, end), 'LineStyle','none','Marker','o','Color','g');
plot(gpsPos_set(2, idx_ValSeg_LS), gpsPos_set(3, idx_ValSeg_LS), 'LineStyle','none','Marker','square','Color','m');
plot(gpsPos_set(2, :), gpsPos_set(3, :), 'LineStyle','none','Marker','.','MarkerSize',4,'Color','k');
%{
N_gpsPos = length(gpsPos_set(1, :));
for i = 1:N_gpsPos
    plot(gpsPos_set(2, i), gpsPos_set(3, i), 'LineStyle','none','Marker','.','MarkerSize',2,'Color',[(N_gpsPos - i)/(N_gpsPos), i/(N_gpsPos), 0]);
end
%}
% plot(gpsPos_set(2, idx_gpsPos_filled(3, :)), gpsPos_set(2, idx_gpsPos_filled(1, :)), 'LineStyle','none','Marker','o','Color','r');
hold off;
grid on;
lngMean = mean( rmoutliers(gpsPos_set(2, :)) );
latMean = mean( rmoutliers(gpsPos_set(3, :)) );
xlim( [ lngMean + PLToffGpsPosLng - PLTrngGpsPosLng, lngMean + PLToffGpsPosLng + PLTrngGpsPosLng ] );
ylim( [ latMean + PLToffGpsPosLat - PLTrngGpsPosLat, latMean + PLToffGpsPosLat + PLTrngGpsPosLat ] );
xlabel('lng');
ylabel('lat');


% % GPS vel.
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(gpsVec_set(1, :), gpsVec_set(2, :), 'LineStyle','none','Marker','.','Color','k');
% if ~isempty(tValSeg_LS); xline(tValSeg_LS, 'Color','r'); end
% grid on;
% if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
% ylim( PLTgpsRNG );
% xlabel('t (sec)');
% ylabel('spd (km/h)');

% GPS vel. and slip ratio
PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
yyaxis left;
plot(gpsVec_set(1, :), gpsVec_set(2, :), 'LineStyle','none','Marker','.','Color','k');
hold on;
if ~isempty(tValSeg_LS); xline(tValSeg_LS, 'Color','r'); end
ylabel('spd (km/h)');
ylim( PLTgpsRNG );
yyaxis right;
plot(slip_rat(1, :), slip_rat(2, :), 'LineStyle','-','Marker','none');
yline(0, 'b');
ylabel('slip ratio (%)');
grid on;
if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
xlabel('t (sec)');

% % Motor Temperature
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(motorTemp_set(1, :), motorTemp_set(2, :), 'LineStyle','none','Marker','.');
% hold on;
% hold off;
% grid on;
% if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
% xlabel('t (sec)');
% ylabel('T_{motor} (\circ C)');

% Motor Torque
PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
plot(Tdmd_set(1, :), Tdmd_set(2, :), 'LineStyle','-','Marker','none');
hold on;
plot(torqueAct_set(1, :), torqueAct_set(2, :), 'LineStyle','-','Marker','.');
hold off;
grid on;
if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
legend({"Dmd", "Act"}, 'location', 'best');
xlabel('t (sec)');
ylabel('Torque (Nm)');

% % Motor RPM and slip ratio
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% yyaxis left;
% plot(vel_set(1, :), vel_set(2, :), 'LineStyle','none','Marker','.');
% ylabel('rpm_{motor}');
% hold on;
% yyaxis right;
% plot(slip_rat(1, :), slip_rat(2, :), 'LineStyle','-','Marker','none');
% yline(0, 'r');
% ylabel('slip ratio (%)');
% hold off;
% grid on;
% if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
% xlabel('t (sec)');

% Motor RPM
PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
plot(Vtgt_set(1, :), Vtgt_set(2, :), 'LineStyle','-','Marker','none');
hold on;
plot(vel_set(1, :), vel_set(2, :), 'LineStyle','-','Marker','.');
hold off;
grid on;
if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
legend({'Dmd', 'Act'}, 'Location','best');
xlabel('t (sec)');
ylabel('rpm_{motor}');

% % slip ratio
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(slip_rat(1, :), slip_rat(2, :), 'LineStyle','none','Marker','.');
% hold on;
% hold off;
% grid on;
% if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
% xlabel('t (sec)');
% ylabel('slip ratio (%)');

% Battery Current and Power
PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
yyaxis right;
plot(Ibatt_set(1, :), Ibatt_set(2, :), 'LineStyle','none','Marker','.');
ylabel('I_{Batt} (A)');
hold on;
yyaxis left;
% plot(Vcap_set(1, :), Vcap_set(2, :), 'LineStyle','none','Marker','.');
% ylabel('V_{cap} (V)');
plot(Pbatt_set(1, :), (1e-3)*Pbatt_set(2, :), 'LineStyle','none','Marker','.');
ylabel('P_{Batt} (kW)');
hold off;
grid on;
if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
xlabel('t (sec)');

% Motor dq-axis Current
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(Idq_set(1, :), Idq_set(2, :), 'LineStyle','none','Marker','.');
% hold on;
% plot(Idq_set(1, :), Idq_set(3, :), 'LineStyle','none','Marker','.');
% hold off;
% grid on;
% legend({"I_{d}", "I_{q}"}, 'location', 'best');
% if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
% xlabel('t (sec)');
% ylabel('Current (A)');

PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
% Motor dq-axis Current
yyaxis left;
plot(Idq_set(1, :), Idq_set(2, :), 'LineStyle','-','Marker','none', 'Color','r');
hold on;
plot(Idq_set(1, :), Idq_set(3, :), 'LineStyle','-','Marker','none', 'Color','b');
ylabel('Current (A)');
% Motor Temperature
yyaxis right;
plot(motorTemp_set(1, :), motorTemp_set(2, :), 'LineStyle','none','Marker','.', 'Color','k');
ylabel('T_{motor} (\circ C)');
hold off;
grid on;
legend({"I_{d}", "I_{q}", "Temp."}, 'location', 'best');
if ( PLTtRNG_ENB == 1 ); xlim( PLTtRNG ); end
xlabel('t (sec)');



% % 시간에 따른 버스 전류
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(CAN_set(1,:), CAN_set(3,:),'LineStyle','none','Marker','.','Color','b');
% xlim([CAN_set(1, 1), CAN_set(1, end)]);
% ylim( PLTratCAN * [0, max(CAN_set(3,:))]);
% xlabel('t (sec)');
% ylabel('Bus A');
% 
% 
% % 시간에 따른 페이즈 전류
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(CAN_set(1,:), CAN_set(4,:),'LineStyle','none','Marker','.','Color','b');
% xlim([CAN_set(1, 1), CAN_set(1, end)]);
% ylim( PLTratCAN * [0, max(CAN_set(4,:))]);
% xlabel('t (sec)');
% ylabel('Phase A');
% 
% 
% % 시간에 따른 RPM 좀 튀는 것 같아 이건 시프팅 조절 할 예정
% % PLT_cntr = PLT_cntr + 1;
% % subplot(PLT_r, PLT_c, PLT_cntr);
% % plot(CAN_set(1,:), CAN_set(5,:),'LineStyle','none','Marker','.','Color','b');
% % xlim([CAN_set(1, 1), CAN_set(1, end)]);
% % % ylim([-4500 4500]);
% % xlabel('t (sec)');
% % ylabel('RPM');
% 
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(CAN_set(1,:), CAN_set(2,:),'LineStyle','none','Marker','.','Color','b');
% xlim([CAN_set(1, 1), CAN_set(1, end)]);
% % ylim([-4500 4500]);
% xlabel('t (sec)');
% ylabel('voltage (V)');
% 
% PLT_cntr = PLT_cntr + 1;
% subplot(PLT_r, PLT_c, PLT_cntr);
% plot(CAN_set(1,:), CAN_set(7,:),'LineStyle','none','Marker','.','Color','b');
% xlim([CAN_set(1, 1), CAN_set(1, end)]);
% % ylim( PLTratCAN * [0, max(CAN_set(7,:))]);
% xlabel('t (sec)');
% ylabel('T (\circ C)');


