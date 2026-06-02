"""
fetch_opendengue.py
-------------------
Downloads Bangladesh national dengue case data from OpenDengue V1.3
(Clarke et al. 2024, Sci Data) and converts monthly totals to
approximate weekly epidemiological observations.

Source:
  Clarke J, Lim A, Gupte P, Pigott DM, van Panhuis WG, Brady OJ.
  OpenDengue: data from the OpenDengue database. Version 1.3. figshare; 2025.
  https://doi.org/10.6084/m9.figshare.24259573

License: CC-BY 4.0

Output: data/dengue_cases.csv
  Columns: epi_year, epi_week, dengue_cases, source
"""

import urllib.request
import zipfile
import io
import csv
import os
import math
import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_FILE  = os.path.join(DATA_DIR, "dengue_cases.csv")
RAW_FILE  = os.path.join(DATA_DIR, "opendengue_bangladesh_raw.csv")

ZIP_URL = (
    "https://github.com/OpenDengue/master-repo/raw/main"
    "/data/releases/V1.3/National_extract_V1_3.zip"
)

# Use 2014-2024: monthly resolution, meaningful surveillance data
START_YEAR = 2014
END_YEAR   = 2024


def download_raw() -> list[dict]:
    """Download OpenDengue national extract and return Bangladesh monthly rows."""
    print("  Fetching OpenDengue national extract (V1.3) ...")
    req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "DengueOps/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    print(f"  Downloaded {len(raw):,} bytes")

    zf = zipfile.ZipFile(io.BytesIO(raw))
    csv_name = next(f for f in zf.namelist() if f.endswith(".csv"))
    content = zf.read(csv_name).decode("utf-8")

    reader = csv.DictReader(io.StringIO(content))
    all_rows = list(reader)

    bd_monthly = [
        r for r in all_rows
        if r.get("adm_0_name", "") == "BANGLADESH"
        and r.get("T_res", "") == "Month"
        and START_YEAR <= int(r.get("Year", 0)) <= END_YEAR
        and r.get("dengue_total", "").strip() not in ("", "NA", "None")
    ]

    print(f"  Bangladesh monthly rows (2014-2024): {len(bd_monthly)}")
    return bd_monthly


def save_raw(rows: list[dict]) -> None:
    """Save raw Bangladesh monthly data for reference."""
    if not rows:
        return
    with open(RAW_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Raw data saved -> {RAW_FILE}")


def month_to_epi_weeks(
    year: int,
    month: int,
    monthly_total: float,
) -> list[dict]:
    """
    Distribute a monthly dengue total into ~4 weekly observations.

    Strategy:
    - Use ISO week numbers that fall within the calendar month.
    - Distribute cases proportionally by days in each week that
      overlap with the month.
    - Apply a seasonal shape multiplier (peaks mid-month) to avoid
      perfectly flat distribution — realistic for dengue reporting.
    """
    import calendar

    _, days_in_month = calendar.monthrange(year, month)
    first_day = datetime.date(year, month, 1)
    last_day  = datetime.date(year, month, days_in_month)

    # Collect all ISO weeks that have any day in this month
    week_buckets: dict[tuple[int, int], float] = {}
    current = first_day
    while current <= last_day:
        iso_year, iso_week, _ = current.isocalendar()
        week_buckets[(iso_year, iso_week)] = (
            week_buckets.get((iso_year, iso_week), 0) + 1
        )
        current += datetime.timedelta(days=1)

    total_days = sum(week_buckets.values())
    # Apply a mild mid-month peak shape (multipliers 0.9, 1.1, 1.1, 0.9)
    shapes = [0.9, 1.1, 1.1, 0.9]

    weeks_sorted = sorted(week_buckets.keys())
    result = []
    for i, (iso_y, iso_w) in enumerate(weeks_sorted):
        day_weight = week_buckets[(iso_y, iso_w)] / total_days
        shape = shapes[min(i, len(shapes) - 1)]
        cases = max(0, round(monthly_total * day_weight * shape))
        result.append({
            "epi_year":     iso_y,
            "epi_week":     iso_w,
            "dengue_cases": cases,
            "source":       "OpenDengue_V1.3_BGD_National",
        })
    return result


def convert_to_weekly(rows: list[dict]) -> list[dict]:
    """Convert monthly rows to weekly rows, deduplicating by (epi_year, epi_week)."""
    weekly: dict[tuple[int, int], dict] = {}

    for row in rows:
        total = float(row["dengue_total"])
        year  = int(row["Year"])
        # Parse month from calendar_start_date
        start_date = datetime.datetime.strptime(
            row["calendar_start_date"], "%Y-%m-%d"
        ).date()
        month = start_date.month

        for w in month_to_epi_weeks(year, month, total):
            key = (w["epi_year"], w["epi_week"])
            if key in weekly:
                # If same epi week appears from two months, sum cases
                weekly[key]["dengue_cases"] += w["dengue_cases"]
            else:
                weekly[key] = w

    # Sort chronologically
    sorted_weeks = sorted(weekly.values(), key=lambda r: (r["epi_year"], r["epi_week"]))
    return sorted_weeks


def week_to_date(epi_year: int, epi_week: int) -> str:
    """Return ISO date string for Monday of the given ISO week."""
    d = datetime.date.fromisocalendar(epi_year, epi_week, 1)
    return d.strftime("%Y-%m-%d")


def save_weekly(rows: list[dict]) -> None:
    """Save weekly dengue_cases.csv in the schema expected by feature_engineering.py.

    Required columns:
        epi_year, epi_week, date_start, city, cases, deaths, source
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    fieldnames = ["epi_year", "epi_week", "date_start", "city", "cases", "deaths", "source"]
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "epi_year":  r["epi_year"],
                "epi_week":  r["epi_week"],
                "date_start": week_to_date(r["epi_year"], r["epi_week"]),
                "city":      "Bangladesh (National)",
                "cases":     r["dengue_cases"],
                "deaths":    0,          # OpenDengue national extract does not include deaths separately
                "source":    r["source"],
            })
    print(f"  Weekly data saved -> {OUT_FILE}  ({len(rows)} weeks)")


def main() -> None:
    print("=" * 60)
    print("OpenDengue Bangladesh Data Fetch")
    print("Source: Clarke et al. 2024 | Sci Data | CC-BY 4.0")
    print("=" * 60)

    monthly_rows = download_raw()
    if not monthly_rows:
        print("ERROR: No Bangladesh monthly data found. Check network or year range.")
        return

    save_raw(monthly_rows)
    weekly_rows = convert_to_weekly(monthly_rows)

    print(f"  Converted to {len(weekly_rows)} weekly observations")
    print(f"  Date range: {weekly_rows[0]['epi_year']} W{weekly_rows[0]['epi_week']}"
          f" -> {weekly_rows[-1]['epi_year']} W{weekly_rows[-1]['epi_week']}")

    # Quick stats
    cases = [r["dengue_cases"] for r in weekly_rows]
    print(f"  Cases range: {min(cases)} - {max(cases)}")
    print(f"  Mean weekly cases: {sum(cases)/len(cases):.0f}")

    save_weekly(weekly_rows)

    print()
    print("OK - Real OpenDengue Bangladesh data written to data/dengue_cases.csv")
    print("This replaces the synthetic dengue_cases.csv with nationally reported data.")
    print()
    print("Citation:")
    print("  Clarke J, et al. OpenDengue: data from the OpenDengue database.")
    print("  Version 1.3. figshare; 2025. https://doi.org/10.6084/m9.figshare.24259573")
    print("=" * 60)


if __name__ == "__main__":
    main()
