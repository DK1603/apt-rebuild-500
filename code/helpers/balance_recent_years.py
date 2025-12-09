"""
Balance 2022/2023 coverage by downloading additional valid PDFs
while keeping the overall dataset at 500 reports.
"""

import random
import time
from pathlib import Path

import pandas as pd
import requests
from PyPDF2 import PdfReader
from tqdm import tqdm

# Configuration
FULL_CSV = "code/Technical_Report_Collection.csv"
CURRENT_CSV = "ArticlesDataset_500_Valid.csv"
OUTPUT_CSV = "ArticlesDataset_500_Valid.csv"
BASE_DIR = Path("Reports/APT_CyberCriminal_Campagin_Collections Reports")
YEARS_TO_BALANCE = {2022: 45, 2023: 25}
TARGET_TOTAL = 500
MIN_SIZE_KB = 50
TIMEOUT = 60
RANDOM_SEED = 1337


def sanitize_filename(filename: str) -> str:
    """Ensure filenames are filesystem-safe and end with .pdf"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    return filename


def check_pdf_valid(pdf_path: Path) -> tuple[bool, str]:
    """Validate a PDF by size and parseability."""
    try:
        if not pdf_path.exists():
            return False, "Missing file"

        size_kb = pdf_path.stat().st_size / 1024
        if size_kb < MIN_SIZE_KB:
            return False, f"Too small ({size_kb:.1f} KB)"

        reader = PdfReader(str(pdf_path))
        if len(reader.pages) == 0:
            return False, "Zero pages"

        _ = reader.pages[0].extract_text()  # smoke test
        return True, "Valid"
    except Exception as exc:  # noqa: BLE001
        return False, f"Error: {str(exc)[:40]}"


def download_and_validate(url: str, dest_path: Path) -> tuple[bool, bool, str]:
    """Download a PDF and validate immediately."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=TIMEOUT, headers=headers, stream=True)

        if response.status_code == 404:
            return False, False, "404 not found"
        if response.status_code != 200:
            return False, False, f"HTTP {response.status_code}"

        with open(dest_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)

        is_valid, msg = check_pdf_valid(dest_path)
        if not is_valid and dest_path.exists():
            dest_path.unlink()
        return True, is_valid, msg
    except requests.Timeout:
        return False, False, "Timeout"
    except Exception as exc:  # noqa: BLE001
        return False, False, f"Error: {str(exc)[:40]}"


def compute_expected_counts(df_original: pd.DataFrame) -> dict[int, int]:
    """Scale original distribution down to TARGET_TOTAL with unbiased rounding."""
    counts = (
        pd.to_datetime(df_original["Date"]).dt.year.value_counts().sort_index()
    )
    total = counts.sum()

    raw_expected: dict[int, int] = {}
    remainders: list[tuple[float, int]] = []
    running_total = 0

    for year, count in counts.items():
        exact = count / total * TARGET_TOTAL
        floored = int(exact)
        raw_expected[year] = floored
        remainders.append((exact - floored, year))
        running_total += floored

    remainder = TARGET_TOTAL - running_total
    remainders.sort(reverse=True)
    idx = 0
    while remainder > 0 and idx < len(remainders):
        _, year = remainders[idx]
        raw_expected[year] += 1
        remainder -= 1
        idx += 1

    return raw_expected


def drop_surplus_rows(
    df: pd.DataFrame, expected_counts: dict[int, int], rng: random.Random
) -> pd.DataFrame:
    """Remove rows from over-represented years to match expected counts."""
    df = df.copy()
    df["Year"] = pd.to_datetime(df["Date"]).dt.year

    to_drop = []
    for year, group in df.groupby("Year"):
        allowed = expected_counts.get(year, 0)
        excess = len(group) - allowed
        if excess > 0:
            drop_idx = rng.sample(list(group.index), k=excess)
            to_drop.extend(drop_idx)

    if to_drop:
        df = df.drop(index=to_drop)

    return df.drop(columns=["Year"])


