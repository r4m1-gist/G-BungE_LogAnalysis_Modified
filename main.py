#!/usr/bin/env python3
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
LOG_RECORD_BYTES = 16
LOG_NOTES = {
    "2nd Test Week": {
        "2025-08-17 00-33-28.log": "Laps: 1/0/0, Remarks: 등 선 빠져서 바로 들어왔음",
        "2025-08-17 00-38-47.log": "ERR",
        "2025-08-17 02-06-14.log": "Laps: 1/3/1, Remarks: 최고 기록: 1:20.605, CAN 데이터 끊김",
        "2025-08-17 02-21-45.log": "정크데이터",
        "2025-08-17 02-22-57.log": "정크데이터",
        "2025-08-17 05-31-36.log": "Iq/Id 파악 가능, Laps: 1/2/1, Remarks: 최고 기록: 1:21.004",
        "2025-08-17 05-44-54.log": "Iq/Id 파악 가능, Laps: 1/0/0, Remarks: 스핀함, 결승선 근처 GPS 튐",
        "2025-08-17 07-08-04.log": "Iq/Id 파악 가능",
        "2025-08-17 07-13-44.log": "Iq/Id 파악 가능, 경민-1(+30kg) 세팅 위와 동일",
        "2025-08-17 07-37-33.log": "Iq/Id 파악 가능, 가속@80n.m. -> 60m",
        "2025-08-17 07-44-39.log": "Iq/Id 파악 가능, 가속@120n.m. -> 65m",
        "2025-08-17 07-57-25.log": "Iq/Id 파악 가능, ERR",
        "2025-08-17 08-13-48.log": "Iq/Id 파악 가능, 경민-2(+30kg) 최대 토크 깎기",
        "2025-08-17 08-24-29.log": "Iq/Id 파악 가능, 동적 성능",
        "2025-08-17 11-14-56.log": "Iq/Id 파악 가능, 정크 데이터",
        "2025-08-17 11-16-12.log": "Iq/Id 파악 가능, 동적성능 아닌것 같음",
    },
    "Main Competition": {
        "2025-08-29 08-56-47.log": "Laps: 0/0/0, Remarks: 가속/제동",
        "2025-08-29 09-01-23.log": "Laps: 0/0/0, Remarks: 동적 성능 1",
        "2025-08-29 09-04-01.log": "Laps: 0/0/0, Remarks: 동적 성능 1(이어짐)",
        "2025-08-29 09-05-08.log": "Laps: 0/0/0, Remarks: 동적 성능 1(이어짐)",
        "2025-08-29 09-09-27.log": "Laps: 0/0/0, Remarks: 동적 성능 2",
        "2025-08-29 09-11-42.log": "Laps: 0/0/0, Remarks: 동적 성능 2(이어짐)",
        "2025-08-30 01-58-39.log": "2일차 온도 터진거(테스트주행)",
        "2025-08-30 06-08-15.log": "오토크로스",
        "2025-08-30 08-32-10.log": "예선",
        "2025-08-31 01-13-33.log": "본선1 (충격으로 꺼짐)",
        "2025-08-31 01-33-25.log": "본선2 (재시작 후 피트인)",
        "2025-08-31 01-48-43.log": "본선3 (김경민 10분)",
        "2025-08-31 02-03-58.log": "본선4 (임동윤, 임동윤, 김경민)",
    },
}
ACTION_ORDER = (
    "gps-only",
    "torque-performance",
    "vector-control",
    "field-weakening",
    "gps-velocity-and-slip",
    "torque-vs-rpm",
    "temperature-profile",
    "torque-vs-temperature",
    "current-vs-torque-efficiency",
    "current-efficiency",
    "advanced-id-iq-analysis",
    "vehicle-dynamics",
    "vehicle-dynamics-lpf",
    "vehicle-dynamics-mv-avg",
    "split-laps",
    "gps-gforce-map",
    "laps-slideshow",
    "power-and-temp",
    "moving-rms",
    "temp-rise-vs-power",
    "temp-slope-trend",
    "thermal-path",
    "thermal-path-v2",
    "power-vs-temp-slope",
    "cooling-trend-regression",
    "cooling-intercept",
    "thermal-lag",
    "cooling-trend-high-temp",
    "power-vs-rpm",
    "tn-curve-envelope",
    "id-iq-vs-rpm",
    "auto-field-weakening-trend",
    "torque-vs-iq",
    "motor-control-constraints",
    "empirical-mtpa-from-log",
)
ACTION_NOTES = {
    "advanced-id-iq-analysis": "[고급 분석] Id/Iq 데이터 기반 기어비, 토크맵, 주행전략 분석",
    "auto-field-weakening-trend": "약계자 max current 기준 Id/Iq operating point 확인",
    "cooling-intercept": "순수 냉각 구간 Power vs Temp Slope 분석",
    "cooling-trend-high-temp": "고온 구간(60도 이상) 순수 냉각 속도 분석",
    "cooling-trend-regression": "순수 냉각 성능 정밀 분석",
    "current-efficiency": "배터리 전류 vs 모터 상전류 비교 (인버터 효율 확인)",
    "current-vs-torque-efficiency": "효율 분석: 토크 대비 소모 전류량",
    "empirical-mtpa-from-log": "저속 로그에서 Torque/Current가 높은 Id-Iq 운전점 추세 확인",
    "field-weakening": "약계자 제어",
    "gps-gforce-map": "GPS G-Force Heatmap",
    "gps-only": "GPS 주행 궤적",
    "gps-velocity-and-slip": "GPS 속도 slip ratio",
    "id-iq-vs-rpm": "RPM 기준 Id/Iq 전류 추세 확인",
    "laps-slideshow": "키보드 좌우 방향키로 랩 넘겨보기",
    "motor-control-constraints": "Id-Iq operating point, 전류 제한원, MTPA, 전압 제한 타원 시각화",
    "moving-rms": "고급 전력 분석 30초 이동 RMS",
    "power-and-temp": "입력 전력(P = V*I)과 모터 온도 비교",
    "power-vs-rpm": "입력 전력과 RPM 관계 확인",
    "power-vs-temp-slope": "입력 전력(VI) vs 온도 상승률",
    "power-flow": "전력 흐름 및 배터리 전류 분석",
    "split-laps": "데이터 랩 분할",
    "temp-rise-vs-power": "냉각 성능 상관관계 분석",
    "temp-slope-trend": "Rolling Linear Regression 온도 상승 기울기",
    "temperature-profile": "시간에 따른 모터 온도 변화 그래프",
    "thermal-lag": "전력과 온도상승 사이의 열 전달 지연 시간 찾기",
    "thermal-path": "특정 온도 이상 주행 구간 데이터 분석",
    "thermal-path-v2": "전력(Power) 기반 필터링 적용",
    "tn-curve-envelope": "T-N Curve Envelope (토크-속도 곡선 봉우리)",
    "torque-performance": "토크 응답성 확인",
    "torque-vs-iq": "실제 토크와 Iq 관계 및 Torque/Iq 추세 확인",
    "torque-vs-rpm": "RPM 변화에 따른 토크 변화",
    "torque-vs-temperature": "온도 변화에 따른 토크 변화",
    "vector-control": "벡터 제어(Id/Iq) 상태 확인",
    "vehicle-dynamics": "가속도 센서를 활용한 차량 거동 분석",
    "vehicle-dynamics-lpf": "NaN 데이터 제거 후 필터링 적용",
    "vehicle-dynamics-mv-avg": "3초 이동 평균(Moving Average) 적용",
}


