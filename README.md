# G-BungE_LogAnalysis_Modified
Based on `GBungE_logger_python` by quserunknownp.
Modified and extended for GIST Baja/Formula EV team logger.
The original workflow selected logs and plots by uncommenting code; this fork adds CLI and interactive menus for quicker repeated analysis.

GIST Student Baja/Formula team logger project. Based on luftaquila/monolith v1.  

Modified and extended for GIST Baja/Formula EV team logger.

## Project Layout

```text
.
├── main.py                # CLI entry point for selecting logs and plots
├── logFetcher.py          # Binary log parser and VehicleLog data container
├── logPostProcessor.py    # Plotting and analysis functions
├── Logs/
│   ├── 2nd Test Week/
│   └── Main Competition/
└── MatLab/                # Original MATLAB reference scripts and output/reference files
    └── Results/           # MATLAB output/reference files
```

## Initial Setup

macOS:

```bash
python3 -m pip install -r requirements.txt
```

Windows:

```powershell
py -m pip install -r requirements.txt
```

If `py` is not available on Windows, use:

```powershell
python -m pip install -r requirements.txt
```

## CAN Data Mapping

The parser is based on 2025 vehicle Mk.4 logs and currently focuses on MK4 CAN data.

When adding new logs, place the `.log` files under `Logs/<group name>/`, then pass the group and log file names to `main.py`.

| Source | Key | Data |
| --- | --- | --- |
| 1 | 0x0A | Actual torque, actual current, velocity |
| 1 | 0x0B | Ud, Uq, Vmod, Vcap |
| 1 | 0x0C | L, Vlim, Iflux, Iqmax |
| 1 | 0x0D | Motor temperature, battery current, torque demand, actual torque |
| 1 | 0x0E | Vtgt, Id, Iq |
| 5 | - | Accelerometer |
| 6 | 0 | GPS position |
| 6 | 1 | GPS velocity and course |
| 6 | 2 | GPS time |

## CLI Usage

Run the interactive menu:

```bash
./main.py
```

The script shows numbered menus. Type the number you want and press Enter:

```text
Log Groups
   1. 2nd Test Week
   2. Main Competition
Select one group number [default: 1]: 1

Logs in 2nd Test Week
  15. 2025-08-17 05-31-36.log  # Iq/Id 파악 가능, Laps: 1/2/1
  16. 2025-08-17 05-44-54.log  # Iq/Id 파악 가능, Laps: 1/0/0
Select log numbers (example: 1,3-5 or all): 15

Plots / Actions
   1. gps-only  # GPS 주행 궤적
   2. torque-performance  # 토크 응답성 확인
   3. vector-control  # 벡터 제어(Id/Iq) 상태 확인
Select plot/action numbers (example: 1,4 or all): 1
```

You can enter one number like `1`, multiple values like `1,3,5`, ranges like `3-7`, or `all`.

You can also force the menu explicitly:

```bash
./main.py --interactive
```

List available log groups and files:

```bash
./main.py --list-logs
```

List available plot/action names:

```bash
./main.py --list-plots
```

Run one plot against one log:

```bash
./main.py --group "2nd Test Week" --log "2025-08-17 05-31-36.log" --plot gps-only
```

Run multiple split-session logs in order:

```bash
./main.py \
  --group "2nd Test Week" \
  --log "2025-08-17 05-31-36.log" "2025-08-17 05-44-54.log" \
  --plot torque-performance \
  --plot vector-control
```

Absolute log paths are also supported. In non-interactive usage, pass at least one log with `--log`.

## Notes

- Logs are expected under `Logs/<group name>/`.
- New log file paths are selected with `--group` and `--log`.
- If a driving session is split into multiple log files, pass them to `--log` in order.
- Most arrays are preallocated with `NaN`, so analysis functions should filter valid data when needed.
- Cooling and thermal regression plots are especially sensitive to `NaN` or sparse data, so defensive filtering is applied before fitting trends.
- `NaN` values usually mean that the signal was not available, not parsed, or not received at that timestamp. They are mainly useful for checking data coverage, CAN dropouts, or parser mapping issues, not as physical values.

Plotting functions in the visualizer module often include built-in assumptions and default constraints (e.g., current limits, bin widths, minimum samples per bin, field weakening thresholds). These are intentionally not hardcoded for all use cases.

Users are expected to adjust key parameters at the main script level when calling these functions, rather than modifying the class implementation directly. This ensures consistency, reusability, and prevents unintended side effects across analyses.

For example:

plot_id_iq_vs_rpm: RPM bin size and minimum sample count should be tuned depending on data density.
plot_auto_field_weakening_trend: Field weakening current limits must be set appropriately to match controller settings.
plot_torque_vs_iq: Iq binning and absolute value usage may affect interpretation of torque linearity.
plot_motor_control_constraints: Current limits and operating boundaries (MTPA, voltage ellipse) should reflect actual system constraints.

In summary, treat plotting parameters as part of the analysis configuration (in main), not as fixed logic inside the visualizer class.
