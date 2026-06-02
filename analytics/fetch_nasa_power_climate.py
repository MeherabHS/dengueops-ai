"""
fetch_nasa_power_climate.py
===========================
DengueOps AI — NASA POWER Climate Data Integration

Downloads daily meteorological data for Dhaka South from the NASA POWER API
and aggregates it to ISO epidemiological weeks to produce data/climate_data.csv.

NASA POWER is a publicly available meteorological dataset from NASA Langley
Research Center. It is used here as a prototype climate input — not official
real-time climate surveillance.

Data source:
  NASA POWER Project (power.larc.nasa.gov)
  Community: Renewable Energy (RE)
  Variables: PRECTOTCORR, T2M, RH2M, T2M_MAX, T2M_MIN, QV2M

Output schema (must match feature_engineering.py contract):
  epi_year, epi_week, date_start, rainfall_mm, avg_temp_c, humidity_pct, source_type

Usage:
  python analytics/fetch_nasa_power_climate.py
      Use cached raw file if it exists; otherwise fetch from NASA POWER.

  python analytics/fetch_nasa_power_climate.py --force-refresh
      Ignore cache and re-fetch from NASA POWER.

  python analytics/fetch_nasa_power_climate.py --start 2014-01-01 --end 2024-12-31
      Custom date range (YYYY-MM-DD).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

# Optional import — checked at call site
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ── Constants ──────────────────────────────────────────────────────────────────

LATITUDE  = 23.7104   # Dhaka South centroid
LONGITUDE = 90.4074

DEFAULT_START = "2014-01-01"
DEFAULT_END   = "2024-12-31"

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Variables to request from NASA POWER
NASA_PARAMETERS = ",".join([
    "PRECTOTCORR",   # Precipitation Corrected (mm/day)
    "T2M",           # Temperature at 2 m (°C)
    "RH2M",          # Relative Humidity at 2 m (%)
    "T2M_MAX",       # Max temperature at 2 m (°C)
    "T2M_MIN",       # Min temperature at 2 m (°C)
    "QV2M",          # Specific humidity at 2 m (g/kg)
])

# ── Paths ──────────────────────────────────────────────────────────────────────

ROOT      = Path(__file__).resolve().parent.parent
DATA_DIR  = ROOT / "data"
RAW_DIR   = DATA_DIR / "raw"
OUT_CSV   = DATA_DIR / "climate_data.csv"
CACHE_CSV = RAW_DIR / "nasa_power_dhaka_south_daily_2014_2024.csv"
META_JSON = RAW_DIR / "nasa_power_dhaka_south_metadata.json"

# ── NASA POWER API ─────────────────────────────────────────────────────────────

def _fmt_date(d: str) -> str:
    """Convert YYYY-MM-DD to YYYYMMDD for NASA API."""
    return d.replace("-", "")


def fetch_from_nasa(start: str, end: str) -> pd.DataFrame:
    """
    Fetch daily data from NASA POWER API and return a DataFrame.
    Raises RuntimeError on failure.
    """
    if not _HAS_REQUESTS:
        raise RuntimeError(
            "The 'requests' package is required.\n"
            "Install it with:  pip install requests"
        )

    params: dict[str, Any] = {
        "latitude":   LATITUDE,
        "longitude":  LONGITUDE,
        "start":      _fmt_date(start),
        "end":        _fmt_date(end),
        "community":  "RE",
        "parameters": NASA_PARAMETERS,
        "format":     "JSON",
        "header":     "true",
        "time-standard": "UTC",
    }

    print(f"  Fetching NASA POWER daily data ({start} to {end}) ...")
    print(f"  Endpoint: {NASA_POWER_URL}")
    print(f"  Coordinates: {LATITUDE}N, {LONGITUDE}E")

    t0 = time.perf_counter()
    try:
        resp = requests.get(NASA_POWER_URL, params=params, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("NASA POWER API request timed out after 120 s.")
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"Could not connect to NASA POWER API: {e}")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"NASA POWER API returned HTTP error: {e}")

    elapsed = time.perf_counter() - t0
    print(f"  Response received in {elapsed:.1f}s  ({len(resp.content):,} bytes)")

    payload = resp.json()
    return _parse_nasa_response(payload)


def _parse_nasa_response(payload: dict) -> pd.DataFrame:
    """Parse the NASA POWER JSON response into a daily DataFrame."""
    try:
        props = payload["properties"]["parameter"]
    except KeyError as e:
        raise RuntimeError(f"Unexpected NASA POWER response structure: missing {e}")

    # NASA POWER returns date keys as YYYYMMDD strings
    # Build unified DataFrame across all variables
    date_keys: list[str] = sorted(props.get("T2M", {}).keys())

    if not date_keys:
        raise RuntimeError("NASA POWER response contains no data rows.")

    rows = []
    for dk in date_keys:
        # Skip any fill / header keys (NASA uses 13 = monthly aggregates)
        if len(dk) != 8 or not dk.isdigit():
            continue
        try:
            date = datetime.date(int(dk[:4]), int(dk[4:6]), int(dk[6:8]))
        except ValueError:
            continue

        row: dict[str, Any] = {"date": date}
        for var in ["PRECTOTCORR", "T2M", "RH2M", "T2M_MAX", "T2M_MIN", "QV2M"]:
            val = props.get(var, {}).get(dk, float("nan"))
            # NASA POWER uses -999 as a fill value
            row[var] = float("nan") if (isinstance(val, (int, float)) and val <= -998) else float(val)

        rows.append(row)

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── Cache helpers ──────────────────────────────────────────────────────────────

def save_raw_cache(df: pd.DataFrame, start: str, end: str) -> None:
    """Save raw daily data and metadata to the raw/ directory."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CACHE_CSV, index=False)
    print(f"  Raw data cached -> {CACHE_CSV}")

    meta = {
        "source":     "NASA POWER (power.larc.nasa.gov)",
        "community":  "RE (Renewable Energy)",
        "parameters": NASA_PARAMETERS,
        "latitude":   LATITUDE,
        "longitude":  LONGITUDE,
        "start_date": start,
        "end_date":   end,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rows":       len(df),
        "variables": {
            "PRECTOTCORR": "Precipitation Corrected (mm/day)",
            "T2M":         "Temperature at 2 m (C)",
            "RH2M":        "Relative Humidity at 2 m (%)",
            "T2M_MAX":     "Max Temperature at 2 m (C)",
            "T2M_MIN":     "Min Temperature at 2 m (C)",
            "QV2M":        "Specific Humidity at 2 m (g/kg)",
        },
        "note": (
            "NASA POWER data is used as a publicly available meteorological input "
            "for prototype modeling only. It is not official BMD surveillance data "
            "and has not been validated for real-time operational climate monitoring."
        ),
    }
    with open(META_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"  Metadata saved -> {META_JSON}")