def normalize_action_name(name: str) -> str:
    """Normalize CLI action names to the registry key format."""
    normalized = name.strip().replace("_", "-")
    if normalized.startswith("plot-"):
        normalized = normalized.removeprefix("plot-")
    return normalized


def get_action_registry() -> dict[str, str]:
    """Return CLI action names mapped to LogVisualizer/VehicleLog method names."""
    from logPostProcessor import LogVisualizer

    action_methods = {
        method.removeprefix("plot_").removeprefix("analyze_").replace("_", "-"): method
        for method in dir(LogVisualizer)
        if method.startswith(("plot_", "analyze_"))
    }
    action_methods["split-laps"] = "split_laps"

    ordered_methods: dict[str, str] = {}
    for action_name in ACTION_ORDER:
        method = action_methods.pop(action_name, None)
        if method is not None:
            ordered_methods[action_name] = method

    for action_name in sorted(action_methods):
        ordered_methods[action_name] = action_methods[action_name]

    return ordered_methods


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


def format_log_option(group: str, log_name: str) -> str:
    """Return a display label with any known memo for the log."""
    note = LOG_NOTES.get(group, {}).get(log_name)
    if note:
        return f"{log_name}  # {note}"
    return log_name


def format_action_option(action_name: str) -> str:
    """Return a display label with any known memo for the action."""
    note = ACTION_NOTES.get(action_name)
    if note:
        return f"{action_name}  # {note}"
    return action_name


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
    return logs


def print_available_actions(registry: dict[str, str]) -> None:
    print("Available plot/action names:")
    for idx, action_name in enumerate(registry, start=1):
        print(f"  {idx:>2}. {format_action_option(action_name)}")


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
        for idx, log_name in enumerate(logs, start=1):
            print(f"  {idx:>2}. {format_log_option(group, log_name)}")


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
    log_options = [format_log_option(group, log_name) for log_name in logs]
    selected_log_indexes = prompt_for_indexes(
        f"Logs in {group}",
        log_options,
        "Select log numbers (example: 1,3-5 or all)",
        default_indexes=None,
        allow_all=True,
    )
    selected_logs = [logs[index] for index in selected_log_indexes]

    action_names = list(registry)
    action_options = [format_action_option(action_name) for action_name in action_names]
    selected_action_indexes = prompt_for_indexes(
        "Plots / Actions",
        action_options,
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

        if not action_names:
            print("INFO: no plots requested. Use --plot NAME or --list-plots.")
            return 0
        if not log_files:
            raise FileNotFoundError("No log files selected. Use --log or --interactive.")

        log_data = load_logs(log_files, group=group, strict=args.strict)
    except (FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))

    run_actions(log_data, action_names, registry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
