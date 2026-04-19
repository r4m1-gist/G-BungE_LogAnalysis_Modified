"""Command line entry point for G-BungE log analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from logFetcher import VehicleLog, setfilename


PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_ROOT = PROJECT_ROOT / "Logs"
DEFAULT_LOG_GROUP = "2nd Test Week"
DEFAULT_LOG_FILES = (
    "2025-08-17 05-31-36.log",
    "2025-08-17 05-44-54.log",
    "2025-08-17 00-33-28.log",
)
LOG_RECORD_BYTES = 16


def normalize_action_name(name: str) -> str:
    """Normalize CLI action names to the registry key format."""
    normalized = name.strip().replace("_", "-")
    if normalized.startswith("plot-"):
        normalized = normalized.removeprefix("plot-")
    return normalized


def get_action_registry() -> dict[str, str]:
    """Return CLI action names mapped to LogVisualizer/VehicleLog method names."""
    from logPostProcessor import LogVisualizer

    plot_methods = {
        method.removeprefix("plot_").replace("_", "-"): method
        for method in dir(LogVisualizer)
        if method.startswith("plot_")
    }
    plot_methods["split-laps"] = "split_laps"
    return dict(sorted(plot_methods.items()))


def discover_log_groups(logs_root: Path = LOGS_ROOT) -> list[str]:
    """Return available log group directory names."""
    if not logs_root.exists():
        return []
    return sorted(path.name for path in logs_root.iterdir() if path.is_dir())


def discover_logs(group: str) -> list[str]:
    """Return .log files available under a log group."""
    group_dir = LOGS_ROOT / group
    if not group_dir.exists():
        return []
    return sorted(path.name for path in group_dir.glob("*.log"))


def resolve_log_path(log_file: str, group: str) -> Path:
    """Resolve absolute paths directly, otherwise resolve under Logs/<group>."""
    expanded = Path(log_file).expanduser()
    if expanded.is_absolute():
        return expanded
    return Path(setfilename(log_file, group=group))


def count_log_records(log_path: Path) -> int:
    """Count fixed-width log records without parsing the whole file."""
    return log_path.stat().st_size // LOG_RECORD_BYTES


def load_logs(log_files: Iterable[str], group: str, strict: bool = False) -> VehicleLog:
    """Load one or more log files into a VehicleLog container."""
    log_data = VehicleLog()
    loaded_count = 0

    for log_file in log_files:
        log_path = resolve_log_path(log_file, group)

        try:
            n_points = count_log_records(log_path)
        except FileNotFoundError:
            message = f"Log file not found: {log_path}"
            if strict:
                raise FileNotFoundError(message) from None
            print(f"WARN: {message}")
            continue

        print(f"INFO: loading {log_path} ({n_points} records)")
        log_data.allocate_or_extend(n_points, is_first_file=(loaded_count == 0))
        log_data.parse_file(str(log_path))
        loaded_count += 1

    if loaded_count == 0:
        raise FileNotFoundError("No log files were loaded.")

    return log_data


def flatten_log_args(log_options: list[list[str]] | None, positional_logs: list[str]) -> list[str]:
    """Combine repeated --log arguments and positional log arguments."""
    logs: list[str] = []
    for option_group in log_options or []:
        logs.extend(option_group)
    logs.extend(positional_logs)
    return logs or list(DEFAULT_LOG_FILES)


def print_available_actions(registry: dict[str, str]) -> None:
    print("Available plot/action names:")
    for action_name in registry:
        print(f"  - {action_name}")


def print_available_logs() -> None:
    groups = discover_log_groups()
    if not groups:
        print(f"No log groups found under {LOGS_ROOT}")
        return

    print("Available logs:")
    for group in groups:
        print(f"\n[{group}]")
        logs = discover_logs(group)
        if not logs:
            print("  (no .log files)")
            continue
        for log_name in logs:
            print(f"  - {log_name}")


def parse_number_selection(raw_value: str, max_count: int, allow_all: bool = True) -> list[int]:
    """Parse selections like '1,3-5' into zero-based indexes."""
    raw_value = raw_value.strip().lower()
    if allow_all and raw_value in {"all", "*"}:
        return list(range(max_count))

    selected: list[int] = []
    for item in raw_value.split(","):
        item = item.strip()
        if not item:
            continue

        if "-" in item:
            start_text, end_text = item.split("-", 1)
            if not start_text.isdigit() or not end_text.isdigit():
                raise ValueError(f"Invalid range: {item}")
            start = int(start_text)
            end = int(end_text)
            if start > end:
                raise ValueError(f"Invalid range: {item}")
            selected.extend(range(start - 1, end))
            continue

        if not item.isdigit():
            raise ValueError(f"Invalid selection: {item}")
        selected.append(int(item) - 1)

    if not selected:
        raise ValueError("No selection entered.")

    invalid = [index + 1 for index in selected if index < 0 or index >= max_count]
    if invalid:
        raise ValueError(f"Selection out of range: {invalid}")

    deduped: list[int] = []
    for index in selected:
        if index not in deduped:
            deduped.append(index)
    return deduped


def print_numbered_options(title: str, options: list[str]) -> None:
    print(f"\n{title}")
    for idx, option in enumerate(options, start=1):
        print(f"  {idx:>2}. {option}")


def prompt_for_indexes(
    title: str,
    options: list[str],
    prompt: str,
    default_indexes: list[int] | None = None,
    allow_all: bool = True,
) -> list[int]:
    if not options:
        raise ValueError(f"No options available for {title}.")

    print_numbered_options(title, options)
    default_label = ""
    if default_indexes:
        default_label = f" [default: {','.join(str(index + 1) for index in default_indexes)}]"

    while True:
        raw_value = input(f"{prompt}{default_label}: ").strip()
        if not raw_value and default_indexes is not None:
            return default_indexes
        try:
            return parse_number_selection(raw_value, len(options), allow_all=allow_all)
        except ValueError as exc:
            print(f"WARN: {exc}")


def select_interactively(registry: dict[str, str]) -> tuple[str, list[str], list[str]]:
    """Prompt the user to choose a group, logs, and plots."""
    groups = discover_log_groups()
    if not groups:
        raise FileNotFoundError(f"No log groups found under {LOGS_ROOT}")

    default_group_index = groups.index(DEFAULT_LOG_GROUP) if DEFAULT_LOG_GROUP in groups else 0
    selected_group_index = prompt_for_indexes(
        "Log Groups",
        groups,
        "Select one group number",
        default_indexes=[default_group_index],
        allow_all=False,
    )[0]
    group = groups[selected_group_index]

    logs = discover_logs(group)
    default_log_indexes = [
        logs.index(log_name) for log_name in DEFAULT_LOG_FILES if log_name in logs
    ]
    selected_log_indexes = prompt_for_indexes(
        f"Logs in {group}",
        logs,
        "Select log numbers (example: 1,3-5 or all)",
        default_indexes=default_log_indexes or None,
        allow_all=True,
    )
    selected_logs = [logs[index] for index in selected_log_indexes]

    action_names = list(registry)
    selected_action_indexes = prompt_for_indexes(
        "Plots / Actions",
        action_names,
        "Select plot/action numbers (example: 1,4 or all)",
        default_indexes=None,
        allow_all=True,
    )
    selected_actions = [action_names[index] for index in selected_action_indexes]

    print("\nSelection summary:")
    print(f"  group: {group}")
    print(f"  logs: {', '.join(selected_logs)}")
    print(f"  plots/actions: {', '.join(selected_actions)}")
    return group, selected_logs, selected_actions


def run_actions(log_data: VehicleLog, action_names: list[str], registry: dict[str, str]) -> None:
    """Run selected plot/actions against loaded log data."""
    from logPostProcessor import LogVisualizer

    visualizer = LogVisualizer(log_data)

    for raw_name in action_names:
        action_name = normalize_action_name(raw_name)
        method_name = registry[action_name]

        print(f"INFO: running {action_name}")
        if method_name == "split_laps":
            log_data.split_laps()
            continue

        getattr(visualizer, method_name)()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse G-BungE logger files and run selected analysis plots.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "logs",
        nargs="*",
        help="Log file names under Logs/<group>/, or absolute log file paths.",
    )
    parser.add_argument(
        "-g",
        "--group",
        default=DEFAULT_LOG_GROUP,
        help="Log group directory under Logs/.",
    )
    parser.add_argument(
        "-l",
        "--log",
        action="append",
        nargs="+",
        dest="log_options",
        metavar="FILE",
        help="Log file name/path. Repeat or pass multiple values to load split sessions in order.",
    )
    parser.add_argument(
        "-p",
        "--plot",
        action="append",
        default=[],
        metavar="NAME",
        help="Plot/action to run. Repeat to run multiple. Use --list-plots to see names.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Choose log group, logs, and plots from numbered menus.",
    )
    parser.add_argument(
        "--list-plots",
        action="store_true",
        help="Print available plot/action names and exit.",
    )
    parser.add_argument(
        "--list-logs",
        action="store_true",
        help="Print available log groups/files and exit.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail immediately when a selected log file is missing.",
    )
    return parser


def validate_actions(action_names: list[str], registry: dict[str, str]) -> list[str]:
    invalid_names = [
        name for name in action_names if normalize_action_name(name) not in registry
    ]
    if invalid_names:
        available = ", ".join(registry)
        invalid = ", ".join(invalid_names)
        raise ValueError(f"Unknown plot/action: {invalid}. Available: {available}")
    return action_names


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_logs:
        print_available_logs()
        return 0

    if args.list_plots:
        registry = get_action_registry()
        print_available_actions(registry)
        return 0

    try:
        registry = get_action_registry()
        should_prompt = args.interactive or (
            not args.plot
            and not args.log_options
            and not args.logs
            and sys.stdin.isatty()
        )
        if should_prompt:
            group, log_files, action_names = select_interactively(registry)
        else:
            group = args.group
            action_names = validate_actions(args.plot, registry)
            log_files = flatten_log_args(args.log_options, args.logs)

        log_data = load_logs(log_files, group=group, strict=args.strict)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    if not action_names:
        print("INFO: no plots requested. Use --plot NAME or --list-plots.")
        return 0

    run_actions(log_data, action_names, registry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