def load_raw_cache() -> pd.DataFrame:
    """Load cached raw daily data."""
    print(f"  Loading cached raw data from {CACHE_CSV} ...")
    df = pd.read_csv(CACHE_CSV, parse_dates=["date"])
    print(f"  Loaded {len(df):,} rows from cache")
    return df


# ── Weekly aggregation ─────────────────────────────────────────────────────────

def _iso_week_monday(year: int, week: int) -> str:
    """Return the ISO date string for Monday of the given ISO year/week."""
    return datetime.date.fromisocalendar(year, week, 1).isoformat()


def aggregate_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert daily NASA POWER data to ISO epidemiological weekly records.

    Weekly aggregation:
      - rainfall_mm  = sum of PRECTOTCORR
      - avg_temp_c   = mean of T2M
      - humidity_pct = mean of RH2M

    Returns a DataFrame with the feature_engineering.py contract columns:
      epi_year, epi_week, date_start, rainfall_mm, avg_temp_c, humidity_pct, source_type
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Attach ISO week identifiers
    df["epi_year"] = df["date"].dt.isocalendar().year.astype(int)
    df["epi_week"] = df["date"].dt.isocalendar().week.astype(int)

    # Aggregate
    weekly = (
        df.groupby(["epi_year", "epi_week"], sort=True)
        .agg(
            rainfall_mm  = ("PRECTOTCORR", "sum"),
            avg_temp_c   = ("T2M",          "mean"),
            humidity_pct = ("RH2M",         "mean"),
        )
        .reset_index()
    )

    # Round
    weekly["rainfall_mm"]  = weekly["rainfall_mm"].round(2)
    weekly["avg_temp_c"]   = weekly["avg_temp_c"].round(2)
    weekly["humidity_pct"] = weekly["humidity_pct"].round(2)

    # date_start = Monday of each ISO week
    weekly["date_start"] = weekly.apply(
        lambda r: _iso_week_monday(int(r["epi_year"]), int(r["epi_week"])),
        axis=1,
    )

    # source_type tag
    weekly["source_type"] = "nasa_power"

    # Reorder to match feature_engineering.py contract exactly
    weekly = weekly[[
        "epi_year", "epi_week", "date_start",
        "rainfall_mm", "avg_temp_c", "humidity_pct",
        "source_type",
    ]]

    return weekly


