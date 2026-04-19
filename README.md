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

## CLI Usage

Start an interactive menu for choosing a group, log files, and plots:

```bash
python3 main.py
```

You can also force the menu explicitly:

```bash
python3 main.py --interactive
```

In the menu, enter numbers like `1`, multiple values like `1,3,5`, ranges like `3-7`, or `all`.

List available log groups and files:

```bash
python3 main.py --list-logs
```

List available plot/action names:

```bash
python3 main.py --list-plots
```

Run one plot against one log:

```bash
python3 main.py --group "2nd Test Week" --log "2025-08-17 05-31-36.log" --plot gps-only
```

Run multiple split-session logs in order:

```bash
python3 main.py \
  --group "2nd Test Week" \
  --log "2025-08-17 05-31-36.log" "2025-08-17 05-44-54.log" \
  --plot torque-performance \
  --plot vector-control
```

Absolute log paths are also supported. In non-interactive usage, pass at least one log with `--log`.

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

## Notes

- Logs are expected under `Logs/<group name>/`.
- New log file paths are selected with `--group` and `--log`.
- If a driving session is split into multiple log files, pass them to `--log` in order.
- Most arrays are preallocated with `NaN`, so analysis functions should filter valid data when needed.
- Cooling and thermal regression plots are especially sensitive to `NaN` or sparse data, so defensive filtering is applied before fitting trends.
- `NaN` values usually mean that the signal was not available, not parsed, or not received at that timestamp. They are mainly useful for checking data coverage, CAN dropouts, or parser mapping issues, not as physical values.
