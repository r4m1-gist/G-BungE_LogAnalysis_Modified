# G-BungE_LogAnalysis_Modified
Based on GBungE_logger_python by quserunknownp, modified and extended.

GIST Student Baja/Formula team logger project. Based on luftaquila/monolith v1.  

Modified and extended for GIST Baja/Formula EV team logger.

## Project Layout

```text
.
├── main.py                # Main script for selecting logs and plots
├── logFetcher.py          # Binary log parser and VehicleLog data container
├── logPostProcessor.py    # Plotting and analysis functions
├── Logs/
│   ├── 2nd Test Week/
│   └── Main Competition/
├── MatLab/                # Original MATLAB reference scripts
└── MatLab_Log/            # MATLAB output/reference files
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

When adding new logs, place the `.log` files under `Logs/<group name>/`, then set `log_group` and `log_files` in `main.py` to match that folder name and file name.

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
- New log file paths are selected from `main.py` through `log_group` and `log_files`.
- If a driving session is split into multiple log files, add them to `log_files` in order.
- Most arrays are preallocated with `NaN`, so analysis functions should filter valid data when needed.