# ── Output validation ──────────────────────────────────────────────────────────

REQUIRED_COLUMNS = {
    "epi_year", "epi_week", "date_start",
    "rainfall_mm", "avg_temp_c", "humidity_pct", "source_type",
}


def validate_weekly(df: pd.DataFrame) -> list[str]:
    """Return a list of validation error strings (empty = OK)."""
    errors: list[str] = []
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        errors.append(f"Missing columns: {sorted(missing)}")
    if df.empty:
        errors.append("Output DataFrame is empty.")
    if df["rainfall_mm"].isna().all():
        errors.append("rainfall_mm is all NaN.")
    if df["avg_temp_c"].isna().all():
        errors.append("avg_temp_c is all NaN.")
    if df["humidity_pct"].isna().all():
        errors.append("humidity_pct is all NaN.")
    return errors


# ── Entry point ────────────────────────────────────────────────────────────────

def _print_summary(df_daily: pd.DataFrame, df_weekly: pd.DataFrame, start: str, end: str) -> None:
    print()
    print("=" * 60)
    print("  NASA POWER Climate — Summary")
    print("=" * 60)
    print(f"  Source      : NASA POWER (power.larc.nasa.gov)")
    print(f"  Community   : RE (Renewable Energy)")
    print(f"  Coordinate  : {LATITUDE}N, {LONGITUDE}E  (Dhaka South)")
    print(f"  Date range  : {start} -> {end}")
    print(f"  Raw daily   : {len(df_daily):,} rows")
    print(f"  Weekly rows : {len(df_weekly):,}")
    if not df_weekly.empty:
        yr_min = df_weekly["epi_year"].min()
        yr_max = df_weekly["epi_year"].max()
        wk_first = df_weekly.iloc[0]
        wk_last  = df_weekly.iloc[-1]
        print(f"  Year range  : {yr_min} W{int(df_weekly.loc[df_weekly['epi_year']==yr_min,'epi_week'].min())}"
              f" -> {yr_max} W{int(df_weekly.loc[df_weekly['epi_year']==yr_max,'epi_week'].max())}")
        print(f"  Rain range  : {df_weekly['rainfall_mm'].min():.1f} – {df_weekly['rainfall_mm'].max():.1f} mm/week")
        print(f"  Temp range  : {df_weekly['avg_temp_c'].min():.1f} – {df_weekly['avg_temp_c'].max():.1f} °C")
        print(f"  Humidity    : {df_weekly['humidity_pct'].min():.1f} – {df_weekly['humidity_pct'].max():.1f} %")
    print(f"  Output file : {OUT_CSV}")
    print("=" * 60)
    print()
    print("  NOTE: NASA POWER data is a publicly available meteorological input")
    print("  for prototype modeling only. It is not official BMD data and has")
    print("  not been validated for real-time operational climate monitoring.")
    print()


