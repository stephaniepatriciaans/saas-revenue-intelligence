"""Inspect the KKBox transactions source dataset
Reads a small sample without loading the full CSV
Does not modify the raw data
"""

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "transactions_v2.csv"
)

SAMPLE_SIZE = 5


def main():
    if not CSV_PATH.is_file():
        raise FileNotFoundError(
            f"Transactions file not found: {CSV_PATH}"
        )

    print("=" * 60)
    print("KKBOX TRANSACTIONS — SOURCE PROFILING")
    print("=" * 60)

    print(f"\nFile: {CSV_PATH.name}")
    print(f"File size: {CSV_PATH.stat().st_size / 1024**2:.2f} MiB")

    with CSV_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        columns = reader.fieldnames

        if not columns:
            raise ValueError("CSV has no header")

        print("\nSOURCE COLUMNS")
        for index, column in enumerate(columns, start=1):
            print(f"{index:2}. {column}")

        rows = []

        for index, row in enumerate(reader):
            if index >= SAMPLE_SIZE:
                break
            rows.append(row)

    print(f"\nFIRST {len(rows)} RECORDS")

    for index, row in enumerate(rows, start=1):
        print(f"\nRecord {index}")

        for column in columns:
            value = row.get(column)
            print(f"  {column}: {value}")

    print("\nSAMPLE MISSING VALUES")

    for column in columns:
        missing = sum(
            row.get(column) is None
            or str(row.get(column)).strip() == ""
            for row in rows
        )

        print(f"{column}: {missing}/{len(rows)}")

    print("\nProfiling completed successfully")


if __name__ == "__main__":
    main()
