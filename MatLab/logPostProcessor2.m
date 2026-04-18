

CMB_U = CMB;

lapToDisp = [2, 3];    % 표시할 랩
% 특정 거리 구간 동안 소요된 시간을 알고 싶을 때
dRNG_ENB = 1;    % 사용할지 말지
dRNG = [900, 1100];    % 범위 지정

PLTgpsRNG = [0, 100];

Nltd = length(lapToDisp);

source_setU = CMB_U.source;
CAN_setU = CMB_U.CAN;
acc_setU = CMB_U.acc;
gpsPos_setU = CMB_U.pos;
gpsVec_setU = CMB_U.vel;
idx_ValSegU = CMB_U.idx_tSeg;
tValSegU = CMB_U.tSeg;


Nseg = length(tValSegU) - 1;
CLL = cell(Nseg, 1);
for i = 1:Nseg
    tRNG = [tValSegU(i), tValSegU(i+1)];
    posSegTmp = tExtract(tRNG, gpsPos_setU);
    velSegTmp = tExtract(tRNG, gpsVec_setU);
    dstSegTmp = nan(1, size(velSegTmp, 2));
    dst_tmp = 0;
    dstSegTmp(1) = dst_tmp;
    for j = 2:size(velSegTmp, 2)
        dst_tmp = dst_tmp + 0.5*(velSegTmp(2, j) + velSegTmp(2, j-1))/3.6 * (velSegTmp(1, j) - velSegTmp(1, j-1));
        dstSegTmp(j) = dst_tmp;
    end
    velSegTmpRev = [velSegTmp; dstSegTmp];

    CMB_segTmp.pos = posSegTmp;
    CMB_segTmp.vel = velSegTmpRev;
    CLL{i} = CMB_segTmp;
end



figure('units','normalized','outerposition', [0.0 0.1 1.0 0.9]);
PLT_r = 2;  PLT_c = 1;  PLT_cntr = 0;

% GPS pos.
PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
plot([pUpr_FL(1), pLwr_FL(1)], [pUpr_FL(2), pLwr_FL(2)], 'LineStyle','--','Marker','*','Color','k');
hold on;
% plot(gpsPos_setSTD(2, 1), gpsPos_setSTD(3, 1), 'LineStyle','none','Marker','o','Color','r');
% plot(gpsPos_setSTD(2, end), gpsPos_setSTD(3, end), 'LineStyle','none','Marker','o','Color','g');
cntr_tmp = 1;
for i = lapToDisp
    plot(CLL{i}.pos(2, :), CLL{i}.pos(3, :), 'LineStyle','none','Marker','.','MarkerSize',5,'Color',[(Nltd-cntr_tmp)/(Nltd-1), 0, (cntr_tmp-1)/(Nltd-1)]);
    cntr_tmp = cntr_tmp + 1;
end
hold off;
grid on;
lngMean = mean( rmoutliers(gpsPos_set(2, :)) );
latMean = mean( rmoutliers(gpsPos_set(3, :)) );
xlim( [ lngMean + PLToffGpsPosLng - PLTrngGpsPosLng, lngMean + PLToffGpsPosLng + PLTrngGpsPosLng ] );
ylim( [ latMean + PLToffGpsPosLat - PLTrngGpsPosLat, latMean + PLToffGpsPosLat + PLTrngGpsPosLat ] );
xlabel('lng');
ylabel('lat');


% GPS vel.
PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
hold on;
cntr_tmp = 1;
tRQRD = nan(1, Nltd);
for i = lapToDisp
    if ( dRNG_ENB == 1 ); [~, tRQRD(cntr_tmp)] = segCalc(dRNG, CLL{i}.vel); end

    plot(CLL{i}.vel(4, :), CLL{i}.vel(2, :), 'LineStyle','none','Marker','.','MarkerSize',5,'Color',[(Nltd-cntr_tmp)/(Nltd-1), 0, (cntr_tmp-1)/(Nltd-1)]);

    cntr_tmp = cntr_tmp + 1;
end
hold off;
grid on;
if ( dRNG_ENB == 1 )
    str_lgnd = cell(1, Nltd);
    cntr_lgnd = 0;
    for i = lapToDisp
        cntr_lgnd = cntr_lgnd + 1;
        str_lgnd{cntr_lgnd} = sprintf("Lap %d, %.3f sec", lapToDisp(cntr_lgnd), tRQRD(cntr_lgnd));
        xline(dRNG(cntr_lgnd), '-', sprintf("%d m", dRNG(cntr_lgnd)));
    end
    legend(str_lgnd, 'Location','best');
end
ylim( PLTgpsRNG );
xlabel('distance (m)');
ylabel('spd (km/h)');





function [arrRes] = tExtract(tRNG, arr)

N = size(arr, 2);
chkr1 = 0;
idx_str = nan;
idx_end = nan;
for i = 1:N
    if ( arr(1, i) >= tRNG(1) ) && (chkr1 == 0)
        idx_str = i;
        chkr1 = 1;
    end
    
    if ( arr(1, i) > tRNG(2) ) && (chkr1 == 1)
        idx_end = i-1;
        chkr1 = 2;
    end
end

if ( chkr1 ~= 2 )
    error("ERR: invalid time range input.");
end
arrRes = arr(:, idx_str:idx_end);
end

function [avgSpd, tRQRD] = segCalc(dRNG, arr)

N = size(arr, 2);
chkr1 = 0;
idx_str = nan;
idx_end = nan;
for i = 1:N
    if ( arr(4, i) >= dRNG(1) ) && (chkr1 == 0)
        idx_str = i;
        chkr1 = 1;
    end
    
    if ( arr(4, i) > dRNG(2) ) && (chkr1 == 1)
        idx_end = i-1;
        chkr1 = 2;
    end
end

if ( chkr1 ~= 2 )
    error("ERR: invalid distance range input.");
end
avgSpd = tMean(arr(1, idx_str:idx_end), arr(2, idx_str:idx_end));
tRQRD = ( dRNG(2) - dRNG(1) ) / (avgSpd/3.6);
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


