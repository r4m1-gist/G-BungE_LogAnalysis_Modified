


figure('units','normalized','outerposition', [0.0 0.1 1.0 0.9]);

PLT_r = 2;  PLT_c = 2;  PLT_cntr = 0;

PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
plot(vel_set(2, :), interp1(Tdmd_set(1, :), Tdmd_set(2, :), vel_set(1, :)), 'LineStyle','none','Marker','.');
hold on;
plot(vel_set(2, :), interp1(torqueAct_set(1, :), torqueAct_set(2, :), vel_set(1, :)), 'LineStyle','none','Marker','.');
hold off;
grid on;
legend({"Dmd", "Act"}, 'location', 'best');
xlabel('rpm_{CAN}');
ylabel('Torque (Nm)');

PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
plot(vel_set(2, :), interp1(Ibatt_set(1, :), Ibatt_set(2, :), vel_set(1, :)), 'LineStyle','none','Marker','.');
% plot(vel_set(2, :), Ibatt_set(2, :), 'LineStyle','none','Marker','.');
hold on;
% plot(vel_set(2, :), interp1(currAct_set(1, :), currAct_set(2, :), vel_set(1, :)), 'LineStyle','none','Marker','.');
plot(vel_set(2, :), currAct_set(2, :), 'LineStyle','none','Marker','.');
hold off;
grid on;
legend({"DC", "AC"}, 'location', 'best');
xlabel('rpm_{CAN}');
ylabel('Current (A)');

PLT_cntr = PLT_cntr + 1;
subplot(PLT_r, PLT_c, PLT_cntr);
plot(Idq_set(2, :), Idq_set(3, :), 'LineStyle','none','Marker','.');
hold on;
Idq_mag = sqrt( Idq_set(2, :).^2 + Idq_set(3, :).^2 );
Idq_mask = ( Idq_mag >= 0 );
Idq_slope = sum(Idq_set(2, Idq_mask) .* Idq_set(3, Idq_mask)) / sum(Idq_set(2, Idq_mask).^2);
Idq_ang = acos( Idq_slope / sqrt( Idq_slope^2 + 1 ) );
if ( Idq_ang >= pi/2 ); Idq_ang = Idq_ang - pi; end
plot(Idq_set(3, :)/Idq_slope, Idq_set(3, :), 'LineStyle','-','Marker','none');
hold off;
grid on;
axis equal;
legend({"", sprintf("%.3f deg", rad2deg(Idq_ang))}, 'Location','best');
xlabel('I_{d} (A)');
ylabel('I_{q} (A)');



