# G-BungE_LogAnalysis_Modified
Based on GBungE_logger_python by quserunknownp, modified and extended.

GIST Student Baja/Formula team logger project. Based on luftaquila/monolith v1.  

Modified and extended for GIST Baja/Formula EV team logger.

## Project Layout

```text
.
├── pymain.py              # Main script for selecting logs and plots
├── pylogFetcher.py        # Binary log parser and VehicleLog data container
├── pylogPostProcessor.py  # Plotting and analysis functions
├── Logs/
│   ├── 2nd Test Week/
│   └── Main Competition/
├── MatLab/                # Original MATLAB reference scripts
└── MatLab_Log/            # MATLAB output/reference files
```

## Install

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

## Run

Edit the log selection block near the top of `pymain.py`.

```python
log_group = '2nd Test Week'
log_files = [
    '2025-08-17 07-13-44.log',
]
```

For competition logs:

```python
log_group = 'Main Competition'
log_files = [
    '2025-08-31 02-03-58.log',
]
```

Then run:

macOS:

```bash
python3 pymain.py
```

Windows:

```powershell
py pymain.py
```

If `py` is not available on Windows, use:

```powershell
python pymain.py
```

To draw a graph, uncomment the plot function you want in the `if __name__ == "__main__":` block of `pymain.py`.

Example:

```python
visualizer.plot_torque_performance()
```

## CAN Data Mapping

The parser currently focuses on MK4 CAN data.

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
- If a driving session is split into multiple log files, add them to `log_files` in order.
- Most arrays are preallocated with `NaN`, so analysis functions should filter valid data when needed.