def main():
    print("=" * 70)
    print("Balancing 2022/2023 coverage")
    print("=" * 70)

    df_current = pd.read_csv(CURRENT_CSV)
    df_current["Year"] = pd.to_datetime(df_current["Date"]).dt.year
    current_counts = df_current["Year"].value_counts().sort_index()

    df_original = pd.read_csv(FULL_CSV)
    expected_counts = compute_expected_counts(df_original)

    print("\nTarget counts (scaled from full dataset):")
    for year in sorted(expected_counts):
        marker = "<-- focus" if year in YEARS_TO_BALANCE else ""
        print(f"  {year}: {expected_counts[year]:3d} {marker}")

    deficits: dict[int, int] = {}
    for year, target in YEARS_TO_BALANCE.items():
        current = current_counts.get(year, 0)
        need = max(0, target - current)
        deficits[year] = need

    total_needed = sum(deficits.values())
    if total_needed == 0:
        print("\n✅ 2022/2023 already at desired levels.")
    else:
        print(f"\nNeed {total_needed} additional reports for late years:")
        for year, need in deficits.items():
            if need > 0:
                print(f"  - {year}: +{need}")
        df_original["Year"] = pd.to_datetime(df_original["Date"]).dt.year
        current_files = set(df_current["Filename"].tolist())
        new_rows = []
        rng = random.Random(RANDOM_SEED)

        for year, need in deficits.items():
            if need <= 0:
                continue

            print(f"\nFetching {need} valid PDFs for {year}...")
            year_candidates = df_original[
                (df_original["Year"] == year)
                & (~df_original["Filename"].isin(current_files))
            ].copy()

            if year_candidates.empty:
                print(f"  ⚠️ No unused candidates left for {year}")
                continue

            year_candidates = year_candidates.sample(
                frac=1, random_state=RANDOM_SEED + year
            ).reset_index(drop=True)

            collected = 0
            stats = {"downloaded": 0, "valid": 0, "invalid": 0, "failed": 0}

            for _, row in tqdm(
                year_candidates.iterrows(),
                total=len(year_candidates),
                desc=f"{year} candidates",
                unit="pdf",
            ):
                if collected >= need:
                    break

                filename = row["Filename"]
                url = row["Download Url"]
                dest_dir = BASE_DIR / str(year)
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / sanitize_filename(filename)

                # re-validate if already downloaded earlier
                if dest_path.exists():
                    is_valid, msg = check_pdf_valid(dest_path)
                    if is_valid:
                        new_rows.append(row)
                        current_files.add(filename)
                        collected += 1
                        stats["valid"] += 1
                        continue
                    dest_path.unlink()

                downloaded, valid, msg = download_and_validate(url, dest_path)
                if downloaded:
                    stats["downloaded"] += 1
                    if valid:
                        new_rows.append(row)
                        current_files.add(filename)
                        collected += 1
                        stats["valid"] += 1
                    else:
                        stats["invalid"] += 1
                else:
                    stats["failed"] += 1

                time.sleep(0.3)

            print(
                f"  Added {collected}/{need} valid PDFs "
                f"(downloaded {stats['downloaded']}, invalid {stats['invalid']}, failed {stats['failed']})"
            )

        if not new_rows:
            print("\n❌ Could not add any new late-year reports.")
            return

        df_new = pd.DataFrame(new_rows)
        df_current = pd.concat(
            [df_current.drop(columns=["Year"]), df_new], ignore_index=True
        )

    # Recompute counts and drop surplus rows from early years
    df_balanced = drop_surplus_rows(
        df_current, expected_counts=expected_counts, rng=random.Random(RANDOM_SEED)
    )

    df_balanced.to_csv(OUTPUT_CSV, index=False)

    df_balanced["Year"] = pd.to_datetime(df_balanced["Date"]).dt.year
    final_counts = df_balanced["Year"].value_counts().sort_index()

    print("\nFinal distribution after balancing:")
    for year in sorted(final_counts.index):
        actual = final_counts[year]
        target = expected_counts.get(year, 0)
        delta = actual - target
        symbol = "=" if delta == 0 else (">" if delta > 0 else "<")
        print(f"  {year}: {actual:3d} (target {target:3d}) {symbol} delta {delta:+d}")

    print(f"\nUpdated dataset saved to {OUTPUT_CSV}")
    print(f"   Total records: {len(df_balanced)}")
    if len(df_balanced) != TARGET_TOTAL:
        print("   Warning: could not hit exact target due to limited valid candidates.")

    print("\nNext: run `python verify_distribution.py --selected ArticlesDataset_500_Valid.csv`")
    print("=" * 70)


if __name__ == "__main__":
    main()