def main(
    start: str = DEFAULT_START,
    end: str   = DEFAULT_END,
    force_refresh: bool = False,
) -> int:
    """
    Main entry point. Returns 0 on success, 1 on failure.
    """
    print()
    print("=" * 60)
    print("  DengueOps AI — NASA POWER Climate Data Fetch")
    print("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Get raw daily data ────────────────────────────────────────────
    df_daily: pd.DataFrame | None = None

    if not force_refresh and CACHE_CSV.exists():
        print(f"  Cache found at {CACHE_CSV.name} — skipping API fetch.")
        print("  Use --force-refresh to re-fetch from NASA POWER.")
        try:
            df_daily = load_raw_cache()
        except Exception as e:
            print(f"  [WARNING] Could not read cache: {e}")
            print("  Falling back to NASA POWER API ...")
            df_daily = None

    if df_daily is None:
        try:
            df_daily = fetch_from_nasa(start, end)
            save_raw_cache(df_daily, start, end)
        except RuntimeError as e:
            print(f"\n  [ERROR] {e}")
            if OUT_CSV.exists():
                print(f"\n  Existing {OUT_CSV.name} was NOT overwritten.")
            else:
                print(f"\n  No existing {OUT_CSV.name} to preserve.")
            return 1

    if df_daily is None or df_daily.empty:
        print("\n  [ERROR] No daily data available. Aborting.")
        return 1

    # ── Step 2: Aggregate to weekly ───────────────────────────────────────────
    print("  Aggregating daily data to ISO epidemiological weeks ...")
    df_weekly = aggregate_to_weekly(df_daily)
    print(f"  Weekly rows: {len(df_weekly)}")

    # ── Step 3: Validate ──────────────────────────────────────────────────────
    errors = validate_weekly(df_weekly)
    if errors:
        print("\n  [ERROR] Weekly output validation failed:")
        for e in errors:
            print(f"    - {e}")
        print("  Existing climate_data.csv was NOT overwritten.")
        return 1

    # ── Step 4: Save ──────────────────────────────────────────────────────────
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_weekly.to_csv(OUT_CSV, index=False)
    print(f"  Saved -> {OUT_CSV}")

    _print_summary(df_daily, df_weekly, start, end)
    return 0


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="fetch_nasa_power_climate.py",
        description="Fetch NASA POWER climate data for Dhaka South and produce weekly climate_data.csv.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analytics/fetch_nasa_power_climate.py
      Use cache if available; fetch if not.

  python analytics/fetch_nasa_power_climate.py --force-refresh
      Ignore cache and re-fetch from NASA POWER.

  python analytics/fetch_nasa_power_climate.py --start 2016-01-01 --end 2022-12-31
      Custom date range.

  python analytics/fetch_nasa_power_climate.py --force-refresh --start 2014-01-01 --end 2024-12-31
      Force re-fetch with explicit date range.
        """,
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Ignore existing cache and re-fetch from NASA POWER API.",
    )
    parser.add_argument(
        "--start",
        default=DEFAULT_START,
        metavar="YYYY-MM-DD",
        help=f"Start date (default: {DEFAULT_START}).",
    )
    parser.add_argument(
        "--end",
        default=DEFAULT_END,
        metavar="YYYY-MM-DD",
        help=f"End date (default: {DEFAULT_END}).",
    )

    args = parser.parse_args()

    # Basic date validation
    for label, val in [("--start", args.start), ("--end", args.end)]:
        try:
            datetime.date.fromisoformat(val)
        except ValueError:
            print(f"[ERROR] Invalid date for {label}: '{val}'. Expected YYYY-MM-DD.")
            sys.exit(1)

    if args.start >= args.end:
        print(f"[ERROR] --start ({args.start}) must be before --end ({args.end}).")
        sys.exit(1)

    sys.exit(main(start=args.start, end=args.end, force_refresh=args.force_refresh))
