#!/usr/bin/env python3
"""
Front desk duty scheduler.

Dependencies:
    pip install ortools pandas openpyxl jpholiday
"""
from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
from ortools.sat.python import cp_model

try:
    import jpholiday
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit("jpholiday is required. Install via 'pip install jpholiday'.") from exc


# ---- Configuration ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = INPUT_DIR
OUTPUT_FILE = OUTPUT_DIR / "schedule.xlsx"

TARGET_PERIOD = (
    date(2026, 1, 5),
    date(2026, 2, 28),
)  # <-- Update this tuple when the coverage period changes.

DEFAULT_GROUP_LIMIT = 1
GROUP_LIMIT_OVERRIDES = {
    "D": 2,  # Dグループは同時間帯2名まで
    "E": 1,  # Eグループは同時間帯1名まで（明示）
}
SHORTFALL_WEIGHT = 1000  # penalty weight to prioritize meeting slot demand
FAIRNESS_WEIGHT = 10
FRIDAY_WEIGHT = 3
AMP_PM_WEIGHT = 1
WEEKDAY_LABELS = ["月", "火", "水", "木", "金", "土", "日"]


# ---- Data containers -------------------------------------------------------

@dataclass(frozen=True)
class DayConfig:
    date: date
    am_slots: int
    pm_slots: int
    busy: int


# ---- Utility helpers -------------------------------------------------------

LOGGER = logging.getLogger("scheduler")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def ensure_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")


def parse_schedule_date(raw_value: str, fallback_year: int) -> date:
    """Parse flexible date strings such as '2025-01-05' or '1月5日'."""
    normalized = str(raw_value).strip()
    if not normalized:
        raise ValueError("Empty date value.")

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue

    match = re.search(r"(?P<month>\d{1,2})\D+(?P<day>\d{1,2})", normalized)
    if not match:
        raise ValueError(f"Unable to parse date string: {raw_value}")
    month = int(match.group("month"))
    day_num = int(match.group("day"))
    return date(fallback_year, month, day_num)


def parse_bool(value: object) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, (int, float)):
        return bool(int(value))
    text = str(value).strip().lower()
    if not text:
        return False
    return text in {"1", "true", "t", "yes", "y", "〇", "○"}


def parse_optional_bool(value: object) -> Optional[bool]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return parse_bool(text)


def is_working_day(target_date: date) -> bool:
    return target_date.weekday() < 5 and not jpholiday.is_holiday(target_date)


def build_group_limit_map(groups: Iterable[str]) -> Dict[str, int]:
    limits = {group: DEFAULT_GROUP_LIMIT for group in groups}
    limits.update(GROUP_LIMIT_OVERRIDES)
    return limits


def rookie_limit(slots: int) -> Optional[int]:
    if slots == 2:
        return 1
    if slots in (3, 4):
        return 2
    return None


# ---- Data loading ----------------------------------------------------------

