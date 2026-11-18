"""Validate KKBox source-to-DuckDB row counts"""

import csv
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "saas_revenue.duckdb"

SOURCES = {
    "transactions_v2.csv": "raw.transactions_v2",
    "members_v3.csv": "raw.members_v3",
    "train_v2.csv": "raw.train_v2",
}


def count_csv_rows(path: Path) -> int:
    """Count CSV records without loading the file in memory."""
    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.reader(file)
        next(reader)
        return sum(1 for _ in reader)


def main() -> None:
    if not DB_PATH.is_file():
        raise FileNotFoundError(DB_PATH)

    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        print("=" * 60)
        print("KKBOX SOURCE-TO-TARGET RECONCILIATION")
        print("=" * 60)

        for filename, table in SOURCES.items():
            csv_path = RAW_DIR / filename

            if not csv_path.is_file():
                raise FileNotFoundError(csv_path)

            source_count = count_csv_rows(csv_path)

            result = con.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()

            if result is None:
                raise RuntimeError(
                    f"No result returned for {table}"
                )

            target_count = result[0]

            status = (
                "PASS"
                if source_count == target_count
                else "FAIL"
            )

            print(f"\n{filename}")
            print(f"Source records: {source_count:,}")
            print(f"DuckDB records: {target_count:,}")
            print(f"Status: {status}")

            if source_count != target_count:
                raise AssertionError(
                    f"Row-count mismatch for {table}"
                )

        print("\nAll source-to-target row counts reconciled")

    finally:
        con.close()


if __name__ == "__main__":
    main()