def load_staff(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "staff.csv"
    ensure_file(path)
    df = pd.read_csv(path, dtype=str).fillna("")

    required = {"staff_id", "name", "group", "am_ok", "pm_ok", "year1"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"staff.csv is missing columns: {missing}")

    df["staff_id"] = pd.to_numeric(df["staff_id"], errors="coerce")
    if df["staff_id"].isna().any():
        raise ValueError("staff.csv contains invalid staff_id values.")

    if df["staff_id"].duplicated().any():
        duplicates = df[df["staff_id"].duplicated()]["staff_id"].tolist()
        raise ValueError(f"Duplicate staff_id detected: {duplicates}")

    df["staff_id"] = df["staff_id"].astype(int)
    df["group"] = df["group"].astype(str).str.strip()
    df["am_ok"] = df["am_ok"].apply(parse_bool)
    df["pm_ok"] = df["pm_ok"].apply(parse_bool)
    df["year1"] = df["year1"].apply(parse_bool)
    return df


def load_special_constraints(
    data_dir: Path, period: Tuple[date, date]
) -> pd.DataFrame:
    path = data_dir / "special_constraints.csv"
    if not path.exists():
        LOGGER.info("special_constraints.csv not found. Continuing without overrides.")
        return pd.DataFrame(columns=["staff_id", "date", "am_ok", "pm_ok", "note"])

    df = pd.read_csv(path, dtype=str).fillna("")
    expected = {"staff_id", "date"}
    if not expected.issubset(df.columns):
        LOGGER.warning(
            "special_constraints.csv does not match expected schema. Overrides ignored."
        )
        return pd.DataFrame(columns=["staff_id", "date", "am_ok", "pm_ok", "note"])

    df["staff_id"] = pd.to_numeric(df["staff_id"], errors="coerce")
    df = df.dropna(subset=["staff_id", "date"])
    if df.empty:
        return pd.DataFrame(columns=["staff_id", "date", "am_ok", "pm_ok", "note"])

    start, end = period
    df["staff_id"] = df["staff_id"].astype(int)
    df["date"] = df["date"].apply(lambda raw: parse_schedule_date(raw, start.year))
    df = df[(df["date"] >= start) & (df["date"] <= end)]

    for field in ("am_ok", "pm_ok"):
        if field not in df.columns:
            df[field] = ""

    df["am_override"] = df["am_ok"].apply(parse_optional_bool)
    df["pm_override"] = df["pm_ok"].apply(parse_optional_bool)
    if "note" not in df.columns:
        df["note"] = ""
    return df[["staff_id", "date", "am_override", "pm_override", "note"]]


def load_schedule_config(data_dir: Path, period: Tuple[date, date]) -> List[DayConfig]:
    path = data_dir / "schedule_config.csv"
    ensure_file(path)
    df = pd.read_csv(path, dtype=str).fillna("")

    required_cols = {"date", "am_slots", "pm_slots"}
    missing = required_cols.difference(df.columns)
    if missing:
        raise ValueError(f"schedule_config.csv is missing columns: {missing}")

    start, end = period
    df["parsed_date"] = df["date"].apply(lambda raw: parse_schedule_date(raw, start.year))
    df = df[(df["parsed_date"] >= start) & (df["parsed_date"] <= end)]
    if df.empty:
        raise ValueError("No schedule_config rows fall into the target period.")

    df = df.sort_values("parsed_date").drop_duplicates(subset="parsed_date", keep="last")
    df["am_slots"] = pd.to_numeric(df["am_slots"], errors="coerce").fillna(0).astype(int)
    df["pm_slots"] = pd.to_numeric(df["pm_slots"], errors="coerce").fillna(0).astype(int)
    if "busy" in df.columns:
        busy_series = df["busy"]
    else:
        busy_series = pd.Series([0] * len(df))
    df["busy"] = pd.to_numeric(busy_series, errors="coerce").fillna(0).astype(int)

    working_rows = [
        DayConfig(
            date=row.parsed_date,
            am_slots=int(row.am_slots),
            pm_slots=int(row.pm_slots),
            busy=int(row.busy),
        )
        for row in df.itertuples()
        if is_working_day(row.parsed_date)
    ]
    return working_rows


# ---- Scheduling core -------------------------------------------------------

def build_override_lookup(specials: pd.DataFrame) -> Dict[Tuple[int, date], Dict[str, Optional[bool]]]:
    lookup: Dict[Tuple[int, date], Dict[str, Optional[bool]]] = {}
    for row in specials.itertuples():
        lookup[(row.staff_id, row.date)] = {
            "AM": row.am_override,
            "PM": row.pm_override,
            "note": row.note,
        }
    return lookup


def build_availability_map(
    staff_df: pd.DataFrame,
    days: List[DayConfig],
    overrides: Dict[Tuple[int, date], Dict[str, Optional[bool]]],
) -> Dict[Tuple[int, date, str], bool]:
    availability: Dict[Tuple[int, date, str], bool] = {}
    for row in staff_df.itertuples():
        for day_conf in days:
            override = overrides.get((row.staff_id, day_conf.date), {})
            for period, base_flag in (("AM", row.am_ok), ("PM", row.pm_ok)):
                availability[(row.staff_id, day_conf.date, period)] = bool(
                    override.get(period, base_flag)
                )
    return availability


def solve_schedule(
    staff_df: pd.DataFrame,
    day_configs: List[DayConfig],
    specials_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[Tuple[date, str], int]]:
    if not day_configs:
        raise ValueError("No working days available to schedule.")

    overrides = build_override_lookup(specials_df)
    availability = build_availability_map(staff_df, day_configs, overrides)
    staff_ids = staff_df["staff_id"].tolist()
    staff_meta = staff_df.set_index("staff_id").to_dict(orient="index")
    new_staff_ids = {
        sid for sid, row in staff_meta.items() if row.get("year1", False)
    }
    experienced_staff_ids = set(staff_ids) - new_staff_ids
    flex_staff_ids = [
        sid
        for sid, row in staff_meta.items()
        if row.get("am_ok", False) and row.get("pm_ok", False)
    ]
    group_limits = build_group_limit_map(staff_df["group"].unique())
    period_labels = ("AM", "PM")
    rookie_risk_warnings: List[str] = []

    model = cp_model.CpModel()
    assignment_vars: Dict[Tuple[int, date, str], cp_model.IntVar] = {}
    shortfall_vars: Dict[Tuple[date, str], cp_model.IntVar] = {}
    day_assignment_vars: Dict[Tuple[int, date], cp_model.IntVar] = {}

    max_slots = max(
        max((cfg.am_slots for cfg in day_configs), default=0),
        max((cfg.pm_slots for cfg in day_configs), default=0),
    )

    for day_conf in day_configs:
        for period, required_slots in zip(period_labels, (day_conf.am_slots, day_conf.pm_slots)):
            terms = []
            for staff_id in staff_ids:
                if availability.get((staff_id, day_conf.date, period), False):
                    var = model.NewBoolVar(
                        f"x_s{staff_id}_{day_conf.date.isoformat()}_{period.lower()}"
                    )
                    assignment_vars[(staff_id, day_conf.date, period)] = var
                    terms.append(var)
                else:
                    assignment_vars[(staff_id, day_conf.date, period)] = None

            slack = model.NewIntVar(
                0,
                max(required_slots, max_slots),
                f"slack_{day_conf.date.isoformat()}_{period.lower()}",
            )
            shortfall_vars[(day_conf.date, period)] = slack
            model.Add(sum(terms) + slack == required_slots)

            rookie_cap = rookie_limit(required_slots)
            if rookie_cap is not None and new_staff_ids:
                rookie_vars = [
                    assignment_vars[(staff_id, day_conf.date, period)]
                    for staff_id in new_staff_ids
                    if assignment_vars[(staff_id, day_conf.date, period)] is not None
                ]
                if rookie_vars:
                    model.Add(sum(rookie_vars) <= rookie_cap)
                experienced_needed = max(0, required_slots - rookie_cap)
                available_experienced = [
                    assignment_vars[(staff_id, day_conf.date, period)]
                    for staff_id in experienced_staff_ids
                    if assignment_vars[(staff_id, day_conf.date, period)] is not None
                ]
                if len(available_experienced) < experienced_needed:
                    warning_msg = (
                        f"Insufficient experienced staff for {day_conf.date} {period}: "
                        f"need {experienced_needed}, have {len(available_experienced)}."
                    )
                    LOGGER.warning(warning_msg)
                    rookie_risk_warnings.append(warning_msg)

    # Daily assignment indicators (1 if the staff works at least once that day)
    for day_conf in day_configs:
        for staff_id in staff_ids:
            day_var = model.NewBoolVar(
                f"day_s{staff_id}_{day_conf.date.isoformat()}"
            )
            day_assignment_vars[(staff_id, day_conf.date)] = day_var
            period_vars = [
                assignment_vars[(staff_id, day_conf.date, period)]
                for period in period_labels
                if assignment_vars[(staff_id, day_conf.date, period)] is not None
            ]
            if not period_vars:
                model.Add(day_var == 0)
                continue
            for var in period_vars:
                model.Add(var <= day_var)
            model.Add(day_var <= sum(period_vars))
            model.Add(sum(period_vars) <= 1)

    # Group capacity constraints
    for day_conf in day_configs:
        for period in period_labels:
            for group_name, limit in group_limits.items():
                vars_in_group = [
                    assignment_vars[(staff_id, day_conf.date, period)]
                    for staff_id in staff_ids
                    if staff_meta[staff_id]["group"] == group_name
                    and assignment_vars[(staff_id, day_conf.date, period)] is not None
                ]
                if vars_in_group:
                    model.Add(sum(vars_in_group) <= limit)

    # Minimum spacing: once assigned, skip the next two working days
    working_dates = [cfg.date for cfg in day_configs]
    for staff_id in staff_ids:
        for i, day_i in enumerate(working_dates):
            var_i = day_assignment_vars[(staff_id, day_i)]
            for j in range(i + 1, min(i + 3, len(working_dates))):
                day_j = working_dates[j]
                var_j = day_assignment_vars[(staff_id, day_j)]
                model.Add(var_i + var_j <= 1)

    # Total assignment variables per staff
    max_daily_periods = len(day_configs) * len(period_labels)
    totals: Dict[int, cp_model.IntVar] = {}
    pm_only_ids: List[int] = [
        sid for sid, row in staff_meta.items() if not row.get("pm_ok", False)
    ]

    for staff_id in staff_ids:
        vars_for_staff = [
            var
            for (sid, _, _), var in assignment_vars.items()
            if sid == staff_id and var is not None
        ]
        total_var = model.NewIntVar(0, max_daily_periods, f"total_s{staff_id}")
        if vars_for_staff:
            model.Add(total_var == sum(vars_for_staff))
        else:
            model.Add(total_var == 0)
        totals[staff_id] = total_var
        if staff_id in pm_only_ids:
            model.Add(total_var >= 7)
            model.Add(total_var <= 8)

    max_count = model.NewIntVar(0, max_daily_periods, "max_assignments")
    min_count = model.NewIntVar(0, max_daily_periods, "min_assignments")

    for total in totals.values():
        model.Add(total <= max_count)
        model.Add(total >= min_count)

    fairness_gap = model.NewIntVar(0, max_daily_periods, "fairness_gap")
    model.Add(fairness_gap == max_count - min_count)

    ampm_diff_vars: List[cp_model.IntVar] = []
    for staff_id in flex_staff_ids:
        am_vars = [
            assignment_vars[(staff_id, day_conf.date, "AM")]
            for day_conf in day_configs
            if assignment_vars[(staff_id, day_conf.date, "AM")] is not None
        ]
        pm_vars = [
            assignment_vars[(staff_id, day_conf.date, "PM")]
            for day_conf in day_configs
            if assignment_vars[(staff_id, day_conf.date, "PM")] is not None
        ]
        am_total = model.NewIntVar(0, len(day_configs), f"am_total_s{staff_id}")
        pm_total = model.NewIntVar(0, len(day_configs), f"pm_total_s{staff_id}")
        if am_vars:
            model.Add(am_total == sum(am_vars))
        else:
            model.Add(am_total == 0)
        if pm_vars:
            model.Add(pm_total == sum(pm_vars))
        else:
            model.Add(pm_total == 0)
        diff_var = model.NewIntVar(0, len(day_configs), f"ampm_diff_s{staff_id}")
        model.Add(am_total - pm_total <= diff_var)
        model.Add(pm_total - am_total <= diff_var)
        ampm_diff_vars.append(diff_var)

    friday_dates = [cfg.date for cfg in day_configs if cfg.date.weekday() == 4]
    if friday_dates:
        max_fridays = len(friday_dates)
        max_fri = model.NewIntVar(0, max_fridays, "max_friday_assignments")
        min_fri = model.NewIntVar(0, max_fridays, "min_friday_assignments")
        friday_gap = model.NewIntVar(0, max_fridays, "friday_gap")
        for staff_id in staff_ids:
            vars_for_fri = [
                day_assignment_vars[(staff_id, shift_date)] for shift_date in friday_dates
            ]
            total_fri = model.NewIntVar(0, max_fridays, f"friday_total_s{staff_id}")
            if vars_for_fri:
                model.Add(total_fri == sum(vars_for_fri))
            else:
                model.Add(total_fri == 0)
            model.Add(total_fri <= max_fri)
            model.Add(total_fri >= min_fri)
        model.Add(friday_gap == max_fri - min_fri)
    else:
        friday_gap = model.NewIntVar(0, 0, "friday_gap")
        model.Add(friday_gap == 0)

    total_shortfall = model.NewIntVar(
        0, max_daily_periods * max(max_slots, 1), "total_shortfall"
    )
    if shortfall_vars:
        model.Add(total_shortfall == sum(shortfall_vars.values()))
    else:
        model.Add(total_shortfall == 0)

    ampm_diff_sum = sum(ampm_diff_vars) if ampm_diff_vars else 0

    model.Minimize(
        SHORTFALL_WEIGHT * total_shortfall
        + FAIRNESS_WEIGHT * fairness_gap
        + FRIDAY_WEIGHT * friday_gap
        + AMP_PM_WEIGHT * ampm_diff_sum
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if rookie_risk_warnings:
            LOGGER.error(
                "Rookie constraint warnings prior to infeasible solve:\n%s",
                "\n".join(rookie_risk_warnings),
            )
        if pm_only_ids:
            LOGGER.error(
                "Afternoon-restricted staff could not satisfy the 7-8 assignment range."
            )
        raise RuntimeError(f"Solver failed with status: {solver.StatusName(status)}")

    records: List[Dict[str, object]] = []
    shortfalls: Dict[Tuple[date, str], int] = {}
    for day_conf in day_configs:
        busy_flag = day_conf.busy
        weekday = WEEKDAY_LABELS[day_conf.date.weekday()]
        for period in period_labels:
            shortfall = int(solver.Value(shortfall_vars[(day_conf.date, period)]))
            if shortfall:
                shortfalls[(day_conf.date, period)] = shortfall
            for staff_id in staff_ids:
                var = assignment_vars[(staff_id, day_conf.date, period)]
                if var is None:
                    continue
                if solver.Value(var):
                    meta = staff_meta[staff_id]
                    records.append(
                        {
                            "date": day_conf.date.isoformat(),
                            "weekday": weekday,
                            "period": period,
                            "staff_id": staff_id,
                            "name": meta["name"],
                            "group": meta["group"],
                            "busy": busy_flag,
                        }
                    )

    schedule_df = pd.DataFrame(records).sort_values(
        ["date", "period", "group", "staff_id"]
    )
    return schedule_df, shortfalls


# ---- Output ----------------------------------------------------------------

def save_schedule(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    def _write(path: Path) -> None:
        if path.suffix.lower() == ".xlsx":
            df.to_excel(path, index=False)
        else:
            df.to_csv(path, index=False, encoding="utf-8-sig")

    try:
        _write(output_path)
        LOGGER.info("Schedule written to %s", output_path)
    except PermissionError:
        fallback = output_path.with_name(
            f"{output_path.stem}_{datetime.now():%Y%m%d_%H%M%S}{output_path.suffix}"
        )
        LOGGER.warning(
            "Primary output %s was locked. Writing to fallback %s.",
            output_path,
            fallback,
        )
        _write(fallback)


def log_shortfalls(shortfalls: Dict[Tuple[date, str], int]) -> None:
    if not shortfalls:
        LOGGER.info("All days fully assigned.")
        return
    for (shift_date, period), missing in shortfalls.items():
        LOGGER.warning(
            "Shortfall detected: %s %s (%d slot(s) unassigned)",
            shift_date.isoformat(),
            period,
            missing,
        )


def summarize_assignments(schedule_df: pd.DataFrame) -> None:
    if schedule_df.empty:
        LOGGER.warning("No assignments were produced.")
        return
    summary = (
        schedule_df.groupby(["staff_id", "name"])["period"]
        .count()
        .reset_index(name="assignments")
        .sort_values("assignments", ascending=False)
    )
    LOGGER.info("Top 5 assignment counts:\n%s", summary.head().to_string(index=False))


# ---- Entrypoint ------------------------------------------------------------

def main() -> None:
    configure_logging()
    try:
        staff_df = load_staff(DATA_DIR)
        specials_df = load_special_constraints(DATA_DIR, TARGET_PERIOD)
        day_configs = load_schedule_config(DATA_DIR, TARGET_PERIOD)
        schedule_df, shortfalls = solve_schedule(staff_df, day_configs, specials_df)
        save_schedule(schedule_df, OUTPUT_FILE)
        summarize_assignments(schedule_df)
        log_shortfalls(shortfalls)
    except Exception as exc:  # pragma: no cover - safety net
        LOGGER.exception("Scheduling failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()


